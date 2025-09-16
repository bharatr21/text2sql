"""
Modern LLM service with support for multiple providers and async operations.
"""

import os
from typing import Any, Dict, List, Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_together import ChatTogether

from ..core.config import LLMSettings
from ..core.logging import LoggerMixin


class LLMService(LoggerMixin):
    """Modern LLM service with multi-provider support."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self._llm: Optional[BaseChatModel] = None
        self._initialize_llm()

    def _initialize_llm(self) -> None:
        """Initialize the LLM based on settings."""
        self.logger.info("Initializing LLM", provider=self.settings.provider, model=self.settings.model)

        if not self.settings.api_key:
            raise ValueError(f"API key not found for provider: {self.settings.provider}")

        if self.settings.provider == "openai":
            self._llm = self._create_openai_llm()
        elif self.settings.provider == "anthropic":
            self._llm = self._create_anthropic_llm()
        elif self.settings.provider == "together":
            self._llm = self._create_together_llm()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.provider}")

    def _create_openai_llm(self) -> ChatOpenAI:
        """Create OpenAI LLM instance."""
        os.environ["OPENAI_API_KEY"] = self.settings.api_key

        return ChatOpenAI(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            timeout=self.settings.timeout,
            max_retries=self.settings.max_retries,
        )

    def _create_anthropic_llm(self) -> ChatAnthropic:
        """Create Anthropic LLM instance."""
        os.environ["ANTHROPIC_API_KEY"] = self.settings.api_key

        return ChatAnthropic(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            timeout=self.settings.timeout,
            max_retries=self.settings.max_retries,
        )

    def _create_together_llm(self) -> ChatTogether:
        """Create Together AI LLM instance."""
        os.environ["TOGETHER_API_KEY"] = self.settings.api_key

        return ChatTogether(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            timeout=self.settings.timeout,
            max_retries=self.settings.max_retries,
        )

    @property
    def llm(self) -> BaseChatModel:
        """Get the LLM instance."""
        if self._llm is None:
            raise RuntimeError("LLM not initialized")
        return self._llm

    def invoke(
        self,
        messages: Union[List[BaseMessage], str],
        **kwargs: Any,
    ) -> Any:
        """Invoke the LLM synchronously."""
        self.logger.debug("Invoking LLM", num_messages=len(messages) if isinstance(messages, list) else 1)

        try:
            return self.llm.invoke(messages, **kwargs)
        except Exception as e:
            self.logger.error("LLM invocation failed", error=str(e))
            raise

    async def ainvoke(
        self,
        messages: Union[List[BaseMessage], str],
        **kwargs: Any,
    ) -> Any:
        """Invoke the LLM asynchronously."""
        self.logger.debug("Async invoking LLM", num_messages=len(messages) if isinstance(messages, list) else 1)

        try:
            return await self.llm.ainvoke(messages, **kwargs)
        except Exception as e:
            self.logger.error("Async LLM invocation failed", error=str(e))
            raise

    def batch(
        self,
        inputs: List[Union[List[BaseMessage], str]],
        **kwargs: Any,
    ) -> List[Any]:
        """Batch invoke the LLM synchronously."""
        self.logger.debug("Batch invoking LLM", batch_size=len(inputs))

        try:
            return self.llm.batch(inputs, **kwargs)
        except Exception as e:
            self.logger.error("LLM batch invocation failed", error=str(e))
            raise

    async def abatch(
        self,
        inputs: List[Union[List[BaseMessage], str]],
        **kwargs: Any,
    ) -> List[Any]:
        """Batch invoke the LLM asynchronously."""
        self.logger.debug("Async batch invoking LLM", batch_size=len(inputs))

        try:
            return await self.llm.abatch(inputs, **kwargs)
        except Exception as e:
            self.logger.error("Async LLM batch invocation failed", error=str(e))
            raise

    def stream(
        self,
        messages: Union[List[BaseMessage], str],
        **kwargs: Any,
    ):
        """Stream LLM responses."""
        self.logger.debug("Streaming LLM", num_messages=len(messages) if isinstance(messages, list) else 1)

        try:
            return self.llm.stream(messages, **kwargs)
        except Exception as e:
            self.logger.error("LLM streaming failed", error=str(e))
            raise

    async def astream(
        self,
        messages: Union[List[BaseMessage], str],
        **kwargs: Any,
    ):
        """Stream LLM responses asynchronously."""
        self.logger.debug("Async streaming LLM", num_messages=len(messages) if isinstance(messages, list) else 1)

        try:
            async for chunk in self.llm.astream(messages, **kwargs):
                yield chunk
        except Exception as e:
            self.logger.error("Async LLM streaming failed", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check LLM service health."""
        try:
            test_message = "Hello, this is a health check."
            await self.ainvoke(test_message)
            return True
        except Exception as e:
            self.logger.error("LLM health check failed", error=str(e))
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.settings.provider,
            "model": self.settings.model,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }