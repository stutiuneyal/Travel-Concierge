import time
from typing import Any, Dict

import httpx

from config.settings import settings


class AmadeusClient:
    BASE_URL = 'https://test.api.amadeus.com'

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0

    async def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < self._expires_at - 60:
            return self._token

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f'{self.BASE_URL}/v1/security/oauth2/token',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': settings.AMADEUS_CLIENT_ID,
                    'client_secret': settings.AMADEUS_CLIENT_SECRET,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            response.raise_for_status()
            payload = response.json()
            self._token = payload['access_token']
            self._expires_at = now + int(payload.get('expires_in', 1800))
            return self._token

    async def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        token = await self._ensure_token()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f'{self.BASE_URL}{path}',
                params=params,
                headers={'Authorization': f'Bearer {token}'},
            )
            response.raise_for_status()
            return response.json()


amadeus_client = AmadeusClient()
