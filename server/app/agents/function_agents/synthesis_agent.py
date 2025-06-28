"""
Synthesis Agent

Specialized agent for synthesizing information from multiple sources and agents
to create comprehensive, coherent, and well-structured responses.
"""

import time
from typing import Dict, Any, Optional, List, Union
from loguru import logger

from .base_agent import BaseFunctionAgent, AgentConfig
from ..models.chat_models import SynthesisResult, ResearchResult, WebSearchResult


class SynthesisAgent(BaseFunctionAgent):
    """
    Synthesis Agent specialized in combining and synthesizing information.
    
    This agent excels at:
    - Combining information from multiple sources
    - Creating coherent narratives from disparate data
    - Identifying key insights and patterns
    - Generating actionable recommendations
    - Structuring complex information clearly
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Synthesis Agent.
        
        Args:
            config: Agent configuration
        """
        # Synthesis agent typically doesn't need external tools
        # as it works with data from other agents
        super().__init__(config, tools=[])
        
        self.synthesis_strategies = {
            "healthcare": self._synthesize_healthcare_info,
            "general": self._synthesize_general_info,
            "comparative": self._synthesize_comparative_info,
            "analytical": self._synthesize_analytical_info
        }
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the synthesis agent."""
        return """
You are a Synthesis Agent specialized in combining information from multiple sources to create comprehensive, coherent, and actionable responses.

Your capabilities include:
- Analyzing and synthesizing information from research and web search results
- Identifying key themes, patterns, and insights across sources
- Creating well-structured, logical narratives
- Distinguishing between facts, opinions, and hypotheses
- Providing balanced perspectives and acknowledging uncertainties
- Generating actionable recommendations based on synthesized information

Synthesis Guidelines:
1. Prioritize information quality and source credibility
2. Identify and resolve conflicts between sources
3. Create logical flow and structure in your synthesis
4. Clearly distinguish between established facts and emerging information
5. Provide context and background for complex topics
6. Include confidence levels for different aspects of information
7. Generate practical insights and recommendations when appropriate

For different domains, adjust synthesis approach:
- Healthcare: Emphasize evidence-based information, clinical guidelines, and safety
- General topics: Focus on multiple perspectives, balanced analysis, and practical application
- Comparative analysis: Highlight similarities, differences, and trade-offs
- Analytical synthesis: Deep dive into cause-effect relationships and implications

Always maintain objectivity and acknowledge limitations in the available information.
"""
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SynthesisResult:
        """
        Execute synthesis of information from multiple sources.
        
        Args:
            query: Original query that prompted the research
            context: Context containing results from other agents
            **kwargs: Additional parameters like synthesis_type
            
        Returns:
            SynthesisResult with synthesized content and insights
        """
        start_time = time.time()
        
        try:
            logger.info(f"Synthesis Agent starting synthesis for: {query}")
            
            # Extract source results from context
            research_results = context.get('research_results', []) if context else []
            web_search_results = context.get('web_search_results', []) if context else []
            synthesis_type = kwargs.get('synthesis_type', 'general')
            
            # Validate input data
            if not research_results and not web_search_results:
                logger.warning("No source data provided for synthesis")
                return self._create_empty_synthesis_result(query)
            
            # Perform synthesis using appropriate strategy
            synthesis_strategy = self.synthesis_strategies.get(
                synthesis_type, 
                self._synthesize_general_info
            )
            
            synthesized_content = await synthesis_strategy(
                query, research_results, web_search_results, **kwargs
            )
            
            # Extract key insights
            key_insights = self._extract_key_insights(
                synthesized_content, research_results, web_search_results
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                query, synthesized_content, synthesis_type
            )
            
            # Calculate overall confidence
            confidence = self._calculate_synthesis_confidence(
                research_results, web_search_results, synthesized_content
            )
            
            # Combine all source results
            all_source_results = research_results + web_search_results
            
            result = SynthesisResult(
                synthesized_content=synthesized_content,
                source_results=all_source_results,
                confidence=confidence,
                key_insights=key_insights,
                recommendations=recommendations
            )
            
            execution_time = time.time() - start_time
            await self._log_execution(query, result, execution_time, True)
            
            logger.info(f"Synthesis Agent completed synthesis with confidence: {confidence}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = SynthesisResult(
                synthesized_content=f"Synthesis failed due to error: {str(e)}",
                source_results=[],
                confidence=0.0,
                key_insights=[],
                recommendations=[]
            )
            
            await self._log_execution(query, error_result, execution_time, False)
            logger.error(f"Synthesis Agent error: {e}")
            return error_result
    
    def _create_empty_synthesis_result(self, query: str) -> SynthesisResult:
        """Create an empty synthesis result when no data is available."""
        return SynthesisResult(
            synthesized_content=f"No information sources were available to synthesize a response to: {query}",
            source_results=[],
            confidence=0.0,
            key_insights=["No data available for analysis"],
            recommendations=["Please try a different query or check data sources"]
        )
    
    async def _synthesize_healthcare_info(
        self,
        query: str,
        research_results: List[ResearchResult],
        web_search_results: List[WebSearchResult],
        **kwargs
    ) -> str:
        """Synthesize healthcare-specific information."""
        
        # Start with query context
        synthesis = f"# Comprehensive Analysis: {query}\n\n"
        
        # Synthesize research findings
        if research_results:
            synthesis += "## Research Findings\n\n"
            
            high_confidence_research = [r for r in research_results if r.confidence >= 0.7]
            medium_confidence_research = [r for r in research_results if 0.4 <= r.confidence < 0.7]
            
            if high_confidence_research:
                synthesis += "### High-Confidence Research\n"
                for result in high_confidence_research:
                    synthesis += f"- **{result.agent_name}**: {result.findings}\n"
                    synthesis += f"  *Confidence: {result.confidence:.1%}*\n\n"
            
            if medium_confidence_research:
                synthesis += "### Supporting Research\n"
                for result in medium_confidence_research:
                    synthesis += f"- {result.findings}\n"
                    synthesis += f"  *Confidence: {result.confidence:.1%}*\n\n"
        
        # Synthesize web search findings
        if web_search_results:
            synthesis += "## Current Information\n\n"
            
            # Group by relevance score
            high_relevance = [r for r in web_search_results if r.relevance_score >= 0.7]
            medium_relevance = [r for r in web_search_results if 0.4 <= r.relevance_score < 0.7]
            
            if high_relevance:
                synthesis += "### Recent Developments\n"
                for result in high_relevance[:3]:  # Top 3 most relevant
                    synthesis += f"- **{result.title}**: {result.snippet}\n"
                    synthesis += f"  *Source: {result.url}*\n\n"
            
            if medium_relevance:
                synthesis += "### Additional Sources\n"
                for result in medium_relevance[:2]:  # Top 2 additional sources
                    synthesis += f"- {result.title}: {result.snippet}\n\n"
        
        # Add healthcare-specific disclaimers and context
        synthesis += "\n## Important Healthcare Information\n\n"
        synthesis += "**Medical Disclaimer**: This information is for educational purposes only. "
        synthesis += "Always consult with qualified healthcare professionals for medical advice, "
        synthesis += "diagnosis, or treatment decisions. Individual cases may vary significantly.\n\n"
        
        # Evidence quality assessment
        if research_results:
            avg_confidence = sum(r.confidence for r in research_results) / len(research_results)
            synthesis += f"**Evidence Quality**: Based on analysis of {len(research_results)} research sources "
            synthesis += f"with average confidence of {avg_confidence:.1%}.\n\n"
        
        return synthesis
    
    async def _synthesize_general_info(
        self,
        query: str,
        research_results: List[ResearchResult],
        web_search_results: List[WebSearchResult],
        **kwargs
    ) -> str:
        """Synthesize general topic information."""
        
        synthesis = f"# Comprehensive Analysis: {query}\n\n"
        
        # Create overview section
        synthesis += "## Overview\n\n"
        
        if research_results:
            # Use the highest confidence research result for overview
            best_research = max(research_results, key=lambda x: x.confidence)
            synthesis += f"{best_research.findings}\n\n"
        
        # Add current information
        if web_search_results:
            synthesis += "## Current Information and Developments\n\n"
            
            # Sort by relevance and include top results
            sorted_results = sorted(web_search_results, key=lambda x: x.relevance_score, reverse=True)
            
            for i, result in enumerate(sorted_results[:4], 1):
                synthesis += f"### {i}. {result.title}\n"
                synthesis += f"{result.snippet}\n"
                synthesis += f"*Source: {result.url}*\n\n"
        
        # Add additional research context
        if len(research_results) > 1:
            synthesis += "## Additional Research Perspectives\n\n"
            
            for result in research_results[1:]:  # Skip the first one used in overview
                if result.confidence >= 0.5:
                    synthesis += f"- {result.findings}\n\n"
        
        # Summary section
        synthesis += "## Summary\n\n"
        synthesis += f"This analysis of '{query}' draws from {len(research_results)} research sources "
        synthesis += f"and {len(web_search_results)} current information sources. "
        synthesis += "The information presented reflects current understanding and may evolve "
        synthesis += "with new developments and research.\n\n"
        
        return synthesis
    
    async def _synthesize_comparative_info(
        self,
        query: str,
        research_results: List[ResearchResult],
        web_search_results: List[WebSearchResult],
        **kwargs
    ) -> str:
        """Synthesize information with comparative analysis."""
        
        synthesis = f"# Comparative Analysis: {query}\n\n"
        
        # Identify different perspectives or options
        all_sources = research_results + web_search_results
        
        if len(all_sources) >= 2:
            synthesis += "## Different Perspectives and Approaches\n\n"
            
            for i, source in enumerate(all_sources[:4], 1):
                if isinstance(source, ResearchResult):
                    synthesis += f"### Perspective {i}: Research-Based\n"
                    synthesis += f"{source.findings}\n"
                    synthesis += f"*Confidence: {source.confidence:.1%}*\n\n"
                else:
                    synthesis += f"### Perspective {i}: Current Information\n"
                    synthesis += f"**{source.title}**: {source.snippet}\n"
                    synthesis += f"*Relevance: {source.relevance_score:.1%}*\n\n"
        
        # Add comparison summary
        synthesis += "## Comparative Summary\n\n"
        synthesis += "Based on the analysis of multiple sources, key points of agreement and "
        synthesis += "difference have been identified. This comparative view helps understand "
        synthesis += "the complexity and various aspects of the topic.\n\n"
        
        return synthesis
    
    async def _synthesize_analytical_info(
        self,
        query: str,
        research_results: List[ResearchResult],
        web_search_results: List[WebSearchResult],
        **kwargs
    ) -> str:
        """Synthesize information with deep analytical approach."""
        
        synthesis = f"# Analytical Deep Dive: {query}\n\n"
        
        # Structured analytical approach
        synthesis += "## Problem Analysis\n\n"
        
        if research_results:
            synthesis += "### Research-Based Analysis\n"
            for result in research_results:
                if result.confidence >= 0.6:
                    synthesis += f"- {result.findings}\n"
                    synthesis += f"  *Evidence Quality: {result.confidence:.1%}*\n\n"
        
        synthesis += "### Current Context and Developments\n"
        if web_search_results:
            for result in web_search_results[:3]:
                synthesis += f"- **{result.title}**: {result.snippet}\n\n"
        
        synthesis += "## Implications and Analysis\n\n"
        synthesis += "The synthesized information reveals several key implications "
        synthesis += "and analytical insights that warrant deeper consideration.\n\n"
        
        return synthesis
    
    def _extract_key_insights(
        self,
        synthesized_content: str,
        research_results: List[ResearchResult],
        web_search_results: List[WebSearchResult]
    ) -> List[str]:
        """Extract key insights from the synthesized content and sources."""
        
        insights = []
        
        # Insight from research quality
        if research_results:
            high_confidence_count = sum(1 for r in research_results if r.confidence >= 0.7)
            if high_confidence_count > 0:
                insights.append(f"Strong research evidence available ({high_confidence_count} high-confidence sources)")
        
        # Insight from web search recency
        if web_search_results:
            high_relevance_count = sum(1 for r in web_search_results if r.relevance_score >= 0.7)
            if high_relevance_count > 0:
                insights.append(f"Current, relevant information available ({high_relevance_count} highly relevant sources)")
        
        # Content-based insights
        content_lower = synthesized_content.lower()
        
        if "clinical trial" in content_lower or "study" in content_lower:
            insights.append("Evidence-based information with clinical research support")
        
        if "recent" in content_lower or "2024" in content_lower:
            insights.append("Includes current and up-to-date information")
        
        if "multiple" in content_lower and "sources" in content_lower:
            insights.append("Multiple independent sources corroborate key findings")
        
        # Source diversity insight
        research_domains = set()
        for result in research_results:
            if "healthcare" in result.agent_name.lower():
                research_domains.add("Healthcare")
            else:
                research_domains.add("General Research")
        
        if len(research_domains) > 1:
            insights.append("Cross-domain research provides comprehensive perspective")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_recommendations(
        self,
        query: str,
        synthesized_content: str,
        synthesis_type: str
    ) -> List[str]:
        """Generate actionable recommendations based on synthesis."""
        
        recommendations = []
        content_lower = synthesized_content.lower()
        
        if synthesis_type == "healthcare":
            recommendations.extend([
                "Consult with healthcare professionals for personalized advice",
                "Consider evidence-based treatment options with proven efficacy",
                "Stay informed about latest research developments"
            ])
            
            if "clinical trial" in content_lower:
                recommendations.append("Explore participation in relevant clinical trials if appropriate")
        
        elif synthesis_type == "general":
            recommendations.extend([
                "Consider multiple perspectives before making decisions",
                "Stay updated with current developments in this area",
                "Seek expert advice for complex implementation"
            ])
        
        elif synthesis_type == "comparative":
            recommendations.extend([
                "Evaluate different options based on specific needs and circumstances",
                "Consider the trade-offs and benefits of each approach",
                "Seek additional expert opinions for important decisions"
            ])
        
        elif synthesis_type == "analytical":
            recommendations.extend([
                "Apply analytical insights to specific use cases",
                "Monitor ongoing developments for strategic planning",
                "Consider long-term implications of current trends"
            ])
        
        # General recommendations based on content
        if "uncertainty" in content_lower or "unclear" in content_lower:
            recommendations.append("Exercise caution due to uncertainties in available information")
        
        if "research" in content_lower and "ongoing" in content_lower:
            recommendations.append("Follow ongoing research for updated information")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _calculate_synthesis_confidence(
        self,
        research_results: List[ResearchResult],
        web_search_results: List[WebSearchResult],
        synthesized_content: str
    ) -> float:
        """Calculate overall confidence in the synthesis."""
        
        confidence_factors = []
        
        # Research quality factor
        if research_results:
            avg_research_confidence = sum(r.confidence for r in research_results) / len(research_results)
            confidence_factors.append(avg_research_confidence * 0.4)
        
        # Web search relevance factor
        if web_search_results:
            avg_search_relevance = sum(r.relevance_score for r in web_search_results) / len(web_search_results)
            confidence_factors.append(avg_search_relevance * 0.3)
        
        # Source count factor
        total_sources = len(research_results) + len(web_search_results)
        source_factor = min(0.2, total_sources * 0.02)
        confidence_factors.append(source_factor)
        
        # Content quality factor
        content_quality = self._assess_content_quality(synthesized_content)
        confidence_factors.append(content_quality * 0.1)
        
        # Calculate weighted average
        if confidence_factors:
            final_confidence = sum(confidence_factors)
            return round(min(0.95, final_confidence), 3)
        else:
            return 0.1
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess the quality of synthesized content."""
        
        quality_indicators = [
            "evidence", "research", "study", "analysis", "comprehensive",
            "multiple sources", "expert", "clinical", "peer-reviewed"
        ]
        
        content_lower = content.lower()
        matches = sum(1 for indicator in quality_indicators if indicator in content_lower)
        
        # Normalize to 0-1 scale
        quality_score = min(1.0, matches / len(quality_indicators))
        
        # Bonus for structure and length
        if len(content) > 500:  # Substantial content
            quality_score += 0.1
        
        if "##" in content:  # Well-structured
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def get_synthesis_capabilities(self) -> Dict[str, Any]:
        """Get information about synthesis capabilities."""
        return {
            "synthesis_types": list(self.synthesis_strategies.keys()),
            "features": [
                "Multi-source information synthesis",
                "Key insight extraction",
                "Actionable recommendation generation",
                "Confidence assessment",
                "Structured content organization",
                "Domain-specific synthesis strategies"
            ],
            "specializations": {
                "healthcare": "Medical information synthesis with evidence focus",
                "general": "Comprehensive topic synthesis across domains",
                "comparative": "Multi-perspective analysis and comparison",
                "analytical": "Deep analytical synthesis with implications"
            }
        } 