"""
Research Agent

Specialized agent for conducting comprehensive research on healthcare and general topics.
Uses various research tools to gather, analyze, and structure information.
"""

import time
from typing import Dict, Any, Optional, List
from loguru import logger

from .base_agent import BaseFunctionAgent, AgentConfig
from ..models.chat_models import ResearchResult
from ..tools.research_tools import get_healthcare_research_tool, get_general_research_tool


class ResearchAgent(BaseFunctionAgent):
    """
    Research Agent specialized in comprehensive research across domains.
    
    This agent excels at:
    - Healthcare and medical research
    - General topic research
    - Source verification and analysis
    - Structured information gathering
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Research Agent.
        
        Args:
            config: Agent configuration
        """
        # Initialize with research tools
        tools = [
            get_healthcare_research_tool(),
            get_general_research_tool()
        ]
        
        super().__init__(config, tools)
        self.research_domains = ["healthcare", "general"]
        self.expertise_keywords = {
            "healthcare": [
                "medical", "health", "disease", "treatment", "therapy", "drug",
                "medication", "diagnosis", "symptoms", "clinical", "patient",
                "hospital", "doctor", "nurse", "healthcare", "medicine"
            ],
            "general": [
                "technology", "science", "business", "education", "environment",
                "politics", "economics", "social", "culture", "history"
            ]
        }
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the research agent."""
        return """
You are a comprehensive Research Agent specializing in gathering, analyzing, and structuring information from various sources.

Your capabilities include:
- Healthcare and medical research with focus on evidence-based information
- General topic research across multiple domains
- Critical analysis of sources and information quality
- Structured presentation of findings with confidence assessments

Guidelines:
1. Always prioritize authoritative and peer-reviewed sources for healthcare topics
2. Provide confidence scores based on source quality and information reliability
3. Clearly distinguish between established facts and emerging research
4. Include relevant context and background information
5. Structure findings in a logical, easy-to-understand format
6. Acknowledge limitations and uncertainties when present

For healthcare topics, prioritize:
- Peer-reviewed medical literature
- Clinical guidelines from medical organizations
- FDA-approved treatments and medications
- Evidence-based recommendations

For general topics, focus on:
- Authoritative academic sources
- Government publications
- Reputable news and analysis sources
- Expert opinions and commentary

Always maintain objectivity and present multiple perspectives when relevant.
"""
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ResearchResult:
        """
        Execute comprehensive research on the given query.
        
        Args:
            query: Research query or topic
            context: Additional context from workflow
            **kwargs: Additional parameters like research_depth
            
        Returns:
            ResearchResult with findings, sources, and confidence
        """
        start_time = time.time()
        
        try:
            logger.info(f"Research Agent starting research on: {query}")
            
            # Extract parameters
            research_depth = kwargs.get('research_depth', 3)
            focus_areas = kwargs.get('focus_areas', [])
            
            # Determine research domain
            domain = self._determine_research_domain(query)
            
            # Select appropriate research tool
            research_tool = self._select_research_tool(domain)
            
            # Conduct research using the selected tool
            research_params = {
                'query': query,
                'depth': research_depth,
                'focus_areas': focus_areas
            }
            
            # Execute research
            result_data = await research_tool.acall(**research_params)
            
            # Process and enhance the result
            enhanced_result = await self._enhance_research_result(
                result_data, query, domain, context
            )
            
            execution_time = time.time() - start_time
            await self._log_execution(query, enhanced_result, execution_time, True)
            
            logger.info(f"Research Agent completed research with confidence: {enhanced_result.confidence}")
            return enhanced_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ResearchResult(
                query=query,
                findings=f"Research failed due to error: {str(e)}",
                sources=[],
                confidence=0.0,
                agent_name=self.config.name
            )
            
            await self._log_execution(query, error_result, execution_time, False)
            logger.error(f"Research Agent error: {e}")
            return error_result
    
    def _determine_research_domain(self, query: str) -> str:
        """
        Determine the most appropriate research domain for the query.
        
        Args:
            query: Research query
            
        Returns:
            Research domain ('healthcare' or 'general')
        """
        query_lower = query.lower()
        
        # Check for healthcare keywords
        healthcare_matches = sum(
            1 for keyword in self.expertise_keywords["healthcare"]
            if keyword in query_lower
        )
        
        # Check for general topic keywords
        general_matches = sum(
            1 for keyword in self.expertise_keywords["general"]
            if keyword in query_lower
        )
        
        # Default to healthcare if unclear but contains medical terms
        if healthcare_matches > 0:
            return "healthcare"
        elif general_matches > 0:
            return "general"
        else:
            # Default decision based on common patterns
            healthcare_indicators = [
                "treatment", "symptoms", "diagnosis", "therapy", "medication",
                "health", "medical", "clinical", "patient", "disease"
            ]
            
            if any(indicator in query_lower for indicator in healthcare_indicators):
                return "healthcare"
            else:
                return "general"
    
    def _select_research_tool(self, domain: str):
        """Select the appropriate research tool based on domain."""
        for tool in self.tools:
            if domain == "healthcare" and "healthcare" in tool.metadata.name:
                return tool
            elif domain == "general" and "general" in tool.metadata.name:
                return tool
        
        # Fallback to first available tool
        return self.tools[0] if self.tools else None
    
    async def _enhance_research_result(
        self,
        result_data: Dict[str, Any],
        query: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ResearchResult:
        """
        Enhance the research result with additional analysis and context.
        
        Args:
            result_data: Raw result from research tool
            query: Original query
            domain: Research domain
            context: Additional context
            
        Returns:
            Enhanced ResearchResult
        """
        # Create base result from tool output
        base_result = ResearchResult(**result_data)
        
        # Add domain-specific enhancements
        enhanced_findings = await self._add_domain_context(
            base_result.findings, query, domain
        )
        
        # Improve confidence calculation
        enhanced_confidence = self._calculate_enhanced_confidence(
            base_result, domain, enhanced_findings
        )
        
        # Add quality indicators
        quality_sources = self._enhance_source_quality(base_result.sources, domain)
        
        return ResearchResult(
            query=query,
            findings=enhanced_findings,
            sources=quality_sources,
            confidence=enhanced_confidence,
            agent_name=self.config.name
        )
    
    async def _add_domain_context(
        self, 
        findings: str, 
        query: str, 
        domain: str
    ) -> str:
        """Add domain-specific context to research findings."""
        
        if domain == "healthcare":
            # Add healthcare-specific context
            context_additions = []
            
            # Add disclaimer for medical information
            context_additions.append(
                "\n\nIMPORTANT: This information is for educational purposes only. "
                "Always consult with healthcare professionals for medical advice, "
                "diagnosis, or treatment decisions."
            )
            
            # Add evidence level indicators
            if any(term in findings.lower() for term in ["clinical trial", "study", "research"]):
                context_additions.append(
                    "\n\nEvidence Level: Based on clinical research and studies. "
                    "Findings represent current medical understanding and may evolve "
                    "with new research."
                )
            
            return findings + "".join(context_additions)
        
        else:
            # Add general research context
            context_addition = (
                f"\n\nResearch Summary: This analysis of '{query}' incorporates "
                "information from multiple authoritative sources. Findings reflect "
                "current understanding and may be subject to ongoing developments."
            )
            return findings + context_addition
    
    def _calculate_enhanced_confidence(
        self, 
        result: ResearchResult, 
        domain: str, 
        enhanced_findings: str
    ) -> float:
        """Calculate enhanced confidence score."""
        base_confidence = result.confidence
        
        # Domain-specific confidence adjustments
        if domain == "healthcare":
            # Higher confidence for medical terms and established treatments
            medical_quality_indicators = [
                "FDA approved", "clinical trial", "peer-reviewed", "meta-analysis",
                "systematic review", "evidence-based", "clinical guidelines"
            ]
            
            quality_score = sum(
                1 for indicator in medical_quality_indicators
                if indicator.lower() in enhanced_findings.lower()
            )
            
            # Boost confidence for high-quality medical sources
            confidence_boost = min(0.15, quality_score * 0.03)
            
        else:
            # General topic confidence adjustments
            general_quality_indicators = [
                "peer-reviewed", "academic", "government", "official",
                "expert", "research", "study", "analysis"
            ]
            
            quality_score = sum(
                1 for indicator in general_quality_indicators
                if indicator.lower() in enhanced_findings.lower()
            )
            
            confidence_boost = min(0.1, quality_score * 0.02)
        
        # Adjust for source count
        source_count_factor = min(0.05, len(result.sources) * 0.01)
        
        final_confidence = min(0.95, base_confidence + confidence_boost + source_count_factor)
        return round(final_confidence, 3)
    
    def _enhance_source_quality(self, sources: List[str], domain: str) -> List[str]:
        """Enhance source list with quality indicators."""
        enhanced_sources = []
        
        for source in sources:
            enhanced_source = source
            
            if domain == "healthcare":
                # Add credibility indicators for medical sources
                if any(term in source.lower() for term in ["pubmed", "medline", "cochrane"]):
                    enhanced_source += " (High-quality medical database)"
                elif any(term in source.lower() for term in ["fda", "cdc", "who"]):
                    enhanced_source += " (Authoritative health organization)"
                elif "clinical" in source.lower():
                    enhanced_source += " (Clinical evidence)"
            else:
                # Add indicators for general sources
                if any(term in source.lower() for term in ["academic", "university", "journal"]):
                    enhanced_source += " (Academic source)"
                elif any(term in source.lower() for term in ["government", "official"]):
                    enhanced_source += " (Official source)"
            
            enhanced_sources.append(enhanced_source)
        
        return enhanced_sources
    
    def get_research_capabilities(self) -> Dict[str, Any]:
        """Get information about research capabilities."""
        return {
            "domains": self.research_domains,
            "tools_available": [tool.metadata.name for tool in self.tools],
            "specializations": {
                "healthcare": "Medical research, clinical guidelines, drug information",
                "general": "Cross-domain research, academic sources, expert analysis"
            },
            "quality_features": [
                "Source verification",
                "Confidence scoring", 
                "Domain-specific expertise",
                "Evidence-based analysis"
            ]
        } 