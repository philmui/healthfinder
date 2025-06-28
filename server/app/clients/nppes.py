"""
HealthFinder - NPPES NPI Registry API Client

This module provides a client for interacting with the NPPES NPI Registry API.
It encapsulates all the logic for making requests, handling responses,
and transforming the data into the application's Pydantic models.

NPPES API Documentation: https://npiregistry.cms.hhs.gov/api-page
"""

from typing import List, Optional, Dict, Any, Union, Tuple
import httpx
from loguru import logger

from app.models import (
    IndividualProvider,
    OrganizationalProvider,
    DoctorDetails,
    ClinicDetails,
    Location,
    ProviderSpecialty,
    ProviderType,
    EnumerationType,
    AddressPurpose,
    SearchProviderRequest,
    NPPESSearchRequest,
    NPPESResponse,
    NPPESProvider,
)

# Provider type mapping based on common taxonomy descriptions
TAXONOMY_TO_PROVIDER_TYPE = {
    # Individual providers
    "allopathic": ProviderType.PHYSICIAN,
    "osteopathic": ProviderType.PHYSICIAN,
    "physician": ProviderType.PHYSICIAN,
    "internal medicine": ProviderType.PHYSICIAN,
    "family medicine": ProviderType.PHYSICIAN,
    "pediatrics": ProviderType.PHYSICIAN,
    "psychiatry": ProviderType.PSYCHIATRIST,
    "psychology": ProviderType.PSYCHOLOGIST,
    "nurse": ProviderType.NURSE,
    "nurse practitioner": ProviderType.NURSE_PRACTITIONER,
    "physician assistant": ProviderType.PHYSICIAN_ASSISTANT,
    "physical therapist": ProviderType.PHYSICAL_THERAPIST,
    "occupational therapist": ProviderType.OCCUPATIONAL_THERAPIST,
    "speech": ProviderType.SPEECH_THERAPIST,
    "dentist": ProviderType.DENTIST,
    "dental": ProviderType.DENTIST,
    "optometrist": ProviderType.OPTOMETRIST,
    "chiropractor": ProviderType.CHIROPRACTOR,
    "pharmacist": ProviderType.PHARMACIST,
    "social worker": ProviderType.SOCIAL_WORKER,
    "dietitian": ProviderType.DIETITIAN,
    "nutritionist": ProviderType.DIETITIAN,
    "respiratory therapist": ProviderType.RESPIRATORY_THERAPIST,
    "radiologic": ProviderType.RADIOLOGIC_TECHNOLOGIST,
    "medical laboratory": ProviderType.CLINICAL_LABORATORY_SCIENTIST,
    "audiologist": ProviderType.AUDIOLOGIST,
    "massage therapist": ProviderType.MASSAGE_THERAPIST,
    "acupuncturist": ProviderType.ACUPUNCTURIST,
    "midwife": ProviderType.MIDWIFE,
    "podiatrist": ProviderType.PODIATRIST,
    
    # Organizational providers
    "hospital": ProviderType.HOSPITAL,
    "clinic": ProviderType.CLINIC,
    "nursing": ProviderType.NURSING_HOME,
    "rehabilitation": ProviderType.REHABILITATION_CENTER,
    "mental health": ProviderType.MENTAL_HEALTH_FACILITY,
    "pharmacy": ProviderType.PHARMACY,
    "laboratory": ProviderType.LABORATORY,
    "medical equipment": ProviderType.MEDICAL_EQUIPMENT_SUPPLIER,
    "ambulance": ProviderType.AMBULANCE_SERVICE,
    "dialysis": ProviderType.DIALYSIS_CENTER,
    "imaging": ProviderType.IMAGING_CENTER,
    "urgent care": ProviderType.URGENT_CARE,
    "surgery center": ProviderType.SURGERY_CENTER,
    "home health": ProviderType.HOME_HEALTH_AGENCY,
    "hospice": ProviderType.HOSPICE,
    "blood bank": ProviderType.BLOOD_BANK,
    "organ procurement": ProviderType.ORGAN_PROCUREMENT,
}


def _parse_name(name_str: str) -> tuple[str, str]:
    """
    Parse a full name string into first and last name components.
    
    Args:
        name_str: Full name string to parse
        
    Returns:
        Tuple of (first_name, last_name)
    """
    if not name_str:
        return "", ""
    
    name_parts = name_str.strip().split()
    if len(name_parts) == 1:
        return name_parts[0], ""
    elif len(name_parts) == 2:
        return name_parts[0], name_parts[1]
    else:
        # Assume first word is first name, rest is last name
        return name_parts[0], " ".join(name_parts[1:])


def _determine_provider_type(basic: Dict[str, Any], taxonomies: List[Dict[str, Any]]) -> ProviderType:
    """
    Determine provider type based on enumeration type and taxonomy information.
    
    Args:
        basic: Basic provider information
        taxonomies: List of taxonomy information
        
    Returns:
        ProviderType enum value
    """
    enumeration_type = basic.get("enumeration_type")
    
    # Check taxonomy descriptions for more specific provider types
    for taxonomy in taxonomies:
        desc = taxonomy.get("desc", "").lower()
        for keyword, provider_type in TAXONOMY_TO_PROVIDER_TYPE.items():
            if keyword in desc:
                return provider_type
    
    # Default based on enumeration type
    if enumeration_type == "NPI-1":
        return ProviderType.OTHER_INDIVIDUAL
    else:
        return ProviderType.OTHER_ORGANIZATIONAL


def _extract_location(addresses: List[Dict[str, Any]]) -> Location:
    """
    Extract location information from NPPES addresses.
    
    Args:
        addresses: List of address dictionaries
        
    Returns:
        Location object
    """
    practice_address = None
    mailing_address = None
    
    for addr in addresses:
        if addr.get("address_purpose") == "LOCATION":
            practice_address = addr
        elif addr.get("address_purpose") == "MAILING":
            mailing_address = addr
    
    # Use practice location if available, otherwise mailing address
    primary_address = practice_address or mailing_address or {}
    
    return Location(
        city=primary_address.get("city"),
        state=primary_address.get("state"),
        postal_code=primary_address.get("postal_code"),
        country=primary_address.get("country_code", "US"),
        address=primary_address.get("address_1"),
        address_2=primary_address.get("address_2"),
        address_purpose=AddressPurpose(primary_address.get("address_purpose")) if primary_address.get("address_purpose") else None,
        telephone_number=primary_address.get("telephone_number"),
        fax_number=primary_address.get("fax_number"),
    )


def _extract_specialties(taxonomies: List[Dict[str, Any]]) -> List[ProviderSpecialty]:
    """
    Extract specialties from taxonomy information.
    
    Args:
        taxonomies: List of taxonomy dictionaries
        
    Returns:
        List of ProviderSpecialty objects
    """
    specialties = []
    for taxonomy in taxonomies:
        if taxonomy.get("desc"):
            specialties.append(ProviderSpecialty(
                name=taxonomy.get("desc"),
                description=taxonomy.get("desc"),
                category=taxonomy.get("classification") or taxonomy.get("grouping"),
                classification=taxonomy.get("classification"),
                grouping=taxonomy.get("grouping"),
                code=taxonomy.get("code"),
                primary=taxonomy.get("primary", False)
            ))
    return specialties


def _transform_nppes_provider(provider_data: Dict[str, Any]) -> Union[IndividualProvider, OrganizationalProvider]:
    """
    Transforms raw provider data from the NPPES API into appropriate provider objects.

    Args:
        provider_data: A dictionary representing a single provider from the NPPES API.

    Returns:
        IndividualProvider or OrganizationalProvider object.
    """
    basic = provider_data.get("basic", {})
    addresses = provider_data.get("addresses", [])
    taxonomies = provider_data.get("taxonomies", [])
    
    # Extract common information
    location = _extract_location(addresses)
    specialties = _extract_specialties(taxonomies)
    provider_type = _determine_provider_type(basic, taxonomies)
    
    # Extract phone number
    phone = location.telephone_number
    
    # Determine enumeration type
    enumeration_type = EnumerationType(basic.get("enumeration_type")) if basic.get("enumeration_type") else None
    
    if basic.get("enumeration_type") == "NPI-1":
        # Individual provider
        first_name = basic.get("first_name", "").strip()
        last_name = basic.get("last_name", "").strip()
        name = f"{first_name} {last_name}".strip()
        if not name:
            name = f"Provider (NPI: {provider_data.get('number', 'Unknown')})"
        
        return IndividualProvider(
            id=f"nppes-{provider_data.get('number')}",
            name=name,
            provider_type=provider_type,
            enumeration_type=enumeration_type,
            specialties=specialties,
            location=location,
            phone=phone,
            website=None,  # NPPES doesn't provide website information
            accepts_new_patients=None,  # NPPES doesn't provide this information
            source="nppes",
            npi=provider_data.get("number"),
            first_name=first_name,
            last_name=last_name,
            middle_name=basic.get("middle_name"),
            name_prefix=basic.get("name_prefix"),
            name_suffix=basic.get("name_suffix"),
            credential=basic.get("credential"),
            gender=basic.get("gender"),
            biography=None,  # NPPES doesn't provide biography
            image_url=None,  # NPPES doesn't provide images
            education=[],  # NPPES doesn't provide education details
            board_certifications=[],  # NPPES doesn't provide certifications
        )
    else:
        # Organizational provider
        name = basic.get("organization_name", "").strip()
        if not name:
            name = f"Organization (NPI: {provider_data.get('number', 'Unknown')})"
        
        return OrganizationalProvider(
            id=f"nppes-{provider_data.get('number')}",
            name=name,
            provider_type=provider_type,
            enumeration_type=enumeration_type,
            specialties=specialties,
            location=location,
            phone=phone,
            website=None,  # NPPES doesn't provide website information
            accepts_new_patients=None,  # NPPES doesn't provide this information
            source="nppes",
            npi=provider_data.get("number"),
            organization_name=basic.get("organization_name"),
            doing_business_as=None,  # Would need to extract from other_names
            facility_type=None,  # Could be derived from taxonomy
            services=[],  # NPPES doesn't provide service details
            staff_count=None,  # NPPES doesn't provide staff count
            hours_of_operation=None,  # NPPES doesn't provide hours
            accepted_insurances=[],  # NPPES doesn't provide insurance info
            amenities=[],  # NPPES doesn't provide amenities
            image_url=None,  # NPPES doesn't provide images
            license_number=None,  # Could extract from identifiers
            accreditation=[],  # NPPES doesn't provide accreditation
        )


async def search_providers_advanced(request: NPPESSearchRequest) -> NPPESResponse:
    """
    Advanced search using NPPES API with full parameter support.
    
    Args:
        request: NPPESSearchRequest with all available parameters
        
    Returns:
        NPPESResponse with raw NPPES data
    """
    base_url = "https://npiregistry.cms.hhs.gov/api/"
    
    # Convert request to params dict, excluding None values
    params = {k: v for k, v in request.model_dump().items() if v is not None}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            return NPPESResponse(
                result_count=data.get("result_count"),
                results=[NPPESProvider(**result) for result in data.get("results", [])]
            )
    
    except httpx.HTTPStatusError as e:
        logger.error(f"NPPES API error: {e.response.status_code} - {e.response.text}")
        return NPPESResponse(result_count=0, results=[])
    except Exception as e:
        logger.error(f"An unexpected error occurred while searching NPPES: {e}", exc_info=True)
        return NPPESResponse(result_count=0, results=[])


async def search_doctors(request: SearchProviderRequest) -> Dict[str, Any]:
    """
    Searches for healthcare providers using the NPPES NPI Registry API.

    Args:
        request: A SearchProviderRequest object containing search criteria.

    Returns:
        A dictionary containing a list of providers and the total count.
    """
    base_url = "https://npiregistry.cms.hhs.gov/api/"
    
    # Build query parameters for NPPES API
    params = {
        "version": "2.1",
        "limit": min(request.limit, 200),  # NPPES max is 200
        "skip": request.skip or ((request.page - 1) * request.limit),
        "pretty": "false"
    }
    
    # Handle name-based search
    if request.query:
        # Parse the query to extract first and last name
        first_name, last_name = _parse_name(request.query)
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
    
    # Direct name parameters take precedence
    if request.first_name:
        params["first_name"] = request.first_name
    if request.last_name:
        params["last_name"] = request.last_name
    if request.organization_name:
        params["organization_name"] = request.organization_name
    
    # Handle location search
    if request.location:
        if request.location.city:
            params["city"] = request.location.city
        if request.location.state:
            params["state"] = request.location.state
        if request.location.postal_code:
            params["postal_code"] = request.location.postal_code
        if request.location.address_purpose:
            params["address_purpose"] = request.location.address_purpose.value
    
    # Direct location parameters take precedence
    if request.city:
        params["city"] = request.city
    if request.state:
        params["state"] = request.state
    if request.postal_code:
        params["postal_code"] = request.postal_code
    if request.address_purpose:
        params["address_purpose"] = request.address_purpose.value
    
    # Handle specialty search
    if request.specialty:
        params["taxonomy_description"] = request.specialty
    if request.taxonomy_description:
        params["taxonomy_description"] = request.taxonomy_description
    
    # Handle enumeration type
    if request.enumeration_type:
        params["enumeration_type"] = request.enumeration_type.value
    elif request.provider_type:
        # Map provider type to enumeration type
        individual_types = [
            ProviderType.PHYSICIAN, ProviderType.NURSE, ProviderType.NURSE_PRACTITIONER,
            ProviderType.PHYSICIAN_ASSISTANT, ProviderType.PHYSICAL_THERAPIST,
            ProviderType.OCCUPATIONAL_THERAPIST, ProviderType.SPEECH_THERAPIST,
            ProviderType.PSYCHIATRIST, ProviderType.PSYCHOLOGIST, ProviderType.DENTIST,
            ProviderType.OPTOMETRIST, ProviderType.CHIROPRACTOR, ProviderType.PHARMACIST,
            ProviderType.SOCIAL_WORKER, ProviderType.DIETITIAN, ProviderType.RESPIRATORY_THERAPIST,
            ProviderType.RADIOLOGIC_TECHNOLOGIST, ProviderType.CLINICAL_LABORATORY_SCIENTIST,
            ProviderType.AUDIOLOGIST, ProviderType.MASSAGE_THERAPIST, ProviderType.ACUPUNCTURIST,
            ProviderType.MIDWIFE, ProviderType.PODIATRIST, ProviderType.OTHER_INDIVIDUAL
        ]
        if request.provider_type in individual_types:
            params["enumeration_type"] = "NPI-1"
        else:
            params["enumeration_type"] = "NPI-2"
    
    # Ensure we have at least one search criterion (NPPES requirement)
    required_params = ["first_name", "last_name", "organization_name", 
                      "city", "state", "postal_code", "taxonomy_description"]
    if not any(key in params for key in required_params):
        logger.warning("NPPES search requires at least one search criterion")
        return {"providers": [], "total": 0}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            providers = []
            results = data.get("results", [])
            
            for provider_data in results:
                try:
                    provider = _transform_nppes_provider(provider_data)
                    providers.append(provider)
                except Exception as e:
                    logger.warning(f"Failed to transform NPPES provider data: {e}")
                    continue
            
            # NPPES doesn't provide total count, so we estimate based on results
            # If we got the full limit, there might be more results
            total_estimate = len(providers)
            if len(results) == params["limit"]:
                # Estimate total by checking if there are more results
                total_estimate = (request.page * request.limit) + 1  # At least one more page
            
            return {
                "providers": providers, 
                "total": total_estimate
            }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"NPPES API error: {e.response.status_code} - {e.response.text}")
        return {"providers": [], "total": 0}
    except Exception as e:
        logger.error(f"An unexpected error occurred while searching NPPES: {e}", exc_info=True)
        return {"providers": [], "total": 0}


async def get_doctor_details(provider_id: str) -> Optional[Union[IndividualProvider, OrganizationalProvider]]:
    """
    Retrieves detailed information for a specific provider from the NPPES API.

    Args:
        provider_id: The unique identifier for the provider (NPI number).

    Returns:
        IndividualProvider or OrganizationalProvider object if found, otherwise None.
    """
    # Extract NPI number from our internal ID format
    if provider_id.startswith("nppes-"):
        npi = provider_id.split("nppes-", 1)[1]
    else:
        npi = provider_id
    
    # Validate NPI format (should be 10 digits)
    if not npi.isdigit() or len(npi) != 10:
        logger.warning(f"Invalid NPI format: {npi}")
        return None
    
    base_url = "https://npiregistry.cms.hhs.gov/api/"
    params = {
        "version": "2.1",
        "number": npi,
        "pretty": "false"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=30.0)
            
            if response.status_code == 404:
                logger.info(f"Provider with NPI {npi} not found in NPPES.")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                logger.info(f"No results found for NPI {npi}")
                return None
            
            # NPPES should return exactly one result for a specific NPI
            provider_data = results[0]
            return _transform_nppes_provider(provider_data)
    
    except httpx.HTTPStatusError as e:
        logger.error(f"NPPES API error for NPI {npi}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching provider details for NPI {npi}: {e}", exc_info=True)
        return None


# Taxonomy-specific search functions

async def search_by_taxonomy(taxonomy_code: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search providers by specific taxonomy code.
    
    Args:
        taxonomy_code: NUCC taxonomy code
        limit: Number of results to return
        
    Returns:
        Dictionary with providers and total count
    """
    request = SearchProviderRequest(
        taxonomy_description=taxonomy_code,
        limit=limit
    )
    return await search_doctors(request)


async def search_individual_providers(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for individual providers (NPI-1).
    
    Args:
        first_name: Provider's first name
        last_name: Provider's last name
        state: State abbreviation
        limit: Number of results to return
        
    Returns:
        Dictionary with providers and total count
    """
    request = SearchProviderRequest(
        first_name=first_name,
        last_name=last_name,
        state=state,
        enumeration_type=EnumerationType.INDIVIDUAL,
        limit=limit
    )
    return await search_doctors(request)


async def search_organizational_providers(
    organization_name: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for organizational providers (NPI-2).
    
    Args:
        organization_name: Organization name
        city: City name
        state: State abbreviation
        limit: Number of results to return
        
    Returns:
        Dictionary with providers and total count
    """
    request = SearchProviderRequest(
        organization_name=organization_name,
        city=city,
        state=state,
        enumeration_type=EnumerationType.ORGANIZATIONAL,
        limit=limit
    )
    return await search_doctors(request) 