import httpx
from typing import Optional
from services.amadeus_client import amadeus_client

import pycountry

COUNTRY_TO_ISO = {
    country.name.lower(): country.alpha_2
    for country in pycountry.countries
}

airport_cache: dict[str, str] = {}

async def resolve_airport_code(city: Optional[str], country: Optional[str]) -> Optional[str]:
    if not city and not country:
        return None

    cache_key = f"{city}-{country}".lower()

    if cache_key in airport_cache:
        return airport_cache[cache_key]

    params = {
        "subType": "CITY,AIRPORT",
        "keyword": city or country,
        "page[limit]": 1,
    }

    # Add country filter if available
    if country:
        country_code = COUNTRY_TO_ISO.get(country.lower())
        if country_code:
            params["countryCode"] = country_code

    try:
        data = await amadeus_client.get(
            "/v1/reference-data/locations",
            params=params,
        )

        locations = data.get("data", [])
        if locations:
            code = locations[0]["iataCode"]
            airport_cache[cache_key] = code
            return code

    except Exception as e:
        print(f"Airport lookup failed: {e}")

    return None
