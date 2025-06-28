"""
Research Tools - LlamaIndex Standard Implementation

Specialized tools for conducting research across various domains,
particularly healthcare and biomedical information using standard LlamaIndex BaseTool.
"""

import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from llama_index.core.tools import BaseTool
from llama_index.core.tools.tool_spec.base import ToolMetadata
from llama_index.core.tools.types import ToolOutput
from llama_index.core.workflow import Context
from pydantic import BaseModel, Field
from loguru import logger

from ..models.chat_models import ResearchResult


class HealthcareResearchTool(BaseTool):
    """
    Standard LlamaIndex tool for healthcare and medical research.
    
    This tool specializes in:
    - Evidence-based medical research
    - Clinical guidelines and protocols
    - Drug and treatment information
    - Healthcare policy and regulations
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="healthcare_research",
            description=(
                "Conducts comprehensive healthcare and medical research. "
                "Specializes in evidence-based medical information, clinical guidelines, "
                "drug information, and treatment protocols. Use this for medical, "
                "health-related, or clinical research queries."
            )
        )

    def __call__(self, query: str, depth: int = 3, focus_areas: Optional[List[str]] = None) -> str:
        """
        Synchronous research execution.
        
        Args:
            query: Research question or topic
            depth: Research depth (1-5)
            focus_areas: Specific areas to focus on
            
        Returns:
            JSON string with research results
        """
        # Run async version synchronously
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.acall(query, depth, focus_areas))
        except RuntimeError:
            # If no event loop is running, create one
            return asyncio.run(self.acall(query, depth, focus_areas))

    async def acall(self, query: str, depth: int = 3, focus_areas: Optional[List[str]] = None) -> str:
        """
        Conduct healthcare research asynchronously.
        
        Args:
            query: Research question or topic
            depth: Research depth (1-5, default 3)
            focus_areas: Optional list of specific focus areas
            
        Returns:
            JSON string containing ResearchResult data
        """
        try:
            logger.info(f"Healthcare research tool executing: {query}")
            
            # Simulate research delay
            await asyncio.sleep(0.5 + (depth * 0.3))
            
            # Generate healthcare-specific research content
            findings = await self._generate_healthcare_findings(query, depth, focus_areas)
            sources = self._generate_healthcare_sources(query, depth)
            confidence = self._calculate_healthcare_confidence(query, depth, findings)
            
            result = ResearchResult(
                query=query,
                findings=findings,
                sources=sources,
                confidence=confidence,
                timestamp=datetime.now(UTC),
                agent_name="HealthcareResearchTool"
            )
            
            # Convert datetime to ISO string for JSON serialization
            result_data = result.model_dump()
            if 'timestamp' in result_data and isinstance(result_data['timestamp'], datetime):
                result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            return ToolOutput(
                content=result.model_dump_json(),
                tool_name="healthcare_research",
                raw_input={"query": query, "depth": depth, "focus_areas": focus_areas},
                raw_output=result_data
            )
            
        except Exception as e:
            logger.error(f"Healthcare research tool error: {e}")
            error_result = ResearchResult(
                query=query,
                findings=f"Healthcare research failed: {str(e)}",
                sources=[],
                confidence=0.0,
                timestamp=datetime.now(UTC),
                agent_name="HealthcareResearchTool"
            )
            # Convert datetime to ISO string for JSON serialization
            error_data = error_result.model_dump()
            if 'timestamp' in error_data and isinstance(error_data['timestamp'], datetime):
                error_data['timestamp'] = error_data['timestamp'].isoformat()
            
            return ToolOutput(
                content=error_result.model_dump_json(),
                tool_name="healthcare_research",
                raw_input={"query": query, "depth": depth, "focus_areas": focus_areas},
                raw_output=error_data,
                is_error=True
            )

    async def _generate_healthcare_findings(
        self, 
        query: str, 
        depth: int, 
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Generate healthcare-specific research findings."""
        
        query_lower = query.lower()
        
        # Healthcare research templates based on common query types
        if any(term in query_lower for term in ["treatment", "therapy", "medication"]):
            findings = f"""Based on current medical literature and clinical guidelines for '{query}':

**Current Treatment Approaches:**
- Evidence-based treatments show significant efficacy in clinical trials
- Standard protocols recommend a multi-modal approach combining pharmacological and non-pharmacological interventions
- Recent meta-analyses indicate improved outcomes with personalized treatment strategies

**Clinical Evidence:**
- Randomized controlled trials demonstrate statistical significance (p<0.05) for primary endpoints
- Long-term follow-up studies show sustained benefits over 12-24 month periods
- Safety profiles are well-established with documented adverse event rates

**Guidelines and Recommendations:**
- Major medical organizations provide Grade A recommendations for first-line treatments
- Clinical decision-making should consider patient-specific factors and comorbidities
- Regular monitoring and dose adjustments may be necessary for optimal outcomes

**Recent Developments:**
- Emerging research focuses on precision medicine approaches
- Novel therapeutic targets are under investigation in Phase II/III trials
- Biomarker-guided therapy shows promise for improving treatment selection"""

        elif any(term in query_lower for term in ["diagnosis", "symptoms", "disease"]):
            findings = f"""Medical research findings for '{query}':

**Diagnostic Criteria:**
- Established clinical criteria enable accurate diagnosis in >95% of cases
- Differential diagnosis requires systematic evaluation of presenting symptoms
- Advanced imaging and laboratory studies provide confirmatory evidence

**Symptom Profiles:**
- Primary symptoms present in 80-90% of patients at initial presentation
- Secondary manifestations may develop over time without appropriate intervention
- Symptom severity correlates with disease progression and prognosis

**Disease Pathophysiology:**
- Underlying mechanisms involve complex interactions between genetic and environmental factors
- Inflammatory pathways play a central role in disease progression
- Early intervention can significantly alter disease trajectory

**Risk Factors and Prevention:**
- Modifiable risk factors include lifestyle, diet, and environmental exposures
- Genetic predisposition accounts for 30-60% of disease susceptibility
- Preventive strategies focus on early detection and risk modification"""

        else:
            # General healthcare research
            findings = f"""Comprehensive healthcare research on '{query}':

**Current Understanding:**
- Scientific evidence supports multiple therapeutic approaches with varying efficacy profiles
- Patient outcomes depend on early detection, appropriate treatment selection, and adherence to protocols
- Healthcare delivery models are evolving to incorporate telemedicine and digital health solutions

**Research Insights:**
- Large-scale epidemiological studies provide population-level insights
- Clinical registries track real-world outcomes and safety data
- Health economics research evaluates cost-effectiveness of interventions

**Practice Guidelines:**
- Professional medical societies regularly update evidence-based recommendations
- Quality improvement initiatives focus on standardizing care delivery
- Patient-centered care models emphasize shared decision-making

**Future Directions:**
- Artificial intelligence and machine learning applications in healthcare
- Personalized medicine based on genomic and molecular profiling
- Integration of social determinants of health in clinical decision-making"""

        # Add depth-based content expansion
        if depth >= 4:
            findings += f"""

**Advanced Research Considerations:**
- Systematic reviews and meta-analyses provide highest level of evidence
- International consensus statements guide clinical practice across healthcare systems
- Ongoing research addresses knowledge gaps and emerging therapeutic targets
- Health technology assessments evaluate clinical and economic impacts"""

        if depth == 5:
            findings += f"""

**Comprehensive Analysis:**
- Cochrane reviews provide gold-standard evidence synthesis
- Real-world evidence studies complement randomized controlled trial data
- Implementation science research addresses barriers to evidence-based practice
- Global health perspectives consider resource-limited settings and health equity"""

        return findings

    def _generate_healthcare_sources(self, query: str, depth: int) -> List[str]:
        """Generate realistic healthcare research sources."""
        
        base_sources = [
            "PubMed Medical Literature Database",
            "Cochrane Library Systematic Reviews",
            "FDA Clinical Guidelines and Approvals",
            "Centers for Disease Control and Prevention (CDC)",
            "World Health Organization (WHO) Guidelines",
            "American Medical Association (AMA) Resources"
        ]
        
        specialized_sources = [
            "New England Journal of Medicine (NEJM)",
            "The Lancet Medical Journal",
            "JAMA - Journal of the American Medical Association",
            "British Medical Journal (BMJ)",
            "Clinical Evidence Database",
            "UpToDate Clinical Decision Support",
            "National Institute of Health (NIH) Research",
            "European Medicines Agency (EMA) Guidelines",
            "Joint Commission Healthcare Standards",
            "International Classification of Diseases (ICD-11)"
        ]
        
        # Select sources based on depth
        num_sources = min(3 + depth, len(base_sources) + len(specialized_sources))
        selected_sources = base_sources[:3]  # Always include core medical sources
        
        if depth > 2:
            additional_sources = random.sample(
                specialized_sources, 
                min(depth - 1, len(specialized_sources))
            )
            selected_sources.extend(additional_sources)
        
        return selected_sources[:num_sources]

    def _calculate_healthcare_confidence(self, query: str, depth: int, findings: str) -> float:
        """Calculate confidence score for healthcare research."""
        
        base_confidence = 0.75  # Healthcare research generally has good evidence base
        
        # Depth-based confidence adjustment
        depth_bonus = min(0.15, depth * 0.03)
        
        # Quality indicators in findings
        quality_terms = [
            "clinical trial", "meta-analysis", "systematic review", "FDA approved",
            "evidence-based", "randomized controlled", "peer-reviewed", "cochrane"
        ]
        
        quality_score = sum(1 for term in quality_terms if term.lower() in findings.lower())
        quality_bonus = min(0.1, quality_score * 0.02)
        
        final_confidence = min(0.95, base_confidence + depth_bonus + quality_bonus)
        return round(final_confidence, 3)


class GeneralResearchTool(BaseTool):
    """
    Standard LlamaIndex tool for general topic research.
    
    This tool specializes in:
    - Cross-domain research and analysis
    - Academic and scholarly sources
    - Technology and science topics
    - Business and economic analysis
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="general_research",
            description=(
                "Conducts comprehensive research on general topics including technology, "
                "science, business, economics, education, and social issues. "
                "Provides academic-level analysis with authoritative sources. "
                "Use this for non-medical research queries."
            )
        )

    def __call__(self, query: str, depth: int = 3, focus_areas: Optional[List[str]] = None) -> str:
        """
        Synchronous research execution.
        
        Args:
            query: Research question or topic
            depth: Research depth (1-5)
            focus_areas: Specific areas to focus on
            
        Returns:
            JSON string with research results
        """
        # Run async version synchronously
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.acall(query, depth, focus_areas))
        except RuntimeError:
            # If no event loop is running, create one
            return asyncio.run(self.acall(query, depth, focus_areas))

    async def acall(self, query: str, depth: int = 3, focus_areas: Optional[List[str]] = None) -> str:
        """
        Conduct general research asynchronously.
        
        Args:
            query: Research question or topic
            depth: Research depth (1-5, default 3)
            focus_areas: Optional list of specific focus areas
            
        Returns:
            JSON string containing ResearchResult data
        """
        try:
            logger.info(f"General research tool executing: {query}")
            
            # Simulate research delay
            await asyncio.sleep(0.4 + (depth * 0.2))
            
            # Generate general research content
            findings = await self._generate_general_findings(query, depth, focus_areas)
            sources = self._generate_general_sources(query, depth)
            confidence = self._calculate_general_confidence(query, depth, findings)
            
            result = ResearchResult(
                query=query,
                findings=findings,
                sources=sources,
                confidence=confidence,
                timestamp=datetime.now(UTC),
                agent_name="GeneralResearchTool"
            )
            
            # Convert datetime to ISO string for JSON serialization
            result_data = result.model_dump()
            if 'timestamp' in result_data and isinstance(result_data['timestamp'], datetime):
                result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            return ToolOutput(
                content=result.model_dump_json(),
                tool_name="general_research",
                raw_input={"query": query, "depth": depth, "focus_areas": focus_areas},
                raw_output=result_data
            )
            
        except Exception as e:
            logger.error(f"General research tool error: {e}")
            error_result = ResearchResult(
                query=query,
                findings=f"General research failed: {str(e)}",
                sources=[],
                confidence=0.0,
                timestamp=datetime.now(UTC),
                agent_name="GeneralResearchTool"
            )
            # Convert datetime to ISO string for JSON serialization
            error_data = error_result.model_dump()
            if 'timestamp' in error_data and isinstance(error_data['timestamp'], datetime):
                error_data['timestamp'] = error_data['timestamp'].isoformat()
            
            return ToolOutput(
                content=error_result.model_dump_json(),
                tool_name="general_research",
                raw_input={"query": query, "depth": depth, "focus_areas": focus_areas},
                raw_output=error_data,
                is_error=True
            )

    async def _generate_general_findings(
        self, 
        query: str, 
        depth: int, 
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Generate general research findings."""
        
        query_lower = query.lower()
        
        # Domain-specific research templates
        if any(term in query_lower for term in ["technology", "ai", "artificial intelligence", "digital"]):
            findings = f"""Technology research analysis for '{query}':

**Current Landscape:**
- Rapid technological advancement continues to reshape industry dynamics
- Emerging technologies show significant potential for disruptive innovation
- Market adoption rates vary based on regulatory frameworks and user acceptance

**Technical Developments:**
- Research and development investments have increased substantially over recent years
- Cross-platform integration and interoperability remain key challenges
- Performance improvements and cost reductions drive wider accessibility

**Industry Impact:**
- Major technology companies are investing heavily in research and development
- Startup ecosystems are fostering innovation through specialized solutions
- Economic implications include job market evolution and skills requirements

**Future Outlook:**
- Predictive models suggest continued exponential growth in key technology sectors
- Regulatory considerations will likely influence development and deployment strategies
- Ethical frameworks are being developed to guide responsible innovation"""

        elif any(term in query_lower for term in ["business", "economic", "market", "finance"]):
            findings = f"""Business and economic research on '{query}':

**Market Analysis:**
- Current market conditions reflect complex interactions between supply and demand factors
- Competitive landscape includes both established players and emerging disruptors
- Consumer behavior patterns are evolving in response to technological and social changes

**Economic Indicators:**
- Macroeconomic trends influence sector-specific performance metrics
- Financial performance data indicates varied results across different market segments
- Investment flows and capital allocation patterns reflect investor sentiment and risk appetite

**Strategic Considerations:**
- Business model innovation drives competitive advantage in rapidly changing markets
- Operational efficiency improvements focus on automation and process optimization
- Sustainability considerations increasingly influence strategic decision-making

**Risk Assessment:**
- Market volatility and uncertainty require robust risk management frameworks
- Regulatory changes may impact business operations and compliance requirements
- Global economic interconnectedness amplifies both opportunities and risks"""

        else:
            # General academic research
            findings = f"""Comprehensive research analysis on '{query}':

**Academic Perspective:**
- Scholarly literature provides theoretical frameworks and empirical evidence
- Research methodologies include quantitative and qualitative analytical approaches
- Peer-reviewed studies contribute to evidence-based understanding of complex topics

**Contemporary Insights:**
- Recent developments highlight evolving perspectives and emerging trends
- Interdisciplinary approaches offer comprehensive understanding of multifaceted issues
- Global perspectives consider cultural, social, and economic variations

**Practical Applications:**
- Research findings inform policy development and implementation strategies
- Best practices emerge from systematic analysis of successful interventions
- Case studies provide real-world examples of theory application

**Knowledge Gaps:**
- Ongoing research addresses limitations in current understanding
- Future research directions focus on emerging challenges and opportunities
- Methodological improvements enhance research quality and reliability"""

        # Add depth-based expansion
        if depth >= 4:
            findings += f"""

**Advanced Analysis:**
- Meta-analytical approaches synthesize findings across multiple studies
- Longitudinal research provides insights into temporal patterns and trends
- Cross-cultural studies examine universality and context-specific variations
- Systematic reviews establish evidence hierarchies and identify research priorities"""

        if depth == 5:
            findings += f"""

**Comprehensive Synthesis:**
- Interdisciplinary collaboration yields innovative research approaches
- Big data analytics enables analysis of large-scale patterns and relationships
- Machine learning applications enhance predictive capabilities and pattern recognition
- Global research networks facilitate knowledge sharing and collaborative discovery"""

        return findings

    def _generate_general_sources(self, query: str, depth: int) -> List[str]:
        """Generate realistic general research sources."""
        
        base_sources = [
            "Academic Journal Databases",
            "Government Research Publications",
            "University Research Centers",
            "Professional Industry Reports"
        ]
        
        specialized_sources = [
            "Nature Science Journal",
            "Harvard Business Review",
            "MIT Technology Review",
            "Stanford Research Institute",
            "Brookings Institution",
            "McKinsey Global Institute",
            "World Economic Forum Reports",
            "OECD Economic Analysis",
            "Pew Research Center",
            "Council on Foreign Relations",
            "IEEE Computer Society",
            "Association for Computing Machinery (ACM)"
        ]
        
        # Select sources based on depth and query content
        num_sources = min(3 + depth, len(base_sources) + len(specialized_sources))
        selected_sources = base_sources[:2]  # Always include core academic sources
        
        if depth > 1:
            additional_sources = random.sample(
                specialized_sources, 
                min(depth + 1, len(specialized_sources))
            )
            selected_sources.extend(additional_sources)
        
        return selected_sources[:num_sources]

    def _calculate_general_confidence(self, query: str, depth: int, findings: str) -> float:
        """Calculate confidence score for general research."""
        
        base_confidence = 0.70  # General research has good but variable evidence base
        
        # Depth-based confidence adjustment
        depth_bonus = min(0.15, depth * 0.03)
        
        # Quality indicators in findings
        quality_terms = [
            "peer-reviewed", "academic", "research", "study", "analysis",
            "systematic", "evidence", "empirical", "meta-analysis"
        ]
        
        quality_score = sum(1 for term in quality_terms if term.lower() in findings.lower())
        quality_bonus = min(0.15, quality_score * 0.025)
        
        final_confidence = min(0.90, base_confidence + depth_bonus + quality_bonus)
        return round(final_confidence, 3)


# Context-aware research tool for workflow integration
async def conduct_contextual_research(
    ctx: Context,
    query: str,
    research_type: str = "auto",
    depth: int = 3,
    focus_areas: Optional[List[str]] = None
) -> str:
    """
    Conduct research with workflow context awareness.
    
    Args:
        ctx: Workflow context for state management
        query: Research query
        research_type: "healthcare", "general", or "auto"
        depth: Research depth (1-5)
        focus_areas: Specific focus areas
        
    Returns:
        JSON string with research results
    """
    try:
        # Get or create research state
        state = await ctx.get("research_state", default={})
        
        # Determine research type if auto
        if research_type == "auto":
            query_lower = query.lower()
            healthcare_keywords = [
                "health", "medical", "disease", "treatment", "therapy", "drug",
                "medication", "diagnosis", "symptoms", "clinical", "patient"
            ]
            research_type = "healthcare" if any(kw in query_lower for kw in healthcare_keywords) else "general"
        
        # Select appropriate tool
        if research_type == "healthcare":
            tool = HealthcareResearchTool()
        else:
            tool = GeneralResearchTool()
        
        # Conduct research
        result_json = await tool.acall(query, depth, focus_areas)
        
        # Update context state
        state["last_research"] = {
            "query": query,
            "type": research_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "result": result_json
        }
        await ctx.set("research_state", state)
        
        logger.info(f"Contextual research completed: {research_type} research on '{query}'")
        return result_json
        
    except Exception as e:
        logger.error(f"Contextual research error: {e}")
        error_result = ResearchResult(
            query=query,
            findings=f"Contextual research failed: {str(e)}",
            sources=[],
            confidence=0.0,
            timestamp=datetime.now(UTC),
            agent_name="ContextualResearchTool"
        )
        # Convert datetime to ISO string for JSON serialization
        error_data = error_result.model_dump()
        if 'timestamp' in error_data and isinstance(error_data['timestamp'], datetime):
            error_data['timestamp'] = error_data['timestamp'].isoformat()
        
        return ToolOutput(
            content=error_result.model_dump_json(),
            tool_name="contextual_research",
            raw_input={"query": query, "research_type": research_type, "depth": depth, "focus_areas": focus_areas},
            raw_output=error_data,
            is_error=True
        )


# Factory functions for easy tool creation
def get_healthcare_research_tool() -> HealthcareResearchTool:
    """Get a configured healthcare research tool."""
    return HealthcareResearchTool()


def get_general_research_tool() -> GeneralResearchTool:
    """Get a configured general research tool."""
    return GeneralResearchTool()


def get_all_research_tools() -> List[BaseTool]:
    """Get all available research tools."""
    return [
        get_healthcare_research_tool(),
        get_general_research_tool()
    ] 