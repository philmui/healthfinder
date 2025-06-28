"""
HealthFinder Providers API Tests

Comprehensive test suite for the providers API endpoints,
following SOLID principles and best testing practices.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models import (
    ProviderType,
    EnumerationType,
    Gender,
    SortOption,
    SearchProviderRequest,
    IndividualProvider,
    OrganizationalProvider,
)


class TestProvidersAPIEndpoints:
    """Test class for providers API endpoints (Single Responsibility)."""
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_success(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider,
        base_test
    ):
        """Test successful provider search."""
        # Arrange - Use the correct mock for provider API
        from unittest.mock import AsyncMock
        mock_nppes_client.search_doctors = AsyncMock(return_value={
            "providers": [mock_provider],
            "total": 1
        })
        
        # Act - Use params that will trigger NPPES call 
        response = test_client.get(
            "/api/v1/providers/search",
            params={
                "query": "John Smith",
                "state": "CA",  # This will create a location with country="US"
                "limit": 10
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        base_test.assert_valid_search_response(data)
        
        # Debug: Check if mock was called
        mock_nppes_client.search_doctors.assert_called_once()
        assert data["total"] == 1
        assert len(data["providers"]) == 1
        base_test.assert_valid_provider(data["providers"][0])
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_with_all_parameters(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test provider search with all possible parameters."""
        # Arrange - Configure async mock properly
        from unittest.mock import AsyncMock
        mock_nppes_client.search_doctors = AsyncMock(return_value={
            "providers": [mock_provider],
            "total": 1
        })
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={
                "first_name": "John",
                "last_name": "Smith",
                "organization_name": "Test Hospital",
                "provider_type": ProviderType.PHYSICIAN.value,
                "enumeration_type": EnumerationType.INDIVIDUAL.value,
                "specialty": "Family Medicine",
                "taxonomy_description": "207Q00000X",
                "city": "Los Angeles",
                "state": "CA",
                "postal_code": "90210",
                "gender": Gender.MALE.value,
                "sort_by": SortOption.NAME.value,
                "page": 1,
                "limit": 20,
                "skip": 0
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Debug: Check if mock was called
        mock_nppes_client.search_doctors.assert_called_once()
        assert data["total"] == 1
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_no_results(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test provider search with no results."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [],
            "total": 0
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "XX"}  # Non-existent state
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["providers"]) == 0
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_error_handling(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test provider search error handling."""
        # Arrange
        mock_nppes_client.search_doctors.side_effect = Exception("API Error")
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA"}
        )
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error searching providers" in data["detail"]
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_individual_providers(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test search for individual providers only."""
        # Arrange
        mock_nppes_client.search_individual_providers.return_value = {
            "providers": [mock_provider],
            "total": 1
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search/individual",
            params={
                "first_name": "John",
                "last_name": "Smith",
                "state": "CA"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_nppes_client.search_individual_providers.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_organizational_providers(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_org_provider
    ):
        """Test search for organizational providers only."""
        # Arrange
        mock_nppes_client.search_organizational_providers.return_value = {
            "providers": [mock_org_provider],
            "total": 1
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search/organizational",
            params={
                "organization_name": "General Hospital",
                "city": "Boston",
                "state": "MA"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_nppes_client.search_organizational_providers.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_by_taxonomy(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test search by taxonomy code."""
        # Arrange
        mock_nppes_client.search_by_taxonomy.return_value = {
            "providers": [mock_provider],
            "total": 1
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search/by-taxonomy",
            params={
                "taxonomy_code": "207Q00000X",
                "state": "CA"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_nppes_client.search_by_taxonomy.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_get_provider_details_success(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test successful provider details retrieval."""
        # Arrange
        mock_nppes_client.get_doctor_details.return_value = mock_provider
        
        # Act
        response = test_client.get(
            "/api/v1/providers/nppes-1234567890",
            params={"source": "nppes"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert data["provider"]["id"] == mock_provider.id
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_get_provider_details_not_found(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test provider details not found."""
        # Arrange
        mock_nppes_client.get_doctor_details.return_value = None
        
        # Act
        response = test_client.get(
            "/api/v1/providers/invalid-id",
            params={"source": "nppes"}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_get_provider_types(self, test_client: TestClient):
        """Test getting all provider types."""
        # Act
        response = test_client.get("/api/v1/providers/types")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "individual_providers" in data
        assert "organizational_providers" in data
        assert isinstance(data["individual_providers"], list)
        assert isinstance(data["organizational_providers"], list)
        
        # Verify some expected provider types
        individual_types = data["individual_providers"]
        assert "physician" in individual_types
        assert "nurse" in individual_types
        assert "physical_therapist" in individual_types
        
        org_types = data["organizational_providers"]
        assert "hospital" in org_types
        assert "clinic" in org_types
        assert "pharmacy" in org_types
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_get_provider_stats_by_state(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test getting provider statistics by state."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [mock_provider, mock_provider],
            "total": 2
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/stats/by-state",
            params={"state": "CA", "limit": 50}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_providers" in data
        assert "by_type" in data
        assert "by_specialty" in data
        assert "by_city" in data
        assert data["total_providers"] == 2


class TestProvidersAPIValidation:
    """Test class for providers API input validation (Single Responsibility)."""
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_invalid_limit(self, test_client: TestClient):
        """Test search with invalid limit parameter."""
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA", "limit": 300}  # Exceeds max limit
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_invalid_skip(self, test_client: TestClient):
        """Test search with invalid skip parameter."""
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA", "skip": 2000}  # Exceeds max skip
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_invalid_page(self, test_client: TestClient):
        """Test search with invalid page parameter."""
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA", "page": 0}  # Page must be >= 1
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_by_taxonomy_missing_code(self, test_client: TestClient):
        """Test taxonomy search without required taxonomy code."""
        # Act
        response = test_client.get("/api/v1/providers/search/by-taxonomy")
        
        # Assert
        assert response.status_code == 422  # Missing required parameter
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_get_provider_details_missing_source(self, test_client: TestClient):
        """Test provider details without required source parameter."""
        # Act
        response = test_client.get("/api/v1/providers/test-id")
        
        # Assert
        assert response.status_code == 422  # Missing required parameter


class TestProvidersAPIEdgeCases:
    """Test class for providers API edge cases (Single Responsibility)."""
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_special_characters(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test search with special characters in names."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [mock_provider],
            "total": 1
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={
                "first_name": "José",
                "last_name": "O'Brien-Smith",
                "state": "CA"
            }
        )
        
        # Assert
        assert response.status_code == 200
        mock_nppes_client.search_doctors.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.providers
    def test_search_providers_empty_query(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test search with empty query parameters."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [],
            "total": 0
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"query": "", "state": "CA"}
        )
        
        # Assert
        assert response.status_code == 200
    
    @pytest.mark.api
    @pytest.mark.providers  
    def test_search_providers_max_pagination(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test search with maximum pagination values."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [],
            "total": 0
        }
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={
                "state": "CA",
                "limit": 200,  # Max limit
                "skip": 1000   # Max skip
            }
        )
        
        # Assert
        assert response.status_code == 200


class TestProvidersAPIIntegration:
    """Test class for providers API integration scenarios."""
    
    @pytest.mark.api
    @pytest.mark.providers
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_providers_async(
        self,
        async_client: AsyncClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test async provider search."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [mock_provider],
            "total": 1
        }
        
        # Act
        response = await async_client.get(
            "/api/v1/providers/search",
            params={"state": "CA", "limit": 5}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
    
    @pytest.mark.api
    @pytest.mark.providers
    @pytest.mark.integration
    def test_multiple_provider_types_search(
        self,
        test_client: TestClient,
        mock_nppes_client,
        base_test
    ):
        """Test search across multiple provider types."""
        # Arrange
        individual_provider = base_test.create_mock_provider(
            ProviderType.PHYSICIAN,
            EnumerationType.INDIVIDUAL
        )
        # Give the individual provider a unique ID
        individual_provider.id = "nppes-1111111111"
        individual_provider.npi = "1111111111"
        
        org_provider = base_test.create_mock_provider(
            ProviderType.HOSPITAL,
            EnumerationType.ORGANIZATIONAL
        )
        # Give the org provider a unique ID
        org_provider.id = "nppes-2222222222"
        org_provider.npi = "2222222222"
        
        # Configure mock to return both provider types
        from unittest.mock import AsyncMock
        mock_nppes_client.search_doctors = AsyncMock(return_value={
            "providers": [individual_provider, org_provider],
            "total": 2
        })
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA", "limit": 10}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        
        # Verify different provider types returned
        provider_types = [p["provider_type"] for p in data["providers"]]
        assert len(set(provider_types)) > 1  # Multiple different types


# Performance and Load Testing Helpers
class TestProvidersAPIPerformance:
    """Test class for providers API performance scenarios."""
    
    @pytest.mark.api
    @pytest.mark.providers
    @pytest.mark.slow
    def test_search_providers_large_result_set(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_data_factory,
        base_test
    ):
        """Test search with large result set."""
        # Arrange
        large_provider_list = []
        for i in range(200):  # Max NPPES limit
            provider = base_test.create_mock_provider()
            # Give each provider a unique ID to avoid deduplication
            provider.id = f"nppes-{1234567890 + i}"
            provider.npi = f"{1234567890 + i}"
            large_provider_list.append(provider)
        
        # Configure mock to return the large provider list
        from unittest.mock import AsyncMock
        mock_nppes_client.search_doctors = AsyncMock(return_value={
            "providers": large_provider_list,
            "total": 200
        })
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA", "limit": 200}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 200
        assert len(data["providers"]) == 200
    
    @pytest.mark.api
    @pytest.mark.providers
    @pytest.mark.slow
    def test_concurrent_requests_simulation(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Simulate concurrent requests to test thread safety."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {
            "providers": [mock_provider],
            "total": 1
        }
        
        # Act & Assert
        responses = []
        for i in range(10):
            response = test_client.get(
                "/api/v1/providers/search",
                params={"state": "CA", "query": f"test{i}"}
            )
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200 