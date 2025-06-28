"""
HealthFinder NPPES API Module

This module provides comprehensive endpoints for the NPPES (National Plan & Provider 
Enumeration System) NPI Registry API, exposing all available search capabilities
and provider information.

NPPES API Documentation: https://npiregistry.cms.hhs.gov/api-page
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger

from app.clients import nppes as nppes_client
from app.models import (
    ProviderType,
    EnumerationType,
    AddressPurpose,
    Gender,
    NPPESSearchRequest,
    NPPESResponse,
    NPPESProvider,
    SearchProviderResponse,
    ProviderDetailsResponse,
    SearchProviderRequest,
)

# Router definition
router = APIRouter(prefix="/nppes", tags=["NPPES NPI Registry"])


@router.get("/search/basic", response_model=SearchProviderResponse)
async def search_basic(
    query: Optional[str] = Query(None, description="General search query (parsed into first/last name)"),
    city: Optional[str] = Query(None, description="City name"),
    state: Optional[str] = Query(None, description="State abbreviation (e.g., 'CA', 'NY')"),
    postal_code: Optional[str] = Query(None, description="ZIP code (5 or 9 digits)"),
    limit: int = Query(10, ge=1, le=200, description="Number of results (max 200)"),
    skip: int = Query(0, ge=0, le=1000, description="Number of results to skip (max 1000)")
):
    """
    Basic NPPES provider search with minimal parameters.
    
    At least one search criterion is required (query, city, state, or postal_code).
    """
    if not any([query, city, state, postal_code]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search criterion is required (query, city, state, or postal_code)"
        )
    
    try:
        request = SearchProviderRequest(
            query=query,
            city=city,
            state=state,
            postal_code=postal_code,
            limit=limit,
            skip=skip
        )
        
        results = await nppes_client.search_doctors(request)
        
        return SearchProviderResponse(
            total=results.get("total", 0),
            page=1,
            limit=limit,
            skip=skip,
            providers=results.get("providers", [])
        )
    
    except Exception as e:
        logger.error(f"Error in basic NPPES search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in basic NPPES search: {str(e)}"
        )


@router.get("/search/individual", response_model=SearchProviderResponse)
async def search_individual(
    first_name: Optional[str] = Query(None, description="First name (supports wildcards like 'jo*')"),
    last_name: Optional[str] = Query(None, description="Last name (supports wildcards)"),
    use_first_name_alias: bool = Query(True, description="Include similar first names (Robert -> Bob, Rob, etc.)"),
    gender: Optional[str] = Query(None, description="Gender (M, F)"),
    state: Optional[str] = Query(None, description="State abbreviation"),
    city: Optional[str] = Query(None, description="City name"),
    postal_code: Optional[str] = Query(None, description="ZIP code"),
    taxonomy_description: Optional[str] = Query(None, description="Provider specialty/taxonomy"),
    limit: int = Query(10, ge=1, le=200),
    skip: int = Query(0, ge=0, le=1000)
):
    """
    Search for individual healthcare providers (NPI-1 enumeration type).
    
    Includes physicians, nurses, therapists, and other individual practitioners.
    """
    if not any([first_name, last_name, state, city, postal_code, taxonomy_description]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search criterion is required"
        )
    
    try:
        request = NPPESSearchRequest(
            enumeration_type=EnumerationType.INDIVIDUAL,
            first_name=first_name,
            last_name=last_name,
            use_first_name_alias=use_first_name_alias,
            state=state,
            city=city,
            postal_code=postal_code,
            taxonomy_description=taxonomy_description,
            limit=limit,
            skip=skip
        )
        
        response = await nppes_client.search_providers_advanced(request)
        
        # Convert NPPES response to our standard format
        providers = []
        for nppes_provider in response.results:
            try:
                provider = nppes_client._transform_nppes_provider(nppes_provider.model_dump())
                providers.append(provider)
            except Exception as e:
                logger.warning(f"Failed to transform provider: {e}")
                continue
        
        return SearchProviderResponse(
            total=response.result_count or len(providers),
            page=1,
            limit=limit,
            skip=skip,
            providers=providers
        )
    
    except Exception as e:
        logger.error(f"Error searching individual providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching individual providers: {str(e)}"
        )


@router.get("/search/organizational", response_model=SearchProviderResponse)
async def search_organizational(
    organization_name: Optional[str] = Query(None, description="Organization name (supports wildcards)"),
    state: Optional[str] = Query(None, description="State abbreviation"),
    city: Optional[str] = Query(None, description="City name"),
    postal_code: Optional[str] = Query(None, description="ZIP code"),
    taxonomy_description: Optional[str] = Query(None, description="Organization type/specialty"),
    limit: int = Query(10, ge=1, le=200),
    skip: int = Query(0, ge=0, le=1000)
):
    """
    Search for organizational healthcare providers (NPI-2 enumeration type).
    
    Includes hospitals, clinics, pharmacies, laboratories, and other healthcare organizations.
    """
    if not any([organization_name, state, city, postal_code, taxonomy_description]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search criterion is required"
        )
    
    try:
        request = NPPESSearchRequest(
            enumeration_type=EnumerationType.ORGANIZATIONAL,
            organization_name=organization_name,
            state=state,
            city=city,
            postal_code=postal_code,
            taxonomy_description=taxonomy_description,
            limit=limit,
            skip=skip
        )
        
        response = await nppes_client.search_providers_advanced(request)
        
        # Convert NPPES response to our standard format
        providers = []
        for nppes_provider in response.results:
            try:
                provider = nppes_client._transform_nppes_provider(nppes_provider.model_dump())
                providers.append(provider)
            except Exception as e:
                logger.warning(f"Failed to transform provider: {e}")
                continue
        
        return SearchProviderResponse(
            total=response.result_count or len(providers),
            page=1,
            limit=limit,
            skip=skip,
            providers=providers
        )
    
    except Exception as e:
        logger.error(f"Error searching organizational providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching organizational providers: {str(e)}"
        )


@router.get("/search/by-npi/{npi}", response_model=ProviderDetailsResponse)
async def search_by_npi(npi: str):
    """
    Get provider information by exact NPI number.
    
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


@router.get("/search/by-taxonomy", response_model=SearchProviderResponse)
async def search_by_taxonomy(
    taxonomy_description: str = Query(..., description="Taxonomy description or code"),
    state: Optional[str] = Query(None, description="State abbreviation"),
    city: Optional[str] = Query(None, description="City name"),
    enumeration_type: Optional[EnumerationType] = Query(None, description="Provider type filter"),
    limit: int = Query(10, ge=1, le=200),
    skip: int = Query(0, ge=0, le=1000)
):
    """
    Search providers by taxonomy description or code.
    
    Examples:
    - "Family Medicine"
    - "Nurse Practitioner"
    - "Hospital"
    - "207Q00000X" (Family Medicine taxonomy code)
    """
    try:
        request = NPPESSearchRequest(
            taxonomy_description=taxonomy_description,
            enumeration_type=enumeration_type,
            state=state,
            city=city,
            limit=limit,
            skip=skip
        )
        
        response = await nppes_client.search_providers_advanced(request)
        
        # Convert NPPES response to our standard format
        providers = []
        for nppes_provider in response.results:
            try:
                provider = nppes_client._transform_nppes_provider(nppes_provider.model_dump())
                providers.append(provider)
            except Exception as e:
                logger.warning(f"Failed to transform provider: {e}")
                continue
        
        return SearchProviderResponse(
            total=response.result_count or len(providers),
            page=1,
            limit=limit,
            skip=skip,
            providers=providers
        )
    
    except Exception as e:
        logger.error(f"Error searching by taxonomy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching by taxonomy: {str(e)}"
        )


@router.get("/search/by-location", response_model=SearchProviderResponse)
async def search_by_location(
    city: Optional[str] = Query(None, description="City name"),
    state: Optional[str] = Query(None, description="State abbreviation"),
    postal_code: Optional[str] = Query(None, description="ZIP code (supports wildcards like '21*')"),
    country_code: str = Query("US", description="Country code"),
    address_purpose: Optional[AddressPurpose] = Query(None, description="Address type filter"),
    provider_type: Optional[EnumerationType] = Query(None, description="Individual or organizational"),
    limit: int = Query(10, ge=1, le=200),
    skip: int = Query(0, ge=0, le=1000)
):
    """
    Search providers by geographic location.
    
    Address purpose options:
    - LOCATION: Practice location address
    - MAILING: Mailing address
    - PRIMARY: Primary location
    - SECONDARY: Secondary location
    """
    if not any([city, state, postal_code]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one location criterion is required (city, state, or postal_code)"
        )
    
    try:
        request = NPPESSearchRequest(
            city=city,
            state=state,
            postal_code=postal_code,
            country_code=country_code,
            address_purpose=address_purpose,
            enumeration_type=provider_type,
            limit=limit,
            skip=skip
        )
        
        response = await nppes_client.search_providers_advanced(request)
        
        # Convert NPPES response to our standard format
        providers = []
        for nppes_provider in response.results:
            try:
                provider = nppes_client._transform_nppes_provider(nppes_provider.model_dump())
                providers.append(provider)
            except Exception as e:
                logger.warning(f"Failed to transform provider: {e}")
                continue
        
        return SearchProviderResponse(
            total=response.result_count or len(providers),
            page=1,
            limit=limit,
            skip=skip,
            providers=providers
        )
    
    except Exception as e:
        logger.error(f"Error searching by location: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching by location: {str(e)}"
        )


@router.post("/search/advanced", response_model=NPPESResponse)
async def search_advanced(request: NPPESSearchRequest):
    """
    Advanced NPPES search with full API parameter support.
    
    This endpoint provides direct access to all NPPES API parameters:
    - version: API version (default "2.1")
    - number: Specific NPI number
    - enumeration_type: NPI-1 (individual) or NPI-2 (organizational)
    - taxonomy_description: Provider specialty
    - name_purpose: AO (Authorized Official) or PROVIDER
    - first_name: Individual provider first name
    - use_first_name_alias: Include similar names
    - last_name: Individual provider last name
    - organization_name: Organization name
    - address_purpose: Address type filter
    - city, state, postal_code: Location filters
    - country_code: Country filter
    - limit: Result limit (1-200)
    - skip: Results to skip (0-1000)
    """
    try:
        response = await nppes_client.search_providers_advanced(request)
        return response
    
    except Exception as e:
        logger.error(f"Error in advanced NPPES search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in advanced NPPES search: {str(e)}"
        )


@router.get("/validate/npi/{npi}")
async def validate_npi(npi: str):
    """
    Validate NPI number format and check if it exists in NPPES.
    
    Args:
        npi: National Provider Identifier to validate
    """
    # Basic format validation
    if not npi.isdigit():
        return {
            "valid": False,
            "error": "NPI must contain only digits",
            "exists": False
        }
    
    if len(npi) != 10:
        return {
            "valid": False,
            "error": "NPI must be exactly 10 digits",
            "exists": False
        }
    
    # Check if NPI exists in NPPES
    try:
        provider = await nppes_client.get_doctor_details(npi)
        exists = provider is not None
        
        result = {
            "valid": True,
            "exists": exists,
            "npi": npi
        }
        
        if exists:
            result["provider_name"] = provider.name
            result["provider_type"] = provider.provider_type.value
            result["enumeration_type"] = provider.enumeration_type.value if provider.enumeration_type else None
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating NPI: {str(e)}", exc_info=True)
        return {
            "valid": True,  # Format is valid
            "exists": None,  # Unknown due to error
            "error": "Unable to verify NPI existence due to system error"
        }


@router.get("/stats/summary")
async def get_nppes_stats():
    """
    Get summary statistics about NPPES data.
    
    Note: These are sample queries due to NPPES API limitations.
    """
    try:
        # Sample some data from different states to get statistics
        states = ["CA", "NY", "TX", "FL", "IL"]
        stats = {
            "sample_states": states,
            "individual_providers": 0,
            "organizational_providers": 0,
            "total_sampled": 0,
            "by_state": {}
        }
        
        for state in states:
            # Get individual providers
            individual_request = NPPESSearchRequest(
                enumeration_type=EnumerationType.INDIVIDUAL,
                state=state,
                limit=50
            )
            individual_response = await nppes_client.search_providers_advanced(individual_request)
            
            # Get organizational providers
            org_request = NPPESSearchRequest(
                enumeration_type=EnumerationType.ORGANIZATIONAL,
                state=state,
                limit=50
            )
            org_response = await nppes_client.search_providers_advanced(org_request)
            
            individual_count = len(individual_response.results)
            org_count = len(org_response.results)
            
            stats["individual_providers"] += individual_count
            stats["organizational_providers"] += org_count
            stats["total_sampled"] += individual_count + org_count
            stats["by_state"][state] = {
                "individual": individual_count,
                "organizational": org_count,
                "total": individual_count + org_count
            }
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting NPPES stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting NPPES stats: {str(e)}"
        )


@router.get("/info")
async def get_nppes_info():
    """
    Get information about the NPPES API and supported parameters.
    """
    return {
        "name": "NPPES NPI Registry API",
        "description": "National Plan & Provider Enumeration System",
        "version": "2.1",
        "base_url": "https://npiregistry.cms.hhs.gov/api/",
        "documentation": "https://npiregistry.cms.hhs.gov/api-page",
        "limitations": {
            "max_results_per_request": 200,
            "max_skip": 1000,
            "max_total_results": 1200,
            "required_criteria": "At least one search criterion required"
        },
        "enumeration_types": {
            "NPI-1": "Individual Providers (physicians, nurses, therapists, etc.)",
            "NPI-2": "Organizational Providers (hospitals, clinics, pharmacies, etc.)"
        },
        "address_purposes": {
            "LOCATION": "Practice location address",
            "MAILING": "Mailing address",
            "PRIMARY": "Primary location address",
            "SECONDARY": "Secondary location address"
        },
        "supported_wildcards": {
            "first_name": "Trailing wildcards (e.g., 'jo*')",
            "last_name": "Trailing wildcards (e.g., 'sm*')",
            "organization_name": "Trailing wildcards (e.g., 'hos*')",
            "postal_code": "Trailing wildcards (e.g., '210*')"
        }
    } 