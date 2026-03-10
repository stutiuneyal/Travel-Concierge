from typing import Any, Dict, List

from services.google_places_client import places_client


async def search_places(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    destination = context.get('destination_city') or context.get('destination_country')
    interests = context.get('interests') or []

    if not destination:
        return []

    query = f'Top attractions in {destination}'
    if interests:
        query = f"Top attractions in {destination} for {', '.join(interests)}"

    data = await places_client.text_search(query)
    places = data.get('places') or []
    normalized = []
    for place in places[:8]:
        normalized.append(
            {
                'name': (place.get('displayName') or {}).get('text'),
                'address': place.get('formattedAddress'),
                'rating': place.get('rating'),
                'reviews': place.get('userRatingCount'),
                'type': place.get('primaryType'),
            }
        )
    return normalized
