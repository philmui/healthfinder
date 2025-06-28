"""
Tools Module - LlamaIndex Standard Tools

Exports all available tools for the HealthFinder multi-agent system.
All tools now follow LlamaIndex's standard BaseTool interface.
"""

from .web_search_tool import (
    DuckDuckGoSearchTool,
    GoogleSearchTool,
    get_duckduckgo_search_tool,
    get_google_search_tool,
    get_all_web_search_tools,
    get_best_search_tool,
    conduct_contextual_web_search
)

from .research_tools import (
    HealthcareResearchTool,
    GeneralResearchTool,
    get_healthcare_research_tool,
    get_general_research_tool,
    get_all_research_tools,
    conduct_contextual_research
)

__all__ = [
    # Web search tools
    "DuckDuckGoSearchTool",
    "GoogleSearchTool",
    "get_duckduckgo_search_tool",
    "get_google_search_tool", 
    "get_all_web_search_tools",
    "get_best_search_tool",
    "conduct_contextual_web_search",
    
    # Research tools
    "HealthcareResearchTool",
    "GeneralResearchTool",
    "get_healthcare_research_tool",
    "get_general_research_tool",
    "get_all_research_tools",
    "conduct_contextual_research"
] 