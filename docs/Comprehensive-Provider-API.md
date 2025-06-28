# Healthcare Provider API Documentation

## Overview

The HealthFinder Provider API has been expanded to support **all types of healthcare providers** including individual practitioners (physicians, nurses, therapists, etc.) and healthcare organizations (hospitals, clinics, laboratories, etc.). The system integrates with the NPPES (National Plan & Provider Enumeration System) NPI Registry to provide comprehensive coverage of all US healthcare providers.

## 🏥 **Supported Provider Types**

### Individual Providers (NPI-1)
- **Physicians** - All medical specialties
- **Nurses** - Registered nurses, nurse practitioners
- **Therapists** - Physical, occupational, speech, respiratory
- **Mental Health** - Psychiatrists, psychologists, social workers
- **Dental** - Dentists, orthodontists
- **Vision** - Optometrists, ophthalmologists
- **Specialists** - Chiropractors, podiatrists, audiologists
- **Allied Health** - Pharmacists, dietitians, massage therapists
- **Technical** - Radiologic technologists, lab scientists
- **Alternative** - Acupuncturists, midwives
- **Other** - Any other individual healthcare providers

### Organizational Providers (NPI-2)
- **Hospitals** - General, specialty, children's hospitals
- **Clinics** - Outpatient clinics, urgent care centers
- **Long-term Care** - Nursing homes, assisted living
- **Rehabilitation** - Physical therapy centers, rehab hospitals
- **Mental Health** - Psychiatric facilities, counseling centers
- **Pharmacies** - Retail, hospital, specialty pharmacies
- **Laboratories** - Clinical labs, imaging centers
- **Specialized** - Dialysis centers, surgery centers
- **Home Care** - Home health agencies, hospice care
- **Emergency** - Ambulance services, emergency departments
- **Support** - Medical equipment suppliers, blood banks

## 🚀 **API Endpoints**

### Main Provider Search

#### `GET /providers/search`
**Comprehensive provider search with all filtering options**

```bash
curl "http://localhost:8000/providers/search?query=Smith&state=CA&provider_type=physician&limit=10"
```

**Parameters:**
- `query` - General search term (parsed into first/last name)
- `first_name` - Individual provider's first name
- `last_name` - Individual provider's last name  
- `organization_name` - Organization name
- `provider_type` - Specific provider type (see enum list)
- `enumeration_type` - Individual (NPI-1) or Organizational (NPI-2)
- `specialty` / `taxonomy_description` - Provider specialty
- `city`, `state`, `postal_code` - Location filters
- `gender` - For individual providers
- `limit` - Results per page (max 200)
- `skip` - Results to skip (pagination)

#### `GET /providers/search/individual`
**Search specifically for individual providers**

```bash
curl "http://localhost:8000/providers/search/individual?first_name=John&last_name=Smith&state=NY"
```

#### `GET /providers/search/organizational`
**Search specifically for organizations**

```bash
curl "http://localhost:8000/providers/search/organizational?organization_name=General%20Hospital&city=Boston"
```

#### `GET /providers/search/by-taxonomy`
**Search by NUCC taxonomy codes**

```bash
curl "http://localhost:8000/providers/search/by-taxonomy?taxonomy_code=207Q00000X&state=CA"
```

### NPPES-Specific Endpoints

#### `GET /api/v1/nppes/search/basic`
**Basic NPPES search**

```bash
curl "http://localhost:8000/api/v1/nppes/search/basic?city=Chicago&state=IL&limit=5"
```

#### `GET /api/v1/nppes/search/individual`
**Advanced individual provider search**

```bash
curl "http://localhost:8000/api/v1/nppes/search/individual?first_name=Mary&taxonomy_description=Family%20Medicine&state=TX"
```

#### `GET /api/v1/nppes/search/organizational`
**Advanced organizational provider search**

```bash
curl "http://localhost:8000/api/v1/nppes/search/organizational?organization_name=Children%20Hospital&city=Philadelphia"
```

#### `GET /api/v1/nppes/search/by-npi/{npi}`
**Get provider by exact NPI number**

```bash
curl "http://localhost:8000/api/v1/nppes/search/by-npi/1234567890"
```

#### `GET /api/v1/nppes/search/by-taxonomy`
**Search by taxonomy with advanced filters**

```bash
curl "http://localhost:8000/api/v1/nppes/search/by-taxonomy?taxonomy_description=Physical%20Therapist&state=FL"
```

#### `GET /api/v1/nppes/search/by-location`
**Location-focused search**

```bash
curl "http://localhost:8000/api/v1/nppes/search/by-location?postal_code=90210&provider_type=individual"
```

#### `POST /api/v1/nppes/search/advanced`
**Advanced search with full NPPES parameters**

```bash
curl -X POST "http://localhost:8000/api/v1/nppes/search/advanced" \
     -H "Content-Type: application/json" \
     -d '{
       "enumeration_type": "NPI-1",
       "first_name": "David",
       "use_first_name_alias": true,
       "state": "CA",
       "limit": 20
     }'
```

### Utility Endpoints

#### `GET /providers/types`
**Get all available provider types**

```bash
curl "http://localhost:8000/providers/types"
```

**Response:**
```json
{
  "individual_providers": [
    "physician", "nurse", "nurse_practitioner", "physical_therapist", 
    "psychiatrist", "dentist", "pharmacist", ...
  ],
  "organizational_providers": [
    "hospital", "clinic", "nursing_home", "pharmacy", 
    "laboratory", "urgent_care", ...
  ]
}
```

#### `GET /api/v1/nppes/validate/npi/{npi}`
**Validate NPI number**

```bash
curl "http://localhost:8000/api/v1/nppes/validate/npi/1234567890"
```

#### `GET /api/v1/nppes/info`
**Get NPPES API information**

```bash
curl "http://localhost:8000/api/v1/nppes/info"
```

#### `GET /providers/stats/by-state?state=CA`
**Get provider statistics for a state**

```bash
curl "http://localhost:8000/providers/stats/by-state?state=CA&limit=50"
```

## 📊 **Data Models**

### IndividualProvider
```json
{
  "id": "nppes-1234567890",
  "name": "Dr. John Smith",
  "provider_type": "physician",
  "enumeration_type": "NPI-1",
  "npi": "1234567890",
  "first_name": "John",
  "last_name": "Smith",
  "gender": "M",
  "specialties": [
    {
      "name": "Family Medicine",
      "code": "207Q00000X",
      "primary": true
    }
  ],
  "location": {
    "city": "Los Angeles",
    "state": "CA",
    "postal_code": "90210",
    "address": "123 Main St",
    "phone": "(555) 123-4567"
  },
  "source": "nppes"
}
```

### OrganizationalProvider
```json
{
  "id": "nppes-9876543210",
  "name": "General Hospital",
  "provider_type": "hospital",
  "enumeration_type": "NPI-2",
  "npi": "9876543210",
  "organization_name": "General Hospital",
  "specialties": [
    {
      "name": "General Acute Care Hospital"
    }
  ],
  "location": {
    "city": "New York",
    "state": "NY",
    "address": "456 Hospital Ave"
  },
  "source": "nppes"
}
```

## 🔍 **Search Examples**

### Find Physical Therapists in California
```bash
curl "http://localhost:8000/providers/search?provider_type=physical_therapist&state=CA&limit=10"
```

### Find Hospitals in New York City
```bash
curl "http://localhost:8000/providers/search?provider_type=hospital&city=New%20York&state=NY"
```

### Find Nurse Practitioners by Name
```bash
curl "http://localhost:8000/providers/search?provider_type=nurse_practitioner&first_name=Sarah&state=TX"
```

### Find Mental Health Facilities
```bash
curl "http://localhost:8000/providers/search?provider_type=mental_health_facility&state=FL"
```

### Find Pharmacies in ZIP Code
```bash
curl "http://localhost:8000/providers/search?provider_type=pharmacy&postal_code=10001"
```

### Advanced Specialty Search
```bash
curl "http://localhost:8000/api/v1/nppes/search/by-taxonomy?taxonomy_description=Pediatric%20Cardiology&limit=20"
```

## 🏗️ **Technical Features**

### Provider Type Intelligence
- **Automatic Classification** - Providers are automatically classified based on NPPES taxonomy codes
- **Comprehensive Mapping** - 40+ provider types mapped from NPPES data
- **Flexible Search** - Search by general terms or specific provider types

### Advanced Filtering
- **Multi-parameter Search** - Combine name, location, specialty, and type filters
- **Pagination Support** - Handle large result sets efficiently
- **Geographic Search** - City, state, ZIP code, and coordinate-based search
- **Specialty Matching** - Search by taxonomy descriptions or codes

### Data Quality
- **Official Source** - All data from NPPES, the authoritative US provider registry
- **Real-time** - Direct API integration, always up-to-date
- **Comprehensive** - Covers 100% of licensed US healthcare providers
- **Structured** - Standardized taxonomies and classifications

### Performance
- **Efficient** - Optimized queries with proper pagination
- **Scalable** - Handles high-volume searches
- **Reliable** - Robust error handling and fallbacks
- **Fast** - Minimal response times with smart caching

## 🚦 **API Limits & Guidelines**

### NPPES API Limitations
- **Max Results**: 200 per request
- **Max Skip**: 1,000 records
- **Total Accessible**: 1,200 records across 6 requests
- **Required Criteria**: At least one search parameter required

### Best Practices
1. **Use Specific Filters** - Combine multiple criteria for targeted results
2. **Implement Pagination** - Use `limit` and `skip` for large datasets
3. **Handle Errors** - Implement proper error handling for API failures
4. **Cache Results** - Cache frequent searches to improve performance
5. **Monitor Usage** - Track API usage patterns and optimize accordingly

## 🔄 **Integration Examples**

### Python Client
```python
import httpx
import asyncio

async def search_providers():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/providers/search",
            params={
                "provider_type": "nurse_practitioner",
                "state": "CA",
                "limit": 10
            }
        )
        data = response.json()
        print(f"Found {data['total']} providers")
        for provider in data['providers']:
            print(f"- {provider['name']} ({provider['provider_type']})")

asyncio.run(search_providers())
```

### JavaScript/Frontend
```javascript
async function searchProviders() {
    const response = await fetch('/providers/search?' + new URLSearchParams({
        provider_type: 'physician',
        specialty: 'Family Medicine',
        city: 'Boston',
        state: 'MA',
        limit: 20
    }));
    
    const data = await response.json();
    console.log(`Found ${data.total} providers`);
    
    data.providers.forEach(provider => {
        console.log(`${provider.name} - ${provider.location.city}, ${provider.location.state}`);
    });
}
```

## 📈 **Benefits**

### For Developers
- **Complete Coverage** - Access to all US healthcare providers in one API
- **Rich Data** - Detailed provider information including specialties and locations
- **Flexible Queries** - Multiple search patterns and filtering options
- **Standard Format** - Consistent data models across all provider types

### For Applications
- **Comprehensive Search** - Find any type of healthcare provider
- **Accurate Data** - Official government data source
- **Real-time** - Always current provider information
- **Scalable** - Handles enterprise-level usage

### For Users
- **Find Any Provider** - Doctors, nurses, therapists, hospitals, clinics, etc.
- **Accurate Results** - Official, verified provider information
- **Location-based** - Find providers near you
- **Specialty Search** - Find providers by exact specialty or service

This comprehensive provider system transforms HealthFinder into a complete healthcare provider directory, supporting all types of medical professionals and organizations with advanced search capabilities. 