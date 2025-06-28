"""
Base Function Agent

Provides the foundational class and interfaces for all function agents
in the multi-agent workflow system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.tools import BaseTool
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger
from datetime import datetime, UTC
import uuid

from ..models.chat_models import AgentState, ResearchResult, WebSearchResult, SynthesisResult
from app.core.config import settings


class AgentRole(str, Enum):
    """Roles that agents can fulfill in the multi-agent system."""
    RESEARCH = "research"
    WEB_SEARCH = "web_search"
    SYNTHESIS = "synthesis"
    ANALYSIS = "analysis"
    COORDINATOR = "coordinator"


class AgentConfig(BaseModel):
    """Configuration for function agents."""
    name: str
    role: AgentRole
    description: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    model_name: str = Field(default="gpt-4")
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default=[])
    max_iterations: int = Field(default=3, ge=1, le=10)
    
    model_config = ConfigDict(use_enum_values=True)


class BaseFunctionAgent(ABC):
    """
    Abstract base class for all function agents.
    
    Provides common functionality including LLM integration, tool management,
    and result processing. All specialized agents inherit from this class.
    """
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        """
        Initialize the base function agent.
        
        Args:
            config: Agent configuration
            tools: List of tools available to the agent
        """
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.tools = tools or []
        self.llm = self._create_llm()
        self.agent_worker = self._create_agent_worker()
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized {config.role} agent: {config.name}")
    
    def _create_llm(self) -> LLM:
        """Create and configure the LLM for this agent."""
        try:
            return OpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=settings.OPENAI_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to create LLM for agent {self.config.name}: {e}")
            # Fallback to a default configuration
            return OpenAI(model="gpt-3.5-turbo", temperature=0.7)
    
    def _create_agent_worker(self) -> FunctionCallingAgentWorker:
        """Create the LlamaIndex FunctionCallingAgentWorker."""
        system_prompt = self.config.system_prompt or self._get_default_system_prompt()
        
        return FunctionCallingAgentWorker.from_tools(
            tools=self.tools,
            llm=self.llm,
            system_prompt=system_prompt,
            max_function_calls=self.config.max_iterations,
            allow_parallel_tool_calls=True
        )
    
    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for this agent type."""
        pass
    
    @abstractmethod
    async def execute(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[ResearchResult, WebSearchResult, SynthesisResult]:
        """
        Execute the agent's primary function.
        
        Args:
            query: The query or task to process
            context: Additional context from other agents
            **kwargs: Additional parameters
            
        Returns:
            Result object specific to the agent type
        """
        pass
    
    async def _log_execution(
        self, 
        query: str, 
        result: Any, 
        execution_time: float,
        success: bool = True
    ) -> None:
        """Log execution details for debugging and monitoring."""
        execution_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_id": self.agent_id,
            "agent_name": self.config.name,
            "agent_role": self.config.role,
            "query": query,
            "success": success,
            "execution_time": execution_time,
            "result_type": type(result).__name__ if result else None,
            "tools_used": [tool.metadata.name for tool in self.tools]
        }
        
        self.execution_history.append(execution_record)
        
        if success:
            logger.info(f"Agent {self.config.name} completed task in {execution_time:.2f}s")
        else:
            logger.error(f"Agent {self.config.name} failed task after {execution_time:.2f}s")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "id": self.agent_id,
            "name": self.config.name,
            "role": self.config.role,
            "description": self.config.description,
            "tools": [tool.metadata.name for tool in self.tools],
            "execution_count": len(self.execution_history),
            "model": self.config.model_name
        }
    
    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to this agent."""
        self.tools.append(tool)
        # Recreate agent worker with new tools
        self.agent_worker = self._create_agent_worker()
        logger.info(f"Added tool {tool.metadata.name} to agent {self.config.name}")
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from this agent."""
        for i, tool in enumerate(self.tools):
            if tool.metadata.name == tool_name:
                removed_tool = self.tools.pop(i)
                self.agent_worker = self._create_agent_worker()
                logger.info(f"Removed tool {tool_name} from agent {self.config.name}")
                return True
        return False
    
    async def _handle_tool_error(self, tool_name: str, error: Exception) -> str:
        """Handle errors that occur during tool execution."""
        error_message = f"Tool {tool_name} failed: {str(error)}"
        logger.error(error_message)
        
        # Try to provide a fallback response
        fallback_response = f"I encountered an error while using {tool_name}. "
        fallback_response += "I'll attempt to provide information based on my training data instead."
        
        return fallback_response
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for this agent."""
        if not self.execution_history:
            return {"total_executions": 0}
        
        successful_executions = sum(1 for exec in self.execution_history if exec["success"])
        total_time = sum(exec["execution_time"] for exec in self.execution_history)
        avg_time = total_time / len(self.execution_history)
        
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": successful_executions,
            "success_rate": successful_executions / len(self.execution_history),
            "average_execution_time": avg_time,
            "total_execution_time": total_time
        }
    
    def reset_history(self) -> None:
        """Reset the execution history."""
        self.execution_history.clear()
        logger.info(f"Reset execution history for agent {self.config.name}")


class AgentFactory:
    """Factory class for creating function agents."""
    
    @staticmethod
    def create_agent_config(
        name: str,
        role: AgentRole,
        description: str,
        **kwargs
    ) -> AgentConfig:
        """Create an agent configuration with defaults."""
        return AgentConfig(
            name=name,
            role=role,
            description=description,
            **kwargs
        )
    
    @staticmethod
    def create_research_agent(
        name: str = "ResearchAgent",
        description: str = "Conducts comprehensive research on healthcare and general topics"
    ) -> "ResearchAgent":
        """Create a research agent with default configuration."""
        from .research_agent import ResearchAgent
        
        config = AgentFactory.create_agent_config(
            name=name,
            role=AgentRole.RESEARCH,
            description=description,
            temperature=0.3,  # Lower temperature for more focused research
            max_tokens=2000
        )
        return ResearchAgent(config)
    
    @staticmethod
    def create_web_search_agent(
        name: str = "WebSearchAgent", 
        description: str = "Performs web searches to find current information"
    ) -> "WebSearchAgent":
        """Create a web search agent with default configuration."""
        from .web_search_agent import WebSearchAgent
        
        config = AgentFactory.create_agent_config(
            name=name,
            role=AgentRole.WEB_SEARCH,
            description=description,
            temperature=0.5,
            max_tokens=1500
        )
        return WebSearchAgent(config)
    
    @staticmethod
    def create_synthesis_agent(
        name: str = "SynthesisAgent",
        description: str = "Synthesizes information from multiple sources into coherent responses"
    ) -> "SynthesisAgent":
        """Create a synthesis agent with default configuration."""
        from .synthesis_agent import SynthesisAgent
        
        config = AgentFactory.create_agent_config(
            name=name,
            role=AgentRole.SYNTHESIS,
            description=description,
            temperature=0.7,  # Higher temperature for creative synthesis
            max_tokens=3000
        )
        return SynthesisAgent(config) 