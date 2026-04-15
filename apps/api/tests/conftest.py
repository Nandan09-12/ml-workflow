import uuid
from collections.abc import Generator
from typing import Any

import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()  # loads apps/api/.env when pytest is run from apps/api/

os.environ["DEBUG"] = "true"
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_SSL_MODE", "disable")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/postgres",
)

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides = {}
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}


@pytest.fixture
def auth_payload_drive_tester() -> dict[str, Any]:
    return {
        "sub": str(uuid.uuid4()),
        "email": "tester@example.com",
        "role": "authenticated",
    }


@pytest.fixture
def auth_payload_admin() -> dict[str, Any]:
    return {
        "sub": str(uuid.uuid4()),
        "email": "admin@example.com",
        "role": "authenticated",
    }


@pytest.fixture
def auth_payload_pending() -> dict[str, Any]:
    return {
        "sub": str(uuid.uuid4()),
        "email": "pending@example.com",
        "role": "authenticated",
    }
