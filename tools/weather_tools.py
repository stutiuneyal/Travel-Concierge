from typing import Any, Dict

from services.open_meteo_client import open_meteo_client


async def get_weather_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    place = context.get('destination_city') or context.get('destination_country')
    if not place:
        return {}

    geocode = await open_meteo_client.geocode(place)
    results = geocode.get('results') or []
    if not results:
        return {}

    first = results[0]
    forecast = await open_meteo_client.forecast(first['latitude'], first['longitude'])
    daily = forecast.get('daily', {})

    return {
        'place': place,
        'timezone': forecast.get('timezone'),
        'dates': daily.get('time', []),
        'max_temps': daily.get('temperature_2m_max', []),
        'min_temps': daily.get('temperature_2m_min', []),
        'rain_probability': daily.get('precipitation_probability_max', []),
    }
