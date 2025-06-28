"""
HealthFinder NPPES API Tests

Comprehensive test suite for the NPPES API endpoints,
following SOLID principles and best testing practices.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models import (
    EnumerationType,
    AddressPurpose,
    NPPESSearchRequest,
    NPPESResponse,
    NPPESProvider,
)


class TestNPPESAPIEndpoints:
    """Test class for NPPES API endpoints (Single Responsibility)."""
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_basic_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_provider,
        base_test
    ):
        """Test successful basic NPPES search."""
        # Arrange
        mock_nppes_api_client.search_doctors.return_value = {
            "providers": [mock_provider],
            "total": 1
        }
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/basic",
            params={
                "city": "Chicago",
                "state": "IL",
                "limit": 5
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        base_test.assert_valid_search_response(data)
        assert data["total"] == 1
        assert len(data["providers"]) == 1
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_basic_missing_criteria(self, test_client: TestClient):
        """Test basic search without required criteria."""
        # Act
        response = test_client.get("/api/v1/nppes/search/basic")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least one search criterion" in data["detail"].lower()
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_individual_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_nppes_response
    ):
        """Test successful individual provider search."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "first_name": "Mary",
                "taxonomy_description": "Family Medicine",
                "state": "TX"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == mock_nppes_response.result_count
        mock_nppes_api_client.search_providers_advanced.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_individual_missing_criteria(self, test_client: TestClient):
        """Test individual search without required criteria."""
        # Act
        response = test_client.get("/api/v1/nppes/search/individual")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least one search criterion" in data["detail"].lower()
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_organizational_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_nppes_response
    ):
        """Test successful organizational provider search."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/organizational",
            params={
                "organization_name": "Children Hospital",
                "city": "Philadelphia"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == mock_nppes_response.result_count
        mock_nppes_api_client.search_providers_advanced.assert_called_once()
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_npi_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_provider
    ):
        """Test successful NPI-based search."""
        # Arrange
        mock_nppes_api_client.get_doctor_details.return_value = mock_provider
        
        # Act
        response = test_client.get("/api/v1/nppes/search/by-npi/1234567890")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert data["provider"]["npi"] == mock_provider.npi
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_npi_invalid_format(self, test_client: TestClient):
        """Test NPI search with invalid format."""
        # Act
        response = test_client.get("/api/v1/nppes/search/by-npi/123")  # Invalid NPI
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "10-digit number" in data["detail"]
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_npi_not_found(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test NPI search with provider not found."""
        # Arrange
        mock_nppes_client.get_doctor_details.return_value = None
        
        # Act
        response = test_client.get("/api/v1/nppes/search/by-npi/9999999999")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_taxonomy_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_nppes_response
    ):
        """Test successful taxonomy-based search."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/by-taxonomy",
            params={
                "taxonomy_description": "Physical Therapist",
                "state": "FL"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == mock_nppes_response.result_count
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_location_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_nppes_response
    ):
        """Test successful location-based search."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/by-location",
            params={
                "postal_code": "90210",
                "city": "Beverly Hills"  # Add required parameter
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == mock_nppes_response.result_count
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_location_missing_criteria(self, test_client: TestClient):
        """Test location search without required criteria."""
        # Act
        response = test_client.get("/api/v1/nppes/search/by-location")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least one location criterion" in data["detail"].lower()
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_advanced_success(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_nppes_response
    ):
        """Test successful advanced search."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.post(
            "/api/v1/nppes/search/advanced",
            json={
                "enumeration_type": "NPI-1",
                "first_name": "David",
                "use_first_name_alias": True,
                "state": "CA",
                "limit": 20
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "result_count" in data
        assert "results" in data
        assert data["result_count"] == mock_nppes_response.result_count
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_validate_npi_valid_exists(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_provider
    ):
        """Test NPI validation with valid existing NPI."""
        # Arrange
        mock_nppes_api_client.get_doctor_details.return_value = mock_provider
        
        # Act
        response = test_client.get("/api/v1/nppes/validate/npi/1234567890")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["exists"] is True
        assert data["npi"] == "1234567890"
        assert "provider_name" in data
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_validate_npi_valid_not_exists(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test NPI validation with valid but non-existent NPI."""
        # Arrange
        mock_nppes_client.get_doctor_details.return_value = None
        
        # Act
        response = test_client.get("/api/v1/nppes/validate/npi/9999999999")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["exists"] is False
        assert data["npi"] == "9999999999"
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_validate_npi_invalid_format(self, test_client: TestClient):
        """Test NPI validation with invalid format."""
        # Act
        response = test_client.get("/api/v1/nppes/validate/npi/123abc")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data
        assert "only digits" in data["error"]
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_validate_npi_wrong_length(self, test_client: TestClient):
        """Test NPI validation with wrong length."""
        # Act
        response = test_client.get("/api/v1/nppes/validate/npi/123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data
        assert "exactly 10 digits" in data["error"]
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_get_nppes_info(self, test_client: TestClient):
        """Test getting NPPES API information."""
        # Act
        response = test_client.get("/api/v1/nppes/info")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "limitations" in data
        assert "enumeration_types" in data
        assert data["version"] == "2.1"
        assert data["limitations"]["max_results_per_request"] == 200
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_get_nppes_stats(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_nppes_response
    ):
        """Test getting NPPES statistics."""
        # Arrange
        mock_nppes_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get("/api/v1/nppes/stats/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sample_states" in data
        assert "individual_providers" in data
        assert "organizational_providers" in data
        assert "total_sampled" in data
        assert "by_state" in data


class TestNPPESAPIValidation:
    """Test class for NPPES API input validation (Single Responsibility)."""
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_individual_invalid_limit(self, test_client: TestClient):
        """Test individual search with invalid limit."""
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "first_name": "John",
                "limit": 300  # Exceeds max limit
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_organizational_invalid_skip(self, test_client: TestClient):
        """Test organizational search with invalid skip."""
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/organizational",
            params={
                "organization_name": "Hospital",
                "skip": 2000  # Exceeds max skip
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_by_taxonomy_missing_description(self, test_client: TestClient):
        """Test taxonomy search without required description."""
        # Act
        response = test_client.get("/api/v1/nppes/search/by-taxonomy")
        
        # Assert
        assert response.status_code == 422  # Missing required parameter
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_advanced_search_invalid_enumeration_type(self, test_client: TestClient):
        """Test advanced search with invalid enumeration type."""
        # Act
        response = test_client.post(
            "/api/v1/nppes/search/advanced",
            json={
                "enumeration_type": "INVALID-TYPE",
                "state": "CA"
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestNPPESAPIEdgeCases:
    """Test class for NPPES API edge cases (Single Responsibility)."""
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_with_special_characters(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_nppes_response
    ):
        """Test search with special characters."""
        # Arrange
        mock_nppes_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "first_name": "José",
                "last_name": "O'Connor-Smith",
                "state": "CA"
            }
        )
        
        # Assert
        assert response.status_code == 200
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_with_wildcard_patterns(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_nppes_response
    ):
        """Test search with wildcard patterns."""
        # Arrange
        mock_nppes_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "first_name": "Jo*",
                "last_name": "Sm*",
                "state": "NY"
            }
        )
        
        # Assert
        assert response.status_code == 200
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_search_max_pagination_values(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_nppes_response
    ):
        """Test search with maximum pagination values."""
        # Arrange
        mock_nppes_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "first_name": "John",
                "limit": 200,  # Max limit
                "skip": 1000   # Max skip
            }
        )
        
        # Assert
        assert response.status_code == 200
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_empty_search_results(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test handling of empty search results."""
        # Arrange
        empty_response = NPPESResponse(result_count=0, results=[])
        mock_nppes_client.search_providers_advanced.return_value = empty_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "first_name": "NonExistent",
                "state": "XX"  # Non-existent state
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["providers"]) == 0


class TestNPPESAPIIntegration:
    """Test class for NPPES API integration scenarios."""
    
    @pytest.mark.api
    @pytest.mark.nppes
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_individual_async(
        self,
        async_client: AsyncClient,
        mock_nppes_api_client,
        mock_nppes_response
    ):
        """Test async individual provider search."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        
        # Act
        response = await async_client.get(
            "/api/v1/nppes/search/individual",
            params={"first_name": "John", "state": "CA"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == mock_nppes_response.result_count
    
    @pytest.mark.api
    @pytest.mark.nppes
    @pytest.mark.integration
    def test_full_search_workflow(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_nppes_response,
        mock_provider
    ):
        """Test complete search workflow from basic to details."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.return_value = mock_nppes_response
        mock_nppes_api_client.get_doctor_details.return_value = mock_provider
        
        # Step 1: Basic search
        search_response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={"first_name": "John", "state": "CA"}
        )
        assert search_response.status_code == 200
        
        # Step 2: Get provider details
        details_response = test_client.get(
            f"/api/v1/nppes/search/by-npi/{mock_provider.npi}"
        )
        assert details_response.status_code == 200
        
        # Step 3: Validate NPI
        validate_response = test_client.get(
            f"/api/v1/nppes/validate/npi/{mock_provider.npi}"
        )
        assert validate_response.status_code == 200
        
        # Verify workflow integrity
        validate_data = validate_response.json()
        assert validate_data["valid"] is True
        assert validate_data["exists"] is True


class TestNPPESAPIPerformance:
    """Test class for NPPES API performance scenarios."""
    
    @pytest.mark.api
    @pytest.mark.nppes
    @pytest.mark.slow
    def test_large_result_set_handling(
        self,
        test_client: TestClient,
        mock_nppes_api_client,
        mock_data_factory
    ):
        """Test handling of large result sets."""
        # Arrange
        large_response = mock_data_factory.create_nppes_response(count=200)
        mock_nppes_api_client.search_providers_advanced.return_value = large_response
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={
                "state": "CA",
                "limit": 200
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 200
        assert len(data["providers"]) == 200
    
    @pytest.mark.api
    @pytest.mark.nppes
    @pytest.mark.slow
    def test_concurrent_npi_validations(
        self,
        test_client: TestClient,
        mock_nppes_client,
        mock_provider
    ):
        """Test concurrent NPI validations."""
        # Arrange
        mock_nppes_client.get_doctor_details.return_value = mock_provider
        
        # Act & Assert
        npis = ["1234567890", "1234567891", "1234567892", "1234567893", "1234567894"]
        responses = []
        
        for npi in npis:
            response = test_client.get(f"/api/v1/nppes/validate/npi/{npi}")
            responses.append(response)
        
        # All validations should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True


class TestNPPESAPIErrorHandling:
    """Test class for NPPES API error handling scenarios."""
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_nppes_client_error_handling(
        self,
        test_client: TestClient,
        mock_nppes_api_client
    ):
        """Test handling of NPPES client errors."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.side_effect = Exception("NPPES API Error")
        
        # Act
        response = test_client.get(
            "/api/v1/nppes/search/individual",
            params={"first_name": "John", "state": "CA"}
        )
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error searching individual providers" in data["detail"]
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_advanced_search_error_handling(
        self,
        test_client: TestClient,
        mock_nppes_api_client
    ):
        """Test handling of advanced search errors."""
        # Arrange
        mock_nppes_api_client.search_providers_advanced.side_effect = Exception("API Timeout")
        
        # Act
        response = test_client.post(
            "/api/v1/nppes/search/advanced",
            json={
                "enumeration_type": "NPI-1",
                "state": "CA"
            }
        )
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error in advanced NPPES search" in data["detail"]
    
    @pytest.mark.api
    @pytest.mark.nppes
    def test_npi_validation_error_handling(
        self,
        test_client: TestClient,
        mock_nppes_api_client
    ):
        """Test handling of NPI validation errors."""
        # Arrange
        mock_nppes_api_client.get_doctor_details.side_effect = Exception("Network Error")
        
        # Act
        response = test_client.get("/api/v1/nppes/validate/npi/1234567890")
        
        # Assert
        assert response.status_code == 200  # Should still return response
        data = response.json()
        assert data["valid"] is True  # Format is valid
        assert data["exists"] is None  # Unknown due to error
