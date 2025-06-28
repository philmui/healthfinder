"""
HealthFinder Agent System - Refactored with LlamaIndex Standards

This module provides the multi-agent system for HealthFinder using standard
LlamaIndex components including AgentWorkflow and FunctionAgent.
"""

from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    MessageRole,
    AgentState,
    AgentInfo,
    ResearchResult,
    WebSearchResult,
    SynthesisResult
)

from .tools import (
    DuckDuckGoSearchTool,
    GoogleSearchTool,
    HealthcareResearchTool,
    GeneralResearchTool,
    get_duckduckgo_search_tool,
    get_google_search_tool,
    get_healthcare_research_tool,
    get_general_research_tool,
    get_all_web_search_tools,
    get_all_research_tools
)

from .workflow_refactored import (
    HealthFinderAgentWorkflow,
    HealthFinderWorkflowConfig,
    create_healthfinder_workflow,
    get_default_workflow,
    get_healthcare_workflow_config,
    get_general_workflow_config,
    get_fast_workflow_config
)

__all__ = [
    # Models
    "ChatCompletionRequest",
    "ChatCompletionResponse", 
    "ChatMessage",
    "MessageRole",
    "AgentState",
    "AgentInfo",
    "ResearchResult",
    "WebSearchResult",
    "SynthesisResult",
    
    # Tools
    "DuckDuckGoSearchTool",
    "GoogleSearchTool",
    "HealthcareResearchTool",
    "GeneralResearchTool",
    "get_duckduckgo_search_tool",
    "get_google_search_tool",
    "get_healthcare_research_tool",
    "get_general_research_tool",
    "get_all_web_search_tools",
    "get_all_research_tools",
    
    # Workflows
    "HealthFinderAgentWorkflow",
    "HealthFinderWorkflowConfig",
    "create_healthfinder_workflow",
    "get_default_workflow",
    "get_healthcare_workflow_config",
    "get_general_workflow_config",
    "get_fast_workflow_config"
]
