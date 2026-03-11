import pycountry
from typing import Optional, Any
from services.amadeus_client import amadeus_client

# ISO country mapping
COUNTRY_TO_ISO = {
    country.name.lower(): country.alpha_2
    for country in pycountry.countries
}

COUNTRY_TO_ISO.update({
    "uae": "AE",
    "united arab emirates": "AE",
})

# Static fallback mappings
CITY_TO_AIRPORT = {
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "delhi": "DEL",
    "mumbai": "BOM",
    "kolkata": "CCU",
    "chennai": "MAA",
    "hyderabad": "HYD",
    "bangkok": "BKK",
    "phuket": "HKT",
    "tokyo": "NRT",
    "osaka": "KIX",
    "dubai": "DXB",
    "paris": "CDG",
    "london": "LHR",
    "singapore": "SIN",
}

COUNTRY_TO_AIRPORT = {
    "india": "DEL",
    "thailand": "BKK",
    "japan": "NRT",
    "uae": "DXB",
    "france": "CDG",
    "uk": "LHR",
    "united kingdom": "LHR",
    "singapore": "SIN",
}

airport_cache: dict[str, str] = {}


def extract_iata_code(locations: list[dict[str, Any]]) -> Optional[str]:
    """Extract best IATA code from Amadeus response."""

    if not locations:
        return None

    # Prefer CITY results over AIRPORT
    sorted_locations = sorted(
        locations,
        key=lambda x: 0 if x.get("subType") == "CITY" else 1
    )

    for loc in sorted_locations:
        code = loc.get("iataCode") or loc.get("address", {}).get("cityCode")
        if code:
            return code

    return None


async def resolve_airport_code(city: Optional[str], country: Optional[str]) -> Optional[str]:

    if not city:
        return None

    city_key = city.lower().strip()
    country_key = (country or "").lower().strip()

    cache_key = f"{city_key}-{country_key}"

    # 1️⃣ Cache
    if cache_key in airport_cache:
        return airport_cache[cache_key]

    # 2️⃣ Try Amadeus API
    try:
        params = {
            "subType": "CITY,AIRPORT",
            "keyword": city,
            "page[limit]": 5,
        }

        country_code = COUNTRY_TO_ISO.get(country_key)
        if country_code:
            params["countryCode"] = country_code

        print("DEBUG airport lookup params:", params)

        data = await amadeus_client.get(
            "/v1/reference-data/locations",
            params=params
        )

        print("DEBUG airport lookup response:", data)

        locations = data.get("data", [])

        code = extract_iata_code(locations)

        if code:
            airport_cache[cache_key] = code
            return code

    except Exception as e:
        print("Airport API lookup failed:", e)

    # 3️⃣ Fallback: city mapping
    if city_key in CITY_TO_AIRPORT:
        print("DEBUG airport fallback via city map:", city_key)
        code = CITY_TO_AIRPORT[city_key]
        airport_cache[cache_key] = code
        return code

    # 4️⃣ Fallback: country mapping
    if country_key in COUNTRY_TO_AIRPORT:
        print("DEBUG airport fallback via country map:", country_key)
        code = COUNTRY_TO_AIRPORT[country_key]
        airport_cache[cache_key] = code
        return code

    print("DEBUG airport resolution failed for:", city, country)

    return None