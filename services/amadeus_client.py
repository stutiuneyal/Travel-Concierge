import time
import httpx
import asyncio
from typing import Any, Dict
from config.settings import settings


class AmadeusClient:
    BASE_URL = "https://test.api.amadeus.com"

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < self._expires_at - 60:
            return self._token

        async with self._lock:
            # double-check after acquiring lock
            now = time.time()
            if self._token and now < self._expires_at - 60:
                return self._token

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.BASE_URL}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.AMADEUS_CLIENT_ID.strip(),
                        "client_secret": settings.AMADEUS_CLIENT_SECRET.strip(),
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()

                payload = response.json()
                access_token = payload.get("access_token")
                expires_in = int(payload.get("expires_in", 1800))

                if not access_token:
                    raise RuntimeError(f"Amadeus token missing in response: {payload}")

                self._token = access_token.strip()
                self._expires_at = time.time() + expires_in
                return self._token

    async def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        token = await self._ensure_token()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.BASE_URL}{path}",
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )

            if response.status_code == 401:
                # force refresh once and retry
                self._token = None
                self._expires_at = 0.0
                token = await self._ensure_token()

                response = await client.get(
                    f"{self.BASE_URL}{path}",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                )

            response.raise_for_status()
            return response.json()


amadeus_client = AmadeusClient()