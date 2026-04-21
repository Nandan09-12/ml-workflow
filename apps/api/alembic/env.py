import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from app.models import (
    AppUser,
    ExpenseEntry,
    MileageEntry,
    Submission,
    SubmissionAttachment,
    SubmissionAuditLog,
    UserApprovalAudit,
    Workorder,
)

# Keep model imports explicit so autogenerate sees metadata for all tables.
_ = (
    AppUser,
    ExpenseEntry,
    MileageEntry,
    Submission,
    SubmissionAttachment,
    SubmissionAuditLog,
    UserApprovalAudit,
    Workorder,
)

config = context.config
settings = get_settings()
# NOTE: Do NOT use config.set_main_option here. ConfigParser treats % as
# interpolation syntax, which breaks URL-encoded passwords (for example %40 for @).
# Pass settings.database_url directly to the engine instead.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
        connect_args=settings.database_connect_args(),
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
