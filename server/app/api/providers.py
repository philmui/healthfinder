"""
HealthFinder Provider Finder API Module

This module implements the Provider Finder API endpoints for searching doctors and clinics,
integrating with healthcare provider APIs like BetterDoctor and Practo.
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum

# Local imports
from app.core.config import settings

# External provider clients (single-responsibility modules)
from app.clients import betterdoctor as bd_client
from app.clients import practo as practo_client

# Router definition
router = APIRouter()

# Enums for standardization
class ProviderType(str, Enum):
    """Type of healthcare provider."""
    DOCTOR = "doctor"
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    PHARMACY = "pharmacy"

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

# Pydantic models for request and response
class Location(BaseModel):
    """Location model for geographic coordinates or address."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = Field(default="US")
    address: Optional[str] = None
    locality: Optional[str] = None # For services like Practo

class Insurance(BaseModel):
    """Insurance information model."""
    insurance_provider: str
    insurance_plan: Optional[str] = None

class ProviderSpecialty(BaseModel):
    """Specialty information for a healthcare provider."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

class ProviderBase(BaseModel):
    """Base model for provider information."""
    id: str
    name: str
    provider_type: ProviderType
    specialties: List[ProviderSpecialty] = []
    location: Location
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    languages: List[str] = []
    accepts_new_patients: Optional[bool] = None
    source: str = Field(..., description="Source API of the provider data")

class DoctorDetails(ProviderBase):
    """Extended model for doctor-specific information."""
    npi: Optional[str] = None
    gender: Optional[str] = None # Keep as string to accommodate different API values
    education: List[str] = []
    board_certifications: List[str] = []
    accepted_insurances: List[Insurance] = []
    hospital_affiliations: List[str] = []
    biography: Optional[str] = None
    years_of_experience: Optional[int] = None
    image_url: Optional[str] = None
    consultation_fees: Optional[float] = None

class ClinicDetails(ProviderBase):
    """Extended model for clinic-specific information."""
    facility_type: Optional[str] = None
    services: List[str] = []
    doctors_count: Optional[int] = None
    hours_of_operation: Optional[Dict[str, str]] = None
    accepted_insurances: List[Insurance] = []
    amenities: List[str] = []
    image_url: Optional[str] = None

class SearchProviderRequest(BaseModel):
    """Request model for provider search."""
    query: Optional[str] = None
    provider_type: Optional[ProviderType] = None
    specialty: Optional[str] = None
    location: Optional[Location] = None
    insurance: Optional[Insurance] = None
    gender: Optional[Gender] = None
    language: Optional[str] = None
    distance: Optional[int] = Field(None, description="Search radius in miles", ge=1, le=100)
    accepts_new_patients: Optional[bool] = None
    sort_by: Optional[SortOption] = SortOption.BEST_MATCH
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)

class SearchProviderResponse(BaseModel):
    """Response model for provider search."""
    total: int
    page: int
    limit: int
    providers: List[Union[DoctorDetails, ClinicDetails]] = []

class ProviderDetailsResponse(BaseModel):
    """Response model for detailed provider information."""
    provider: Union[DoctorDetails, ClinicDetails]

# API endpoints
@router.get("/search", response_model=SearchProviderResponse)
async def search_providers(
    query: Optional[str] = None,
    provider_type: Optional[ProviderType] = None,
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    insurance_provider: Optional[str] = None,
    gender: Optional[Gender] = None,
    language: Optional[str] = None,
    distance: Optional[int] = Query(None, ge=1, le=100),
    accepts_new_patients: Optional[bool] = None,
    sort_by: SortOption = SortOption.BEST_MATCH,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Search for healthcare providers (doctors, clinics, hospitals) based on various criteria.
    
    This endpoint aggregates results from multiple provider APIs (BetterDoctor, Practo)
    and returns a unified response.
    """
    logger.info(
        "Provider search request", 
        extra={
            "query": query,
            "provider_type": provider_type,
            "location": {
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "coordinates": {"lat": latitude, "lng": longitude} if latitude and longitude else None
            },
            "page": page,
            "limit": limit
        }
    )
    
    try:
        location = None
        if any([city, state, postal_code, latitude, longitude]):
            location = Location(
                city=city,
                state=state,
                postal_code=postal_code,
                latitude=latitude,
                longitude=longitude
            )
        
        insurance = Insurance(insurance_provider=insurance_provider) if insurance_provider else None
        
        search_request = SearchProviderRequest(
            query=query, provider_type=provider_type, specialty=specialty,
            location=location, insurance=insurance, gender=gender, language=language,
            distance=distance, accepts_new_patients=accepts_new_patients,
            sort_by=sort_by, page=page, limit=limit
        )
        
        providers = []
        total = 0
        
        if (latitude and longitude) or (location and location.country == "US"):
            better_doctor_results = await search_better_doctor(search_request)
            providers.extend(better_doctor_results.get("providers", []))
            total += better_doctor_results.get("total", 0)
        
        if not location or location.country != "US":
            practo_results = await search_practo(search_request)
            providers.extend(practo_results.get("providers", []))
            total += practo_results.get("total", 0)
            
        unique_providers = {p['id']: p for p in providers}.values()
        
        # Simplified sorting for MVP
        sorted_providers = list(unique_providers)
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_providers = sorted_providers[start_idx:end_idx]
        
        return SearchProviderResponse(
            total=total,
            page=page,
            limit=limit,
            providers=paginated_providers
        )
    
    except Exception as e:
        logger.error(f"Error searching providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching providers: {str(e)}"
        )

@router.get("/{provider_id}", response_model=ProviderDetailsResponse)
async def get_provider_details(
    provider_id: str,
    source: str = Query(..., description="Source API of the provider data (e.g., 'betterdoctor', 'practo')")
):
    """
    Get detailed information about a specific healthcare provider.
    """
    logger.info(f"Provider details request for ID: {provider_id} from source: {source}")
    
    try:
        provider_details = None
        if source == "betterdoctor":
            provider_details = await get_better_doctor_provider(provider_id)
        elif source == "practo":
            provider_details = await get_practo_provider(provider_id)
        
        if not provider_details:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with ID {provider_id} from source {source} not found")
        
        return ProviderDetailsResponse(provider=provider_details)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving provider details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving provider details: {str(e)}")

# Integration with external provider APIs
async def search_better_doctor(search_request: SearchProviderRequest) -> Dict[str, Any]:
    """Search for providers using the BetterDoctor API."""
    if not settings.BETTERDOCTOR_API_KEY:
        logger.warning("BETTERDOCTOR_API_KEY not set. Skipping BetterDoctor search.")
        return {"providers": [], "total": 0}
        
    params = {"user_key": settings.BETTERDOCTOR_API_KEY, "limit": search_request.limit, "skip": (search_request.page - 1) * search_request.limit}
    if search_request.query: params["name"] = search_request.query
    if search_request.specialty: params["specialty_uid"] = search_request.specialty
    if search_request.location:
        if search_request.location.latitude and search_request.location.longitude:
            params["location"] = f"{search_request.location.latitude},{search_request.location.longitude},{search_request.distance or 10}"
    if search_request.gender and search_request.gender != Gender.ANY: params["gender"] = search_request.gender
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.betterdoctor.com/2016-03-01/doctors", params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            providers = [_transform_better_doctor(doc) for doc in data.get("data", [])]
            return {"providers": providers, "total": data.get("meta", {}).get("total", 0)}
    except httpx.HTTPStatusError as e:
        logger.error(f"BetterDoctor API error: {e.response.status_code} - {e.response.text}")
        return {"providers": [], "total": 0}
    except Exception as e:
        logger.error(f"Error searching BetterDoctor: {str(e)}", exc_info=True)
        return {"providers": [], "total": 0}

async def search_practo(search_request: SearchProviderRequest) -> Dict[str, Any]:
    """Search for providers using the Practo API."""
    if not settings.PRACTO_API_KEY or not settings.PRACTO_CLIENT_ID:
        logger.warning("PRACTO_API_KEY or PRACTO_CLIENT_ID not set. Skipping Practo search.")
        return {"providers": [], "total": 0}

    params = {"limit": search_request.limit, "offset": (search_request.page - 1) * search_request.limit}
    if search_request.location and search_request.location.city:
        params["city"] = search_request.location.city
    else:
        params["city"] = "bangalore" # Practo requires a city
    if search_request.query: params["q"] = search_request.query
    if search_request.specialty: params["speciality"] = search_request.specialty
    
    headers = {"X-API-KEY": settings.PRACTO_API_KEY, "X-CLIENT-ID": settings.PRACTO_CLIENT_ID}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.practo.com/search", params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            providers = [_transform_practo_doctor(doc) for doc in data.get("doctors", [])]
            return {"providers": providers, "total": data.get("total", 0)}
    except httpx.HTTPStatusError as e:
        logger.error(f"Practo API error: {e.response.status_code} - {e.response.text}")
        return {"providers": [], "total": 0}
    except Exception as e:
        logger.error(f"Error searching Practo: {str(e)}", exc_info=True)
        return {"providers": [], "total": 0}

async def get_better_doctor_provider(provider_id: str) -> Optional[DoctorDetails]:
    """Get detailed information about a provider from BetterDoctor API."""
    if not settings.BETTERDOCTOR_API_KEY: return None
    params = {"user_key": settings.BETTERDOCTOR_API_KEY}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.betterdoctor.com/2016-03-01/doctors/{provider_id}", params=params, timeout=10.0)
            if response.status_code == 404: return None
            response.raise_for_status()
            return _transform_better_doctor(response.json().get("data", {}))
    except Exception:
        return None

async def get_practo_provider(provider_id: str) -> Optional[DoctorDetails]:
    """Get detailed information about a provider from Practo API."""
    if not settings.PRACTO_API_KEY or not settings.PRACTO_CLIENT_ID: return None
    headers = {"X-API-KEY": settings.PRACTO_API_KEY, "X-CLIENT-ID": settings.PRACTO_CLIENT_ID}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.practo.com/doctors/{provider_id}?with_relations=true", headers=headers, timeout=10.0)
            if response.status_code == 404: return None
            response.raise_for_status()
            return _transform_practo_doctor(response.json())
    except Exception:
        return None

def _transform_better_doctor(doctor_data: Dict) -> DoctorDetails:
    """Transforms a BetterDoctor API doctor object into our DoctorDetails model."""
    profile = doctor_data.get("profile", {})
    practice = doctor_data.get("practices", [{}])[0]
    
    return DoctorDetails(
        id=f"betterdoctor-{doctor_data.get('uid')}",
        name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
        provider_type=ProviderType.DOCTOR,
        specialties=[ProviderSpecialty(name=s.get('name'), description=s.get('description'), category=s.get('category')) for s in doctor_data.get("specialties", [])],
        location=Location(
            latitude=practice.get("lat"), longitude=practice.get("lon"), city=practice.get("city"),
            state=practice.get("state"), postal_code=practice.get("zip"), country="US",
            address=practice.get("street")
        ),
        phone=next((p.get("number") for p in practice.get("phones", []) if p.get("type") == "landline"), None),
        website=practice.get("website"),
        accepts_new_patients=practice.get("accepts_new_patients"),
        source="betterdoctor",
        npi=doctor_data.get("npi"),
        gender=profile.get("gender"),
        biography=profile.get("bio"),
        image_url=profile.get("image_url")
    )

def _transform_practo_doctor(doctor_data: Dict) -> DoctorDetails:
    """Transforms a Practo API doctor object into our DoctorDetails model."""
    practice = doctor_data.get("relations", [{}])[0].get("practice", {}) if doctor_data.get("relations") else {}
    locality = practice.get("locality", {})
    
    return DoctorDetails(
        id=f"practo-{doctor_data.get('id') or doctor_data.get('doctor_id')}",
        name=doctor_data.get("name") or doctor_data.get("doctor_name"),
        provider_type=ProviderType.DOCTOR,
        specialties=[ProviderSpecialty(name=s.get('subspecialization', {}).get('subspecialization', s.get('specialty', {}).get('speciality')), category=s.get('specialty', {}).get('speciality')) for s in doctor_data.get("specializations", doctor_data.get("specialties", []))],
        location=Location(
            latitude=practice.get("latitude") or doctor_data.get("latitude"),
            longitude=practice.get("longitude") or doctor_data.get("longitude"),
            city=locality.get("city", {}).get("name") or doctor_data.get("city"),
            address=practice.get("street_address") or doctor_data.get("locality"),
            country=locality.get("city", {}).get("state", {}).get("country", {}).get("name", "India")
        ),
        review_count=doctor_data.get("recommendation", {}).get("recommendation") or doctor_data.get("recommendation"),
        source="practo",
        gender=doctor_data.get("gender"),
        education=[q.get('qualification', {}).get('name') for q in doctor_data.get("qualifications", [])],
        biography=doctor_data.get("summary"),
        years_of_experience=doctor_data.get("experience_years"),
        image_url=next((p.get('photo_url') or p.get('url') for p in doctor_data.get("photos", doctor_data.get("doctor_photos", [])) if p.get('photo_default') or p.get('is_default')), None),
        consultation_fees=doctor_data.get("consultation_fees")
    )
