"""
Chat Completions API

Implements OpenAI-compatible chat completions endpoint with multi-agent
research capabilities using the HealthFinder agent system.

NOTE: For testability, all endpoints use FastAPI dependency injection for the workflow via Depends(get_workflow).
Tests should use app.dependency_overrides[get_workflow] to inject mocks.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime, UTC
from loguru import logger

from ..agents.models.chat_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    StreamChoice
)
from ..agents.workflow_refactored import (
    HealthFinderAgentWorkflow,
    HealthFinderWorkflowConfig,
    create_healthfinder_workflow,
    get_default_workflow,
    get_healthcare_workflow_config,
    get_general_workflow_config,
    get_fast_workflow_config
)

router = APIRouter()

# Global workflow instance for efficiency (can be moved to dependency injection)
_workflow_instance: Optional[HealthFinderAgentWorkflow] = None
_workflow_config: Optional[HealthFinderWorkflowConfig] = None


def get_workflow() -> HealthFinderAgentWorkflow:
    """
    Dependency-injected workflow factory. Always returns a new instance unless overridden in tests.
    """
    return get_default_workflow()


def update_workflow_config(new_config: HealthFinderWorkflowConfig) -> None:
    """
    Update workflow configuration.
    
    This will recreate the workflow instance with the new configuration.
    """
    global _workflow_instance, _workflow_config
    
    logger.info("Updating workflow configuration")
    _workflow_config = new_config
    _workflow_instance = create_healthfinder_workflow(new_config)


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    workflow: HealthFinderAgentWorkflow = Depends(get_workflow)
) -> ChatCompletionResponse:
    """
    Create a chat completion using the multi-agent research system.
    
    This endpoint implements OpenAI's chat completions API format while
    extending it with HealthFinder's multi-agent capabilities.
    
    Args:
        request: Chat completion request following OpenAI format
        background_tasks: FastAPI background tasks for cleanup
        workflow: Injected workflow instance
        
    Returns:
        Chat completion response with agent orchestration results
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        # Check if streaming is requested
        if request.stream:
            logger.warning("Streaming completions not yet fully implemented with AgentWorkflow")
            raise HTTPException(status_code=501, detail="Streaming completions not yet implemented")
            
        # Log the incoming request (without sensitive data)
        logger.info(f"Received chat completion request with {len(request.messages)} messages")
        
        # Update workflow configuration from request if needed
        if hasattr(request, 'enable_web_search') or hasattr(request, 'enable_deep_research'):
            config_update = HealthFinderWorkflowConfig(
                enable_web_search=getattr(request, 'enable_web_search', True),
                enable_research=getattr(request, 'enable_deep_research', True),
                research_depth=getattr(request, 'research_depth', 3),
                max_search_results=getattr(request, 'max_search_results', 10)
            )
            # Only update config if changed
            if config_update.model_dump() != workflow.config.model_dump():
                # In production, update_workflow_config would recreate the workflow, but for DI/mocks, update config in place
                if hasattr(workflow, 'config'):
                    workflow.config = config_update
                # If the workflow has a method to update config, call it as well
                if hasattr(workflow, 'update_config'):
                    workflow.update_config(config_update)
        
        # Process the request through the workflow
        response = await workflow.process_query(request)
        
        # Schedule background cleanup
        background_tasks.add_task(_cleanup_workflow_state, workflow.workflow_id)
        
        logger.info(f"Chat completion completed successfully: {workflow.workflow_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTPExceptions to preserve their status codes
        raise
        
    except ValueError as e:
        logger.error(f"Validation error in chat completion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")


@router.post("/chat/completions/stream")
async def create_chat_completion_stream(
    request: ChatCompletionRequest,
    workflow: HealthFinderAgentWorkflow = Depends(get_workflow)
) -> StreamingResponse:
    """
    Create a streaming chat completion.
    
    Note: This endpoint is not yet fully implemented with AgentWorkflow streaming.
    This is a placeholder that demonstrates the streaming interface.
    
    Args:
        request: Chat completion request
        workflow: Injected workflow instance
        
    Returns:
        Streaming response with incremental updates
        
    Raises:
        HTTPException: For implementation or processing errors
    """
    logger.warning("Streaming completions not yet fully implemented with AgentWorkflow")
    raise HTTPException(status_code=501, detail="Streaming completions not yet implemented")
    
    async def stream_generator():
        """Generate streaming response chunks."""
        try:
            # Initial chunk
            chunk = ChatCompletionStreamResponse(
                id=f"chatcmpl-{workflow.workflow_id}",
                created=int(datetime.now(UTC).timestamp()),
                model=request.model,
                choices=[StreamChoice(
                    index=0,
                    delta={"role": "assistant", "content": ""},
                    finish_reason=None
                )]
            )
            
            yield f"data: {chunk.model_dump_json()}\n\n"
            
            # For now, process normally and stream the result
            response = await workflow.process_query(request)
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                
                # Stream content in chunks
                for i, char in enumerate(content):
                    chunk = ChatCompletionStreamResponse(
                        id=f"chatcmpl-{workflow.workflow_id}",
                        created=int(datetime.now(UTC).timestamp()),
                        model=request.model,
                        choices=[StreamChoice(
                            index=0,
                            delta={"content": char},
                            finish_reason=None
                        )]
                    )
                    
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    
                    # Small delay for streaming effect
                    await asyncio.sleep(0.01)
            
            # Final chunk
            final_chunk = ChatCompletionStreamResponse(
                id=f"chatcmpl-{workflow.workflow_id}",
                created=int(datetime.now(UTC).timestamp()),
                model=request.model,
                choices=[StreamChoice(
                    index=0,
                    delta={},
                    finish_reason="stop"
                )]
            )
            
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            error_chunk = ChatCompletionStreamResponse(
                id=f"chatcmpl-{workflow.workflow_id}",
                created=int(datetime.now(UTC).timestamp()),
                model=request.model,
                choices=[StreamChoice(
                    index=0,
                    delta={"content": f"Error: {str(e)}"},
                    finish_reason="stop"
                )]
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat/status")
async def get_chat_status(
    workflow: HealthFinderAgentWorkflow = Depends(get_workflow)
) -> Dict[str, Any]:
    """
    Get the current status of the chat system.
    
    Returns information about the workflow, agents, and system health.
    
    Args:
        workflow: Injected workflow instance
        
    Returns:
        System status information
    """
    try:
        workflow_info = workflow.get_workflow_info()
        agent_status = workflow.get_agent_status()
        execution_stats = workflow.get_execution_stats()
        
        status = {
            "status": "operational",
            "timestamp": datetime.now(UTC).isoformat(),
            "workflow_info": workflow_info,
            "agent_status": agent_status,
            "execution_stats": execution_stats,
            "capabilities": {
                "research": workflow.config.enable_research,
                "deep_research": workflow.config.enable_research,
                "web_search": workflow.config.enable_web_search,
                "synthesis": True,
                "streaming": False,  # Not yet fully implemented
                "context_memory": True
            },
            "configuration": workflow.config.model_dump()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e)
        }


@router.post("/chat/config")
async def update_chat_config(
    config: HealthFinderWorkflowConfig
) -> Dict[str, Any]:
    """
    Update the chat system configuration.
    
    This will recreate the workflow instance with the new configuration.
    
    Args:
        config: New workflow configuration
        
    Returns:
        Configuration update confirmation
    """
    try:
        logger.info("Updating chat configuration via API")
        
        # Update the global configuration
        update_workflow_config(config)
        
        return {
            "status": "configuration_updated", 
            "message": "Configuration updated successfully",
            "timestamp": datetime.now(UTC).isoformat(),
            "new_config": config.model_dump(),
            "applied_updates": config.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error updating chat config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.get("/chat/config/presets")
async def get_config_presets() -> Dict[str, HealthFinderWorkflowConfig]:
    """
    Get predefined configuration presets.
    
    Returns:
        Available configuration presets
    """
    return {
        "healthcare": get_healthcare_workflow_config(),
        "general": get_general_workflow_config(),
        "fast": get_fast_workflow_config(),
        "default": HealthFinderWorkflowConfig()
    }


@router.get("/chat/metrics")
async def get_chat_metrics(
    workflow: HealthFinderAgentWorkflow = Depends(get_workflow)
) -> Dict[str, Any]:
    """
    Get detailed metrics about the chat system performance.
    
    Args:
        workflow: Injected workflow instance
        
    Returns:
        Performance metrics and statistics
    """
    try:
        execution_stats = workflow.get_execution_stats()
        
        metrics = {
            "timestamp": datetime.now(UTC).isoformat(),
            "workflow_id": workflow.workflow_id,
            "workflow_metrics": execution_stats,
            "execution_metrics": execution_stats,
            "agent_metrics": {
                "total_agents": len(workflow.agents),
                "enabled_agents": [agent.name for agent in workflow.agents],
                "agent_capabilities": workflow.get_agent_status()
            },
            "performance_metrics": {
                "average_response_time": execution_stats.get("execution_time", 0),
                "success_rate": execution_stats.get("success_rate", 0),
                "total_requests": execution_stats.get("total_executions", 0)
            },
            "system_metrics": {
                "memory_usage": "N/A",  # Placeholder for system memory metrics
                "cpu_usage": "N/A",     # Placeholder for CPU usage metrics
                "uptime": "N/A",        # Placeholder for system uptime
                "active_connections": 1,  # Placeholder for active connection count
                "success_rate": execution_stats.get("success_rate", 0.0),
                "total_steps_executed": execution_stats.get("total_steps_executed", 0),
                "average_step_time": execution_stats.get("average_step_time", 0.0)
            },
            "configuration_metrics": {
                "research_enabled": workflow.config.enable_research,
                "web_search_enabled": workflow.config.enable_web_search,
                "research_depth": workflow.config.research_depth,
                "max_search_results": workflow.config.max_search_results
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting chat metrics: {e}")
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e)
        }


async def _cleanup_workflow_state(workflow_id: str) -> None:
    """
    Background task to clean up workflow state.
    
    Args:
        workflow_id: ID of the workflow to clean up
    """
    try:
        logger.info(f"Cleaning up workflow state: {workflow_id}")
        # In a production system, this might clean up:
        # - Temporary files
        # - Cache entries
        # - Database records
        # - Memory allocations
        
        await asyncio.sleep(1)  # Simulate cleanup work
        logger.info(f"Workflow cleanup completed: {workflow_id}")
        
    except Exception as e:
        logger.error(f"Error in workflow cleanup: {e}")


# Health check endpoint
@router.get("/chat/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "HealthFinder Chat API",
        "version": "2.0.0-refactored"
    } 