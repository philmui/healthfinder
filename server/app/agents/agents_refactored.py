"""
Refactored Agents using Standard LlamaIndex FunctionAgent

This module implements the HealthFinder multi-agent system using LlamaIndex's
standard FunctionAgent and AgentWorkflow patterns following SOLID principles.
"""

from typing import List, Dict, Any, Optional
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import Context
from loguru import logger

from .tools.research_tools import (
    get_healthcare_research_tool, 
    get_general_research_tool,
    conduct_contextual_research
)
from .tools.web_search_tool import (
    get_duckduckgo_search_tool,
    get_google_search_tool,
    conduct_contextual_web_search
)
from app.core.config import settings


class HealthFinderAgentFactory:
    """
    Factory for creating standard LlamaIndex agents using SOLID principles.
    
    This factory encapsulates the creation logic for different agent types
    and ensures consistent configuration across the multi-agent system.
    """

    @staticmethod
    def get_default_llm() -> LLM:
        """Get the default LLM configuration for agents."""
        return OpenAI(
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
            api_key=settings.OPENAI_API_KEY
        )

    @staticmethod
    def create_research_agent(
        name: str = "ResearchAgent",
        llm: Optional[LLM] = None
    ) -> FunctionAgent:
        """
        Create a research agent using LlamaIndex FunctionAgent.
        
        This agent specializes in conducting comprehensive research on healthcare
        and general topics using evidence-based approaches.
        
        Args:
            name: Agent name
            llm: LLM instance (defaults to GPT-4)
            
        Returns:
            Configured FunctionAgent for research
        """
        if llm is None:
            llm = HealthFinderAgentFactory.get_default_llm()
            # Use lower temperature for more focused research
            llm.temperature = 0.3
        
        # Create research tools
        tools = [
            get_healthcare_research_tool(),
            get_general_research_tool()
        ]
        
        # Add contextual research tool
        async def research_with_context(ctx: Context, query: str, research_type: str = "auto") -> str:
            """Research with workflow context integration."""
            return await conduct_contextual_research(ctx, query, research_type)
        
        tools.append(research_with_context)
        
        system_prompt = """You are a specialized Research Agent in the HealthFinder multi-agent system.

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
- Recommendations for next steps"""

        agent = FunctionAgent(
            name=name,
            description="Conducts comprehensive research on healthcare and general topics with evidence-based analysis",
            system_prompt=system_prompt,
            llm=llm,
            tools=tools,
            can_handoff_to=["WebSearchAgent"]
        )
        
        logger.info(f"Created research agent: {name}")
        return agent

    @staticmethod
    def create_web_search_agent(
        name: str = "WebSearchAgent",
        llm: Optional[LLM] = None
    ) -> FunctionAgent:
        """
        Create a web search agent using LlamaIndex FunctionAgent.
        
        This agent specializes in finding current information through web search
        and validating research findings with real-time data.
        
        Args:
            name: Agent name
            llm: LLM instance (defaults to GPT-4)
            
        Returns:
            Configured FunctionAgent for web search
        """
        if llm is None:
            llm = HealthFinderAgentFactory.get_default_llm()
            # Use moderate temperature for balanced search
            llm.temperature = 0.5
        
        # Create web search tools
        tools = [
            get_duckduckgo_search_tool(),
            get_google_search_tool()
        ]
        
        # Add contextual search tool
        async def search_with_context(
            ctx: Context, 
            query: str, 
            search_engine: str = "duckduckgo"
        ) -> str:
            """Web search with workflow context integration."""
            return await conduct_contextual_web_search(ctx, query, search_engine)
        
        tools.append(search_with_context)
        
        system_prompt = """You are a specialized Web Search Agent in the HealthFinder multi-agent system.

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
- Relevance to original query"""

        agent = FunctionAgent(
            name=name,
            description="Finds current information through web search and validates research findings",
            system_prompt=system_prompt,
            llm=llm,
            tools=tools,
            can_handoff_to=["SynthesisAgent"]
        )
        
        logger.info(f"Created web search agent: {name}")
        return agent

    @staticmethod
    def create_synthesis_agent(
        name: str = "SynthesisAgent",
        llm: Optional[LLM] = None
    ) -> FunctionAgent:
        """
        Create a synthesis agent using LlamaIndex FunctionAgent.
        
        This agent specializes in combining information from multiple sources
        into coherent, comprehensive responses.
        
        Args:
            name: Agent name
            llm: LLM instance (defaults to GPT-4)
            
        Returns:
            Configured FunctionAgent for synthesis
        """
        if llm is None:
            llm = HealthFinderAgentFactory.get_default_llm()
            # Use higher temperature for creative synthesis
            llm.temperature = 0.7
        
        # Synthesis tools (functions that work with context)
        async def synthesize_healthcare_information(
            ctx: Context,
            topic: str,
            focus_areas: Optional[List[str]] = None
        ) -> str:
            """Synthesize healthcare information from research and web search results."""
            try:
                # Get research and search results from context
                research_state = await ctx.get("research_state", default={})
                search_state = await ctx.get("search_state", default={})
                
                research_results = research_state.get("last_research", {})
                search_results = search_state.get("last_search", {})
                
                # Create healthcare-specific synthesis
                synthesis = f"""## Comprehensive Healthcare Analysis: {topic}

### Evidence-Based Research Findings
{research_results.get('result', 'No research results available')}

### Current Information from Web Search
{search_results.get('results', 'No search results available')}

### Clinical Recommendations
Based on the gathered evidence, current clinical guidelines recommend:
- Following evidence-based treatment protocols
- Consulting with healthcare professionals for personalized advice
- Considering patient-specific factors and comorbidities
- Monitoring treatment response and adjusting as needed

### Important Medical Disclaimer
This information is for educational purposes only and should not replace professional medical advice. Always consult qualified healthcare providers for diagnosis, treatment, and medical decisions.

### Source Quality Assessment
- Research sources: Peer-reviewed medical literature, clinical guidelines
- Web search sources: Medical institutions, government health agencies
- Information currency: Current as of {search_results.get('timestamp', 'N/A')}
"""
                
                # Update synthesis state
                synthesis_state = await ctx.get("synthesis_state", default={})
                synthesis_state["healthcare_synthesis"] = {
                    "topic": topic,
                    "synthesis": synthesis,
                    "timestamp": search_results.get('timestamp', 'N/A')
                }
                await ctx.set("synthesis_state", synthesis_state)
                
                return synthesis
                
            except Exception as e:
                logger.error(f"Healthcare synthesis error: {e}")
                return f"Error synthesizing healthcare information: {str(e)}"

        async def synthesize_general_information(
            ctx: Context,
            topic: str,
            focus_areas: Optional[List[str]] = None
        ) -> str:
            """Synthesize general information from research and web search results."""
            try:
                # Get research and search results from context
                research_state = await ctx.get("research_state", default={})
                search_state = await ctx.get("search_state", default={})
                
                research_results = research_state.get("last_research", {})
                search_results = search_state.get("last_search", {})
                
                # Create general synthesis
                synthesis = f"""## Comprehensive Analysis: {topic}

### Research Findings
{research_results.get('result', 'No research results available')}

### Current Information and Developments
{search_results.get('results', 'No search results available')}

### Key Insights
- Academic research provides theoretical foundations and evidence
- Current information shows ongoing developments and trends
- Multiple perspectives offer comprehensive understanding
- Expert analysis guides practical applications

### Recommendations
- Consider multiple viewpoints when making decisions
- Stay updated with recent developments in the field
- Consult authoritative sources for important decisions
- Apply findings appropriately to specific contexts

### Information Quality
- Research sources: Academic journals, expert analysis
- Web search sources: Authoritative news, government publications
- Information currency: Current as of {search_results.get('timestamp', 'N/A')}
"""
                
                # Update synthesis state
                synthesis_state = await ctx.get("synthesis_state", default={})
                synthesis_state["general_synthesis"] = {
                    "topic": topic,
                    "synthesis": synthesis,
                    "timestamp": search_results.get('timestamp', 'N/A')
                }
                await ctx.set("synthesis_state", synthesis_state)
                
                return synthesis
                
            except Exception as e:
                logger.error(f"General synthesis error: {e}")
                return f"Error synthesizing general information: {str(e)}"

        tools = [
            synthesize_healthcare_information,
            synthesize_general_information
        ]
        
        system_prompt = """You are a specialized Synthesis Agent in the HealthFinder multi-agent system.

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
- Source quality assessment"""

        agent = FunctionAgent(
            name=name,
            description="Synthesizes information from multiple sources into comprehensive responses",
            system_prompt=system_prompt,
            llm=llm,
            tools=tools,
            can_handoff_to=[]  # Terminal agent - no handoffs
        )
        
        logger.info(f"Created synthesis agent: {name}")
        return agent

    @staticmethod
    def create_all_agents() -> Dict[str, FunctionAgent]:
        """
        Create all agents for the HealthFinder multi-agent system.
        
        Returns:
            Dictionary of agent names to FunctionAgent instances
        """
        agents = {
            "ResearchAgent": HealthFinderAgentFactory.create_research_agent(),
            "WebSearchAgent": HealthFinderAgentFactory.create_web_search_agent(),
            "SynthesisAgent": HealthFinderAgentFactory.create_synthesis_agent()
        }
        
        logger.info(f"Created {len(agents)} agents for HealthFinder system")
        return agents


# Convenience functions for backward compatibility
def get_research_agent() -> FunctionAgent:
    """Get a configured research agent."""
    return HealthFinderAgentFactory.create_research_agent()


def get_web_search_agent() -> FunctionAgent:
    """Get a configured web search agent."""
    return HealthFinderAgentFactory.create_web_search_agent()


def get_synthesis_agent() -> FunctionAgent:
    """Get a configured synthesis agent."""
    return HealthFinderAgentFactory.create_synthesis_agent()


def get_all_agents() -> List[FunctionAgent]:
    """Get all configured agents as a list."""
    agents_dict = HealthFinderAgentFactory.create_all_agents()
    return list(agents_dict.values()) 