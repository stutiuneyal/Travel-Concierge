from typing import Dict

import httpx


class OpenMeteoClient:
    async def geocode(self, name: str) -> Dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                'https://geocoding-api.open-meteo.com/v1/search',
                params={
                    'name': name,
                    'count': 1,
                    'language': 'en',
                    'format': 'json',
                },
            )
            response.raise_for_status()
            return response.json()

    async def forecast(self, latitude: float, longitude: float) -> Dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                'https://api.open-meteo.com/v1/forecast',
                params={
                    'latitude': latitude,
                    'longitude': longitude,
                    'daily': 'weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
                    'timezone': 'auto',
                    'forecast_days': 7,
                },
            )
            response.raise_for_status()
            return response.json()


open_meteo_client = OpenMeteoClient()
