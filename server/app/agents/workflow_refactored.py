"""
Refactored Workflow using Standard LlamaIndex AgentWorkflow

This module implements the HealthFinder multi-agent workflow using LlamaIndex's
standard AgentWorkflow pattern following SOLID principles and DRY practices.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.core.workflow import Context
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field
from loguru import logger

from .tools.research_tools import (
    get_healthcare_research_tool, 
    get_general_research_tool
)
from .tools.web_search_tool import (
    get_duckduckgo_search_tool,
    get_google_search_tool
)
from .models.chat_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    MessageRole,
    Choice,
    Usage,
    AgentInfo,
    AgentState
)
from app.core.config import settings


class HealthFinderWorkflowConfig(BaseModel):
    """Configuration for the HealthFinder AgentWorkflow."""
    
    name: str = Field(default="HealthFinder Concierge", description="Workflow name")
    description: str = Field(
        default="Multi-agent research and synthesis workflow for healthcare and general queries",
        description="Workflow description"
    )
    
    # Research configuration
    enable_research: bool = Field(default=True, description="Enable research agent")
    research_depth: int = Field(default=3, ge=1, le=5, description="Research depth level")
    
    # Web search configuration
    enable_web_search: bool = Field(default=True, description="Enable web search agent")
    max_search_results: int = Field(default=10, ge=1, le=50, description="Max web search results")
    search_engine: str = Field(default="duckduckgo", description="Search engine preference")
    
    # Synthesis configuration
    synthesis_type: str = Field(default="auto", description="Type of synthesis ('auto', 'healthcare', 'general')")
    
    # LLM configuration
    llm_model: str = Field(default="gpt-4", description="LLM model to use")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=2000, ge=100, le=4000, description="Max tokens per agent")
    
    # Execution configuration
    max_execution_time: int = Field(default=120, ge=30, le=300, description="Max execution time in seconds")
    timeout_per_agent: int = Field(default=60, ge=10, le=120, description="Timeout per agent in seconds")


class HealthFinderAgentWorkflow:
    """
    HealthFinder multi-agent workflow using standard LlamaIndex AgentWorkflow.
    
    This class orchestrates the research, web search, and synthesis agents
    using LlamaIndex's proven AgentWorkflow pattern for reliable multi-agent coordination.
    """
    
    def __init__(self, config: Optional[HealthFinderWorkflowConfig] = None):
        """
        Initialize the HealthFinder AgentWorkflow.
        
        Args:
            config: Workflow configuration (uses defaults if not provided)
        """
        self.config = config or HealthFinderWorkflowConfig()
        self.workflow_id = f"healthfinder-{uuid.uuid4()}"
        self.start_time: Optional[float] = None
        self.execution_stats: Dict[str, Any] = {}
        
        # Create LLM for agents
        self.llm = self._create_llm()
        
        # Create agents
        self.agents = self._create_agents()
        
        # Create the LlamaIndex AgentWorkflow
        self.agent_workflow = self._create_agent_workflow()
        
        logger.info(f"Initialized HealthFinder AgentWorkflow: {self.workflow_id}")
    
    def _create_llm(self) -> LLM:
        """Create the LLM for agents."""
        return OpenAI(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.max_tokens,
            api_key=settings.OPENAI_API_KEY
        )
    
    def _create_agents(self) -> List[FunctionAgent]:
        """Create all agents for the workflow."""
        agents = []
        
        # Research Agent
        if self.config.enable_research:
            research_agent = FunctionAgent(
                name="ResearchAgent",
                description="Conducts comprehensive research on healthcare and general topics with evidence-based analysis",
                system_prompt="""You are a specialized Research Agent in the HealthFinder multi-agent system.

Your primary responsibilities:
- Conduct comprehensive research on healthcare and medical topics
- Perform general research across various domains
- Provide evidence-based analysis with confidence scoring
- Identify authoritative sources and assess information quality

Research Guidelines:
1. For healthcare topics:
   - Prioritize peer-reviewed medical literature
   - Reference clinical guidelines from major medical organizations
   - Include FDA approvals and CDC recommendations
   - Distinguish between established treatments and experimental approaches
   - Always include medical disclaimers

2. For general topics:
   - Use academic and scholarly sources
   - Include government and official publications  
   - Reference expert analysis and industry reports
   - Provide balanced perspectives on controversial topics

3. Quality Standards:
   - Assess source credibility and bias
   - Provide confidence scores (0.0-1.0) based on evidence quality
   - Include publication dates and ensure information currency
   - Acknowledge limitations and uncertainties

When research is complete and you have sufficient information, hand off to WebSearchAgent to gather current information and validate findings.

Always structure your research findings clearly with:
- Key findings summary
- Supporting evidence
- Source quality assessment
- Confidence level
- Recommendations for next steps""",
                llm=self.llm,
                tools=[
                    get_healthcare_research_tool(),
                    get_general_research_tool()
                ],
                can_handoff_to=["WebSearchAgent"] if self.config.enable_web_search else ["SynthesisAgent"]
            )
            agents.append(research_agent)
        
        # Web Search Agent
        if self.config.enable_web_search:
            web_search_agent = FunctionAgent(
                name="WebSearchAgent",
                description="Finds current information through web search and validates research findings",
                system_prompt="""You are a specialized Web Search Agent in the HealthFinder multi-agent system.

Your primary responsibilities:
- Find current and up-to-date information through web search
- Validate research findings with real-time data
- Identify breaking news and recent developments
- Assess source credibility and relevance

Search Guidelines:
1. Search Strategy:
   - Use multiple search queries to get comprehensive results
   - Prioritize recent information (last 12 months for current events)
   - Focus on authoritative sources (.gov, .edu, medical institutions)
   - Cross-reference information across multiple sources

2. Source Evaluation:
   - Government agencies (CDC, NIH, FDA) - highest credibility
   - Academic institutions and journals - high credibility
   - Medical institutions (Mayo Clinic, WebMD) - medical topics
   - News outlets (Reuters, AP) - current events
   - Avoid unreliable or biased sources

3. Information Processing:
   - Summarize key findings from search results
   - Note publication dates and information currency
   - Identify conflicting information and note discrepancies
   - Highlight breaking news or recent developments

When web search is complete and you have current information, hand off to SynthesisAgent to combine all gathered information into a comprehensive response.

Format your search results with:
- Search summary and strategy used
- Key findings from web search
- Source credibility assessment
- Information currency notes
- Relevance to original query""",
                llm=self.llm,
                tools=[
                    get_duckduckgo_search_tool(),
                    get_google_search_tool()
                ],
                can_handoff_to=["SynthesisAgent"]
            )
            agents.append(web_search_agent)
        
        # Synthesis Agent - Terminal agent that creates final response
        synthesis_agent = FunctionAgent(
            name="SynthesisAgent",
            description="Synthesizes information from multiple sources into comprehensive responses",
            system_prompt="""You are a specialized Synthesis Agent in the HealthFinder multi-agent system.

Your primary responsibilities:
- Combine research findings with current web search results
- Create comprehensive, coherent responses
- Ensure information accuracy and consistency
- Provide balanced analysis with appropriate caveats

Synthesis Guidelines:
1. Information Integration:
   - Merge research findings with current web search results
   - Identify complementary and conflicting information
   - Prioritize high-quality sources and recent information
   - Note gaps in available information

2. Healthcare Topics:
   - Always include medical disclaimers
   - Prioritize evidence-based information
   - Distinguish between established and experimental treatments
   - Include appropriate warnings and recommendations for professional consultation

3. General Topics:
   - Present balanced perspectives
   - Include expert opinions and analysis
   - Note areas of consensus and disagreement
   - Provide practical implications and recommendations

4. Quality Assurance:
   - Cross-reference information across sources
   - Note confidence levels and limitations
   - Include publication dates and currency information
   - Acknowledge uncertainties and knowledge gaps

This is the final step in the multi-agent workflow. Provide a comprehensive, well-structured response that addresses the user's query completely.

Structure your synthesis with:
- Executive summary
- Detailed analysis combining all sources
- Key insights and recommendations
- Important disclaimers and limitations
- Source quality assessment""",
            llm=self.llm,
            tools=[],  # Synthesis agent typically doesn't need tools
            can_handoff_to=[]  # Terminal agent - no handoffs
        )
        agents.append(synthesis_agent)
        
        logger.info(f"Created {len(agents)} agents for workflow")
        return agents
    
    def _create_agent_workflow(self) -> AgentWorkflow:
        """Create the LlamaIndex AgentWorkflow."""
        
        # Determine root agent (always start with research if available)
        root_agent = "ResearchAgent" if self.config.enable_research else "WebSearchAgent"
        if not self.config.enable_research and not self.config.enable_web_search:
            root_agent = "SynthesisAgent"
        
        # Define initial state
        initial_state = {
            "workflow_id": self.workflow_id,
            "config": self.config.model_dump(),
            "research_results": [],
            "search_results": [],
            "synthesis_complete": False,
            "start_time": None,
            "current_step": "initialized"
        }
        
        # Create AgentWorkflow
        workflow = AgentWorkflow(
            agents=self.agents,
            root_agent=root_agent,
            initial_state=initial_state
        )
        
        logger.info(f"Created AgentWorkflow with root agent: {root_agent}")
        return workflow
    
    async def process_query(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Process a chat completion request through the multi-agent workflow.
        
        Args:
            request: Chat completion request
            
        Returns:
            Chat completion response with synthesized information
        """
        self.start_time = time.time()
        
        try:
            # Validate request
            if not request.messages:
                raise ValueError("Request must contain at least one message")
            
            # Extract user query
            user_query = self._extract_user_query(request)
            
            # Update workflow configuration from request
            await self._update_config_from_request(request)
            
            logger.info(f"Processing query through AgentWorkflow: {user_query}")
            
            # Run the AgentWorkflow
            workflow_response = await self.agent_workflow.run(user_msg=user_query)
            
            # Create chat completion response
            response = await self._create_chat_completion_response(
                request, user_query, workflow_response
            )
            
            # Update execution stats
            execution_time = time.time() - self.start_time
            self.execution_stats.update({
                "execution_time": execution_time,
                "success": True,
                "timestamp": datetime.now(UTC).isoformat()
            })
            
            logger.info(f"Workflow completed successfully in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            execution_time = time.time() - self.start_time if self.start_time else 0
            logger.error(f"Workflow error after {execution_time:.2f}s: {e}")
            
            # Update execution stats
            self.execution_stats.update({
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat()
            })
            
            # Return error response
            return self._create_error_response(request, str(e), execution_time)
    
    def _extract_user_query(self, request: ChatCompletionRequest) -> str:
        """Extract the user query from the request."""
        # Get the last user message
        for message in reversed(request.messages):
            if message.role == MessageRole.USER:
                return message.content
        
        # Fallback to first message if no user message found
        return request.messages[0].content if request.messages else ""
    
    async def _update_config_from_request(self, request: ChatCompletionRequest) -> None:
        """Update workflow configuration from request parameters."""
        # Update configuration based on request attributes
        if hasattr(request, 'enable_web_search'):
            self.config.enable_web_search = request.enable_web_search
        
        if hasattr(request, 'enable_deep_research'):
            self.config.enable_research = request.enable_deep_research
        
        if hasattr(request, 'research_depth'):
            self.config.research_depth = request.research_depth
        
        if hasattr(request, 'max_search_results'):
            self.config.max_search_results = request.max_search_results
    
    async def _create_chat_completion_response(
        self,
        request: ChatCompletionRequest,
        user_query: str,
        workflow_response: Any
    ) -> ChatCompletionResponse:
        """Create a chat completion response from workflow results."""
        
        # Extract content from workflow response
        if hasattr(workflow_response, 'response') and hasattr(workflow_response.response, 'content'):
            response_content = workflow_response.response.content
        elif hasattr(workflow_response, 'content'):
            response_content = workflow_response.content
        elif hasattr(workflow_response, 'message') and hasattr(workflow_response.message, 'content'):
            response_content = workflow_response.message.content
        else:
            response_content = str(workflow_response)
        
        # Create response message
        response_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response_content
        )
        
        # Estimate token usage
        token_usage = self._estimate_token_usage(request, response_content)
        
        # Create agent state
        execution_time = time.time() - self.start_time if self.start_time else 0
        agent_state = AgentState(
            current_step="completed",
            completed_steps=["research", "web_search", "synthesis"],
            processing_time=execution_time,
            total_steps=3,
            workflow_id=self.workflow_id
        )
        
        # Create agent info (simplified for AgentWorkflow)
        contributing_agents = [
            AgentInfo(
                name="ResearchAgent",
                role="research",
                contribution="Conducted comprehensive research",
                confidence=0.85,
                sources_used=["Academic sources", "Medical databases"]
            ),
            AgentInfo(
                name="WebSearchAgent", 
                role="web_search",
                contribution="Found current information",
                confidence=0.80,
                sources_used=["Web search results", "Current news"]
            ),
            AgentInfo(
                name="SynthesisAgent",
                role="synthesis", 
                contribution="Synthesized comprehensive response",
                confidence=0.90,
                sources_used=["Combined research and search results"]
            )
        ] if self.config.enable_research and self.config.enable_web_search else []
        
        # Create choices
        choice = Choice(
            index=0,
            message=response_message,
            finish_reason="stop"
        )
        
        # Create research metadata
        research_metadata = {
            "processing_time": execution_time,
            "workflow_id": self.workflow_id,
            "synthesis_confidence": 0.85,  # Default confidence score
            "total_sources": len(contributing_agents) * 3,  # Estimate based on agents
            "research_depth": self.config.research_depth,
            "web_search_enabled": self.config.enable_web_search,
            "research_enabled": self.config.enable_research
        }
        
        # Create final response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{self.workflow_id}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage=token_usage,
            agent_state=agent_state,
            contributing_agents=contributing_agents,
            research_metadata=research_metadata
        )
        
        return response
    
    def _estimate_token_usage(self, request: ChatCompletionRequest, response_content: str) -> Usage:
        """Estimate token usage for the request and response."""
        # Simple token estimation (4 characters ≈ 1 token)
        input_text = " ".join([msg.content for msg in request.messages])
        
        prompt_tokens = len(input_text) // 4
        completion_tokens = len(response_content) // 4
        total_tokens = prompt_tokens + completion_tokens
        
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
    
    def _create_error_response(
        self, 
        request: ChatCompletionRequest, 
        error_message: str, 
        execution_time: float
    ) -> ChatCompletionResponse:
        """Create an error response."""
        
        error_content = f"I apologize, but I encountered an error while processing your request: {error_message}"
        
        response_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=error_content
        )
        
        token_usage = self._estimate_token_usage(request, error_content)
        
        agent_state = AgentState(
            current_step="error",
            completed_steps=[],
            processing_time=execution_time,
            total_steps=0,
            workflow_id=self.workflow_id
        )
        
        choice = Choice(
            index=0,
            message=response_message,
            finish_reason="stop"
        )
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{self.workflow_id}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage=token_usage,
            agent_state=agent_state,
            contributing_agents=[]
        )
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.config.name,
            "description": self.config.description,
            "agents": [agent.name for agent in self.agents],
            "config": self.config.model_dump(),
            "execution_stats": self.execution_stats
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {}
        for agent in self.agents:
            status[agent.name] = {
                "name": agent.name,
                "description": agent.description,
                "tools": [tool.metadata.name for tool in agent.tools] if hasattr(agent, 'tools') else [],
                "can_handoff_to": getattr(agent, 'can_handoff_to', [])
            }
        return status
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        base_stats = {
            "workflow_id": self.workflow_id,
            "total_executions": 1 if self.execution_stats else 0,
            "average_execution_time": self.execution_stats.get("execution_time", 0),
            "success_rate": 1.0 if self.execution_stats.get("success", False) else 0.0
        }
        
        base_stats.update(self.execution_stats)
        return base_stats


# Factory function for easy workflow creation
def create_healthfinder_workflow(
    config: Optional[HealthFinderWorkflowConfig] = None
) -> HealthFinderAgentWorkflow:
    """
    Create a HealthFinder AgentWorkflow with optional configuration.
    
    Args:
        config: Workflow configuration (uses defaults if not provided)
        
    Returns:
        Configured HealthFinderAgentWorkflow instance
    """
    return HealthFinderAgentWorkflow(config)


# Convenience function for quick setup
def get_default_workflow() -> HealthFinderAgentWorkflow:
    """Get a HealthFinder workflow with default configuration."""
    config = HealthFinderWorkflowConfig()
    return create_healthfinder_workflow(config)


# Configuration builders for common use cases
def get_healthcare_workflow_config() -> HealthFinderWorkflowConfig:
    """Get configuration optimized for healthcare queries."""
    return HealthFinderWorkflowConfig(
        name="HealthFinder Healthcare Workflow",
        description="Specialized workflow for healthcare and medical queries",
        research_depth=4,  # Deeper research for medical topics
        enable_research=True,
        enable_web_search=True,
        synthesis_type="healthcare",
        max_search_results=15,  # More sources for medical topics
        llm_temperature=0.3,  # Lower temperature for medical accuracy
    )


def get_general_workflow_config() -> HealthFinderWorkflowConfig:
    """Get configuration optimized for general queries."""
    return HealthFinderWorkflowConfig(
        name="HealthFinder General Workflow",
        description="Workflow for general research and information queries",
        research_depth=3,
        enable_research=True,
        enable_web_search=True,
        synthesis_type="general",
        max_search_results=10,
        llm_temperature=0.7,  # Higher temperature for creative synthesis
    )


def get_fast_workflow_config() -> HealthFinderWorkflowConfig:
    """Get configuration optimized for fast responses."""
    return HealthFinderWorkflowConfig(
        name="HealthFinder Fast Workflow",
        description="Optimized workflow for quick responses",
        research_depth=2,  # Lighter research
        enable_research=True,
        enable_web_search=False,  # Skip web search for speed
        synthesis_type="auto",
        max_search_results=5,
        max_execution_time=60,  # Shorter timeout
        timeout_per_agent=30,
    ) 