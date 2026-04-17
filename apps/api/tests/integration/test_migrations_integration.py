import asyncio
import os
import ssl
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command
from app.core.config import get_settings

pytestmark = pytest.mark.integration

_API_ROOT = Path(__file__).resolve().parents[2]
_ALEMBIC_INI = _API_ROOT / "alembic.ini"


@dataclass(frozen=True)
class MigrationDatabase:
    admin_url: str
    database_url: str
    database_name: str


def _integration_database_url() -> str:
    database_url = os.getenv("INTEGRATION_DATABASE_URL")
    if not database_url:
        pytest.skip(
            "Migration integration tests require INTEGRATION_DATABASE_URL "
            "and RUN_INTEGRATION_TESTS=1."
        )
    return database_url


def _integration_connect_args() -> dict[str, object]:
    ssl_mode = (
        os.getenv("INTEGRATION_DATABASE_SSL_MODE", "disable").strip().lower()
    )
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
            "INTEGRATION_DATABASE_SSL_MODE must be one of: disable, require, "
            "verify-ca, verify-full"
        )
    return {"ssl": ssl_context}


def _alembic_config() -> Config:
    config = Config(str(_ALEMBIC_INI))
    config.set_main_option("script_location", str(_API_ROOT / "alembic"))
    return config


async def _alembic_upgrade(revision: str) -> None:
    get_settings.cache_clear()
    await asyncio.to_thread(command.upgrade, _alembic_config(), revision)


async def _alembic_downgrade(revision: str) -> None:
    get_settings.cache_clear()
    await asyncio.to_thread(command.downgrade, _alembic_config(), revision)


def _make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        connect_args=_integration_connect_args(),
    )


async def _scalar(database_url: str, sql: str, **params: object) -> object:
    engine = _make_engine(database_url)
    try:
        async with engine.connect() as conn:
            return await conn.scalar(text(sql), params)
    finally:
        await engine.dispose()


async def _execute(database_url: str, sql: str, **params: object) -> None:
    engine = _make_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text(sql), params)
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def migration_database() -> AsyncGenerator[MigrationDatabase, None]:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip(
            "Migration integration tests require RUN_INTEGRATION_TESTS=1 "
            "and INTEGRATION_DATABASE_URL."
        )

    integration_url = make_url(_integration_database_url())
    database_name = f"it_migration_{uuid.uuid4().hex[:10]}"
    admin_url = integration_url.render_as_string(hide_password=False)
    database_url = integration_url.set(database=database_name).render_as_string(
        hide_password=False
    )

    old_database_url = os.environ.get("DATABASE_URL")
    old_database_ssl_mode = os.environ.get("DATABASE_SSL_MODE")
    os.environ["DATABASE_URL"] = database_url
    os.environ["DATABASE_SSL_MODE"] = os.getenv(
        "INTEGRATION_DATABASE_SSL_MODE",
        "disable",
    )
    get_settings.cache_clear()

    admin_engine = create_async_engine(
        admin_url,
        connect_args=_integration_connect_args(),
        isolation_level="AUTOCOMMIT",
    )

    try:
        async with admin_engine.connect() as conn:
            await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
        yield MigrationDatabase(
            admin_url=admin_url,
            database_url=database_url,
            database_name=database_name,
        )
    finally:
        async with admin_engine.connect() as conn:
            await conn.execute(
                text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')
            )
        await admin_engine.dispose()

        if old_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old_database_url

        if old_database_ssl_mode is None:
            os.environ.pop("DATABASE_SSL_MODE", None)
        else:
            os.environ["DATABASE_SSL_MODE"] = old_database_ssl_mode

        get_settings.cache_clear()


async def test_migrate_up_down_smoke_covering_new_schema_and_constraints(
    migration_database: MigrationDatabase,
) -> None:
    await _alembic_upgrade("head")

    assert await _scalar(
        migration_database.database_url,
        "SELECT to_regclass('workorders')::text",
    ) == "workorders"
    assert await _scalar(
        migration_database.database_url,
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'submissions'
          AND column_name = 'workorder_id'
        """,
    ) == 1
    assert await _scalar(
        migration_database.database_url,
        """
        SELECT COUNT(*)
        FROM pg_indexes
        WHERE tablename = 'submission_attachments'
          AND indexname = 'uq_submission_attachments_one_active_per_submission'
        """,
    ) == 1

    await _alembic_downgrade("0001_init_core_tables")

    assert await _scalar(
        migration_database.database_url,
        "SELECT to_regclass('workorders')::text",
    ) is None
    assert await _scalar(
        migration_database.database_url,
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'submissions'
                    AND column_name IN (
                            'zone',
                            'cluster_name',
                            'cluster_name_normalized',
                            'number_of_grids',
                            'pending_grids'
                    )
        """,
    ) == 5
    assert await _scalar(
        migration_database.database_url,
        """
        SELECT COUNT(*)
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'submission_status_enum'
          AND e.enumlabel IN ('ONGOING', 'COMPLETED')
        """,
    ) == 2

    await _alembic_upgrade("head")
    assert await _scalar(
        migration_database.database_url,
        "SELECT to_regclass('workorders')::text",
    ) == "workorders"


async def test_data_backfill_correctness_from_legacy_submissions(
    migration_database: MigrationDatabase,
) -> None:
    await _alembic_downgrade("base")
    await _alembic_upgrade("0001_init_core_tables")

    owner_id = uuid.uuid4()
    auth_user_id = uuid.uuid4()
    now = datetime.now(UTC)
    created_at = now

    await _execute(
        migration_database.database_url,
        """
        INSERT INTO app_users (
            id,
            auth_user_id,
            full_name,
            email,
            requested_role,
            approved_role,
            account_status,
            approved_at,
            created_at,
            updated_at
        ) VALUES (
            :id,
            :auth_user_id,
            'Legacy Owner',
            'legacy-owner@example.com',
            'DRIVE_TESTER',
            'DRIVE_TESTER',
            'APPROVED',
            :approved_at,
            :created_at,
            :updated_at
        )
        """,
        id=str(owner_id),
        auth_user_id=str(auth_user_id),
        approved_at=created_at,
        created_at=created_at,
        updated_at=created_at,
    )

    legacy_rows = [
        {
            "id": str(uuid.uuid4()),
            "client_generated_id": str(uuid.uuid4()),
            "work_date": date(2026, 4, 14),
            "cluster_name": "Alpha Cluster",
            "cluster_name_normalized": "ALPHA CLUSTER",
            "zone": "NORTHEAST",
            "status": "ONGOING",
            "number_of_grids": 10,
            "skipped_grids": 1,
            "pending_grids": 6,
            "completed_grids": 3,
            "completed_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "client_generated_id": str(uuid.uuid4()),
            "work_date": date(2026, 4, 15),
            "cluster_name": "Alpha Cluster",
            "cluster_name_normalized": "ALPHA CLUSTER",
            "zone": "NORTHEAST",
            "status": "ONGOING",
            "number_of_grids": 10,
            "skipped_grids": 0,
            "pending_grids": 8,
            "completed_grids": 2,
            "completed_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "client_generated_id": str(uuid.uuid4()),
            "work_date": date(2026, 4, 14),
            "cluster_name": "Beta Cluster",
            "cluster_name_normalized": "BETA CLUSTER",
            "zone": "CENTRAL",
            "status": "COMPLETED",
            "number_of_grids": 10,
            "skipped_grids": 1,
            "pending_grids": 0,
            "completed_grids": 9,
            "completed_at": created_at,
        },
    ]

    for row in legacy_rows:
        await _execute(
            migration_database.database_url,
            """
            INSERT INTO submissions (
                id,
                client_generated_id,
                owner_user_id,
                submitter_name_snapshot,
                submitter_email_snapshot,
                zone,
                work_date,
                shift,
                team_number,
                ticket_number,
                cluster_name,
                cluster_name_normalized,
                number_of_grids,
                skipped_grids,
                force_tested_grids,
                pending_grids,
                completed_grids,
                status,
                created_at,
                created_by_user_id,
                updated_at,
                updated_by_user_id,
                completed_at,
                completed_by_user_id,
                reopened_at,
                reopened_by_user_id,
                version_number
            ) VALUES (
                :id,
                :client_generated_id,
                :owner_user_id,
                'Legacy Owner',
                'legacy-owner@example.com',
                :zone,
                :work_date,
                'AM',
                '11',
                'TKT-1',
                :cluster_name,
                :cluster_name_normalized,
                :number_of_grids,
                :skipped_grids,
                0,
                :pending_grids,
                :completed_grids,
                :status,
                :created_at,
                :created_by_user_id,
                :updated_at,
                :updated_by_user_id,
                :completed_at,
                :completed_by_user_id,
                NULL,
                NULL,
                1
            )
            """,
            owner_user_id=str(owner_id),
            created_at=created_at,
            created_by_user_id=str(owner_id),
            updated_at=created_at,
            updated_by_user_id=str(owner_id),
            completed_by_user_id=(str(owner_id) if row["completed_at"] else None),
            **row,
        )

    await _alembic_upgrade("head")

    engine = _make_engine(migration_database.database_url)
    try:
        async with engine.connect() as conn:
            workorders = list(
                (
                    await conn.execute(
                        text(
                            """
                            SELECT
                                workorder_code_normalized,
                                region::text,
                                total_grids,
                                status::text
                            FROM workorders
                            ORDER BY workorder_code_normalized
                            """
                        )
                    )
                ).all()
            )
            alpha_children = list(
                (
                    await conn.execute(
                        text(
                            """
                            SELECT
                                s.work_date,
                                w.workorder_code_normalized,
                                w.status::text,
                                s.started_at,
                                s.workorder_id
                            FROM submissions AS s
                            JOIN workorders AS w ON w.id = s.workorder_id
                            WHERE w.workorder_code_normalized = 'ALPHA CLUSTER'
                            ORDER BY s.work_date
                            """
                        )
                    )
                ).all()
            )
            beta_parent = (
                await conn.execute(
                    text(
                        """
                        SELECT
                            w.workorder_code_normalized,
                            w.region::text,
                            w.status::text,
                            s.ended_at
                        FROM submissions AS s
                        JOIN workorders AS w ON w.id = s.workorder_id
                        WHERE w.workorder_code_normalized = 'BETA CLUSTER'
                        """
                    )
                )
            ).one()
    finally:
        await engine.dispose()

    assert workorders == [
        ("ALPHA CLUSTER", "NE_UP", 10, "ACTIVE"),
        ("BETA CLUSTER", "CENTRAL", 10, "COMPLETED"),
    ]
    assert len(alpha_children) == 2
    assert alpha_children[0][1] == "ALPHA CLUSTER"
    assert alpha_children[0][2] == "ACTIVE"
    assert alpha_children[0][3] is not None
    assert alpha_children[0][4] == alpha_children[1][4]
    assert beta_parent[0] == "BETA CLUSTER"
    assert beta_parent[1] == "CENTRAL"
    assert beta_parent[2] == "COMPLETED"
    assert beta_parent[3] is not None


async def test_uniqueness_and_fk_guarantees_after_head_migration(
    migration_database: MigrationDatabase,
) -> None:
    await _alembic_downgrade("base")
    await _alembic_upgrade("head")

    owner_id = uuid.uuid4()
    auth_user_id = uuid.uuid4()
    workorder_id = uuid.uuid4()
    submission_id = uuid.uuid4()
    now = datetime.now(UTC)

    await _execute(
        migration_database.database_url,
        """
        INSERT INTO app_users (
            id,
            auth_user_id,
            full_name,
            email,
            requested_role,
            approved_role,
            account_status,
            approved_at,
            created_at,
            updated_at
        ) VALUES (
            :id,
            :auth_user_id,
            'Constraint Owner',
            'constraint-owner@example.com',
            'DRIVE_TESTER',
            'DRIVE_TESTER',
            'APPROVED',
            :approved_at,
            :created_at,
            :updated_at
        )
        """,
        id=str(owner_id),
        auth_user_id=str(auth_user_id),
        approved_at=now,
        created_at=now,
        updated_at=now,
    )
    await _execute(
        migration_database.database_url,
        """
        INSERT INTO workorders (
            id,
            workorder_code,
            workorder_code_normalized,
            region,
            total_grids,
            status,
            created_at,
            created_by_user_id,
            updated_at,
            updated_by_user_id,
            completed_at,
            completed_by_user_id
        ) VALUES (
            :id,
            'WO-UNIQUENESS',
            'WO-UNIQUENESS',
            'NE_UP',
            10,
            'ACTIVE',
            :created_at,
            :owner_id,
            :updated_at,
            :owner_id,
            NULL,
            NULL
        )
        """,
        id=str(workorder_id),
        created_at=now,
        updated_at=now,
        owner_id=str(owner_id),
    )
    await _execute(
        migration_database.database_url,
        """
        INSERT INTO submissions (
            id,
            client_generated_id,
            workorder_id,
            owner_user_id,
            submitter_name_snapshot,
            submitter_email_snapshot,
            work_date,
            shift,
            team_number,
            ticket_number,
            skipped_grids,
            force_tested_grids,
            completed_grids,
            status,
            started_at,
            ended_at,
            created_at,
            created_by_user_id,
            updated_at,
            updated_by_user_id,
            completed_at,
            completed_by_user_id,
            reopened_at,
            reopened_by_user_id,
            version_number
        ) VALUES (
            :id,
            :client_generated_id,
            :workorder_id,
            :owner_user_id,
            'Constraint Owner',
            'constraint-owner@example.com',
            '2026-04-14',
            'AM',
            '11',
            'TKT-1',
            0,
            0,
            0,
            'IN_PROGRESS',
            :started_at,
            NULL,
            :created_at,
            :owner_user_id,
            :updated_at,
            :owner_user_id,
            NULL,
            NULL,
            NULL,
            NULL,
            1
        )
        """,
        id=str(submission_id),
        client_generated_id=str(uuid.uuid4()),
        workorder_id=str(workorder_id),
        owner_user_id=str(owner_id),
        started_at=now,
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(IntegrityError):
        await _execute(
            migration_database.database_url,
            """
            INSERT INTO workorders (
                id,
                workorder_code,
                workorder_code_normalized,
                region,
                total_grids,
                status,
                created_at,
                created_by_user_id,
                updated_at,
                updated_by_user_id
            ) VALUES (
                :id,
                'WO-DUP-2',
                'WO-UNIQUENESS',
                'NE_UP',
                10,
                'ACTIVE',
                :created_at,
                :owner_id,
                :updated_at,
                :owner_id
            )
            """,
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            owner_id=str(owner_id),
        )

    with pytest.raises(IntegrityError):
        await _execute(
            migration_database.database_url,
            """
            INSERT INTO submissions (
                id,
                client_generated_id,
                workorder_id,
                owner_user_id,
                submitter_name_snapshot,
                submitter_email_snapshot,
                work_date,
                shift,
                team_number,
                ticket_number,
                skipped_grids,
                force_tested_grids,
                completed_grids,
                status,
                started_at,
                created_at,
                created_by_user_id,
                updated_at,
                updated_by_user_id,
                version_number
            ) VALUES (
                :id,
                :client_generated_id,
                :workorder_id,
                :owner_user_id,
                'Constraint Owner',
                'constraint-owner@example.com',
                '2026-04-14',
                'PM',
                '22',
                'TKT-2',
                0,
                0,
                0,
                'IN_PROGRESS',
                :started_at,
                :created_at,
                :owner_user_id,
                :updated_at,
                :owner_user_id,
                1
            )
            """,
            id=str(uuid.uuid4()),
            client_generated_id=str(uuid.uuid4()),
            workorder_id=str(workorder_id),
            owner_user_id=str(owner_id),
            started_at=now,
            created_at=now,
            updated_at=now,
        )

    with pytest.raises(IntegrityError):
        await _execute(
            migration_database.database_url,
            """
            INSERT INTO submissions (
                id,
                client_generated_id,
                workorder_id,
                owner_user_id,
                submitter_name_snapshot,
                submitter_email_snapshot,
                work_date,
                shift,
                team_number,
                ticket_number,
                skipped_grids,
                force_tested_grids,
                completed_grids,
                status,
                started_at,
                created_at,
                created_by_user_id,
                updated_at,
                updated_by_user_id,
                version_number
            ) VALUES (
                :id,
                :client_generated_id,
                :workorder_id,
                :owner_user_id,
                'Constraint Owner',
                'constraint-owner@example.com',
                '2026-04-15',
                'AM',
                '11',
                'TKT-3',
                0,
                0,
                0,
                'IN_PROGRESS',
                :started_at,
                :created_at,
                :owner_user_id,
                :updated_at,
                :owner_user_id,
                1
            )
            """,
            id=str(uuid.uuid4()),
            client_generated_id=str(uuid.uuid4()),
            workorder_id=str(uuid.uuid4()),
            owner_user_id=str(owner_id),
            started_at=now,
            created_at=now,
            updated_at=now,
        )

    await _execute(
        migration_database.database_url,
        """
        INSERT INTO submission_attachments (
            id,
            submission_id,
            file_name,
            bucket_name,
            object_path,
            mime_type,
            file_extension,
            file_size_bytes,
            uploaded_by_user_id,
            uploaded_at,
            is_active
        ) VALUES (
            :id,
            :submission_id,
            'file-1.csv',
            'attachments',
            :object_path,
            'text/csv',
            '.csv',
            100,
            :owner_user_id,
            :uploaded_at,
            TRUE
        )
        """,
        id=str(uuid.uuid4()),
        submission_id=str(submission_id),
        object_path=f"{submission_id}/file-1.csv",
        owner_user_id=str(owner_id),
        uploaded_at=now,
    )

    with pytest.raises(IntegrityError):
        await _execute(
            migration_database.database_url,
            """
            INSERT INTO submission_attachments (
                id,
                submission_id,
                file_name,
                bucket_name,
                object_path,
                mime_type,
                file_extension,
                file_size_bytes,
                uploaded_by_user_id,
                uploaded_at,
                is_active
            ) VALUES (
                :id,
                :submission_id,
                'file-2.csv',
                'attachments',
                :object_path,
                'text/csv',
                '.csv',
                100,
                :owner_user_id,
                :uploaded_at,
                TRUE
            )
            """,
            id=str(uuid.uuid4()),
            submission_id=str(submission_id),
            object_path=f"{submission_id}/file-2.csv",
            owner_user_id=str(owner_id),
            uploaded_at=now,
        )
