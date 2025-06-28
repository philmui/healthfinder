"""
HealthFinder - Provider Data Models

This module defines all Pydantic models and enumerations related to the
Provider Finder feature. Centralizing these models here prevents circular
dependencies between the API routers and the data access clients.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

# --- Enums for Standardization ---

class ProviderType(str, Enum):
    """Type of healthcare provider - expanded to cover all NPPES provider types."""
    # Individual Providers (NPI-1)
    PHYSICIAN = "physician"
    NURSE = "nurse"
    NURSE_PRACTITIONER = "nurse_practitioner"
    PHYSICIAN_ASSISTANT = "physician_assistant"
    PHYSICAL_THERAPIST = "physical_therapist"
    OCCUPATIONAL_THERAPIST = "occupational_therapist"
    SPEECH_THERAPIST = "speech_therapist"
    PSYCHIATRIST = "psychiatrist"
    PSYCHOLOGIST = "psychologist"
    DENTIST = "dentist"
    OPTOMETRIST = "optometrist"
    CHIROPRACTOR = "chiropractor"
    PHARMACIST = "pharmacist"
    SOCIAL_WORKER = "social_worker"
    DIETITIAN = "dietitian"
    RESPIRATORY_THERAPIST = "respiratory_therapist"
    RADIOLOGIC_TECHNOLOGIST = "radiologic_technologist"
    CLINICAL_LABORATORY_SCIENTIST = "clinical_laboratory_scientist"
    AUDIOLOGIST = "audiologist"
    MASSAGE_THERAPIST = "massage_therapist"
    ACUPUNCTURIST = "acupuncturist"
    MIDWIFE = "midwife"
    PODIATRIST = "podiatrist"
    OTHER_INDIVIDUAL = "other_individual"
    
    # Organizational Providers (NPI-2)
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    NURSING_HOME = "nursing_home"
    REHABILITATION_CENTER = "rehabilitation_center"
    MENTAL_HEALTH_FACILITY = "mental_health_facility"
    PHARMACY = "pharmacy"
    LABORATORY = "laboratory"
    MEDICAL_EQUIPMENT_SUPPLIER = "medical_equipment_supplier"
    AMBULANCE_SERVICE = "ambulance_service"
    DIALYSIS_CENTER = "dialysis_center"
    IMAGING_CENTER = "imaging_center"
    URGENT_CARE = "urgent_care"
    SURGERY_CENTER = "surgery_center"
    HOME_HEALTH_AGENCY = "home_health_agency"
    HOSPICE = "hospice"
    BLOOD_BANK = "blood_bank"
    ORGAN_PROCUREMENT = "organ_procurement"
    OTHER_ORGANIZATIONAL = "other_organizational"

class Gender(str, Enum):
    """Gender options for provider filtering."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    ANY = "any"

class SortOption(str, Enum):
    """Sort options for provider results."""
    BEST_MATCH = "best_match"
    DISTANCE = "distance"
    RATING = "rating"
    AVAILABILITY = "availability"
    NAME = "name"
    SPECIALTY = "specialty"

class EnumerationType(str, Enum):
    """NPPES enumeration types."""
    INDIVIDUAL = "NPI-1"  # Individual providers
    ORGANIZATIONAL = "NPI-2"  # Organizational providers

class AddressPurpose(str, Enum):
    """NPPES address purpose types."""
    LOCATION = "LOCATION"  # Practice location
    MAILING = "MAILING"   # Mailing address
    PRIMARY = "PRIMARY"   # Primary location
    SECONDARY = "SECONDARY"  # Secondary location

# --- Pydantic Data Models ---

class Location(BaseModel):
    """Location model for geographic coordinates or address."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "US"
    address: Optional[str] = None
    address_2: Optional[str] = None
    locality: Optional[str] = None  # For services like Practo
    address_purpose: Optional[AddressPurpose] = None
    telephone_number: Optional[str] = None
    fax_number: Optional[str] = None

class Insurance(BaseModel):
    """Insurance information model."""
    insurance_provider: str
    insurance_plan: Optional[str] = None

class ProviderSpecialty(BaseModel):
    """Specialty information for a healthcare provider."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    classification: Optional[str] = None
    grouping: Optional[str] = None
    code: Optional[str] = None
    primary: Optional[bool] = False

class ProviderBase(BaseModel):
    """Base model for provider information."""
    id: str
    name: str
    provider_type: ProviderType
    enumeration_type: Optional[EnumerationType] = None
    specialties: List[ProviderSpecialty]
    location: Location
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    languages: List[str] = []
    accepts_new_patients: Optional[bool] = None
    source: str = Field(..., description="Source API of the provider data")

class IndividualProvider(ProviderBase):
    """Model for individual healthcare providers (NPI-1)."""
    npi: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    name_prefix: Optional[str] = None
    name_suffix: Optional[str] = None
    credential: Optional[str] = None
    gender: Optional[str] = None
    fax: Optional[str] = None
    education: List[str] = []
    board_certifications: List[str] = []
    accepted_insurances: List[Insurance] = []
    hospital_affiliations: List[str] = []
    biography: Optional[str] = None
    years_of_experience: Optional[int] = None
    image_url: Optional[str] = None
    consultation_fees: Optional[float] = None

class OrganizationalProvider(ProviderBase):
    """Model for organizational healthcare providers (NPI-2)."""
    npi: Optional[str] = None
    organization_name: Optional[str] = None
    doing_business_as: Optional[str] = None
    facility_type: Optional[str] = None
    fax: Optional[str] = None
    services: List[str] = []
    staff_count: Optional[int] = None
    hours_of_operation: Optional[Dict[str, str]] = None
    accepted_insurances: List[Insurance] = []
    amenities: List[str] = []
    image_url: Optional[str] = None
    license_number: Optional[str] = None
    accreditation: List[str] = []
    authorized_official_first_name: Optional[str] = None
    authorized_official_last_name: Optional[str] = None
    authorized_official_title: Optional[str] = None

# Legacy models for backward compatibility
class DoctorDetails(IndividualProvider):
    """Legacy model for doctor information - now inherits from IndividualProvider."""
    pass

class ClinicDetails(OrganizationalProvider):
    """Legacy model for clinic information - now inherits from OrganizationalProvider."""
    pass

class SearchProviderRequest(BaseModel):
    """Request model for provider search."""
    # Basic search parameters
    query: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    
    # Provider filtering
    provider_type: Optional[ProviderType] = None
    enumeration_type: Optional[EnumerationType] = None
    specialty: Optional[str] = None
    taxonomy_description: Optional[str] = None
    
    # Location filtering
    location: Optional[Location] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    address_purpose: Optional[AddressPurpose] = None
    
    # Additional filters
    insurance: Optional[Insurance] = None
    gender: Optional[Gender] = None
    language: Optional[str] = None
    distance: Optional[int] = Field(None, description="Search radius in miles", ge=1, le=100)
    accepts_new_patients: Optional[bool] = None
    
    # Search options
    sort_by: Optional[SortOption] = SortOption.BEST_MATCH
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=200)  # NPPES max is 200
    skip: Optional[int] = Field(default=0, ge=0, le=1000)  # NPPES max skip is 1000

class SearchProviderResponse(BaseModel):
    """Response model for provider search."""
    total: int
    page: int
    limit: int
    skip: Optional[int] = None
    providers: List[Union[IndividualProvider, OrganizationalProvider, DoctorDetails, ClinicDetails]] = []

class ProviderDetailsResponse(BaseModel):
    """Response model for detailed provider information."""
    provider: Union[IndividualProvider, OrganizationalProvider, DoctorDetails, ClinicDetails]

# NPPES-specific models for advanced searches

class NPPESSearchRequest(BaseModel):
    """Advanced NPPES search request model."""
    version: str = Field(default="2.1")
    number: Optional[str] = Field(None, description="10-digit NPI number")
    enumeration_type: Optional[EnumerationType] = None
    taxonomy_description: Optional[str] = None
    name_purpose: Optional[str] = Field(None, description="AO for Authorized Official, PROVIDER for Provider")
    first_name: Optional[str] = None
    use_first_name_alias: Optional[bool] = Field(True, description="Include similar first names")
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    address_purpose: Optional[AddressPurpose] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = Field(default="US")
    limit: int = Field(10, ge=1, le=200)
    skip: int = Field(0, ge=0, le=1000)
    pretty: Optional[bool] = False

class NPPESAddress(BaseModel):
    """NPPES address model."""
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    address_purpose: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    telephone_number: Optional[str] = None
    fax_number: Optional[str] = None

class NPPESTaxonomy(BaseModel):
    """NPPES taxonomy model."""
    code: Optional[str] = None
    taxonomy_group: Optional[str] = None
    desc: Optional[str] = None
    primary: Optional[bool] = None
    state: Optional[str] = None
    license: Optional[str] = None

class NPPESBasic(BaseModel):
    """NPPES basic information model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    name_prefix: Optional[str] = None
    name_suffix: Optional[str] = None
    credential: Optional[str] = None
    sole_proprietor: Optional[str] = None
    gender: Optional[str] = None
    enumeration_date: Optional[str] = None
    last_updated: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None
    organization_name: Optional[str] = None

class NPPESProvider(BaseModel):
    """Complete NPPES provider model."""
    number: Optional[str] = None
    basic: Optional[NPPESBasic] = None
    addresses: List[NPPESAddress] = []
    taxonomies: List[NPPESTaxonomy] = []
    identifiers: List[Dict[str, Any]] = []
    endpoints: List[Dict[str, Any]] = []
    other_names: List[Dict[str, Any]] = []
    practice_locations: List[NPPESAddress] = []

class NPPESResponse(BaseModel):
    """NPPES API response model."""
    result_count: Optional[int] = None
    results: List[NPPESProvider] = []
