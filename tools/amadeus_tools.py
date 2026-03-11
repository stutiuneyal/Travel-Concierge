from typing import Any, Dict, List, Optional

from services.amadeus_client import amadeus_client
from tools.airport_tools import resolve_airport_code
import httpx
from config.settings import settings
import asyncio

GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


async def search_google_place_for_hotel(name: str, city: str, country: Optional[str] = None) -> Dict[str, Any]:
    query = f"{name}, {city}"
    if country:
        query += f", {country}"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join(
            [
                "places.displayName",
                "places.formattedAddress",
                "places.rating",
                "places.userRatingCount",
                "places.location",
                "places.id",
                "places.googleMapsUri",
                "places.primaryType",
            ]
        ),
    }

    body = {
        "textQuery": query,
        "maxResultCount": 1,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(GOOGLE_PLACES_TEXT_SEARCH_URL, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    places = data.get("places", [])
    if not places:
        return {}

    place = places[0]
    return {
        "place_id": place.get("id"),
        "name": (place.get("displayName") or {}).get("text"),
        "address": place.get("formattedAddress"),
        "rating": place.get("rating"),
        "user_rating_count": place.get("userRatingCount"),
        "latitude": (place.get("location") or {}).get("latitude"),
        "longitude": (place.get("location") or {}).get("longitude"),
        "google_maps_url": place.get("googleMapsUri"),
        "primary_type": place.get("primaryType"),
    }

async def search_flights(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    print("DEBUG search_flights context:", context)

    origin_city = context.get("origin_city")
    origin_country = context.get("origin_country")
    destination_city = context.get("destination_city")
    destination_country = context.get("destination_country")
    departure_date = context.get("start_date")
    currency = context.get("home_currency", "INR")

    print("DEBUG extracted:", {
        "origin_city": origin_city,
        "origin_country": origin_country,
        "destination_city": destination_city,
        "destination_country": destination_country,
        "departure_date": departure_date,
    })
    
    origin_code = await resolve_airport_code(origin_city, origin_country)
    destination_code = await resolve_airport_code(destination_city, destination_country)
    departure_date = context.get('start_date')
    currency = context.get('home_currency', 'INR')
    
    print("DEBUG resolved codes:", {
        "origin_code": origin_code,
        "destination_code": destination_code,
        "departure_date": departure_date,
    })

    if not origin_code or not destination_code or not departure_date:
        print("DEBUG early return from search_flights")
        return []

    params = {
        'originLocationCode': origin_code,
        'destinationLocationCode': destination_code,
        'departureDate': departure_date,
        'adults': 1,
        'currencyCode': currency,
        'max': 5,
    }
    
    print("DEBUG flight params:", params)

    data = await amadeus_client.get('/v2/shopping/flight-offers', params=params)
    print("DEBUG raw flight response:", data)
    offers = data.get('data', [])
    print("DEBUG offers count:", len(offers))

    normalized = []
    for offer in offers[:5]:
        price = offer.get('price', {})
        itineraries = offer.get('itineraries') or []
        segments = itineraries[0].get('segments', []) if itineraries else []
        first = segments[0] if segments else {}
        last = segments[-1] if segments else {}
        validating = offer.get('validatingAirlineCodes') or []

        normalized.append(
            {
                'airline': ', '.join(validating) if validating else 'Unknown',
                'origin': first.get('departure', {}).get('iataCode', origin_code),
                'destination': last.get('arrival', {}).get('iataCode', destination_code),
                'departure': first.get('departure', {}).get('at'),
                'arrival': last.get('arrival', {}).get('at'),
                'stops': max(len(segments) - 1, 0),
                'price': price.get('grandTotal'),
                'currency': price.get('currency'),
            }
        )

    return normalized


async def search_hotels(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    city = context.get("destination_city") or context.get("destination_country")
    country = context.get("destination_country")
    if not city:
        return []

    city_code = await resolve_airport_code(city, None) or city[:3].upper()

    data = await amadeus_client.get(
        "/v1/reference-data/locations/hotels/by-city",
        params={
            "cityCode": city_code,
            "radius": 10,
            "radiusUnit": "KM",
            "hotelSource": "ALL",
        },
    )

    hotels = data.get("data", [])[:5]
    if not hotels:
        return []

    enriched = await asyncio.gather(
        *(enrich_single_hotel(hotel, city, country,context) for hotel in hotels),
        return_exceptions=True,
    )

    normalized = []
    for item in enriched:
        if isinstance(item, Exception):
            continue
        normalized.append(item)

    return normalized


async def fetch_hotel_offer_price(hotel_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    check_in_date = context.get("start_date")
    adults = context.get("travelers") or 1

    if not hotel_id or not check_in_date:
        return {}
    try:
        data = await amadeus_client.get(
            "/v3/shopping/hotel-offers",
            params={
                "hotelIds": hotel_id,
                "adults": adults,
                "checkInDate": check_in_date,
                "roomQuantity": 1,
            },
        )
        hotels = data.get("data", [])
        if not hotels:
            return {}

        offers = hotels[0].get("offers", [])
        if not offers:
            return {}

        first_offer = offers[0]
        price = first_offer.get("price", {})
        return {
            "price": price.get("total"),
            "currency": price.get("currency"),
            "check_in_date": first_offer.get("checkInDate"),
            "check_out_date": first_offer.get("checkOutDate"),
            "room_description": ((first_offer.get("room") or {}).get("description") or {}).get("text"),
        }
    except Exception:
        return {}

async def enrich_single_hotel(hotel: Dict[str, Any], city: str, country: str | None, context: Dict[str, Any]) -> Dict[str, Any]:
    hotel_id = hotel.get("hotelId")
    hotel_name = hotel.get("name")

    google_task = search_google_place_for_hotel(hotel_name, city, country) if hotel_name else None
    price_task = fetch_hotel_offer_price(hotel_id,context) if hotel_id else None

    google_result, price_result = await asyncio.gather(
        google_task if google_task else asyncio.sleep(0, result={}),
        price_task if price_task else asyncio.sleep(0, result={}),
        return_exceptions=True,
    )

    if isinstance(google_result, Exception):
        google_result = {}
    if isinstance(price_result, Exception):
        price_result = {}

    return {
        "name": hotel_name,
        "hotel_id": hotel_id,
        "chain_code": hotel.get("chainCode"),
        "city": city,
        "country": country,
        "distance_km": (hotel.get("distance") or {}).get("value"),
        "distance_unit": (hotel.get("distance") or {}).get("unit"),
        "latitude": google_result.get("latitude") or ((hotel.get("geoCode") or {}).get("latitude")),
        "longitude": google_result.get("longitude") or ((hotel.get("geoCode") or {}).get("longitude")),
        "address": google_result.get("address"),
        "rating": google_result.get("rating"),
        "user_rating_count": google_result.get("user_rating_count"),
        "place_id": google_result.get("place_id"),
        "google_maps_url": google_result.get("google_maps_url"),
        "primary_type": google_result.get("primary_type"),
        "price": price_result.get("price"),
        "currency": price_result.get("currency"),
        "room_description": price_result.get("room_description"),
        "check_in_date": price_result.get("check_in_date"),
        "check_out_date": price_result.get("check_out_date"),
    }