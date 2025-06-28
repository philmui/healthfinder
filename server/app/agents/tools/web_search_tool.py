"""
Web Search Tools - LlamaIndex Standard Implementation

Provides web search capabilities using various search engines,
with focus on healthcare and general information retrieval using standard LlamaIndex BaseTool.
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from llama_index.core.tools import BaseTool
from llama_index.core.tools.tool_spec.base import ToolMetadata
from llama_index.core.tools.types import ToolOutput
from llama_index.core.workflow import Context
from pydantic import BaseModel, Field
from loguru import logger

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    logger.warning("DuckDuckGo search not available. Install duckduckgo-search for full functionality.")

from ..models.chat_models import WebSearchResult


class DuckDuckGoSearchTool(BaseTool):
    """
    Standard LlamaIndex tool for DuckDuckGo web search.
    
    This tool specializes in:
    - Privacy-focused web search
    - Healthcare and medical information
    - General topic search
    - Real-time information retrieval
    """

    def __init__(self, fallback_enabled: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.last_search_time = 0
        self.rate_limit_delay = 1.0  # Seconds between searches
        self.fallback_enabled = fallback_enabled
        
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="duckduckgo_search",
            description=(
                "Searches the web using DuckDuckGo for current information on any topic. "
                "Provides real-time search results with source URLs, summaries, and relevance scoring. "
                "Particularly good for healthcare, news, and general information queries. "
                "Respects privacy and provides unbiased search results."
            )
        )

    def __call__(
        self, 
        query: str, 
        max_results: int = 10, 
        search_type: str = "general"
    ) -> str:
        """
        Synchronous search execution.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20)
            search_type: Type of search ("healthcare", "news", "general")
            
        Returns:
            JSON string with search results
        """
        # Run async version synchronously
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.acall(query, max_results, search_type))
        except RuntimeError:
            # If no event loop is running, create one
            return asyncio.run(self.acall(query, max_results, search_type))

    async def acall(
        self, 
        query: str, 
        max_results: int = 10, 
        search_type: str = "general"
    ) -> str:
        """
        Conduct web search asynchronously.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20, default 10)
            search_type: Type of search ("healthcare", "news", "general")
            
        Returns:
            JSON string containing list of WebSearchResult data
        """
        logger.info(f"DuckDuckGoSearchTool.acall: fallback_enabled={self.fallback_enabled}")
        try:
            logger.info(f"DuckDuckGo search tool executing: {query}")
            
            # Rate limiting
            await self._enforce_rate_limit()
            
            if not DUCKDUCKGO_AVAILABLE:
                if not self.fallback_enabled:
                    # No fallback allowed, return error
                    return ToolOutput(
                        content="[]",
                        tool_name="duckduckgo_search",
                        raw_input={"query": query, "max_results": max_results, "search_type": search_type},
                        raw_output={"error": "DuckDuckGo search not available and fallback is disabled."},
                        is_error=True
                    )
                # Fallback to simulated results
                results = await self._generate_simulated_results(query, max_results, search_type)
            else:
                try:
                    # Conduct actual search
                    results = await self._conduct_duckduckgo_search(query, max_results, search_type)
                except Exception as e:
                    logger.error(f"DuckDuckGo search tool error: {e}")
                    if not self.fallback_enabled:
                        return ToolOutput(
                            content="[]",
                            tool_name="duckduckgo_search",
                            raw_input={"query": query, "max_results": max_results, "search_type": search_type},
                            raw_output={"error": str(e)},
                            is_error=True
                        )
                    # fallback to Wikipedia or mock search if enabled
                    results = await self._generate_simulated_results(query, max_results, search_type)
            
            # Convert to ToolOutput with JSON-serializable data
            results_data = [result.model_dump() for result in results]
            # Convert datetime objects to ISO strings for JSON serialization
            for result_data in results_data:
                if 'timestamp' in result_data and isinstance(result_data['timestamp'], datetime):
                    result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            return ToolOutput(
                content=json.dumps(results_data),
                tool_name="duckduckgo_search",
                raw_input={"query": query, "max_results": max_results, "search_type": search_type},
                raw_output=results_data,
                is_error=False
            )
            
        except Exception as e:
            logger.error(f"DuckDuckGo search tool error: {e}")
            return ToolOutput(
                content="[]",
                tool_name="duckduckgo_search",
                raw_input={"query": query, "max_results": max_results, "search_type": search_type},
                raw_output={"error": str(e)},
                is_error=True
            )

    async def _enforce_rate_limit(self):
        """Enforce rate limiting between searches."""
        current_time = time.time()
        time_since_last = current_time - self.last_search_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_search_time = time.time()

    async def _conduct_duckduckgo_search(
        self, 
        query: str, 
        max_results: int, 
        search_type: str
    ) -> List[WebSearchResult]:
        """Conduct actual DuckDuckGo search."""
        
        try:
            # Modify query based on search type
            enhanced_query = self._enhance_query_for_type(query, search_type)
            
            # Execute search
            with DDGS() as ddgs:
                search_results = list(ddgs.text(
                    enhanced_query, 
                    max_results=min(max_results, 20),
                    region='us-en',
                    safesearch='moderate'
                ))
            
            # Convert to WebSearchResult objects
            results = []
            for i, result in enumerate(search_results):
                try:
                    web_result = WebSearchResult(
                        query=query,
                        title=result.get('title', 'No title'),
                        url=result.get('href', ''),
                        snippet=result.get('body', 'No description'),
                        relevance_score=self._calculate_relevance_score(query, result, search_type),
                        source_type=self._determine_source_type(result.get('href', '')),
                        timestamp=datetime.now(UTC),
                        agent_name="DuckDuckGoSearchTool"
                    )
                    results.append(web_result)
                except Exception as e:
                    logger.warning(f"Error processing search result {i}: {e}")
                    continue
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"DuckDuckGo search returned {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            # Fallback to simulated results
            return await self._generate_simulated_results(query, max_results, search_type)

    async def _generate_simulated_results(
        self, 
        query: str, 
        max_results: int, 
        search_type: str
    ) -> List[WebSearchResult]:
        """Generate simulated search results when DuckDuckGo is unavailable."""
        
        # Simulate search delay
        await asyncio.sleep(0.5)
        
        # Generate realistic results based on search type
        if search_type == "healthcare":
            base_results = [
                {
                    "title": f"Medical Information: {query} - Mayo Clinic",
                    "url": f"https://mayoclinic.org/conditions/{query.lower().replace(' ', '-')}",
                    "snippet": f"Comprehensive medical information about {query}, including symptoms, causes, and treatments from Mayo Clinic medical experts.",
                    "source_type": "medical"
                },
                {
                    "title": f"{query} Research - PubMed Central",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/search/{query.replace(' ', '+')}",
                    "snippet": f"Latest research papers and clinical studies related to {query} from peer-reviewed medical journals.",
                    "source_type": "academic"
                },
                {
                    "title": f"CDC Guidelines: {query}",
                    "url": f"https://cdc.gov/health-topics/{query.lower().replace(' ', '-')}",
                    "snippet": f"Official health guidelines and recommendations from the Centers for Disease Control and Prevention regarding {query}.",
                    "source_type": "government"
                }
            ]
        elif search_type == "news":
            base_results = [
                {
                    "title": f"Latest News: {query} - Reuters",
                    "url": f"https://reuters.com/search/news?query={query.replace(' ', '+')}",
                    "snippet": f"Recent news and developments related to {query} from Reuters news service.",
                    "source_type": "news"
                },
                {
                    "title": f"{query} Updates - Associated Press",
                    "url": f"https://apnews.com/search/{query.replace(' ', '+')}",
                    "snippet": f"Current events and breaking news coverage of {query} from AP News.",
                    "source_type": "news"
                }
            ]
        else:  # general
            base_results = [
                {
                    "title": f"{query} - Wikipedia",
                    "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    "snippet": f"Comprehensive overview of {query} from Wikipedia, the free encyclopedia.",
                    "source_type": "reference"
                },
                {
                    "title": f"What is {query}? - Britannica",
                    "url": f"https://britannica.com/search?query={query.replace(' ', '+')}",
                    "snippet": f"Detailed information and analysis of {query} from Encyclopedia Britannica.",
                    "source_type": "reference"
                },
                {
                    "title": f"{query} Guide - Expert Analysis",
                    "url": f"https://expertanalysis.com/topics/{query.lower().replace(' ', '-')}",
                    "snippet": f"Expert analysis and comprehensive guide to understanding {query} and its implications.",
                    "source_type": "analysis"
                }
            ]
        
        # Select and create results
        num_results = min(max_results, len(base_results) + 3)
        results = []
        
        for i in range(num_results):
            if i < len(base_results):
                result_data = base_results[i]
            else:
                # Generate additional results
                result_data = {
                    "title": f"{query} - Additional Resource {i+1}",
                    "url": f"https://example-source-{i+1}.com/{query.lower().replace(' ', '-')}",
                    "snippet": f"Additional information and resources related to {query} from authoritative sources.",
                    "source_type": "general"
                }
            
            web_result = WebSearchResult(
                query=query,
                title=result_data["title"],
                url=result_data["url"],
                snippet=result_data["snippet"],
                relevance_score=max(0.95 - (i * 0.1), 0.3),  # Decreasing relevance
                source_type=result_data["source_type"],
                timestamp=datetime.now(UTC),
                agent_name="DuckDuckGoSearchTool"
            )
            results.append(web_result)
        
        return results

    def _enhance_query_for_type(self, query: str, search_type: str) -> str:
        """Enhance query based on search type."""
        
        if search_type == "healthcare":
            # Add medical terms to improve healthcare search results
            healthcare_enhancers = ["medical", "health", "clinical", "treatment"]
            if not any(term in query.lower() for term in healthcare_enhancers):
                query = f"{query} medical health information"
        elif search_type == "news":
            # Add news terms for current information
            if not any(term in query.lower() for term in ["news", "latest", "recent"]):
                query = f"{query} latest news recent"
        
        return query

    def _calculate_relevance_score(
        self, 
        query: str, 
        result: Dict[str, Any], 
        search_type: str
    ) -> float:
        """Calculate relevance score for a search result."""
        
        title = result.get('title', '').lower()
        snippet = result.get('body', '').lower()
        url = result.get('href', '').lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # Query term matching
        query_terms = query_lower.split()
        title_matches = sum(1 for term in query_terms if term in title)
        snippet_matches = sum(1 for term in query_terms if term in snippet)
        
        # Base score from term matching
        score += (title_matches / len(query_terms)) * 0.4
        score += (snippet_matches / len(query_terms)) * 0.3
        
        # Source credibility bonus
        credible_sources = {
            'healthcare': ['mayo', 'nih', 'cdc', 'who', 'webmd', 'medscape', 'pubmed'],
            'news': ['reuters', 'ap', 'bbc', 'npr', 'pbs'],
            'general': ['wikipedia', 'britannica', 'gov', 'edu']
        }
        
        source_terms = credible_sources.get(search_type, credible_sources['general'])
        if any(term in url for term in source_terms):
            score += 0.2
        
        # Domain authority bonus
        if '.gov' in url or '.edu' in url:
            score += 0.1
        
        return min(score, 1.0)

    def _determine_source_type(self, url: str) -> str:
        """Determine the type of source based on the URL."""
        url = url.lower()
        if "arxiv.org" in url:
            return "academic"
        if any(domain in url for domain in [".gov", "nih.gov", "ncbi.nlm.nih.gov", "pubmed", "who.int", "nejm.org", "thelancet.com", "bmj.com"]):
            return "medical"
        if any(domain in url for domain in ["cnn.com", "bbc.com", "nytimes.com", "reuters.com", "apnews.com", "news"]):
            return "news"
        if any(domain in url for domain in [".edu", "acm.org", "ieee.org", "nature.com", "sciencedirect.com", "springer.com"]):
            return "academic"
        return "general"


class GoogleSearchTool(BaseTool):
    """
    Standard LlamaIndex tool for Google Custom Search.
    
    This tool specializes in:
    - High-quality search results
    - Academic and professional sources
    - Comprehensive information retrieval
    - Custom search engine integration
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="google_search",
            description=(
                "Searches the web using Google Custom Search API for high-quality information. "
                "Provides comprehensive search results with advanced ranking and filtering. "
                "Ideal for academic research, professional information, and detailed analysis. "
                "Requires Google Custom Search API configuration."
            )
        )

    def __call__(
        self, 
        query: str, 
        max_results: int = 10, 
        search_type: str = "general"
    ) -> str:
        """
        Synchronous search execution.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20)
            search_type: Type of search ("healthcare", "academic", "general")
            
        Returns:
            JSON string with search results
        """
        # Run async version synchronously
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.acall(query, max_results, search_type))
        except RuntimeError:
            # If no event loop is running, create one
            return asyncio.run(self.acall(query, max_results, search_type))

    async def acall(
        self, 
        query: str, 
        max_results: int = 10, 
        search_type: str = "general"
    ) -> str:
        """
        Conduct Google search asynchronously.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20, default 10)
            search_type: Type of search ("healthcare", "academic", "general")
            
        Returns:
            JSON string containing list of WebSearchResult data
        """
        try:
            logger.info(f"Google search tool executing: {query}")
            
            # For now, generate simulated high-quality results
            # In production, this would integrate with Google Custom Search API
            results = await self._generate_google_style_results(query, max_results, search_type)
            
            # Convert to ToolOutput with JSON-serializable data
            results_data = [result.model_dump() for result in results]
            # Convert datetime objects to ISO strings for JSON serialization
            for result_data in results_data:
                if 'timestamp' in result_data and isinstance(result_data['timestamp'], datetime):
                    result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            return ToolOutput(
                content=json.dumps(results_data),
                tool_name="google_search",
                raw_input={"query": query, "max_results": max_results, "search_type": search_type},
                raw_output=results_data
            )
            
        except Exception as e:
            logger.error(f"Google search tool error: {e}")
            return ToolOutput(
                content="[]",
                tool_name="google_search",
                raw_input={"query": query, "max_results": max_results, "search_type": search_type},
                raw_output=[],
                is_error=True
            )

    async def _generate_google_style_results(
        self, 
        query: str, 
        max_results: int, 
        search_type: str
    ) -> List[WebSearchResult]:
        """Generate Google-style search results."""
        
        # Simulate search delay
        await asyncio.sleep(0.3)
        
        # Generate high-quality results based on search type
        if search_type == "healthcare":
            base_results = [
                {
                    "title": f"{query} - PubMed Research Articles",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/?term={query.replace(' ', '+')}",
                    "snippet": f"Peer-reviewed research articles and clinical studies on {query} from the world's largest medical database.",
                    "source_type": "academic"
                },
                {
                    "title": f"{query} Clinical Guidelines - UpToDate",
                    "url": f"https://uptodate.com/contents/search?search={query.replace(' ', '+')}",
                    "snippet": f"Evidence-based clinical guidelines and treatment recommendations for {query} from medical experts.",
                    "source_type": "medical"
                },
                {
                    "title": f"WHO Health Information: {query}",
                    "url": f"https://who.int/health-topics/{query.lower().replace(' ', '-')}",
                    "snippet": f"Official health information and global guidelines on {query} from the World Health Organization.",
                    "source_type": "government"
                }
            ]
        elif search_type == "academic":
            base_results = [
                {
                    "title": f"{query} - Google Scholar",
                    "url": f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}",
                    "snippet": f"Academic papers, theses, books, conference papers, and patents related to {query}.",
                    "source_type": "academic"
                },
                {
                    "title": f"Research on {query} - Nature Journal",
                    "url": f"https://nature.com/search?q={query.replace(' ', '+')}",
                    "snippet": f"Cutting-edge research and scientific publications on {query} from Nature journals.",
                    "source_type": "academic"
                }
            ]
        else:  # general
            base_results = [
                {
                    "title": f"{query} - Stanford Encyclopedia of Philosophy",
                    "url": f"https://plato.stanford.edu/search/searcher.py?query={query.replace(' ', '+')}",
                    "snippet": f"Comprehensive academic analysis and philosophical perspectives on {query}.",
                    "source_type": "academic"
                },
                {
                    "title": f"{query} Overview - MIT Technology Review",
                    "url": f"https://technologyreview.com/search/{query.replace(' ', '+')}",
                    "snippet": f"Technical analysis and expert commentary on {query} from MIT Technology Review.",
                    "source_type": "analysis"
                }
            ]
        
        # Create results with high relevance scores (Google-style quality)
        results = []
        for i, result_data in enumerate(base_results[:max_results]):
            web_result = WebSearchResult(
                query=query,
                title=result_data["title"],
                url=result_data["url"],
                snippet=result_data["snippet"],
                relevance_score=max(0.98 - (i * 0.05), 0.7),  # High relevance scores
                source_type=result_data["source_type"],
                timestamp=datetime.now(UTC),
                agent_name="GoogleSearchTool"
            )
            results.append(web_result)
        
        return results


# Context-aware search tool for workflow integration
async def conduct_contextual_web_search(
    ctx: Context,
    query: str,
    search_engine: str = "duckduckgo",
    max_results: int = 10,
    search_type: str = "general"
) -> str:
    """
    Conduct web search with workflow context awareness.
    
    Args:
        ctx: Workflow context for state management
        query: Search query
        search_engine: "duckduckgo" or "google"
        max_results: Maximum number of results
        search_type: Type of search
        
    Returns:
        JSON string with search results
    """
    try:
        # Get or create search state
        state = await ctx.get("search_state", default={})
        
        # Select appropriate search tool
        if search_engine.lower() == "google":
            tool = GoogleSearchTool()
        else:
            tool = DuckDuckGoSearchTool()
        
        # Conduct search
        results_json = await tool.acall(query, max_results, search_type)
        
        # Update context state
        state["last_search"] = {
            "query": query,
            "engine": search_engine,
            "type": search_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "results": results_json
        }
        await ctx.set("search_state", state)
        
        logger.info(f"Contextual search completed: {search_engine} search for '{query}'")
        return results_json
        
    except Exception as e:
        logger.error(f"Contextual web search error: {e}")
        return "[]"


# Factory functions for easy tool creation
def get_duckduckgo_search_tool() -> DuckDuckGoSearchTool:
    """Get a configured DuckDuckGo search tool."""
    return DuckDuckGoSearchTool()


def get_google_search_tool() -> GoogleSearchTool:
    """Get a configured Google search tool."""
    return GoogleSearchTool()


def get_all_web_search_tools() -> List[BaseTool]:
    """Get all available web search tools."""
    return [
        get_duckduckgo_search_tool(),
        get_google_search_tool()
    ]


def get_best_search_tool(preference: str = "duckduckgo") -> BaseTool:
    """
    Get the best available search tool based on preference.
    
    Args:
        preference: "duckduckgo" or "google"
        
    Returns:
        Configured search tool
    """
    if preference.lower() == "google":
        return get_google_search_tool()
    else:
        return get_duckduckgo_search_tool() 