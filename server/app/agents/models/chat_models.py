"""
Chat Completion Models

Pydantic models for the agentic search and chat completion API, following
OpenAI's chat completions API format while extending it for multi-agent workflows.
"""

from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, UTC
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles following OpenAI's format."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single chat message in the conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Find me information about diabetes treatment options"
            }
        }
    )


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions endpoint."""
    messages: List[ChatMessage] = Field(..., min_length=1, description="List of messages in the conversation")
    model: str = Field(default="gpt-4", description="Model to use for generation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum number of tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stream: bool = Field(default=False, description="Whether to stream the response")
    
    # HealthFinder-specific parameters
    enable_web_search: bool = Field(default=True, description="Enable web search capability")
    enable_deep_research: bool = Field(default=True, description="Enable deep research with multiple agents")
    research_depth: int = Field(default=3, ge=1, le=5, description="Depth of research (1=basic, 5=comprehensive)")
    max_search_results: int = Field(default=10, ge=1, le=50, description="Maximum web search results to consider")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "What are the latest treatment options for Type 2 diabetes?"}
                ],
                "model": "gpt-4",
                "temperature": 0.7,
                "enable_web_search": True,
                "enable_deep_research": True,
                "research_depth": 3
            }
        }
    )


class AgentInfo(BaseModel):
    """Information about an agent that contributed to the response."""
    name: str
    role: str
    contribution: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources_used: List[str] = []


class ResearchResult(BaseModel):
    """Result from a research agent."""
    query: str
    findings: str
    sources: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent_name: str
    
    model_config = ConfigDict(from_attributes=True)


class WebSearchResult(BaseModel):
    """Result from web search."""
    query: str
    title: str
    url: str
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_type: str = Field(default="general", description="Type of source (academic, medical, news, etc.)")
    agent_name: str = Field(default="WebSearchTool", description="Name of the search tool used")
    
    model_config = ConfigDict(from_attributes=True)


class SynthesisResult(BaseModel):
    """Result from synthesis agent that combines multiple sources."""
    synthesized_content: str
    source_results: List[Union[ResearchResult, WebSearchResult]]
    confidence: float = Field(ge=0.0, le=1.0)
    key_insights: List[str] = []
    recommendations: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class AgentState(BaseModel):
    """State tracking for the multi-agent workflow."""
    current_step: str
    completed_steps: List[str] = []
    research_results: List[ResearchResult] = []
    web_search_results: List[WebSearchResult] = []
    synthesis_result: Optional[SynthesisResult] = None
    active_agents: List[str] = []
    total_tokens_used: int = 0
    processing_time: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)


class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    model_config = ConfigDict(from_attributes=True)


class Choice(BaseModel):
    """A single choice in the chat completion response."""
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls", "function_call"] = "stop"
    
    model_config = ConfigDict(from_attributes=True)


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions endpoint."""
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for the completion")
    choices: List[Choice] = Field(..., description="List of completion choices")
    usage: Usage = Field(..., description="Token usage information")
    
    # HealthFinder-specific fields
    agent_state: Optional[AgentState] = Field(None, description="Multi-agent workflow state")
    contributing_agents: List[AgentInfo] = Field(default=[], description="Agents that contributed to response")
    research_metadata: Dict[str, Any] = Field(default={}, description="Research process metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "chatcmpl-123",
                "object": "chat.completion", 
                "created": 1677652288,
                "model": "gpt-4",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Based on my research, here are the latest Type 2 diabetes treatment options..."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 56,
                    "completion_tokens": 31,
                    "total_tokens": 87
                }
            }
        }
    )


class StreamChoice(BaseModel):
    """A streaming choice chunk."""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatCompletionStreamResponse(BaseModel):
    """Streaming response model for chat completions."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]
    
    model_config = ConfigDict(from_attributes=True) 