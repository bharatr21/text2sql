"""
LangGraph-based conversation summarization agent for context management.
"""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from ..core.logging import LoggerMixin
from ..services.llm_service import LLMService


class SummarizationState(TypedDict):
    """State for the summarization agent graph."""

    messages: List[Dict[str, Any]]
    session_id: str
    existing_summary: Optional[str]
    new_summary: Optional[str]
    error: Optional[str]


class SummarizationAgent(LoggerMixin):
    """LangGraph-based conversation summarization agent."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for summarization."""

        workflow = StateGraph(SummarizationState)

        # Add nodes
        workflow.add_node("prepare_content", self._prepare_content)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("finalize_summary", self._finalize_summary)

        # Define edges
        workflow.set_entry_point("prepare_content")
        workflow.add_edge("prepare_content", "generate_summary")
        workflow.add_edge("generate_summary", "finalize_summary")
        workflow.add_edge("finalize_summary", END)

        return workflow.compile()

    async def _prepare_content(self, state: SummarizationState) -> SummarizationState:
        """Prepare conversation content for summarization."""
        self.logger.info("Preparing content for summarization", session_id=state["session_id"])

        try:
            # Filter out system messages and prepare conversation text
            conversation_messages = [
                msg for msg in state["messages"]
                if msg.get("role") in ["human", "ai"]
            ]

            if not conversation_messages:
                state["error"] = "No conversation messages to summarize"
                return state

            self.logger.info(
                "Prepared conversation content",
                session_id=state["session_id"],
                message_count=len(conversation_messages)
            )

        except Exception as e:
            self.logger.error("Failed to prepare content", error=str(e), session_id=state["session_id"])
            state["error"] = f"Failed to prepare content: {str(e)}"

        return state

    async def _generate_summary(self, state: SummarizationState) -> SummarizationState:
        """Generate conversation summary using LLM."""
        if state.get("error"):
            return state

        self.logger.info("Generating conversation summary", session_id=state["session_id"])

        try:
            # Build conversation text
            conversation_messages = [
                msg for msg in state["messages"]
                if msg.get("role") in ["human", "ai"]
            ]

            conversation_text = ""
            for msg in conversation_messages:
                role = "User" if msg["role"] == "human" else "Assistant"
                conversation_text += f"{role}: {msg['content']}\n"

            # Create summarization prompt
            if state.get("existing_summary"):
                # Progressive summarization
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_progressive_summary_prompt()),
                    ("human", "Previous summary:\n{existing_summary}\n\nNew conversation:\n{conversation}\n\nGenerate updated summary:")
                ])

                messages = await prompt.aformat_messages(
                    existing_summary=state["existing_summary"],
                    conversation=conversation_text
                )
            else:
                # Initial summarization
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_initial_summary_prompt()),
                    ("human", "Conversation to summarize:\n{conversation}\n\nGenerate summary:")
                ])

                messages = await prompt.aformat_messages(conversation=conversation_text)

            # Generate summary using LLM
            response = await self.llm_service.ainvoke(messages)
            state["new_summary"] = response.content.strip()

            self.logger.info(
                "Generated conversation summary",
                session_id=state["session_id"],
                summary_length=len(state["new_summary"])
            )

        except Exception as e:
            self.logger.error("Failed to generate summary", error=str(e), session_id=state["session_id"])
            state["error"] = f"Failed to generate summary: {str(e)}"

        return state

    async def _finalize_summary(self, state: SummarizationState) -> SummarizationState:
        """Finalize the summarization process."""
        if state.get("error"):
            return state

        self.logger.info("Finalizing conversation summary", session_id=state["session_id"])

        try:
            # Validate summary
            if not state.get("new_summary"):
                state["error"] = "No summary was generated"
                return state

            # Ensure summary is reasonable length (not too short or too long)
            summary_length = len(state["new_summary"])
            if summary_length < 20:
                self.logger.warning("Generated summary is very short", summary_length=summary_length)
            elif summary_length > 1000:
                self.logger.warning("Generated summary is very long", summary_length=summary_length)

            self.logger.info(
                "Conversation summary finalized",
                session_id=state["session_id"],
                final_summary_length=summary_length
            )

        except Exception as e:
            self.logger.error("Failed to finalize summary", error=str(e), session_id=state["session_id"])
            state["error"] = f"Failed to finalize summary: {str(e)}"

        return state

    def _get_initial_summary_prompt(self) -> str:
        """Get the initial summarization system prompt."""
        return """You are an expert at summarizing SQL database conversations. Your task is to create a concise but comprehensive summary of the conversation.

Focus on:
1. What data the user was exploring (tables, datasets, domains)
2. Key questions asked and patterns of inquiry
3. Important findings, insights, or results discovered
4. Any specific metrics, comparisons, or analyses performed
5. Context that would be helpful for continuing the conversation

Guidelines:
- Keep the summary between 100-300 words
- Be specific about database tables and data domains mentioned
- Include key numerical findings or trends if any
- Maintain the chronological flow of the conversation
- Use clear, professional language
- Focus on factual information rather than opinions

Generate a summary that would allow someone to understand the conversation context and continue meaningfully."""

    def _get_progressive_summary_prompt(self) -> str:
        """Get the progressive summarization system prompt."""
        return """You are updating an existing conversation summary with new information. Your task is to create a comprehensive summary that incorporates both the previous summary and new conversation content.

Guidelines:
- Integrate new information with the existing summary
- Remove outdated or superseded information
- Maintain focus on data exploration patterns and findings
- Keep the updated summary between 100-400 words
- Preserve important context from both old and new content
- Ensure the summary flows logically and chronologically
- Highlight any new insights or data domains explored
- Maintain specificity about tables, metrics, and findings

Create an updated summary that captures the full scope of the conversation while emphasizing the most recent developments."""

    async def summarize_conversation(
        self,
        messages: List[Dict[str, Any]],
        session_id: str,
        existing_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Summarize a conversation using the LangGraph agent."""
        self.logger.info("Starting conversation summarization", session_id=session_id)

        # Initial state
        initial_state = SummarizationState(
            messages=messages,
            session_id=session_id,
            existing_summary=existing_summary,
            new_summary=None,
            error=None,
        )

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        # Return results
        result = {
            "summary": final_state.get("new_summary"),
            "error": final_state.get("error"),
            "success": final_state.get("new_summary") is not None and final_state.get("error") is None,
        }

        if result["success"]:
            self.logger.info("Conversation summarization completed", session_id=session_id)
        else:
            self.logger.error("Conversation summarization failed", session_id=session_id, error=result["error"])

        return result