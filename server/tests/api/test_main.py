"""
HealthFinder Main Application Tests

Comprehensive test suite for the main FastAPI application,
including health checks, root endpoints, and core functionality.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestMainApplicationEndpoints:
    """Test class for main application endpoints (Single Responsibility)."""
    
    @pytest.mark.api
    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        # Act
        response = test_client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
    
    @pytest.mark.api
    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint information."""
        # Act
        response = test_client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        required_fields = ["name", "version", "description", "docs_url", "capabilities", "endpoints"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify content
        assert data["name"] == "HealthFinder API"
        assert data["version"] == "0.1.0"
        assert "capabilities" in data
        assert "endpoints" in data
        
        # Verify capabilities
        capabilities = data["capabilities"]
        assert "provider_search" in capabilities
        assert "nppes_integration" in capabilities
        assert "provider_types" in capabilities
        assert "search_features" in capabilities
        
        # Verify endpoints use consistent /api/v1 prefix
        endpoints = data["endpoints"]
        assert endpoints["providers"].startswith("/api/v1/providers")
        assert endpoints["nppes"].startswith("/api/v1/nppes")
        assert endpoints["auth"].startswith("/api/v1/auth")
        assert endpoints["biomcp"].startswith("/api/v1/biomcp")
    
    @pytest.mark.api
    def test_docs_endpoint_accessible(self, test_client: TestClient):
        """Test that API documentation is accessible."""
        # Act
        response = test_client.get("/docs")
        
        # Assert
        assert response.status_code == 200
        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.api
    def test_openapi_schema(self, test_client: TestClient):
        """Test OpenAPI schema endpoint."""
        # Act
        response = test_client.get("/openapi.json")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify OpenAPI schema structure
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        
        # Verify API info
        assert data["info"]["title"] == "HealthFinder API"
        assert data["info"]["version"] == "0.1.0"
        
        # Verify paths use consistent /api/v1 prefix
        paths = data["paths"]
        api_v1_paths = [path for path in paths.keys() if path.startswith("/api/v1")]
        assert len(api_v1_paths) > 0, "Should have /api/v1 prefixed endpoints"


class TestMainApplicationCORS:
    """Test class for CORS configuration (Single Responsibility)."""
    
    @pytest.mark.api
    def test_cors_preflight_request(self, test_client: TestClient):
        """Test CORS preflight request handling."""
        # Act
        response = test_client.options(
            "/api/v1/providers/search",
            headers={
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
                "Origin": "http://localhost:3000"
            }
        )
        
        # Assert
        assert response.status_code == 200
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers
    
    @pytest.mark.api
    def test_cors_actual_request(self, test_client: TestClient, mock_nppes_client):
        """Test CORS headers on actual request."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {"providers": [], "total": 0}
        
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"state": "CA"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Assert
        assert response.status_code == 200
        headers = response.headers
        assert "access-control-allow-origin" in headers


class TestMainApplicationErrorHandling:
    """Test class for application-level error handling (Single Responsibility)."""
    
    @pytest.mark.api
    def test_404_error_handling(self, test_client: TestClient):
        """Test 404 error handling."""
        # Act
        response = test_client.get("/non-existent-endpoint")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.api
    def test_method_not_allowed_error(self, test_client: TestClient):
        """Test method not allowed error handling."""
        # Act
        response = test_client.post("/health")  # Health endpoint only supports GET
        
        # Assert
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.api
    def test_request_validation_error(self, test_client: TestClient):
        """Test request validation error handling."""
        # Act
        response = test_client.get(
            "/api/v1/providers/search",
            params={"limit": "invalid"}  # Should be integer
        )
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.api
    def test_internal_server_error_handling(
        self,
        test_client: TestClient
    ):
        """Test internal server error handling."""
        # Arrange - Mock the NPPES client where it's imported in the providers module
        with patch("app.api.providers.nppes_client") as mock_client:
            mock_client.search_doctors.side_effect = Exception("Internal error")
            
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


class TestMainApplicationSecurity:
    """Test class for application security features (Single Responsibility)."""
    
    @pytest.mark.api
    def test_security_headers_present(self, test_client: TestClient):
        """Test that security headers are present."""
        # Act
        response = test_client.get("/")
        
        # Assert
        assert response.status_code == 200
        # Note: Add security header checks here when implemented
    
    @pytest.mark.api
    def test_sql_injection_protection(self, test_client: TestClient, mock_nppes_client):
        """Test protection against SQL injection attempts."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {"providers": [], "total": 0}
        
        # Act - Try SQL injection in search query
        response = test_client.get(
            "/api/v1/providers/search",
            params={
                "query": "'; DROP TABLE providers; --",
                "state": "CA"
            }
        )
        
        # Assert - Should handle gracefully without error
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_xss_protection(self, test_client: TestClient, mock_nppes_client):
        """Test protection against XSS attempts."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {"providers": [], "total": 0}
        
        # Act - Try XSS in search query
        response = test_client.get(
            "/api/v1/providers/search",
            params={
                "query": "<script>alert('xss')</script>",
                "state": "CA"
            }
        )
        
        # Assert - Should handle gracefully
        assert response.status_code == 200


class TestMainApplicationIntegration:
    """Test class for application integration scenarios."""
    
    @pytest.mark.api
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_endpoint_access(self, async_client: AsyncClient):
        """Test async access to endpoints."""
        # Act
        response = await async_client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_multiple_endpoints_consistency(
        self,
        test_client: TestClient,
        mock_nppes_client
    ):
        """Test consistency across multiple endpoints."""
        # Arrange
        mock_nppes_client.search_doctors.return_value = {"providers": [], "total": 0}
        mock_nppes_client.search_providers_advanced.return_value = {
            "result_count": 0,
            "results": []
        }
        
        # Act - Test multiple provider-related endpoints
        endpoints_to_test = [
            ("/api/v1/providers/search?state=CA", 200),
            ("/api/v1/providers/types", 200),
            ("/api/v1/nppes/info", 200),
            ("/health", 200),
            ("/", 200)
        ]
        
        responses = []
        for endpoint, expected_status in endpoints_to_test:
            response = test_client.get(endpoint)
            responses.append((endpoint, response.status_code, expected_status))
        
        # Assert - All endpoints should return expected status
        for endpoint, actual_status, expected_status in responses:
            assert actual_status == expected_status, f"Endpoint {endpoint} returned {actual_status}, expected {expected_status}"


class TestMainApplicationPerformance:
    """Test class for application performance scenarios."""
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_health_check_performance(self, test_client: TestClient):
        """Test health check endpoint performance."""
        import time
        
        # Act - Multiple rapid health checks
        start_time = time.time()
        for _ in range(100):
            response = test_client.get("/health")
            assert response.status_code == 200
        end_time = time.time()
        
        # Assert - Should complete quickly
        total_time = end_time - start_time
        assert total_time < 5.0, f"100 health checks took {total_time:.2f}s, should be under 5s"
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_concurrent_requests_handling(self, test_client: TestClient):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            start = time.time()
            response = test_client.get("/health")
            end = time.time()
            results.append({
                "status": response.status_code,
                "duration": end - start
            })
        
        # Act - Create multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Assert - All requests should succeed
        assert len(results) == 10
        for result in results:
            assert result["status"] == 200
            assert result["duration"] < 1.0  # Should respond quickly


class TestMainApplicationConfiguration:
    """Test class for application configuration (Single Responsibility)."""
    
    @pytest.mark.api
    def test_environment_configuration(self, test_client: TestClient):
        """Test that environment configuration is properly loaded."""
        # This is mostly verified by the app starting successfully
        # Additional environment-specific tests can be added here
        
        # Act
        response = test_client.get("/")
        
        # Assert
        assert response.status_code == 200
        # Configuration is working if the app responds
    
    @pytest.mark.api
    def test_cors_configuration(self, test_client: TestClient):
        """Test CORS configuration is properly applied."""
        # Act
        response = test_client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Assert
        assert response.status_code == 200
        # CORS headers should be present (tested in CORS section)
    
    @pytest.mark.api
    def test_api_versioning_consistency(self, test_client: TestClient):
        """Test API versioning is consistently applied."""
        # Act
        response = test_client.get("/openapi.json")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify all API paths use /api/v1 prefix
        paths = data.get("paths", {})
        api_paths = [path for path in paths.keys() if not path in ["/", "/health", "/docs", "/openapi.json"]]
        
        for path in api_paths:
            assert path.startswith("/api/v1"), f"Path {path} should start with /api/v1" 