from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class SupabaseJWTVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cached_jwks: dict[str, Any] | None = None

    async def verify(self, token: str) -> dict[str, Any]:
        if self._settings.resolved_supabase_jwks_url is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWKS URL is not configured.",
            )

        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token header does not include kid.",
            )

        jwk_key = await self._get_key(kid)
        try:
            payload = jwt.decode(
                token,
                jwk_key,
                algorithms=["RS256"],
                audience=self._settings.supabase_jwt_audience,
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            ) from exc

        return payload

    async def _get_key(self, kid: str) -> dict[str, Any]:
        jwks = await self._get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT signing key not found.",
        )

    async def _get_jwks(self) -> dict[str, Any]:
        if self._cached_jwks is not None:
            return self._cached_jwks

        assert self._settings.resolved_supabase_jwks_url is not None
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._settings.resolved_supabase_jwks_url)
            response.raise_for_status()
            self._cached_jwks = response.json()
            return self._cached_jwks


def get_jwt_verifier(
    settings: Settings = Depends(get_settings),
) -> SupabaseJWTVerifier:
    return SupabaseJWTVerifier(settings=settings)


async def get_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    return credentials.credentials


async def get_current_auth_payload(
    token: str = Depends(get_access_token),
    verifier: SupabaseJWTVerifier = Depends(get_jwt_verifier),
) -> dict[str, Any]:
    return await verifier.verify(token)


async def get_optional_auth_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: SupabaseJWTVerifier = Depends(get_jwt_verifier),
) -> dict[str, Any] | None:
    if credentials is None:
        return None
    return await verifier.verify(credentials.credentials)
