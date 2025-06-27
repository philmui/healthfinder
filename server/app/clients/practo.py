"""
HealthFinder - Practo API Client

This module provides a client for interacting with the Practo API.
It handles searching for doctors, retrieving detailed information,
and transforming the data into the application's Pydantic models.
"""

from typing import List, Optional, Dict, Any
import httpx
from loguru import logger

from app.core.config import settings
from app.api.providers import DoctorDetails, Location, ProviderSpecialty, ProviderType, SearchProviderRequest

def _transform_doctor_data(doctor_data: Dict[str, Any]) -> DoctorDetails:
    """
    Transforms a raw doctor data dictionary from the Practo API
    into the application's DoctorDetails Pydantic model.

    Args:
        doctor_data: A dictionary representing a single doctor from the Practo API.

    Returns:
        A DoctorDetails object.
    """
    # Location data can be in different places depending on the endpoint (search vs. details)
    practice = {}
    if doctor_data.get("relations"):
        practice = doctor_data.get("relations", [{}])[0].get("practice", {})
    
    locality = practice.get("locality", {})
    city_info = locality.get("city", {})
    
    location = Location(
        latitude=practice.get("latitude") or doctor_data.get("latitude"),
        longitude=practice.get("longitude") or doctor_data.get("longitude"),
        city=city_info.get("name") or doctor_data.get("city"),
        state=city_info.get("state", {}).get("name"),
        country=city_info.get("state", {}).get("country", {}).get("name", "India"),
        address=practice.get("street_address") or doctor_data.get("locality"),
        locality=locality.get("name")
    )

    # Specialties can also have different structures
    specialties_raw = doctor_data.get("specializations", doctor_data.get("specialties", []))
    specialties = []
    for s in specialties_raw:
        specialty_name = s.get('specialty', {}).get('specialty')
        sub_specialty_name = s.get('subspecialization', {}).get('subspecialization')
        specialties.append(ProviderSpecialty(
            name=sub_specialty_name or specialty_name,
            category=specialty_name
        ))

    # Image URL can be in different keys
    photos = doctor_data.get("photos", doctor_data.get("doctor_photos", []))
    image_url = next((p.get('photo_url') or p.get('url') for p in photos if p.get('photo_default') or p.get('is_default')), None)
    
    # Review count can be nested
    review_count_raw = doctor_data.get("recommendation")
    review_count = review_count_raw.get("recommendation") if isinstance(review_count_raw, dict) else review_count_raw

    return DoctorDetails(
        id=f"practo-{doctor_data.get('id') or doctor_data.get('doctor_id')}",
        name=doctor_data.get("name") or doctor_data.get("doctor_name"),
        provider_type=ProviderType.DOCTOR,
        specialties=specialties,
        location=location,
        source="practo",
        review_count=review_count,
        gender=doctor_data.get("gender"),
        education=[q.get('qualification', {}).get('name') for q in doctor_data.get("qualifications", [])],
        biography=doctor_data.get("summary"),
        years_of_experience=doctor_data.get("experience_years"),
        image_url=image_url,
        consultation_fees=doctor_data.get("consultation_fees") or doctor_data.get("relations", [{}])[0].get("consultation_fee")
    )

async def search_doctors(request: SearchProviderRequest) -> Dict[str, Any]:
    """
    Searches for doctors using the Practo API.

    Args:
        request: A SearchProviderRequest object containing search criteria.

    Returns:
        A dictionary containing a list of providers and the total count.
    """
    if not settings.PRACTO_API_KEY or not settings.PRACTO_CLIENT_ID:
        logger.warning("PRACTO_API_KEY or PRACTO_CLIENT_ID not set. Skipping Practo search.")
        return {"providers": [], "total": 0}

    base_url = "https://api.practo.com/search"
    params = {
        "limit": request.limit,
        "offset": (request.page - 1) * request.limit,
    }

    if request.location and request.location.city:
        params["city"] = request.location.city
    else:
        params["city"] = "bangalore"  # Practo API requires a city

    if request.query:
        params["q"] = request.query
    if request.specialty:
        params["speciality"] = request.specialty
    if request.location and request.location.locality:
        params["locality"] = request.location.locality

    headers = {
        "X-API-KEY": settings.PRACTO_API_KEY,
        "X-CLIENT-ID": settings.PRACTO_CLIENT_ID
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            providers = [_transform_doctor_data(doc) for doc in data.get("doctors", [])]
            return {"providers": providers, "total": data.get("total", 0)}

    except httpx.HTTPStatusError as e:
        logger.error(f"Practo API error: {e.response.status_code} - {e.response.text}")
        return {"providers": [], "total": 0}
    except Exception as e:
        logger.error(f"An unexpected error occurred while searching Practo: {e}", exc_info=True)
        return {"providers": [], "total": 0}

async def get_doctor_details(provider_id: str) -> Optional[DoctorDetails]:
    """
    Retrieves detailed information for a specific doctor from the Practo API.

    Args:
        provider_id: The unique identifier for the doctor, prefixed with 'practo-'.

    Returns:
        A DoctorDetails object if the doctor is found, otherwise None.
    """
    if not settings.PRACTO_API_KEY or not settings.PRACTO_CLIENT_ID:
        logger.warning("PRACTO_API_KEY or PRACTO_CLIENT_ID not set. Cannot fetch doctor details.")
        return None

    if provider_id.startswith("practo-"):
        practo_id = provider_id.split("practo-", 1)[1]
    else:
        practo_id = provider_id

    url = f"https://api.practo.com/doctors/{practo_id}"
    params = {"with_relations": "true"}  # To get practice and fee details
    headers = {
        "X-API-KEY": settings.PRACTO_API_KEY,
        "X-CLIENT-ID": settings.PRACTO_CLIENT_ID
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)

            if response.status_code == 404:
                logger.info(f"Doctor with ID {practo_id} not found in Practo.")
                return None

            response.raise_for_status()
            data = response.json()
            return _transform_doctor_data(data)

    except httpx.HTTPStatusError as e:
        logger.error(f"Practo API error for ID {practo_id}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching doctor details for ID {practo_id}: {e}", exc_info=True)
        return None
