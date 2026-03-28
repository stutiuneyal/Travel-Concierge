import os
from typing import Any, Dict, Optional

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from jwt import PyJWKClient

load_dotenv()

SUPABASE_ISSUER = os.getenv("SUPABASE_ISSUER")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")

if not SUPABASE_ISSUER or not SUPABASE_JWKS_URL:
    raise RuntimeError("SUPABASE_ISSUER and SUPABASE_JWKS_URL must be set")

_jwk_client: Optional[PyJWKClient] = None


def get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(SUPABASE_JWKS_URL)
    return _jwk_client


def extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization[len("Bearer "):].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")

    return token


def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    try:
        signing_key = get_jwk_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            issuer=SUPABASE_ISSUER,
            options={"verify_aud": False},
        )
        print("payload ",payload)
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = extract_bearer_token(authorization)
    payload = verify_supabase_jwt(token)

    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {
        "user_id": user_id,
        "email": email,
        "claims": payload,
    }