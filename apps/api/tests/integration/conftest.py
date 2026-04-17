import os
import ssl
import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import app_user as _app_user  # noqa: F401
from app.models import submission as _submission  # noqa: F401
from app.models import submission_attachment as _submission_attachment  # noqa: F401
from app.models import submission_audit_log as _submission_audit_log  # noqa: F401
from app.models import user_approval_audit as _user_approval_audit  # noqa: F401
from app.models import workorder as _workorder  # noqa: F401

RUN_INTEGRATION_TESTS = os.getenv("RUN_INTEGRATION_TESTS") == "1"
INTEGRATION_DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")


def _integration_connect_args() -> dict[str, object]:
    ssl_mode = os.getenv("INTEGRATION_DATABASE_SSL_MODE", "disable").strip().lower()
    ssl_root_cert = os.getenv("INTEGRATION_DATABASE_SSL_ROOT_CERT")
    if ssl_mode == "disable":
        return {}

    ssl_context = ssl.create_default_context(cafile=ssl_root_cert)
    if ssl_mode == "require":
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    elif ssl_mode == "verify-ca":
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    elif ssl_mode == "verify-full":
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        raise ValueError(
            "INTEGRATION_DATABASE_SSL_MODE must be one of: disable, require, verify-ca, verify-full"
        )
    return {"ssl": ssl_context}

def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if RUN_INTEGRATION_TESTS and INTEGRATION_DATABASE_URL:
        return
    reason = (
        "Integration tests are disabled. Set RUN_INTEGRATION_TESTS=1 "
        "and INTEGRATION_DATABASE_URL to enable."
    )
    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        node_id = item.nodeid.replace("\\", "/")
        if "tests/integration/" in node_id or "integration" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture
async def integration_session() -> AsyncGenerator[AsyncSession, None]:
    if not RUN_INTEGRATION_TESTS or not INTEGRATION_DATABASE_URL:
        pytest.skip(
            "Integration tests require RUN_INTEGRATION_TESTS=1 and INTEGRATION_DATABASE_URL."
        )

    schema_name = f"it_{uuid.uuid4().hex[:10]}"
    connect_args = _integration_connect_args()
    admin_engine = create_async_engine(
        INTEGRATION_DATABASE_URL,
        connect_args=connect_args,
    )
    test_connect_args = dict(connect_args)
    test_connect_args["server_settings"] = {"search_path": schema_name}
    test_engine = create_async_engine(
        INTEGRATION_DATABASE_URL,
        connect_args=test_connect_args,
    )
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with admin_engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with admin_engine.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    await test_engine.dispose()
    await admin_engine.dispose()
