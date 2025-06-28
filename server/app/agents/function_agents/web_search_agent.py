"""
Web Search Agent

Specialized agent for conducting web searches to find current and relevant information online.
Uses web search tools to gather real-time data and recent developments.
"""

import time
from typing import Dict, Any, Optional, List
from loguru import logger

from .base_agent import BaseFunctionAgent, AgentConfig
from ..models.chat_models import WebSearchResult
from ..tools.web_search_tool import get_default_web_search_tool


class WebSearchAgent(BaseFunctionAgent):
    """
    Web Search Agent specialized in finding current information online.
    
    This agent excels at:
    - Real-time information gathering
    - Current news and developments
    - Recent research and publications
    - Fact verification through multiple sources
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Web Search Agent.
        
        Args:
            config: Agent configuration
        """
        # Initialize with web search tools
        tools = [get_default_web_search_tool()]
        
        super().__init__(config, tools)
        self.search_strategies = {
            "healthcare": self._get_healthcare_search_terms,
            "news": self._get_news_search_terms,
            "academic": self._get_academic_search_terms,
            "general": self._get_general_search_terms
        }
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the web search agent."""
        return """
You are a Web Search Agent specialized in finding current, accurate, and relevant information through web searches.

Your capabilities include:
- Conducting targeted web searches for specific information needs
- Finding recent news, developments, and current events
- Locating authoritative sources and expert opinions
- Verifying facts through multiple independent sources
- Identifying the most relevant and reliable search results

Search Guidelines:
1. Use multiple search queries to ensure comprehensive coverage
2. Prioritize recent and authoritative sources
3. Cross-reference information from multiple sources when possible
4. Focus on relevance and credibility of search results
5. Identify potential bias or conflicting information
6. Provide clear attribution to sources

For different topics, adjust search strategy:
- Healthcare: Focus on medical organizations, recent studies, clinical guidelines
- News: Prioritize recent articles from reputable news sources
- Academic: Target scholarly articles, research papers, academic institutions
- General: Use broad search terms, then narrow down to most relevant results

Always evaluate source credibility and recency when presenting findings.
"""
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[WebSearchResult]:
        """
        Execute web search for the given query.
        
        Args:
            query: Search query
            context: Additional context from workflow
            **kwargs: Additional parameters like max_results, search_type
            
        Returns:
            List of WebSearchResult objects
        """
        start_time = time.time()
        
        try:
            logger.info(f"Web Search Agent starting search for: {query}")
            
            # Extract parameters
            max_results = kwargs.get('max_results', 10)
            search_type = kwargs.get('search_type', 'general')
            time_range = kwargs.get('time_range', None)
            
            # Generate search queries using different strategies
            search_queries = self._generate_search_queries(query, search_type)
            
            # Execute searches
            all_results = []
            for search_query in search_queries[:3]:  # Limit to 3 queries to avoid rate limiting
                results = await self._execute_single_search(
                    search_query, max_results, time_range
                )
                all_results.extend(results)
            
            # Process and rank results
            processed_results = self._process_search_results(
                all_results, query, max_results
            )
            
            execution_time = time.time() - start_time
            await self._log_execution(query, processed_results, execution_time, True)
            
            logger.info(f"Web Search Agent found {len(processed_results)} relevant results")
            return processed_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = [WebSearchResult(
                query=query,
                title="Search Error",
                url="",
                snippet=f"Web search failed: {str(e)}",
                relevance_score=0.0
            )]
            
            await self._log_execution(query, error_result, execution_time, False)
            logger.error(f"Web Search Agent error: {e}")
            return error_result
    
    def _generate_search_queries(self, query: str, search_type: str) -> List[str]:
        """
        Generate multiple search queries for comprehensive coverage.
        
        Args:
            query: Original query
            search_type: Type of search (healthcare, news, academic, general)
            
        Returns:
            List of search queries
        """
        queries = [query]  # Always include original query
        
        # Get search strategy for the type
        strategy_func = self.search_strategies.get(search_type, self._get_general_search_terms)
        additional_queries = strategy_func(query)
        
        queries.extend(additional_queries)
        return queries
    
    def _get_healthcare_search_terms(self, query: str) -> List[str]:
        """Generate healthcare-specific search terms."""
        healthcare_modifiers = [
            f"{query} clinical guidelines",
            f"{query} recent research 2024",
            f"{query} FDA approved treatment",
            f"{query} medical literature review",
            f"latest {query} developments"
        ]
        return healthcare_modifiers[:3]
    
    def _get_news_search_terms(self, query: str) -> List[str]:
        """Generate news-specific search terms."""
        news_modifiers = [
            f"{query} news today",
            f"recent {query} developments",
            f"{query} latest updates",
            f"breaking {query} news"
        ]
        return news_modifiers[:3]
    
    def _get_academic_search_terms(self, query: str) -> List[str]:
        """Generate academic-specific search terms."""
        academic_modifiers = [
            f"{query} research paper",
            f"{query} academic study",
            f"{query} scholarly article",
            f"peer reviewed {query} research"
        ]
        return academic_modifiers[:3]
    
    def _get_general_search_terms(self, query: str) -> List[str]:
        """Generate general search terms."""
        general_modifiers = [
            f"{query} overview",
            f"{query} comprehensive guide",
            f"what is {query}",
            f"{query} expert analysis"
        ]
        return general_modifiers[:3]
    
    async def _execute_single_search(
        self, 
        query: str, 
        max_results: int,
        time_range: Optional[str] = None
    ) -> List[WebSearchResult]:
        """Execute a single web search query."""
        try:
            # Get the web search tool
            search_tool = self.tools[0] if self.tools else None
            if not search_tool:
                logger.error("No web search tool available")
                return []
            
            # Prepare search parameters
            search_params = {
                'query': query,
                'max_results': min(max_results, 10),  # Limit per query
            }
            
            if time_range:
                search_params['time_range'] = time_range
            
            # Execute search
            results_data = await search_tool.acall(**search_params)
            
            # Convert to WebSearchResult objects
            web_results = []
            for result_dict in results_data:
                try:
                    web_result = WebSearchResult(**result_dict)
                    web_results.append(web_result)
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
                    continue
            
            return web_results
            
        except Exception as e:
            logger.error(f"Single search execution failed: {e}")
            return []
    
    def _process_search_results(
        self, 
        results: List[WebSearchResult], 
        original_query: str,
        max_results: int
    ) -> List[WebSearchResult]:
        """
        Process and rank search results.
        
        Args:
            results: Raw search results
            original_query: Original search query
            max_results: Maximum number of results to return
            
        Returns:
            Processed and ranked results
        """
        if not results:
            return []
        
        # Remove duplicates based on URL
        unique_results = []
        seen_urls = set()
        
        for result in results:
            if result.url not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result.url)
        
        # Re-calculate relevance scores for better ranking
        for result in unique_results:
            result.relevance_score = self._calculate_enhanced_relevance(
                result, original_query
            )
        
        # Sort by relevance score
        sorted_results = sorted(
            unique_results, 
            key=lambda x: x.relevance_score, 
            reverse=True
        )
        
        # Add quality indicators
        enhanced_results = []
        for result in sorted_results[:max_results]:
            enhanced_result = self._enhance_result_metadata(result)
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def _calculate_enhanced_relevance(
        self, 
        result: WebSearchResult, 
        query: str
    ) -> float:
        """Calculate enhanced relevance score."""
        try:
            # Base relevance from search result
            base_score = result.relevance_score
            
            # Query term matching
            query_terms = query.lower().split()
            title_lower = result.title.lower()
            snippet_lower = result.snippet.lower()
            
            # Title relevance (higher weight)
            title_matches = sum(1 for term in query_terms if term in title_lower)
            title_score = (title_matches / len(query_terms)) * 0.4
            
            # Snippet relevance
            snippet_matches = sum(1 for term in query_terms if term in snippet_lower)
            snippet_score = (snippet_matches / len(query_terms)) * 0.3
            
            # Source credibility boost
            credibility_score = self._assess_source_credibility(result.url)
            
            # Recency boost (if we can determine it)
            recency_score = 0.1  # Default small boost for recent sources
            
            # Combine scores
            final_score = min(1.0, 
                base_score * 0.3 + 
                title_score + 
                snippet_score + 
                credibility_score + 
                recency_score
            )
            
            return round(final_score, 3)
            
        except Exception as e:
            logger.warning(f"Error calculating relevance: {e}")
            return result.relevance_score
    
    def _assess_source_credibility(self, url: str) -> float:
        """Assess the credibility of a source based on its URL."""
        try:
            url_lower = url.lower()
            
            # High credibility domains
            high_credibility_domains = [
                '.gov', '.edu', '.org',
                'pubmed', 'who.int', 'cdc.gov', 'fda.gov',
                'nature.com', 'science.org', 'nejm.org',
                'bbc.com', 'reuters.com', 'apnews.com'
            ]
            
            # Medium credibility domains
            medium_credibility_domains = [
                'wikipedia.org', 'mayo clinic', 'cleveland clinic',
                'nytimes.com', 'washingtonpost.com', 'guardian.com'
            ]
            
            # Check for high credibility
            if any(domain in url_lower for domain in high_credibility_domains):
                return 0.15
            
            # Check for medium credibility
            elif any(domain in url_lower for domain in medium_credibility_domains):
                return 0.1
            
            # Check for potential low credibility indicators
            low_credibility_indicators = [
                'blog', 'personal', 'forum', 'social'
            ]
            
            if any(indicator in url_lower for indicator in low_credibility_indicators):
                return -0.05
            
            return 0.05  # Default neutral score
            
        except Exception:
            return 0.0
    
    def _enhance_result_metadata(self, result: WebSearchResult) -> WebSearchResult:
        """Enhance result with additional metadata."""
        # Add source type indicator
        source_type = self._identify_source_type(result.url)
        
        # Enhance title with source type
        if source_type and source_type != "general":
            enhanced_title = f"{result.title} [{source_type.title()}]"
        else:
            enhanced_title = result.title
        
        # Create enhanced result
        return WebSearchResult(
            query=result.query,
            title=enhanced_title,
            url=result.url,
            snippet=result.snippet,
            relevance_score=result.relevance_score,
            timestamp=result.timestamp
        )
    
    def _identify_source_type(self, url: str) -> str:
        """Identify the type of source based on URL."""
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in ['.gov', 'cdc.gov', 'fda.gov']):
            return "government"
        elif any(domain in url_lower for domain in ['.edu', 'university', 'college']):
            return "academic"
        elif any(domain in url_lower for domain in ['pubmed', 'nature.com', 'science.org']):
            return "scientific"
        elif any(domain in url_lower for domain in ['news', 'bbc', 'reuters', 'ap']):
            return "news"
        elif '.org' in url_lower:
            return "organization"
        else:
            return "general"
    
    def get_search_capabilities(self) -> Dict[str, Any]:
        """Get information about search capabilities."""
        return {
            "search_engines": ["DuckDuckGo"],
            "search_strategies": list(self.search_strategies.keys()),
            "features": [
                "Real-time web search",
                "Multi-query strategies",
                "Source credibility assessment",
                "Relevance scoring",
                "Duplicate removal",
                "Result ranking"
            ],
            "source_types": [
                "Government (.gov)",
                "Academic (.edu)",
                "Scientific journals",
                "News organizations",
                "Non-profit organizations (.org)",
                "General web sources"
            ]
        } 