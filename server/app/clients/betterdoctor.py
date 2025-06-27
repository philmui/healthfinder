"""
HealthFinder - BetterDoctor API Client

This module provides a client for interacting with the BetterDoctor API.
It encapsulates all the logic for making requests, handling responses,
and transforming the data into the application's Pydantic models.
"""

from typing import List, Optional, Dict, Any
import httpx
from loguru import logger

from app.core.config import settings
from app.api.providers import DoctorDetails, Location, ProviderSpecialty, ProviderType, SearchProviderRequest

def _transform_doctor_data(doctor_data: Dict[str, Any]) -> DoctorDetails:
    """
    Transforms a raw doctor data dictionary from the BetterDoctor API
    into the application's DoctorDetails Pydantic model.

    Args:
        doctor_data: A dictionary representing a single doctor from the BetterDoctor API.

    Returns:
        A DoctorDetails object.
    """
    profile = doctor_data.get("profile", {})
    practice = doctor_data.get("practices", [{}])[0]

    specialties = [
        ProviderSpecialty(
            name=s.get("name"),
            description=s.get("description"),
            category=s.get("category")
        ) for s in doctor_data.get("specialties", [])
    ]

    location = Location(
        latitude=practice.get("lat"),
        longitude=practice.get("lon"),
        city=practice.get("city"),
        state=practice.get("state"),
        postal_code=practice.get("zip"),
        country="US",
        address=practice.get("street")
    )

    return DoctorDetails(
        id=f"betterdoctor-{doctor_data.get('uid')}",
        name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
        provider_type=ProviderType.DOCTOR,
        specialties=specialties,
        location=location,
        phone=next((p.get("number") for p in practice.get("phones", []) if p.get("type") == "landline"), None),
        website=practice.get("website"),
        accepts_new_patients=practice.get("accepts_new_patients"),
        source="betterdoctor",
        npi=doctor_data.get("npi"),
        gender=profile.get("gender"),
        biography=profile.get("bio"),
        image_url=profile.get("image_url"),
        education=[edu.get("school") for edu in doctor_data.get("educations", [])],
        board_certifications=[cert.get("name") for cert in doctor_data.get("certifications", [])],
    )

async def search_doctors(request: SearchProviderRequest) -> Dict[str, Any]:
    """
    Searches for doctors using the BetterDoctor API.

    Args:
        request: A SearchProviderRequest object containing search criteria.

    Returns:
        A dictionary containing a list of providers and the total count.
    """
    if not settings.BETTERDOCTOR_API_KEY:
        logger.warning("BETTERDOCTOR_API_KEY is not set. Skipping BetterDoctor search.")
        return {"providers": [], "total": 0}

    base_url = "https://api.betterdoctor.com/2016-03-01/doctors"
    params = {
        "user_key": settings.BETTERDOCTOR_API_KEY,
        "limit": request.limit,
        "skip": (request.page - 1) * request.limit,
    }

    if request.query:
        params["name"] = request.query
    if request.specialty:
        params["specialty_uid"] = request.specialty
    if request.location and request.location.latitude and request.location.longitude:
        params["location"] = f"{request.location.latitude},{request.location.longitude},{request.distance or 10}"
    if request.gender and request.gender != "any":
        params["gender"] = request.gender.value

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            providers = [_transform_doctor_data(doc) for doc in data.get("data", [])]
            return {"providers": providers, "total": data.get("meta", {}).get("total", 0)}

    except httpx.HTTPStatusError as e:
        logger.error(f"BetterDoctor API error: {e.response.status_code} - {e.response.text}")
        return {"providers": [], "total": 0}
    except Exception as e:
        logger.error(f"An unexpected error occurred while searching BetterDoctor: {e}", exc_info=True)
        return {"providers": [], "total": 0}

async def get_doctor_details(provider_id: str) -> Optional[DoctorDetails]:
    """
    Retrieves detailed information for a specific doctor from the BetterDoctor API.

    Args:
        provider_id: The unique identifier for the doctor (UID from BetterDoctor).

    Returns:
        A DoctorDetails object if the doctor is found, otherwise None.
    """
    if not settings.BETTERDOCTOR_API_KEY:
        logger.warning("BETTERDOCTOR_API_KEY is not set. Cannot fetch doctor details.")
        return None

    # The provider_id from our system is prefixed, so we remove it.
    if provider_id.startswith("betterdoctor-"):
        uid = provider_id.split("betterdoctor-", 1)[1]
    else:
        uid = provider_id

    url = f"https://api.betterdoctor.com/2016-03-01/doctors/{uid}"
    params = {"user_key": settings.BETTERDOCTOR_API_KEY}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)

            if response.status_code == 404:
                logger.info(f"Doctor with UID {uid} not found in BetterDoctor.")
                return None

            response.raise_for_status()
            data = response.json().get("data", {})
            return _transform_doctor_data(data)

    except httpx.HTTPStatusError as e:
        logger.error(f"BetterDoctor API error for UID {uid}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching doctor details for UID {uid}: {e}", exc_info=True)
        return None
