"""
HealthFinder Test Configuration and Fixtures

This module provides comprehensive test fixtures and configuration for the
HealthFinder test suite, following SOLID principles and best practices.
"""

# Set up test environment variables BEFORE importing the app
import os
os.environ["DEBUG"] = "False"  # Ensure DEBUG is a proper boolean value
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_DB_FILE"] = ":memory:"

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any, Union
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.models import (
    SearchProviderRequest,
    IndividualProvider,
    OrganizationalProvider,
    ProviderType,
    EnumerationType,
    Location,
    ProviderSpecialty,
    NPPESSearchRequest,
    NPPESResponse,
    NPPESProvider,
    NPPESBasic,
    NPPESAddress,
    NPPESTaxonomy,
)


# Test Configuration
class TestConfig:
    """Test configuration constants."""
    TEST_BASE_URL = "http://testserver"
    API_V1_PREFIX = "/api/v1"
    DEFAULT_TIMEOUT = 10.0
    MOCK_NPI = "1234567890"
    MOCK_PROVIDER_ID = "nppes-1234567890"


# Base Test Classes (Single Responsibility Principle)
class BaseTestCase:
    """Base test case with common functionality."""
    
    @staticmethod
    def assert_valid_provider(provider: Dict[str, Any]) -> None:
        """Assert that a provider dictionary contains required fields."""
        required_fields = ["id", "name", "provider_type", "source", "location"]
        for field in required_fields:
            assert field in provider, f"Missing required field: {field}"
        
        assert provider["location"] is not None
        assert "city" in provider["location"] or "state" in provider["location"]
    
    @staticmethod
    def assert_valid_search_response(response: Dict[str, Any]) -> None:
        """Assert that a search response has the correct structure."""
        required_fields = ["total", "page", "limit", "providers"]
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"
        
        assert isinstance(response["total"], int)
        assert isinstance(response["providers"], list)
    
    @staticmethod
    def create_mock_provider(
        provider_type: ProviderType = ProviderType.PHYSICIAN,
        enumeration_type: EnumerationType = EnumerationType.INDIVIDUAL
    ) -> Union[IndividualProvider, OrganizationalProvider]:
        """Create a mock provider for testing."""
        location = Location(
            city="Test City",
            state="CA",
            postal_code="90210",
            country="US"
        )
        
        specialty = ProviderSpecialty(
            name="Family Medicine",
            description="Family Medicine",
            primary=True
        )
        
        if enumeration_type == EnumerationType.INDIVIDUAL:
            return IndividualProvider(
                id=TestConfig.MOCK_PROVIDER_ID,
                name="Dr. Test Provider",
                provider_type=provider_type,
                enumeration_type=enumeration_type,
                specialties=[specialty],
                location=location,
                source="nppes",
                npi=TestConfig.MOCK_NPI,
                first_name="Test",
                last_name="Provider",
                gender="M"
            )
        else:
            return OrganizationalProvider(
                id=TestConfig.MOCK_PROVIDER_ID,
                name="Test Hospital",
                provider_type=provider_type,
                enumeration_type=enumeration_type,
                specialties=[specialty],
                location=location,
                source="nppes",
                npi=TestConfig.MOCK_NPI,
                organization_name="Test Hospital"
            )


class MockDataFactory:
    """Factory for creating test data (Factory Pattern)."""
    
    @staticmethod
    def create_nppes_response(count: int = 3) -> NPPESResponse:
        """Create mock NPPES response."""
        providers = []
        for i in range(count):
            basic = NPPESBasic(
                first_name=f"John{i}",
                last_name=f"Doe{i}",
                enumeration_type="NPI-1",
                gender="M"
            )
            
            address = NPPESAddress(
                city="Test City",
                state="CA",
                address_purpose="LOCATION"
            )
            
            taxonomy = NPPESTaxonomy(
                desc="Family Medicine",
                primary=True
            )
            
            provider = NPPESProvider(
                number=f"123456789{i}",
                basic=basic,
                addresses=[address],
                taxonomies=[taxonomy]
            )
            providers.append(provider)
        
        return NPPESResponse(result_count=count, results=providers)
    
    @staticmethod
    def create_search_request(**kwargs) -> SearchProviderRequest:
        """Create mock search request."""
        defaults = {
            "state": "CA",
            "limit": 10,
            "page": 1
        }
        defaults.update(kwargs)
        return SearchProviderRequest(**defaults)


# Pytest Fixtures
@pytest.fixture
def test_config() -> TestConfig:
    """Provide test configuration."""
    return TestConfig()


@pytest.fixture
def base_test() -> BaseTestCase:
    """Provide base test case utilities."""
    return BaseTestCase()


@pytest.fixture
def mock_data_factory() -> MockDataFactory:
    """Provide mock data factory."""
    return MockDataFactory()


@pytest.fixture
def test_client() -> TestClient:
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide async HTTP client for testing."""
    from fastapi.testclient import TestClient
    # For async testing, we'll use the regular test client 
    # since FastAPI handles async internally
    test_client = TestClient(app)
    
    # Create a mock async client that delegates to the sync test client
    class MockAsyncClient:
        def __init__(self, client):
            self._client = client
            
        async def get(self, url, **kwargs):
            response = self._client.get(url, **kwargs)
            # Create a mock response object with json() method
            class MockResponse:
                def __init__(self, response):
                    self._response = response
                    self.status_code = response.status_code
                    
                def json(self):
                    return self._response.json()
                    
            return MockResponse(response)
    
    yield MockAsyncClient(test_client)


@pytest.fixture
def mock_provider(base_test: BaseTestCase) -> IndividualProvider:
    """Provide mock provider instance."""
    return base_test.create_mock_provider()


@pytest.fixture
def mock_org_provider(base_test: BaseTestCase) -> OrganizationalProvider:
    """Provide mock organizational provider instance."""
    return base_test.create_mock_provider(
        provider_type=ProviderType.HOSPITAL,
        enumeration_type=EnumerationType.ORGANIZATIONAL
    )


@pytest.fixture
def mock_search_request(mock_data_factory: MockDataFactory) -> SearchProviderRequest:
    """Provide mock search request."""
    return mock_data_factory.create_search_request()


@pytest.fixture
def mock_nppes_response(mock_data_factory: MockDataFactory) -> NPPESResponse:
    """Provide mock NPPES API response."""
    return mock_data_factory.create_nppes_response()


# Mock External Dependencies (Dependency Inversion Principle)
@pytest.fixture
def mock_nppes_client():
    """Mock NPPES client for testing."""
    from unittest.mock import AsyncMock
    
    with patch("app.api.providers.nppes_client") as mock_client:
        # Configure mock methods as async
        mock_client.search_doctors = AsyncMock(return_value={
            "providers": [
                BaseTestCase.create_mock_provider()
            ],
            "total": 1
        })
        
        mock_client.get_doctor_details = AsyncMock(return_value=BaseTestCase.create_mock_provider())
        
        mock_client.search_providers_advanced = AsyncMock(return_value=MockDataFactory.create_nppes_response())
        
        mock_client.search_individual_providers = AsyncMock(return_value={
            "providers": [BaseTestCase.create_mock_provider()],
            "total": 1
        })
        
        mock_client.search_organizational_providers = AsyncMock(return_value={
            "providers": [BaseTestCase.create_mock_provider(
                provider_type=ProviderType.HOSPITAL,
                enumeration_type=EnumerationType.ORGANIZATIONAL
            )],
            "total": 1
        })
        
        mock_client.search_by_taxonomy = AsyncMock(return_value={
            "providers": [BaseTestCase.create_mock_provider()],
            "total": 1
        })
        
        # Mock the transformation method that converts NPPES data to our models
        def mock_transform(nppes_data):
            """Transform any NPPES data to a valid provider instance."""
            return BaseTestCase.create_mock_provider()
        
        mock_client._transform_nppes_provider = mock_transform
        
        yield mock_client


@pytest.fixture
def mock_nppes_api_client():
    """Mock NPPES client for NPPES API endpoints."""
    from unittest.mock import AsyncMock
    
    with patch("app.api.nppes.nppes_client") as mock_client:
        mock_client.search_doctors = AsyncMock(return_value={
            "providers": [BaseTestCase.create_mock_provider()],
            "total": 1
        })
        
        mock_client.get_doctor_details = AsyncMock(return_value=BaseTestCase.create_mock_provider())
        
        mock_client.search_providers_advanced = AsyncMock(return_value=MockDataFactory.create_nppes_response())
        
        # Mock the transformation method that converts NPPES data to our models
        def mock_transform(nppes_data):
            """Transform any NPPES data to a valid provider instance."""
            return BaseTestCase.create_mock_provider()
        
        mock_client._transform_nppes_provider = mock_transform
        
        yield mock_client

@pytest.fixture
def mock_practo_client():
    """Mock Practo client for testing."""
    with patch("app.clients.practo") as mock_client:
        mock_client.search_doctors.return_value = {
            "providers": [],
            "total": 0
        }
        
        mock_client.get_doctor_details.return_value = None
        
        yield mock_client


@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    with patch("app.core.db.database") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.disconnect = AsyncMock()
        yield mock_db


# Event Loop Management
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test Data Validation Utilities
class TestDataValidator:
    """Validator for test data integrity (Single Responsibility)."""
    
    @staticmethod
    def validate_provider_response(response: Dict[str, Any]) -> bool:
        """Validate provider response structure."""
        try:
            BaseTestCase.assert_valid_search_response(response)
            for provider in response["providers"]:
                BaseTestCase.assert_valid_provider(provider)
            return True
        except AssertionError:
            return False
    
    @staticmethod
    def validate_api_response_format(response: Dict[str, Any]) -> bool:
        """Validate standard API response format."""
        if "error" in response:
            return "detail" in response
        return "data" in response or "total" in response


@pytest.fixture
def test_validator() -> TestDataValidator:
    """Provide test data validator."""
    return TestDataValidator()


# Custom Pytest Markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "providers: mark test as provider-related")
    config.addinivalue_line("markers", "nppes: mark test as NPPES-related")
    config.addinivalue_line("markers", "auth: mark test as authentication-related")


# Pytest Collection Hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add markers based on test file location
        if "test_providers" in str(item.fspath):
            item.add_marker(pytest.mark.providers)
        elif "test_nppes" in str(item.fspath):
            item.add_marker(pytest.mark.nppes)
        elif "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.auth)
        
        # Add API marker for all endpoint tests
        if "api" in str(item.fspath) or "endpoint" in item.name:
            item.add_marker(pytest.mark.api)


# Test Environment Setup/Teardown
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    # Only override if not already set properly
    if os.environ.get("DEBUG") not in ["True", "False"]:
        monkeypatch.setenv("DEBUG", "False")
    
    # Mock external API calls
    monkeypatch.setenv("NPPES_API_BASE_URL", "http://mock-nppes-api")
    
    yield
    
    # Cleanup can be added here if needed 