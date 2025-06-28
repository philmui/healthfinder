"""
HealthFinder Provider Models Tests

Comprehensive test suite for provider data models,
following SOLID principles and best testing practices.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from app.models import (
    IndividualProvider,
    OrganizationalProvider,
    Location,
    ProviderSpecialty,
    ProviderType,
    EnumerationType,
    Gender,
    AddressPurpose,
    SortOption,
    SearchProviderRequest,
    NPPESSearchRequest,
    NPPESResponse,
    NPPESProvider,
)


class TestLocationModel:
    """Test class for Location model (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_location_creation_valid(self):
        """Test valid location creation."""
        # Act
        location = Location(
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="US"
        )
        
        # Assert
        assert location.city == "San Francisco"
        assert location.state == "CA"
        assert location.postal_code == "94102"
        assert location.country == "US"
    
    @pytest.mark.unit
    def test_location_minimal_required_fields(self):
        """Test location with minimal required fields."""
        # Act
        location = Location(city="Boston", state="MA")
        
        # Assert
        assert location.city == "Boston"
        assert location.state == "MA"
        assert location.postal_code is None
        assert location.country == "US"  # Default country is now US
    
    @pytest.mark.unit
    def test_location_empty_required_fields(self):
        """Test location validation with empty required fields."""
        # Act - Location has no required fields, so this should succeed
        location = Location()
        
        # Assert - All fields should be None/default
        assert location.city is None
        assert location.state is None
        assert location.country == "US"  # Default country is now US
    
    @pytest.mark.unit
    def test_location_serialization(self):
        """Test location serialization to dict."""
        # Arrange
        location = Location(
            city="Chicago",
            state="IL",
            postal_code="60601",
            country="US"
        )
        
        # Act
        location_dict = location.model_dump()
        
        # Assert
        assert isinstance(location_dict, dict)
        assert location_dict["city"] == "Chicago"
        assert location_dict["state"] == "IL"
        assert location_dict["postal_code"] == "60601"
        assert location_dict["country"] == "US"


class TestProviderSpecialtyModel:
    """Test class for ProviderSpecialty model (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_specialty_creation_valid(self):
        """Test valid specialty creation."""
        # Act
        specialty = ProviderSpecialty(
            name="Family Medicine",
            description="Family Medicine Physician",
            primary=True
        )
        
        # Assert
        assert specialty.name == "Family Medicine"
        assert specialty.description == "Family Medicine Physician"
        assert specialty.primary is True
    
    @pytest.mark.unit
    def test_specialty_default_primary_false(self):
        """Test specialty with default primary value."""
        # Act
        specialty = ProviderSpecialty(
            name="Cardiology",
            description="Cardiovascular Medicine"
        )
        
        # Assert
        assert specialty.primary is False
    
    @pytest.mark.unit
    def test_specialty_required_fields_validation(self):
        """Test specialty validation with missing required fields."""
        # Act & Assert
        with pytest.raises(ValidationError):
            ProviderSpecialty()  # Missing required name field


class TestIndividualProviderModel:
    """Test class for IndividualProvider model (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_individual_provider_creation_valid(self):
        """Test valid individual provider creation."""
        # Arrange
        location = Location(city="New York", state="NY")
        specialty = ProviderSpecialty(name="Internal Medicine", primary=True)
        
        # Act
        provider = IndividualProvider(
            id="nppes-1234567890",
            name="Dr. John Smith",
            provider_type=ProviderType.PHYSICIAN,
            enumeration_type=EnumerationType.INDIVIDUAL,
            specialties=[specialty],
            location=location,
            source="nppes",
            npi="1234567890",
            first_name="John",
            last_name="Smith",
            gender=Gender.MALE
        )
        
        # Assert
        assert provider.id == "nppes-1234567890"
        assert provider.name == "Dr. John Smith"
        assert provider.provider_type == ProviderType.PHYSICIAN
        assert provider.enumeration_type == EnumerationType.INDIVIDUAL
        assert len(provider.specialties) == 1
        assert provider.location.city == "New York"
        assert provider.npi == "1234567890"
        assert provider.first_name == "John"
        assert provider.last_name == "Smith"
        assert provider.gender == Gender.MALE
    
    @pytest.mark.unit
    def test_individual_provider_optional_fields(self):
        """Test individual provider with optional fields."""
        # Arrange
        location = Location(city="Boston", state="MA")
        specialty = ProviderSpecialty(name="Family Medicine", primary=True)
        
        # Act
        provider = IndividualProvider(
            id="nppes-9876543210",
            name="Dr. Jane Doe",
            provider_type=ProviderType.NURSE_PRACTITIONER,
            enumeration_type=EnumerationType.INDIVIDUAL,
            specialties=[specialty],
            location=location,
            source="nppes",
            npi="9876543210",
            first_name="Jane",
            last_name="Doe",
            gender=Gender.FEMALE,
            middle_name="Marie",
            credential="NP",
            phone="555-0123",
            fax="555-0124"
        )
        
        # Assert
        assert provider.middle_name == "Marie"
        assert provider.credential == "NP"
        assert provider.phone == "555-0123"
        assert provider.fax == "555-0124"
    
    @pytest.mark.unit
    def test_individual_provider_validation_errors(self):
        """Test individual provider validation errors."""
        # Act & Assert - Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            IndividualProvider()
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        
        # Check for specific required field errors
        required_fields = ["id", "name", "provider_type", "specialties", "location", "source"]
        error_fields = {error["loc"][0] for error in errors if error["loc"]}
        
        for field in required_fields:
            assert field in error_fields, f"Expected validation error for required field: {field}"
    
    @pytest.mark.unit
    def test_individual_provider_serialization(self):
        """Test individual provider serialization."""
        # Arrange
        location = Location(city="Seattle", state="WA")
        specialty = ProviderSpecialty(name="Psychiatry", primary=True)
        
        provider = IndividualProvider(
            id="nppes-5555555555",
            name="Dr. Alex Johnson",
            provider_type=ProviderType.PSYCHIATRIST,
            enumeration_type=EnumerationType.INDIVIDUAL,
            specialties=[specialty],
            location=location,
            source="nppes",
            npi="5555555555",
            first_name="Alex",
            last_name="Johnson",
            gender=Gender.OTHER
        )
        
        # Act
        provider_dict = provider.model_dump()
        
        # Assert
        assert isinstance(provider_dict, dict)
        assert provider_dict["id"] == "nppes-5555555555"
        assert provider_dict["provider_type"] == ProviderType.PSYCHIATRIST
        assert provider_dict["enumeration_type"] == EnumerationType.INDIVIDUAL
        assert isinstance(provider_dict["specialties"], list)
        assert isinstance(provider_dict["location"], dict)


class TestOrganizationalProviderModel:
    """Test class for OrganizationalProvider model (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_organizational_provider_creation_valid(self):
        """Test valid organizational provider creation."""
        # Arrange
        location = Location(city="Houston", state="TX")
        specialty = ProviderSpecialty(name="General Hospital", primary=True)
        
        # Act
        provider = OrganizationalProvider(
            id="nppes-8888888888",
            name="Houston General Hospital",
            provider_type=ProviderType.HOSPITAL,
            enumeration_type=EnumerationType.ORGANIZATIONAL,
            specialties=[specialty],
            location=location,
            source="nppes",
            npi="8888888888",
            organization_name="Houston General Hospital"
        )
        
        # Assert
        assert provider.id == "nppes-8888888888"
        assert provider.name == "Houston General Hospital"
        assert provider.provider_type == ProviderType.HOSPITAL
        assert provider.enumeration_type == EnumerationType.ORGANIZATIONAL
        assert provider.organization_name == "Houston General Hospital"
    
    @pytest.mark.unit
    def test_organizational_provider_with_optional_fields(self):
        """Test organizational provider with optional fields."""
        # Arrange
        location = Location(city="Phoenix", state="AZ")
        specialty = ProviderSpecialty(name="Retail Pharmacy", primary=True)
        
        # Act
        provider = OrganizationalProvider(
            id="nppes-7777777777",
            name="Phoenix Pharmacy",
            provider_type=ProviderType.PHARMACY,
            enumeration_type=EnumerationType.ORGANIZATIONAL,
            specialties=[specialty],
            location=location,
            source="nppes",
            npi="7777777777",
            organization_name="Phoenix Pharmacy",
            phone="555-PHARMACY",
            fax="555-FAX-PHARM",
            website="https://phoenixpharmacy.com"
        )
        
        # Assert
        assert provider.phone == "555-PHARMACY"
        assert provider.fax == "555-FAX-PHARM"
        assert provider.website == "https://phoenixpharmacy.com"


class TestSearchProviderRequestModel:
    """Test class for SearchProviderRequest model (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_search_request_minimal_valid(self):
        """Test minimal valid search request."""
        # Act
        request = SearchProviderRequest(state="CA")
        
        # Assert
        assert request.state == "CA"
        assert request.limit == 10  # Default value
        assert request.page == 1    # Default value
        assert request.skip == 0    # Default value
    
    @pytest.mark.unit
    def test_search_request_all_fields(self):
        """Test search request with all fields."""
        # Act
        request = SearchProviderRequest(
            query="John Smith",
            first_name="John",
            last_name="Smith",
            organization_name="General Hospital",
            provider_type=ProviderType.PHYSICIAN,
            enumeration_type=EnumerationType.INDIVIDUAL,
            specialty="Family Medicine",
            taxonomy_description="207Q00000X",
            city="Los Angeles",
            state="CA",
            postal_code="90210",
            gender=Gender.MALE,
            sort_by=SortOption.NAME,
            page=2,
            limit=20,
            skip=10
        )
        
        # Assert
        assert request.query == "John Smith"
        assert request.first_name == "John"
        assert request.last_name == "Smith"
        assert request.organization_name == "General Hospital"
        assert request.provider_type == ProviderType.PHYSICIAN
        assert request.enumeration_type == EnumerationType.INDIVIDUAL
        assert request.specialty == "Family Medicine"
        assert request.taxonomy_description == "207Q00000X"
        assert request.city == "Los Angeles"
        assert request.state == "CA"
        assert request.postal_code == "90210"
        assert request.gender == Gender.MALE
        assert request.sort_by == SortOption.NAME
        assert request.page == 2
        assert request.limit == 20
        assert request.skip == 10
    
    @pytest.mark.unit
    def test_search_request_validation_errors(self):
        """Test search request validation errors."""
        # Act & Assert - Invalid limit
        with pytest.raises(ValidationError):
            SearchProviderRequest(state="CA", limit=300)  # Exceeds max
        
        # Act & Assert - Invalid skip
        with pytest.raises(ValidationError):
            SearchProviderRequest(state="CA", skip=2000)  # Exceeds max
        
        # Act & Assert - Invalid page
        with pytest.raises(ValidationError):
            SearchProviderRequest(state="CA", page=0)  # Below min


class TestNPPESModels:
    """Test class for NPPES-specific models (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_nppes_search_request_creation(self):
        """Test NPPES search request creation."""
        # Act
        request = NPPESSearchRequest(
            enumeration_type="NPI-1",
            first_name="Mary",
            state="TX",
            limit=50
        )
        
        # Assert
        assert request.enumeration_type == "NPI-1"
        assert request.first_name == "Mary"
        assert request.state == "TX"
        assert request.limit == 50
    
    @pytest.mark.unit
    def test_nppes_provider_creation(self):
        """Test NPPES provider creation."""
        # Act
        provider = NPPESProvider(
            number="1234567890",
            basic={
                "first_name": "John",
                "last_name": "Doe",
                "enumeration_type": "NPI-1",
                "gender": "M"
            },
            addresses=[{
                "city": "Dallas",
                "state": "TX",
                "address_purpose": "LOCATION"
            }],
            taxonomies=[{
                "desc": "Family Medicine",
                "primary": True
            }]
        )
        
        # Assert
        assert provider.number == "1234567890"
        assert provider.basic.first_name == "John"
        assert provider.basic.last_name == "Doe"
        assert len(provider.addresses) == 1
        assert len(provider.taxonomies) == 1
    
    @pytest.mark.unit
    def test_nppes_response_creation(self):
        """Test NPPES response creation."""
        # Arrange
        provider = NPPESProvider(
            number="1234567890",
            basic={
                "first_name": "Jane",
                "last_name": "Smith",
                "enumeration_type": "NPI-1",
                "gender": "F"
            },
            addresses=[],
            taxonomies=[]
        )
        
        # Act
        response = NPPESResponse(
            result_count=1,
            results=[provider]
        )
        
        # Assert
        assert response.result_count == 1
        assert len(response.results) == 1
        assert response.results[0].number == "1234567890"


class TestModelEnums:
    """Test class for model enums (Single Responsibility)."""
    
    @pytest.mark.unit
    def test_provider_type_enum_values(self):
        """Test ProviderType enum values."""
        # Assert individual provider types
        assert ProviderType.PHYSICIAN == "physician"
        assert ProviderType.NURSE == "nurse"
        assert ProviderType.PHYSICAL_THERAPIST == "physical_therapist"
        assert ProviderType.DENTIST == "dentist"
        
        # Assert organizational provider types
        assert ProviderType.HOSPITAL == "hospital"
        assert ProviderType.CLINIC == "clinic"
        assert ProviderType.PHARMACY == "pharmacy"
    
    @pytest.mark.unit
    def test_enumeration_type_enum_values(self):
        """Test EnumerationType enum values."""
        assert EnumerationType.INDIVIDUAL == "NPI-1"
        assert EnumerationType.ORGANIZATIONAL == "NPI-2"
    
    @pytest.mark.unit
    def test_gender_enum_values(self):
        """Test Gender enum values."""
        assert Gender.MALE == "male"
        assert Gender.FEMALE == "female"
        assert Gender.OTHER == "other"
    
    @pytest.mark.unit
    def test_sort_option_enum_values(self):
        """Test SortOption enum values."""
        assert SortOption.NAME == "name"
        assert SortOption.DISTANCE == "distance"
        assert SortOption.BEST_MATCH == "best_match"
    
    @pytest.mark.unit
    def test_address_purpose_enum_values(self):
        """Test AddressPurpose enum values."""
        assert AddressPurpose.LOCATION == "LOCATION"
        assert AddressPurpose.MAILING == "MAILING"


class TestModelIntegration:
    """Test class for model integration scenarios."""
    
    @pytest.mark.unit
    @pytest.mark.integration
    def test_complete_provider_workflow(self):
        """Test complete provider model workflow."""
        # Arrange - Create complete provider structure
        location = Location(
            city="Miami",
            state="FL",
            postal_code="33101",
            country="US"
        )
        
        primary_specialty = ProviderSpecialty(
            name="Emergency Medicine",
            description="Emergency Medicine Physician",
            primary=True
        )
        
        secondary_specialty = ProviderSpecialty(
            name="Critical Care",
            description="Critical Care Medicine",
            primary=False
        )
        
        provider = IndividualProvider(
            id="nppes-1111111111",
            name="Dr. Emergency Doctor",
            provider_type=ProviderType.PHYSICIAN,
            enumeration_type=EnumerationType.INDIVIDUAL,
            specialties=[primary_specialty, secondary_specialty],
            location=location,
            source="nppes",
            npi="1111111111",
            first_name="Emergency",
            last_name="Doctor",
            gender=Gender.FEMALE,
            middle_name="Response",
            credential="MD",
            phone="555-EMERGENCY",
            fax="555-ER-FAX"
        )
        
        # Act - Serialize and verify
        provider_dict = provider.model_dump()
        
        # Assert - Complete structure validation
        assert provider_dict["id"] == "nppes-1111111111"
        assert provider_dict["name"] == "Dr. Emergency Doctor"
        assert provider_dict["provider_type"] == "physician"
        assert provider_dict["enumeration_type"] == "NPI-1"
        assert len(provider_dict["specialties"]) == 2
        assert provider_dict["specialties"][0]["primary"] is True
        assert provider_dict["specialties"][1]["primary"] is False
        assert provider_dict["location"]["city"] == "Miami"
        assert provider_dict["location"]["state"] == "FL"
        assert provider_dict["first_name"] == "Emergency"
        assert provider_dict["last_name"] == "Doctor"
        assert provider_dict["middle_name"] == "Response"
        assert provider_dict["credential"] == "MD"
    
    @pytest.mark.unit
    def test_model_json_serialization_deserialization(self):
        """Test JSON serialization and deserialization of models."""
        import json
        
        # Arrange
        location = Location(city="Denver", state="CO")
        specialty = ProviderSpecialty(name="Cardiology", primary=True)
        
        original_provider = IndividualProvider(
            id="nppes-2222222222",
            name="Dr. Heart Specialist",
            provider_type=ProviderType.PHYSICIAN,
            enumeration_type=EnumerationType.INDIVIDUAL,
            specialties=[specialty],
            location=location,
            source="nppes",
            npi="2222222222",
            first_name="Heart",
            last_name="Specialist",
            gender=Gender.MALE
        )
        
        # Act - Serialize to JSON and back
        json_str = original_provider.model_dump_json()
        provider_dict = json.loads(json_str)
        reconstructed_provider = IndividualProvider(**provider_dict)
        
        # Assert - Data integrity maintained
        assert reconstructed_provider.id == original_provider.id
        assert reconstructed_provider.name == original_provider.name
        assert reconstructed_provider.provider_type == original_provider.provider_type
        assert reconstructed_provider.npi == original_provider.npi
        assert reconstructed_provider.first_name == original_provider.first_name
        assert reconstructed_provider.last_name == original_provider.last_name 