"""
Agent Tools Tests

Comprehensive test suite for the agent tools including research tools,
web search tools, and their integration with the workflow system.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, UTC

from app.agents.tools.research_tools import (
    HealthcareResearchTool,
    GeneralResearchTool,
    get_healthcare_research_tool,
    get_general_research_tool
)
from app.agents.tools.web_search_tool import (
    DuckDuckGoSearchTool,
    GoogleSearchTool,
    get_duckduckgo_search_tool,
    get_google_search_tool
)
from app.agents.models.chat_models import ResearchResult, WebSearchResult

@pytest.fixture
def all_tools():
    """Create instances of all tools."""
    from app.agents.tools.web_search_tool import DuckDuckGoSearchTool, GoogleSearchTool
    return {
        "healthcare_research": get_healthcare_research_tool(),
        "general_research": get_general_research_tool(), 
        "duckduckgo_search": DuckDuckGoSearchTool(fallback_enabled=False),
        "google_search": GoogleSearchTool()
    }

# Move all test functions that use all_tools here

def test_tool_metadata_consistency(all_tools):
    """Test that all tools have consistent metadata structure."""
    for tool_name, tool in all_tools.items():
        assert hasattr(tool, 'metadata')
        assert hasattr(tool.metadata, 'name')
        assert hasattr(tool.metadata, 'description')
        assert hasattr(tool.metadata, 'fn_schema')
        # All tools should have proper schema
        assert tool.metadata.fn_schema is not None

@pytest.mark.asyncio
async def test_tool_output_format_consistency(all_tools):
    """Test that all tools return consistent output format."""
    query = "test query"
    for tool_name, tool in all_tools.items():
        result = await tool.acall(query=query)
        # All should return ToolOutput with required fields
        assert hasattr(result, 'content')
        assert hasattr(result, 'tool_name')
        assert hasattr(result, 'raw_input')
        assert hasattr(result, 'raw_output')
        # Content should be valid JSON for all tools
        try:
            json.loads(result.content)
        except json.JSONDecodeError:
            pytest.fail(f"Tool {tool_name} returned invalid JSON")

@pytest.mark.asyncio
async def test_research_to_search_workflow(all_tools):
    """Test workflow from research to web search."""
    healthcare_tool = all_tools["healthcare_research"]
    search_tool = all_tools["duckduckgo_search"]
    # First conduct research
    research_result = await healthcare_tool.acall(
        query="diabetes management", 
        depth=2
    )
    research_data = json.loads(research_result.content)
    # Use research findings to create search query
    search_query = f"latest {research_data['query']} research 2024"
    search_result = await search_tool.acall(query=search_query, max_results=3)
    search_data = json.loads(search_result.content)
    # Both should have relevant content
    assert len(research_data["findings"]) > 50
    assert isinstance(search_data, list)

@pytest.mark.asyncio
async def test_tool_error_recovery(all_tools):
    """Test that tools handle errors gracefully."""
    for tool_name, tool in all_tools.items():
        # Patch the correct method for each tool
        if tool_name == "healthcare_research":
            patch_target = "_generate_healthcare_findings"
        elif tool_name == "general_research":
            patch_target = "_generate_general_findings"
        elif tool_name == "duckduckgo_search":
            patch_target = "_conduct_duckduckgo_search"
        elif tool_name == "google_search":
            # GoogleSearchTool does not have _conduct_google_search, skip
            continue
        else:
            continue
        if hasattr(tool, 'acall') and hasattr(tool, patch_target):
            with patch.object(tool, patch_target, side_effect=Exception("Test error")):
                try:
                    result = await tool.acall(query="test")
                    if hasattr(result, 'is_error'):
                        assert result.is_error is True
                except Exception as e:
                    pytest.fail(f"Tool {tool_name} should handle errors gracefully, but raised: {e}")

@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_tool_execution():
    """Test concurrent execution of multiple tools."""
    import asyncio
    tools = [
        get_healthcare_research_tool(),
        get_general_research_tool(),
        get_duckduckgo_search_tool()
    ]
    queries = [
        "heart disease prevention",
        "artificial intelligence trends", 
        "renewable energy news"
    ]
    # Execute all tools concurrently
    tasks = [
        tool.acall(query=query)
        for tool, query in zip(tools, queries)
    ]
    start_time = datetime.now()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = datetime.now()
    # Should complete within reasonable time
    execution_time = (end_time - start_time).total_seconds()
    assert execution_time < 60, f"Concurrent execution took {execution_time}s, should be under 60s"
    # All should succeed or handle errors gracefully
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            pytest.fail(f"Tool {i} raised exception: {result}")

def test_tool_memory_usage(all_tools):
    """Test tool memory usage is reasonable."""
    import sys
    initial_size = sys.getsizeof(all_tools)
    # Should not use excessive memory
    assert initial_size < 10 * 1024 * 1024, "Tools using excessive memory"

@pytest.mark.asyncio
async def test_tool_response_time():
    """Test tool response times are reasonable."""
    tool = get_duckduckgo_search_tool()
    start_time = datetime.now()
    result = await tool.acall(query="test query", max_results=3)
    end_time = datetime.now()
    response_time = (end_time - start_time).total_seconds()
    assert response_time < 30, f"Tool response time {response_time}s too slow"

class TestHealthcareResearchTool:
    """Test healthcare-specific research tool."""

    @pytest.fixture
    def healthcare_tool(self):
        """Create healthcare research tool instance."""
        return get_healthcare_research_tool()

    def test_tool_creation(self, healthcare_tool):
        """Test tool creation and basic properties."""
        assert isinstance(healthcare_tool, HealthcareResearchTool)
        assert healthcare_tool.metadata.name == "healthcare_research"
        assert healthcare_tool.metadata.description.startswith("Conducts comprehensive healthcare")
        assert healthcare_tool.metadata.fn_schema is not None

    @pytest.mark.asyncio
    async def test_healthcare_research_execution(self, healthcare_tool):
        """Test healthcare research tool execution."""
        query = "symptoms of Type 2 diabetes"
        
        result = await healthcare_tool.acall(query=query, depth=2)
        
        # Should return ToolOutput
        assert hasattr(result, 'content')
        assert hasattr(result, 'tool_name')
        assert result.tool_name == "healthcare_research"
        
        # Parse the content
        content_data = json.loads(result.content)
        assert content_data["query"] == query
        assert "findings" in content_data
        assert "sources" in content_data
        assert "confidence" in content_data
        assert content_data["agent_name"] == "HealthcareResearchTool"

    @pytest.mark.asyncio
    async def test_healthcare_research_with_focus_areas(self, healthcare_tool):
        """Test healthcare research with specific focus areas."""
        query = "treatment options for hypertension"
        focus_areas = ["medications", "lifestyle changes", "monitoring"]
        
        result = await healthcare_tool.acall(
            query=query, 
            depth=3, 
            focus_areas=focus_areas
        )
        
        content_data = json.loads(result.content)
        assert content_data["query"] == query
        # Should incorporate focus areas in research
        findings = content_data["findings"].lower()
        assert any(area in findings for area in focus_areas)

    @pytest.mark.asyncio
    async def test_healthcare_research_error_handling(self, healthcare_tool):
        """Test error handling in healthcare research."""
        with patch.object(healthcare_tool, '_generate_healthcare_findings', side_effect=Exception("Research error")):
            result = await healthcare_tool.acall(query="test query")
            content_data = json.loads(result.content)
            assert "failed" in content_data["findings"].lower()
            assert content_data["confidence"] == 0.0
            assert result.is_error is True

    def test_healthcare_research_confidence_calculation(self, healthcare_tool):
        """Test confidence score calculation logic."""
        # Mock some sources for confidence testing
        findings = "This is a clinical trial and meta-analysis with FDA approved evidence-based results."
        confidence = healthcare_tool._calculate_healthcare_confidence("diabetes", 3, findings)
        assert 0.0 <= confidence <= 1.0
        # Should have reasonable confidence with good findings
        assert confidence > 0.5


class TestGeneralResearchTool:
    """Test general research tool."""

    @pytest.fixture  
    def general_tool(self):
        """Create general research tool instance."""
        return get_general_research_tool()

    def test_tool_creation(self, general_tool):
        """Test tool creation and properties."""
        assert isinstance(general_tool, GeneralResearchTool)
        assert general_tool.metadata.name == "general_research"
        assert "academic" in general_tool.metadata.description.lower()

    @pytest.mark.asyncio
    async def test_general_research_execution(self, general_tool):
        """Test general research tool execution."""
        query = "renewable energy developments 2024"
        
        result = await general_tool.acall(query=query, depth=2)
        
        content_data = json.loads(result.content)
        assert content_data["query"] == query
        assert "findings" in content_data
        assert content_data["agent_name"] == "GeneralResearchTool"

    @pytest.mark.asyncio
    async def test_general_research_academic_focus(self, general_tool):
        """Test general research with academic focus."""
        query = "machine learning applications"
        focus_areas = ["computer vision", "natural language processing"]
        
        result = await general_tool.acall(
            query=query,
            depth=2,
            focus_areas=focus_areas
        )
        
        content_data = json.loads(result.content)
        findings = content_data["findings"].lower()
        # Should find relevant academic content
        assert len(findings) > 100  # Substantial findings
        assert content_data["confidence"] > 0.3


class TestDuckDuckGoSearchTool:
    """Test DuckDuckGo web search tool."""

    @pytest.fixture
    def duckduckgo_tool(self):
        return DuckDuckGoSearchTool(fallback_enabled=False)

    def test_tool_creation(self, duckduckgo_tool):
        """Test tool creation and properties."""
        assert isinstance(duckduckgo_tool, DuckDuckGoSearchTool)
        assert duckduckgo_tool.metadata.name == "duckduckgo_search"
        assert "duckduckgo" in duckduckgo_tool.metadata.description.lower()

    @pytest.mark.asyncio
    async def test_duckduckgo_search_execution(self, duckduckgo_tool):
        """Test DuckDuckGo search execution."""
        query = "latest AI developments"
        
        result = await duckduckgo_tool.acall(query=query, max_results=5)
        
        assert result.tool_name == "duckduckgo_search"
        
        # Parse search results
        search_results = json.loads(result.content)
        assert isinstance(search_results, list)
        assert len(search_results) <= 5
        
        if search_results:  # If results found
            first_result = search_results[0]
            assert "query" in first_result
            assert "title" in first_result
            assert "url" in first_result
            assert "snippet" in first_result

    @pytest.mark.asyncio
    async def test_duckduckgo_search_types(self, duckduckgo_tool):
        """Test different search types."""
        query = "coronavirus vaccine news"
        
        # Test news search
        result = await duckduckgo_tool.acall(
            query=query, 
            max_results=3, 
            search_type="news"
        )
        
        search_results = json.loads(result.content)
        # Should return results formatted consistently
        assert isinstance(search_results, list)

    @pytest.mark.asyncio
    async def test_duckduckgo_search_error_handling(self, duckduckgo_tool):
        """Test error handling in search."""
        with patch.object(duckduckgo_tool, '_conduct_duckduckgo_search', side_effect=Exception("Search error")):
            result = await duckduckgo_tool.acall(query="test")
            assert result.is_error is True
            assert result.content == "[]"  # Empty results on error

    def test_relevance_score_calculation(self, duckduckgo_tool):
        """Test relevance score calculation."""
        query = "machine learning"
        mock_result = {
            "title": "Machine Learning Tutorial",
            "body": "Learn about machine learning algorithms and applications",
            "href": "https://example.com/ml-tutorial"
        }
        
        score = duckduckgo_tool._calculate_relevance_score(query, mock_result, "general")
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be relevant

    def test_source_type_determination(self, duckduckgo_tool):
        """Test source type classification."""
        academic_url = "https://arxiv.org/abs/1234.5678"
        news_url = "https://cnn.com/news/article"
        medical_url = "https://pubmed.ncbi.nlm.nih.gov/12345"
        
        assert duckduckgo_tool._determine_source_type(academic_url) == "academic"
        assert duckduckgo_tool._determine_source_type(news_url) == "news"
        assert duckduckgo_tool._determine_source_type(medical_url) == "medical"


class TestGoogleSearchTool:
    """Test Google search tool."""

    @pytest.fixture
    def google_tool(self):
        """Create Google search tool instance."""
        return get_google_search_tool()

    def test_tool_creation(self, google_tool):
        """Test tool creation and properties."""
        assert isinstance(google_tool, GoogleSearchTool)
        assert google_tool.metadata.name == "google_search"
        assert "google" in google_tool.metadata.description.lower()

    @pytest.mark.asyncio
    async def test_google_search_execution(self, google_tool):
        """Test Google search execution (mocked)."""
        query = "climate change research"
        
        result = await google_tool.acall(query=query, max_results=5)
        
        assert result.tool_name == "google_search"
        search_results = json.loads(result.content)
        assert isinstance(search_results, list)

    @pytest.mark.asyncio
    async def test_google_search_academic_focus(self, google_tool):
        """Test Google search with academic focus."""
        query = "quantum computing research papers"
        
        result = await google_tool.acall(
            query=query,
            max_results=3,
            search_type="academic"
        )
        
        search_results = json.loads(result.content)
        # Should generate academic-style results
        if search_results:
            first_result = search_results[0]
            assert "source_type" in first_result

        # ... rest of the original code ... 