from typing import Dict

import httpx

from config.settings import settings


class GooglePlacesClient:
    BASE_URL = 'https://places.googleapis.com/v1'

    async def text_search(self, text_query: str) -> Dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f'{self.BASE_URL}/places:searchText',
                headers={
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': settings.GOOGLE_PLACES_API_KEY,
                    'X-Goog-FieldMask': (
                        'places.displayName,places.formattedAddress,places.rating,'
                        'places.userRatingCount,places.primaryType,places.location'
                    ),
                },
                json={'textQuery': text_query},
            )
            response.raise_for_status()
            return response.json()


places_client = GooglePlacesClient()
