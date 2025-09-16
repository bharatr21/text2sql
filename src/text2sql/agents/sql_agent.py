"""
LangGraph-based SQL agent for natural language to SQL conversion.
"""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from ..core.logging import LoggerMixin
from ..services.llm_service import LLMService
from ..services.session_service import SessionService


class SQLAgentState(TypedDict):
    """State for the SQL agent graph."""

    messages: List[BaseMessage]
    question: str
    session_id: str
    sql_query: Optional[str]
    query_results: Optional[Any]
    error: Optional[str]
    table_info: Optional[str]
    execution_time: Optional[float]


class SQLAgent(LoggerMixin):
    """LangGraph-based SQL agent."""

    def __init__(
        self,
        database: SQLDatabase,
        llm_service: LLMService,
        session_service: SessionService,
        max_rows: int = 100,
    ):
        self.database = database
        self.llm_service = llm_service
        self.session_service = session_service
        self.max_rows = max_rows

        # SQL execution tool
        self.sql_tool = QuerySQLDataBaseTool(db=self.database)

        # Build the agent graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""

        # Define the graph
        workflow = StateGraph(SQLAgentState)

        # Add nodes
        workflow.add_node("load_history", self._load_history)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_sql", self._execute_sql)
        workflow.add_node("save_history", self._save_history)

        # Define edges
        workflow.set_entry_point("load_history")
        workflow.add_edge("load_history", "generate_sql")
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "save_history")
        workflow.add_edge("save_history", END)

        return workflow.compile()

    async def _load_history(self, state: SQLAgentState) -> SQLAgentState:
        """Load conversation history for the session."""
        self.logger.info("Loading conversation history", session_id=state["session_id"])

        try:
            # Get conversation history
            history = await self.session_service.get_history(state["session_id"])

            # Convert to messages
            messages = []
            for msg in history:
                if msg["role"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))

            # Get table info
            table_info = self.database.get_table_info()

            state["messages"] = messages
            state["table_info"] = table_info

        except Exception as e:
            self.logger.error("Failed to load history", error=str(e))
            state["error"] = f"Failed to load conversation history: {str(e)}"

        return state

    async def _generate_sql(self, state: SQLAgentState) -> SQLAgentState:
        """Generate SQL query from natural language."""
        self.logger.info("Generating SQL query", question=state["question"])

        try:
            # Create prompt based on whether we have history
            if not state["messages"]:
                # Initial prompt with table info
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_initial_system_prompt()),
                    ("human", "{question}")
                ])

                # Add system message to history
                system_msg = SystemMessage(content=self._get_initial_system_prompt())
                await self.session_service.add_message(
                    state["session_id"], "system", system_msg.content
                )

                messages = [system_msg, HumanMessage(content=state["question"])]

            else:
                # Continuation prompt with history
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_continuation_system_prompt()),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{question}")
                ])

                messages = (
                    [SystemMessage(content=self._get_continuation_system_prompt())] +
                    state["messages"] +
                    [HumanMessage(content=state["question"])]
                )

            # Generate SQL using LLM
            response = await self.llm_service.ainvoke(messages)

            # Extract SQL query from response
            sql_query = self._extract_sql_query(response.content)
            state["sql_query"] = sql_query

            self.logger.info("Generated SQL query", sql=sql_query)

        except Exception as e:
            self.logger.error("Failed to generate SQL", error=str(e))
            state["error"] = f"Failed to generate SQL query: {str(e)}"

        return state

    async def _execute_sql(self, state: SQLAgentState) -> SQLAgentState:
        """Execute the generated SQL query."""
        if state.get("error") or not state.get("sql_query"):
            return state

        self.logger.info("Executing SQL query", sql=state["sql_query"])

        try:
            import time
            start_time = time.time()

            # Execute the query
            result = self.sql_tool.invoke({"query": state["sql_query"]})

            execution_time = time.time() - start_time

            state["query_results"] = result
            state["execution_time"] = execution_time

            self.logger.info(
                "SQL query executed successfully",
                execution_time=execution_time,
                result_length=len(str(result))
            )

        except Exception as e:
            self.logger.error("SQL execution failed", error=str(e))
            state["error"] = f"SQL execution failed: {str(e)}"

        return state

    async def _save_history(self, state: SQLAgentState) -> SQLAgentState:
        """Save the conversation to history."""
        self.logger.info("Saving conversation history", session_id=state["session_id"])

        try:
            # Save human message
            await self.session_service.add_message(
                state["session_id"], "human", state["question"]
            )

            # Save AI response
            if state.get("sql_query"):
                await self.session_service.add_message(
                    state["session_id"], "ai", state["sql_query"]
                )

        except Exception as e:
            self.logger.error("Failed to save history", error=str(e))

        return state

    def _get_initial_system_prompt(self) -> str:
        """Get the initial system prompt with table information."""
        return f"""You are a MySQL expert. Given an input question, create a syntactically correct SQL query to run.
Unless otherwise specified, do not return more than {self.max_rows} rows.

Here is the relevant table info: {self.database.get_table_info()}

Guidelines:
1. Generate ONLY the SQL query, without any additional text or explanation.
2. Filter out rows with any NULL field when possible.
3. Ensure all non-aggregated columns in the SELECT list are included in the GROUP BY clause.
4. Use aggregate functions appropriately to avoid grouping errors.
5. Provide meaningful aliases for calculated columns.

If you cannot generate a SQL query, explain the reason in at most 50 words."""

    def _get_continuation_system_prompt(self) -> str:
        """Get the continuation system prompt."""
        return f"""Generate ONLY the SQL query based on the user's question and conversation history.
Filter out rows with any NULL field when possible. If the question is unclear, try your best to create a SQL query.

Guidelines:
1. Generate ONLY the SQL query, without any additional text or explanation.
2. Consider the conversation context when generating the query.
3. Do not return more than {self.max_rows} rows unless specified.
4. Ensure proper SQL syntax and grouping rules.

If you cannot generate a SQL query, explain the reason in at most 50 words."""

    def _extract_sql_query(self, content: str) -> str:
        """Extract SQL query from LLM response content."""
        # Handle markdown code blocks
        if content.startswith('```sql') and content.endswith('```'):
            return content[6:-3].strip()
        elif content.startswith('```') and content.endswith('```'):
            return content[3:-3].strip()
        else:
            return content.strip()

    async def arun(
        self,
        question: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Run the SQL agent asynchronously."""
        self.logger.info("Starting SQL agent", question=question, session_id=session_id)

        # Initial state
        initial_state = SQLAgentState(
            messages=[],
            question=question,
            session_id=session_id,
            sql_query=None,
            query_results=None,
            error=None,
            table_info=None,
            execution_time=None,
        )

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        # Return results
        return {
            "sql_query": final_state.get("sql_query"),
            "query_results": final_state.get("query_results"),
            "error": final_state.get("error"),
            "execution_time": final_state.get("execution_time"),
        }