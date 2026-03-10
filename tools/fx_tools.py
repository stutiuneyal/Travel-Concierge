import httpx


async def get_fx_rate(from_ccy: str, to_ccy: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            'https://api.frankfurter.dev/latest',
            params={'from': from_ccy.upper(), 'to': to_ccy.upper()},
        )
        response.raise_for_status()
        data = response.json()
        return {
            'date': data.get('date'),
            'from': from_ccy.upper(),
            'to': to_ccy.upper(),
            'rate': (data.get('rates') or {}).get(to_ccy.upper()),
        }
