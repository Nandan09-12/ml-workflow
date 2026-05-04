import json
import ssl

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import Settings
from app.core.errors import http_exception_handler


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }
    )


def test_settings_require_ssl_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
            database_ssl_mode="disable",
        )


def test_settings_build_connect_args_for_ssl_require_mode() -> None:
    settings = Settings(
        app_env="development",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        database_ssl_mode="require",
    )

    connect_args = settings.database_connect_args()

    assert "ssl" in connect_args
    ssl_ctx = connect_args["ssl"]
    assert isinstance(ssl_ctx, ssl.SSLContext)
    assert ssl_ctx.verify_mode == ssl.CERT_NONE
    assert ssl_ctx.check_hostname is False


def test_settings_build_connect_args_for_ssl_verify_full_mode() -> None:
    settings = Settings(
        app_env="production",
        debug=False,
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        database_ssl_mode="verify-full",
    )

    connect_args = settings.database_connect_args()

    assert "ssl" in connect_args
    ssl_ctx = connect_args["ssl"]
    assert isinstance(ssl_ctx, ssl.SSLContext)
    assert ssl_ctx.verify_mode == ssl.CERT_REQUIRED
    assert ssl_ctx.check_hostname is True


def test_settings_accept_release_style_debug_strings() -> None:
    settings = Settings(
        app_env="development",
        debug="release",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        database_ssl_mode="require",
    )

    assert settings.debug is False


def test_settings_default_debug_tracks_development_like_envs() -> None:
    dev_settings = Settings(
        app_env="development",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        database_ssl_mode="require",
    )
    test_settings = Settings(
        app_env="test",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        database_ssl_mode="require",
    )

    assert dev_settings.debug is True
    assert test_settings.debug is True


def test_settings_reject_debug_in_production_like_envs() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="staging",
            debug=True,
            database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
            database_ssl_mode="require",
        )


async def test_http_exception_400_maps_to_bad_request_code() -> None:
    response = await http_exception_handler(_request(), HTTPException(status_code=400, detail="Bad request."))
    payload = json.loads(response.body)

    assert response.status_code == 400
    assert payload["error"]["code"] == "BAD_REQUEST"


async def test_http_exception_409_maps_to_conflict_code() -> None:
    response = await http_exception_handler(_request(), HTTPException(status_code=409, detail="Conflict."))
    payload = json.loads(response.body)

    assert response.status_code == 409
    assert payload["error"]["code"] == "CONFLICT"
