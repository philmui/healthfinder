"""
HealthFinder Agent Models

Pydantic models for the HealthFinder multi-agent system following
OpenAI's chat completions API format.
"""

from .chat_models import (
    MessageRole,
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    StreamChoice,
    Choice,
    Usage,
    AgentInfo,
    AgentState,
    ResearchResult,
    WebSearchResult,
    SynthesisResult
)

__all__ = [
    "MessageRole",
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionStreamResponse",
    "StreamChoice",
    "Choice",
    "Usage",
    "AgentInfo",
    "AgentState",
    "ResearchResult",
    "WebSearchResult",
    "SynthesisResult"
] 