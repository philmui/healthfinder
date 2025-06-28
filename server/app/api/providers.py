"""
HealthFinder Provider Finder API Module

This module implements the Provider Finder API endpoints for searching all types of healthcare
providers including doctors, nurses, therapists, clinics, hospitals, and other medical facilities,
integrating with healthcare provider APIs like NPPES NPI Registry and Practo.
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, status, Depends
from loguru import logger

# Local imports
from app.core.config import settings

# External provider clients (single-responsibility modules)
from app.clients import nppes as nppes_client
from app.clients import practo as practo_client

# Shared data models
from app.models import (
    ProviderType,
    EnumerationType,
    AddressPurpose,
    Gender,
    SortOption,
    Location,
    Insurance,
    IndividualProvider,
    OrganizationalProvider,
    DoctorDetails,
    ClinicDetails,
    SearchProviderRequest,
    SearchProviderResponse,
    ProviderDetailsResponse,
    NPPESSearchRequest,
    NPPESResponse,
)

# Router definition
router = APIRouter()


# Main provider search endpoints
@router.get("/search", response_model=SearchProviderResponse)
async def search_providers(
    # Basic search parameters
    query: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    organization_name: Optional[str] = None,
    
    # Provider filtering
    provider_type: Optional[ProviderType] = None,
    enumeration_type: Optional[EnumerationType] = None,
    specialty: Optional[str] = None,
    taxonomy_description: Optional[str] = None,
    
    # Location filtering
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address_purpose: Optional[AddressPurpose] = None,
    
    # Additional filters
    insurance_provider: Optional[str] = None,
    gender: Optional[Gender] = None,
    language: Optional[str] = None,
    distance: Optional[int] = Query(None, ge=1, le=100),
    accepts_new_patients: Optional[bool] = None,
    
    # Search options
    sort_by: SortOption = SortOption.BEST_MATCH,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    skip: Optional[int] = Query(None, ge=0, le=1000),
):
    """
    Search for all types of healthcare providers based on various criteria.
    
    This endpoint supports searching for:
    - Individual providers: physicians, nurses, therapists, dentists, etc.
    - Organizational providers: hospitals, clinics, pharmacies, labs, etc.
    
    The search aggregates results from NPPES (US providers) and Practo (international).
    """
    logger.info(
        "Provider search request", 
        extra={
            "query": query,
            "provider_type": provider_type,
            "enumeration_type": enumeration_type,
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
                longitude=longitude,
                address_purpose=address_purpose
            )
        
        insurance = Insurance(insurance_provider=insurance_provider) if insurance_provider else None
        
        search_request = SearchProviderRequest(
            query=query,
            first_name=first_name,
            last_name=last_name,
            organization_name=organization_name,
            provider_type=provider_type,
            enumeration_type=enumeration_type,
            specialty=specialty,
            taxonomy_description=taxonomy_description,
            location=location,
            city=city,
            state=state,
            postal_code=postal_code,
            address_purpose=address_purpose,
            insurance=insurance,
            gender=gender,
            language=language,
            distance=distance,
            accepts_new_patients=accepts_new_patients,
            sort_by=sort_by,
            page=page,
            limit=limit,
            skip=skip
        )
        
        providers = []
        total = 0
        
        # Always search NPPES for US providers (NPPES covers all US healthcare providers)
        if not location or location.country == "US" or (latitude and longitude):
            nppes_results = await nppes_client.search_doctors(search_request)
            providers.extend(nppes_results.get("providers", []))
            total += nppes_results.get("total", 0)
        
        # Search Practo for international providers
        # if location and location.country != "US":
        #     practo_results = await practo_client.search_doctors(search_request)
        #     providers.extend(practo_results.get("providers", []))
        #     total += practo_results.get("total", 0)
            
        unique_providers = {p.id: p for p in providers}.values()
        
        # Simplified sorting for MVP
        sorted_providers = list(unique_providers)
        
        start_idx = (page - 1) * limit if not skip else skip
        end_idx = start_idx + limit
        paginated_providers = sorted_providers[start_idx:end_idx]
        
        return SearchProviderResponse(
            total=total,
            page=page,
            limit=limit,
            skip=skip,
            providers=paginated_providers
        )
    
    except Exception as e:
        logger.error(f"Error searching providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching providers: {str(e)}"
        )


@router.get("/search/individual", response_model=SearchProviderResponse)
async def search_individual_providers(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    specialty: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    gender: Optional[Gender] = None,
    limit: int = Query(10, ge=1, le=200)
):
    """
    Search specifically for individual healthcare providers (NPI-1).
    
    Includes: physicians, nurses, therapists, dentists, pharmacists, etc.
    """
    try:
        results = await nppes_client.search_individual_providers(
            first_name=first_name,
            last_name=last_name,
            state=state,
            limit=limit
        )
        
        return SearchProviderResponse(
            total=results.get("total", 0),
            page=1,
            limit=limit,
            providers=results.get("providers", [])
        )
    
    except Exception as e:
        logger.error(f"Error searching individual providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching individual providers: {str(e)}"
        )


@router.get("/search/organizational", response_model=SearchProviderResponse)
async def search_organizational_providers(
    organization_name: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    facility_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=200)
):
    """
    Search specifically for organizational healthcare providers (NPI-2).
    
    Includes: hospitals, clinics, nursing homes, pharmacies, labs, etc.
    """
    try:
        results = await nppes_client.search_organizational_providers(
            organization_name=organization_name,
            city=city,
            state=state,
            limit=limit
        )
        
        return SearchProviderResponse(
            total=results.get("total", 0),
            page=1,
            limit=limit,
            providers=results.get("providers", [])
        )
    
    except Exception as e:
        logger.error(f"Error searching organizational providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching organizational providers: {str(e)}"
        )


@router.get("/search/by-taxonomy", response_model=SearchProviderResponse)
async def search_by_taxonomy(
    taxonomy_code: str = Query(..., description="NUCC taxonomy code"),
    state: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(10, ge=1, le=200)
):
    """
    Search providers by specific taxonomy code.
    
    Use NUCC taxonomy codes to find providers with specific specialties.
    Examples: '207Q00000X' for Family Medicine, '363L00000X' for Nurse Practitioner
    """
    try:
        results = await nppes_client.search_by_taxonomy(
            taxonomy_code=taxonomy_code,
            limit=limit
        )
        
        return SearchProviderResponse(
            total=results.get("total", 0),
            page=1,
            limit=limit,
            providers=results.get("providers", [])
        )
    
    except Exception as e:
        logger.error(f"Error searching by taxonomy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching by taxonomy: {str(e)}"
        )


@router.get("/types", response_model=Dict[str, List[str]])
def get_provider_types():
    """
    Get all available provider types categorized by individual and organizational.
    """
    individual_types = [
        ProviderType.PHYSICIAN.value,
        ProviderType.NURSE.value,
        ProviderType.NURSE_PRACTITIONER.value,
        ProviderType.PHYSICIAN_ASSISTANT.value,
        ProviderType.PHYSICAL_THERAPIST.value,
        ProviderType.OCCUPATIONAL_THERAPIST.value,
        ProviderType.SPEECH_THERAPIST.value,
        ProviderType.PSYCHIATRIST.value,
        ProviderType.PSYCHOLOGIST.value,
        ProviderType.DENTIST.value,
        ProviderType.OPTOMETRIST.value,
        ProviderType.CHIROPRACTOR.value,
        ProviderType.PHARMACIST.value,
        ProviderType.SOCIAL_WORKER.value,
        ProviderType.DIETITIAN.value,
        ProviderType.RESPIRATORY_THERAPIST.value,
        ProviderType.RADIOLOGIC_TECHNOLOGIST.value,
        ProviderType.CLINICAL_LABORATORY_SCIENTIST.value,
        ProviderType.AUDIOLOGIST.value,
        ProviderType.MASSAGE_THERAPIST.value,
        ProviderType.ACUPUNCTURIST.value,
        ProviderType.MIDWIFE.value,
        ProviderType.PODIATRIST.value,
        ProviderType.OTHER_INDIVIDUAL.value,
    ]
    
    organizational_types = [
        ProviderType.HOSPITAL.value,
        ProviderType.CLINIC.value,
        ProviderType.NURSING_HOME.value,
        ProviderType.REHABILITATION_CENTER.value,
        ProviderType.MENTAL_HEALTH_FACILITY.value,
        ProviderType.PHARMACY.value,
        ProviderType.LABORATORY.value,
        ProviderType.MEDICAL_EQUIPMENT_SUPPLIER.value,
        ProviderType.AMBULANCE_SERVICE.value,
        ProviderType.DIALYSIS_CENTER.value,
        ProviderType.IMAGING_CENTER.value,
        ProviderType.URGENT_CARE.value,
        ProviderType.SURGERY_CENTER.value,
        ProviderType.HOME_HEALTH_AGENCY.value,
        ProviderType.HOSPICE.value,
        ProviderType.BLOOD_BANK.value,
        ProviderType.ORGAN_PROCUREMENT.value,
        ProviderType.OTHER_ORGANIZATIONAL.value,
    ]
    
    return {
        "individual_providers": individual_types,
        "organizational_providers": organizational_types
    }


# Advanced NPPES endpoints

@router.post("/nppes/search", response_model=NPPESResponse)
async def nppes_advanced_search(request: NPPESSearchRequest):
    """
    Advanced NPPES search with full API parameter support.
    
    This endpoint provides direct access to all NPPES API parameters for advanced searches.
    """
    try:
        response = await nppes_client.search_providers_advanced(request)
        return response
    
    except Exception as e:
        logger.error(f"Error in NPPES advanced search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in NPPES advanced search: {str(e)}"
        )


@router.get("/nppes/by-npi/{npi}", response_model=ProviderDetailsResponse)
async def get_provider_by_npi(npi: str):
    """
    Get provider details directly by NPI number.
    
    Args:
        npi: 10-digit National Provider Identifier
    """
    if not npi.isdigit() or len(npi) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NPI must be a 10-digit number"
        )
    
    try:
        provider = await nppes_client.get_doctor_details(npi)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider with NPI {npi} not found"
            )
        
        return ProviderDetailsResponse(provider=provider)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving provider by NPI: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving provider by NPI: {str(e)}"
        )


@router.get("/{provider_id}", response_model=ProviderDetailsResponse)
async def get_provider_details(
    provider_id: str,
    source: str = Query(..., description="Source API of the provider data (e.g., 'nppes', 'practo')")
):
    """
    Get detailed information about a specific healthcare provider.
    """
    logger.info(f"Provider details request for ID: {provider_id} from source: {source}")
    
    try:
        provider_details = None
        if source == "nppes":
            provider_details = await nppes_client.get_doctor_details(provider_id)
        elif source == "practo":
            provider_details = await practo_client.get_doctor_details(provider_id)
        
        if not provider_details:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with ID {provider_id} from source {source} not found")
        
        return ProviderDetailsResponse(provider=provider_details)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving provider details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving provider details: {str(e)}")


# Statistics and analytics endpoints

@router.get("/stats/by-state")
async def get_provider_stats_by_state(
    state: str = Query(..., description="State abbreviation (e.g., 'CA', 'NY')"),
    provider_type: Optional[ProviderType] = None,
    limit: int = Query(100, ge=1, le=200)
):
    """
    Get provider statistics for a specific state.
    """
    try:
        request = SearchProviderRequest(
            state=state,
            provider_type=provider_type,
            limit=limit
        )
        
        results = await nppes_client.search_doctors(request)
        providers = results.get("providers", [])
        
        # Aggregate statistics
        stats = {
            "total_providers": len(providers),
            "by_type": {},
            "by_specialty": {},
            "by_city": {}
        }
        
        for provider in providers:
            # Count by provider type
            provider_type_str = provider.provider_type.value
            stats["by_type"][provider_type_str] = stats["by_type"].get(provider_type_str, 0) + 1
            
            # Count by specialty
            for specialty in provider.specialties:
                if specialty.name:
                    stats["by_specialty"][specialty.name] = stats["by_specialty"].get(specialty.name, 0) + 1
            
            # Count by city
            if provider.location.city:
                city = provider.location.city
                stats["by_city"][city] = stats["by_city"].get(city, 0) + 1
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting provider stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting provider stats: {str(e)}"
        )


# Legacy helper wrappers (thin proxies to client functions)
# --------------------------------------------------------------------------- #

async def search_nppes(request: SearchProviderRequest) -> Dict[str, Any]:
    """Proxy to NPPES search."""
    return await nppes_client.search_doctors(request)


async def search_practo(request: SearchProviderRequest) -> Dict[str, Any]:
    """Proxy to Practo search."""
    return await practo_client.search_doctors(request)


async def get_nppes_provider(provider_id: str) -> Optional[Union[IndividualProvider, OrganizationalProvider]]:
    """Proxy to NPPES provider details."""
    return await nppes_client.get_doctor_details(provider_id)


async def get_practo_provider(provider_id: str) -> Optional[DoctorDetails]:
    """Proxy to Practo provider details."""
    return await practo_client.get_doctor_details(provider_id)
