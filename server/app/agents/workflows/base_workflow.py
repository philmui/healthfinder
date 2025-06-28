"""
Base Workflow

Provides the foundational class and interfaces for all workflows
in the multi-agent system.
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, List
from llama_index.core.workflow import Workflow, Event, StartEvent, StopEvent
from pydantic import BaseModel, Field
from loguru import logger
from datetime import datetime, UTC
import uuid

from ..models.chat_models import AgentState, ChatCompletionRequest, ChatCompletionResponse


class WorkflowConfig(BaseModel):
    """Base configuration for workflows."""
    name: str
    description: str
    max_execution_time: int = Field(default=120, description="Maximum execution time in seconds")
    enable_parallel_execution: bool = Field(default=True, description="Enable parallel agent execution")
    log_execution_details: bool = Field(default=True, description="Log detailed execution information")


class WorkflowEvent(Event):
    """Base event class for workflow communication."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str
    data: Dict[str, Any] = Field(default={})


class QueryAnalysisEvent(WorkflowEvent):
    """Event for query analysis completion."""
    event_type: str = "query_analysis"
    query: str
    analysis_result: Dict[str, Any]


class ResearchCompleteEvent(WorkflowEvent):
    """Event for research completion."""
    event_type: str = "research_complete"
    research_results: List[Any]


class WebSearchCompleteEvent(WorkflowEvent):
    """Event for web search completion."""
    event_type: str = "web_search_complete"
    search_results: List[Any]


class SynthesisCompleteEvent(WorkflowEvent):
    """Event for synthesis completion."""
    event_type: str = "synthesis_complete"
    synthesis_result: Any


class MultipleEventsEvent(WorkflowEvent):
    """Event that carries multiple other events."""
    event_type: str = "multiple_events"
    events: List[Any]


class BaseWorkflow(Workflow):
    """
    Base class for all workflows.
    
    Provides common functionality including event handling, state management,
    and execution monitoring. All specialized workflows inherit from this class.
    
    Note: This is an abstract base class that inherits from LlamaIndex Workflow.
    Subclasses must implement the process_query method.
    """
    
    def __init__(self, config: WorkflowConfig):
        """
        Initialize the base workflow.
        
        Args:
            config: Workflow configuration
        """
        super().__init__()
        self.config = config
        self.workflow_id = str(uuid.uuid4())
        self.execution_history: List[Dict[str, Any]] = []
        self.current_state: Optional[AgentState] = None
        
        logger.info(f"Initialized workflow: {config.name}")
    
    @abstractmethod
    async def process_query(
        self, 
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Process a chat completion request through the workflow.
        
        Args:
            request: Chat completion request
            
        Returns:
            Chat completion response
        """
        raise NotImplementedError("Subclasses must implement process_query method")
    
    def _initialize_agent_state(self, request: ChatCompletionRequest) -> AgentState:
        """Initialize the agent state for workflow execution."""
        return AgentState(
            current_step="initialization",
            completed_steps=[],
            research_results=[],
            web_search_results=[],
            synthesis_result=None,
            active_agents=[],
            total_tokens_used=0,
            processing_time=0.0
        )
    
    async def _log_execution_step(
        self,
        step_name: str,
        execution_time: float,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log workflow execution step details."""
        
        if not self.config.log_execution_details:
            return
        
        execution_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "workflow_id": self.workflow_id,
            "workflow_name": self.config.name,
            "step_name": step_name,
            "execution_time": execution_time,
            "success": success,
            "details": details or {}
        }
        
        self.execution_history.append(execution_record)
        
        if success:
            logger.info(f"Workflow step '{step_name}' completed in {execution_time:.2f}s")
        else:
            logger.error(f"Workflow step '{step_name}' failed after {execution_time:.2f}s")
    
    def _update_agent_state(
        self,
        step_name: str,
        agent_name: Optional[str] = None,
        **updates
    ) -> None:
        """Update the current agent state."""
        
        if self.current_state is None:
            logger.warning("Agent state not initialized")
            return
        
        # Update current step
        self.current_state.current_step = step_name
        
        # Add to completed steps if not already there
        if step_name not in self.current_state.completed_steps:
            self.current_state.completed_steps.append(step_name)
        
        # Update active agents
        if agent_name and agent_name not in self.current_state.active_agents:
            self.current_state.active_agents.append(agent_name)
        
        # Apply any additional updates
        for key, value in updates.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about this workflow."""
        return {
            "id": self.workflow_id,
            "name": self.config.name,
            "description": self.config.description,
            "execution_count": len(self.execution_history),
            "max_execution_time": self.config.max_execution_time,
            "parallel_execution_enabled": self.config.enable_parallel_execution
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for this workflow."""
        
        if not self.execution_history:
            return {"total_executions": 0}
        
        successful_steps = sum(1 for record in self.execution_history if record["success"])
        total_time = sum(record["execution_time"] for record in self.execution_history)
        avg_time = total_time / len(self.execution_history)
        
        return {
            "total_steps_executed": len(self.execution_history),
            "successful_steps": successful_steps,
            "success_rate": successful_steps / len(self.execution_history),
            "average_step_time": avg_time,
            "total_execution_time": total_time
        }
    
    def reset_execution_history(self) -> None:
        """Reset the execution history."""
        self.execution_history.clear()
        logger.info(f"Reset execution history for workflow {self.config.name}")
    
    def _create_error_response(
        self,
        request: ChatCompletionRequest,
        error_message: str,
        execution_time: float = 0.0
    ) -> ChatCompletionResponse:
        """Create an error response for failed workflow execution."""
        
        from ..models.chat_models import (
            ChatMessage, MessageRole, Choice, Usage, AgentInfo
        )
        import time
        
        error_choice = Choice(
            index=0,
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content=f"I apologize, but I encountered an error while processing your request: {error_message}"
            ),
            finish_reason="stop"
        )
        
        # Create basic usage stats
        usage = Usage(
            prompt_tokens=len(str(request.messages)) // 4,  # Rough estimate
            completion_tokens=len(error_message) // 4,
            total_tokens=len(str(request.messages) + error_message) // 4
        )
        
        # Create error agent info
        error_agent = AgentInfo(
            name="WorkflowManager",
            role="error_handler",
            contribution="Error handling and user notification",
            confidence=0.0,
            sources_used=[]
        )
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{self.workflow_id}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[error_choice],
            usage=usage,
            agent_state=self.current_state,
            contributing_agents=[error_agent],
            research_metadata={
                "error": error_message,
                "execution_time": execution_time,
                "workflow_id": self.workflow_id
            }
        )
    
    def _estimate_token_usage(
        self,
        request: ChatCompletionRequest,
        response_content: str
    ) -> Dict[str, int]:
        """Estimate token usage for the request and response."""
        
        # Simple estimation: 1 token ≈ 4 characters
        prompt_text = " ".join([msg.content for msg in request.messages])
        prompt_tokens = len(prompt_text) // 4
        completion_tokens = len(response_content) // 4
        total_tokens = prompt_tokens + completion_tokens
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    
    async def _handle_workflow_timeout(self) -> None:
        """Handle workflow execution timeout."""
        logger.error(f"Workflow {self.config.name} exceeded maximum execution time")
        # Could implement cleanup logic here
    
    async def _validate_request(self, request: ChatCompletionRequest) -> bool:
        """Validate the incoming request."""
        
        if not request.messages:
            logger.error("Request contains no messages")
            return False
        
        if not any(msg.role == "user" for msg in request.messages):
            logger.error("Request contains no user messages")
            return False
        
        return True 