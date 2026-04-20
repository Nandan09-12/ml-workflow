import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import SupabaseJWTVerifier


@pytest.mark.asyncio
async def test_verify_uses_signing_key_algorithm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = SupabaseJWTVerifier(
        Settings(
            supabase_url="https://example.supabase.co",
            supabase_jwt_audience="authenticated",
        )
    )

    monkeypatch.setattr(
        "app.core.security.jwt.get_unverified_header",
        lambda _: {"kid": "kid-1", "alg": "ES256"},
    )

    decode_calls: list[dict[str, object]] = []

    def fake_decode(
        token: str,
        key: dict[str, str],
        algorithms: list[str],
        audience: str,
    ) -> dict[str, str]:
        decode_calls.append(
            {
                "token": token,
                "key": key,
                "algorithms": algorithms,
                "audience": audience,
            }
        )
        return {"sub": "user-1", "email": "user@example.com"}

    monkeypatch.setattr("app.core.security.jwt.decode", fake_decode)

    async def fake_get_key(_: str) -> dict[str, str]:
        return {"kid": "kid-1", "alg": "ES256"}

    monkeypatch.setattr(verifier, "_get_key", fake_get_key)

    payload = await verifier.verify("token-value")

    assert payload["sub"] == "user-1"
    assert decode_calls[0]["algorithms"] == ["ES256"]


@pytest.mark.asyncio
async def test_verify_rejects_header_key_algorithm_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = SupabaseJWTVerifier(
        Settings(
            supabase_url="https://example.supabase.co",
            supabase_jwt_audience="authenticated",
        )
    )

    monkeypatch.setattr(
        "app.core.security.jwt.get_unverified_header",
        lambda _: {"kid": "kid-1", "alg": "ES256"},
    )

    async def fake_get_key(_: str) -> dict[str, str]:
        return {"kid": "kid-1", "alg": "RS256"}

    monkeypatch.setattr(verifier, "_get_key", fake_get_key)

    with pytest.raises(HTTPException) as exc:
        await verifier.verify("token-value")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token algorithm does not match signing key."
