"""
Concierge Workflow

Main workflow that orchestrates the multi-agent system for comprehensive
research and response generation. Implements the concierge pattern where
a coordinator agent manages multiple specialized function agents.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from llama_index.core.workflow import StartEvent, StopEvent, step
from pydantic import BaseModel, Field
from loguru import logger

from .base_workflow import (
    BaseWorkflow, WorkflowConfig, 
    QueryAnalysisEvent, ResearchCompleteEvent, 
    WebSearchCompleteEvent, SynthesisCompleteEvent,
    MultipleEventsEvent
)
from ..models.chat_models import (
    ChatCompletionRequest, ChatCompletionResponse, ChatMessage, MessageRole,
    Choice, Usage, AgentInfo, AgentState
)
from ..function_agents import AgentFactory


class ConciergeWorkflowConfig(WorkflowConfig):
    """Configuration specific to the concierge workflow."""
    enable_web_search: bool = Field(default=True, description="Enable web search agent")
    enable_deep_research: bool = Field(default=True, description="Enable research agent")
    research_depth: int = Field(default=3, ge=1, le=5, description="Research depth level")
    max_search_results: int = Field(default=10, ge=1, le=50, description="Max web search results")
    synthesis_type: str = Field(default="general", description="Type of synthesis to perform")
    parallel_agent_execution: bool = Field(default=True, description="Run agents in parallel when possible")


class ConciergeWorkflow(BaseWorkflow):
    """
    Concierge Workflow that orchestrates multiple agents for comprehensive research.
    
    This workflow implements the multi-agent pattern where:
    1. Query analysis determines research strategy
    2. Research and web search agents work in parallel
    3. Synthesis agent combines all results
    4. Final response is generated with full context
    """
    
    def __init__(self, config: ConciergeWorkflowConfig):
        """
        Initialize the concierge workflow.
        
        Args:
            config: Workflow configuration
        """
        super().__init__(config)
        self.config: ConciergeWorkflowConfig = config
        
        # Initialize agents
        self.research_agent = AgentFactory.create_research_agent()
        self.web_search_agent = AgentFactory.create_web_search_agent()
        self.synthesis_agent = AgentFactory.create_synthesis_agent()
        
        # Track contributing agents
        self.contributing_agents: List[AgentInfo] = []
        
        logger.info("Concierge Workflow initialized with multi-agent coordination")
    
    async def process_query(
        self, 
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Process a chat completion request through the multi-agent workflow.
        
        Args:
            request: Chat completion request
            
        Returns:
            Chat completion response with synthesized information
        """
        start_time = time.time()
        
        try:
            # Validate request
            if not await self._validate_request(request):
                return self._create_error_response(
                    request, "Invalid request format", time.time() - start_time
                )
            
            # Initialize workflow state
            self.current_state = self._initialize_agent_state(request)
            self.contributing_agents = []
            
            # Extract user query from last message
            user_query = self._extract_user_query(request)
            
            # Start workflow execution
            logger.info(f"Starting concierge workflow for query: {user_query}")
            
            # Run the workflow
            result = await self.run(
                query=user_query,
                request=request
            )
            
            execution_time = time.time() - start_time
            
            # Update final state
            self.current_state.processing_time = execution_time
            self.current_state.current_step = "completed"
            
            await self._log_execution_step("workflow_complete", execution_time, True)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Concierge workflow error: {e}")
            await self._log_execution_step("workflow_error", execution_time, False)
            return self._create_error_response(request, str(e), execution_time)
    
    @step
    async def analyze_query(self, ev: StartEvent) -> QueryAnalysisEvent:
        """
        Analyze the user query to determine research strategy.
        
        Args:
            ev: Start event containing query and request
            
        Returns:
            QueryAnalysisEvent with analysis results
        """
        step_start = time.time()
        
        try:
            query = ev.query
            request = ev.request
            
            logger.info(f"Analyzing query: {query}")
            self._update_agent_state("query_analysis")
            
            # Determine query characteristics
            analysis_result = await self._analyze_query_content(query, request)
            
            execution_time = time.time() - step_start
            await self._log_execution_step("query_analysis", execution_time, True, analysis_result)
            
            return QueryAnalysisEvent(
                query=query,
                analysis_result=analysis_result,
                data={"request": request}
            )
            
        except Exception as e:
            execution_time = time.time() - step_start
            await self._log_execution_step("query_analysis", execution_time, False)
            raise e
    
    @step
    async def execute_research_and_search(
        self, 
        ev: QueryAnalysisEvent
    ) -> MultipleEventsEvent:
        """
        Execute research and web search in parallel based on query analysis.
        
        Args:
            ev: Query analysis event
            
        Returns:
            MultipleEventsEvent containing research and search completion events
        """
        step_start = time.time()
        
        try:
            query = ev.query
            analysis = ev.analysis_result
            request = ev.data["request"]
            
            logger.info("Executing parallel research and web search")
            self._update_agent_state("parallel_execution")
            
            # Prepare execution tasks
            tasks = []
            
            # Research task
            if self.config.enable_deep_research and analysis.get("needs_research", True):
                research_task = self._execute_research_agent(query, analysis, request)
                tasks.append(research_task)
            
            # Web search task
            if self.config.enable_web_search and analysis.get("needs_current_info", True):
                search_task = self._execute_web_search_agent(query, analysis, request)
                tasks.append(search_task)
            
            # Execute tasks in parallel or sequentially
            if self.config.parallel_agent_execution and len(tasks) > 1:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                results = []
                for task in tasks:
                    result = await task
                    results.append(result)
            
            # Process results and create events
            events = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Agent execution error: {result}")
                    continue
                events.append(result)
            
            execution_time = time.time() - step_start
            await self._log_execution_step("parallel_execution", execution_time, True)
            
            return MultipleEventsEvent(events=events)
            
        except Exception as e:
            execution_time = time.time() - step_start
            await self._log_execution_step("parallel_execution", execution_time, False)
            raise e
    
    @step
    async def synthesize_results(
        self, 
        ev: MultipleEventsEvent
    ) -> SynthesisCompleteEvent:
        """
        Synthesize results from all agents into a coherent response.
        
        Args:
            ev: MultipleEventsEvent containing completion events from various agents
            
        Returns:
            SynthesisCompleteEvent with final synthesis
        """
        step_start = time.time()
        
        try:
            logger.info("Synthesizing results from all agents")
            self._update_agent_state("synthesis", "SynthesisAgent")
            
            # Extract results from events
            research_results = []
            web_search_results = []
            
            for event in ev.events:
                if isinstance(event, ResearchCompleteEvent):
                    research_results.extend(event.research_results)
                elif isinstance(event, WebSearchCompleteEvent):
                    web_search_results.extend(event.search_results)
            
            # Update state with collected results
            self.current_state.research_results = research_results
            self.current_state.web_search_results = web_search_results
            
            # Determine synthesis type
            synthesis_type = self._determine_synthesis_type(research_results, web_search_results)
            
            # Execute synthesis
            synthesis_context = {
                "research_results": research_results,
                "web_search_results": web_search_results
            }
            
            # Get the original query from the first event
            original_query = getattr(ev.events[0], 'query', 'Unknown query') if ev.events else 'Unknown query'
            
            synthesis_result = await self.synthesis_agent.execute(
                query=original_query,
                context=synthesis_context,
                synthesis_type=synthesis_type
            )
            
            # Update state
            self.current_state.synthesis_result = synthesis_result
            
            # Add synthesis agent to contributors
            self.contributing_agents.append(AgentInfo(
                name=self.synthesis_agent.config.name,
                role="synthesis",
                contribution="Synthesized information from multiple sources",
                confidence=synthesis_result.confidence,
                sources_used=[str(len(synthesis_result.source_results)) + " total sources"]
            ))
            
            execution_time = time.time() - step_start
            await self._log_execution_step("synthesis", execution_time, True)
            
            return SynthesisCompleteEvent(
                synthesis_result=synthesis_result,
                data={"original_query": original_query}
            )
            
        except Exception as e:
            execution_time = time.time() - step_start
            await self._log_execution_step("synthesis", execution_time, False)
            raise e
    
    @step
    async def generate_final_response(
        self, 
        ev: SynthesisCompleteEvent
    ) -> StopEvent:
        """
        Generate the final chat completion response.
        
        Args:
            ev: Synthesis completion event
            
        Returns:
            StopEvent with the final response
        """
        step_start = time.time()
        
        try:
            logger.info("Generating final response")
            self._update_agent_state("response_generation")
            
            synthesis_result = ev.synthesis_result
            original_query = ev.data.get("original_query", "Unknown query")
            
            # Create the response message
            response_content = self._format_final_response(synthesis_result, original_query)
            
            # Estimate token usage
            dummy_request = ChatCompletionRequest(messages=[ChatMessage(role=MessageRole.USER, content=original_query)])
            token_usage = self._estimate_token_usage(dummy_request, response_content)
            
            # Create final response
            final_response = self._create_success_response(
                dummy_request,
                response_content,
                token_usage,
                synthesis_result
            )
            
            execution_time = time.time() - step_start
            await self._log_execution_step("response_generation", execution_time, True)
            
            return StopEvent(result=final_response)
            
        except Exception as e:
            execution_time = time.time() - step_start
            await self._log_execution_step("response_generation", execution_time, False)
            raise e
    
    def _extract_user_query(self, request: ChatCompletionRequest) -> str:
        """Extract the user query from the request."""
        # Get the last user message
        for message in reversed(request.messages):
            if message.role == MessageRole.USER:
                return message.content
        
        # Fallback to first message if no user message found
        return request.messages[0].content if request.messages else ""
    
    async def _analyze_query_content(
        self, 
        query: str, 
        request: ChatCompletionRequest
    ) -> Dict[str, Any]:
        """Analyze query content to determine processing strategy."""
        
        query_lower = query.lower()
        
        # Determine if healthcare-related
        healthcare_keywords = [
            "health", "medical", "disease", "treatment", "therapy", "drug",
            "medication", "diagnosis", "symptoms", "clinical", "patient",
            "hospital", "doctor", "medicine"
        ]
        
        is_healthcare = any(keyword in query_lower for keyword in healthcare_keywords)
        
        # Determine if needs current information
        current_info_indicators = [
            "latest", "recent", "current", "new", "2024", "today",
            "now", "breakthrough", "development", "update"
        ]
        
        needs_current_info = any(indicator in query_lower for indicator in current_info_indicators)
        
        # Determine research depth needed
        depth_indicators = {
            1: ["simple", "quick", "brief", "summary"],
            2: ["detailed", "explain", "describe"],
            3: ["comprehensive", "complete", "thorough"],
            4: ["in-depth", "extensive", "detailed analysis"],
            5: ["exhaustive", "complete analysis", "research paper"]
        }
        
        suggested_depth = self.config.research_depth
        for depth, indicators in depth_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                suggested_depth = depth
                break
        
        return {
            "is_healthcare": is_healthcare,
            "needs_research": True,  # Always beneficial
            "needs_current_info": needs_current_info or self.config.enable_web_search,
            "suggested_depth": suggested_depth,
            "query_complexity": len(query.split()),
            "domain": "healthcare" if is_healthcare else "general"
        }
    
    async def _execute_research_agent(
        self, 
        query: str, 
        analysis: Dict[str, Any], 
        request: ChatCompletionRequest
    ) -> ResearchCompleteEvent:
        """Execute the research agent."""
        
        try:
            logger.info("Executing research agent")
            
            research_result = await self.research_agent.execute(
                query=query,
                research_depth=analysis.get("suggested_depth", self.config.research_depth)
            )
            
            # Add to contributing agents
            self.contributing_agents.append(AgentInfo(
                name=self.research_agent.config.name,
                role="research",
                contribution="Conducted comprehensive research",
                confidence=research_result.confidence,
                sources_used=research_result.sources
            ))
            
            return ResearchCompleteEvent(
                query=query,
                research_results=[research_result]
            )
            
        except Exception as e:
            logger.error(f"Research agent error: {e}")
            # Return empty result rather than failing
            return ResearchCompleteEvent(
                query=query,
                research_results=[]
            )
    
    async def _execute_web_search_agent(
        self, 
        query: str, 
        analysis: Dict[str, Any], 
        request: ChatCompletionRequest
    ) -> WebSearchCompleteEvent:
        """Execute the web search agent."""
        
        try:
            logger.info("Executing web search agent")
            
            search_type = "healthcare" if analysis.get("is_healthcare") else "general"
            
            search_results = await self.web_search_agent.execute(
                query=query,
                max_results=self.config.max_search_results,
                search_type=search_type
            )
            
            # Add to contributing agents
            self.contributing_agents.append(AgentInfo(
                name=self.web_search_agent.config.name,
                role="web_search",
                contribution="Found current information through web search",
                confidence=sum(r.relevance_score for r in search_results) / len(search_results) if search_results else 0.0,
                sources_used=[r.url for r in search_results[:3]]  # Top 3 sources
            ))
            
            return WebSearchCompleteEvent(
                query=query,
                search_results=search_results
            )
            
        except Exception as e:
            logger.error(f"Web search agent error: {e}")
            # Return empty result rather than failing
            return WebSearchCompleteEvent(
                query=query,
                search_results=[]
            )
    
    def _determine_synthesis_type(
        self, 
        research_results: List[Any], 
        web_search_results: List[Any]
    ) -> str:
        """Determine the type of synthesis to perform."""
        
        # Check if healthcare domain
        healthcare_indicators = sum(
            1 for result in research_results 
            if hasattr(result, 'agent_name') and 'healthcare' in result.agent_name.lower()
        )
        
        if healthcare_indicators > 0:
            return "healthcare"
        
        # Check if comparative analysis needed
        if len(research_results) + len(web_search_results) >= 4:
            return "comparative"
        
        # Check if analytical synthesis appropriate
        total_confidence = sum(
            getattr(result, 'confidence', 0.5) for result in research_results
        )
        
        if total_confidence >= 2.0:  # High total confidence suggests analytical depth
            return "analytical"
        
        return self.config.synthesis_type
    
    def _format_final_response(
        self, 
        synthesis_result: Any, 
        original_query: str
    ) -> str:
        """Format the final response content."""
        
        response = synthesis_result.synthesized_content
        
        # Add metadata footer
        response += f"\n\n---\n\n"
        response += f"**Research Methodology**: This response was generated using a multi-agent research system.\n\n"
        
        if synthesis_result.key_insights:
            response += "**Key Insights**:\n"
            for insight in synthesis_result.key_insights:
                response += f"• {insight}\n"
            response += "\n"
        
        if synthesis_result.recommendations:
            response += "**Recommendations**:\n"
            for rec in synthesis_result.recommendations:
                response += f"• {rec}\n"
            response += "\n"
        
        response += f"**Confidence Level**: {synthesis_result.confidence:.1%}\n"
        response += f"**Sources Analyzed**: {len(synthesis_result.source_results)} total sources\n"
        
        return response
    
    def _create_success_response(
        self,
        request: ChatCompletionRequest,
        response_content: str,
        token_usage: Dict[str, int],
        synthesis_result: Any
    ) -> ChatCompletionResponse:
        """Create a successful chat completion response."""
        
        import time
        
        choice = Choice(
            index=0,
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response_content
            ),
            finish_reason="stop"
        )
        
        usage = Usage(
            prompt_tokens=token_usage["prompt_tokens"],
            completion_tokens=token_usage["completion_tokens"],
            total_tokens=token_usage["total_tokens"]
        )
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{self.workflow_id}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage=usage,
            agent_state=self.current_state,
            contributing_agents=self.contributing_agents,
            research_metadata={
                "synthesis_confidence": synthesis_result.confidence,
                "total_sources": len(synthesis_result.source_results),
                "workflow_id": self.workflow_id,
                "processing_time": self.current_state.processing_time
            }
        )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents in the workflow."""
        return {
            "research_agent": self.research_agent.get_agent_info(),
            "web_search_agent": self.web_search_agent.get_agent_info(),
            "synthesis_agent": self.synthesis_agent.get_agent_info(),
            "workflow_stats": self.get_execution_stats()
        } 