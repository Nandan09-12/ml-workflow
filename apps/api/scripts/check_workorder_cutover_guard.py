from __future__ import annotations

import argparse
import asyncio
import os
import ssl
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

# Allow running as `python scripts/check_workorder_cutover_guard.py` from apps/api.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.workorder_cutover_guard import WorkorderCutoverFindings, format_cutover_report

DEFAULT_SAMPLE_LIMIT = 20

_HAS_SUBMISSIONS_TABLE_QUERY = """
SELECT to_regclass('public.submissions') IS NOT NULL AS has_submissions;
"""

_HAS_ATTACHMENTS_TABLE_QUERY = """
SELECT to_regclass('public.submission_attachments') IS NOT NULL AS has_submission_attachments;
"""

_DUPLICATE_DAILY_SUBMISSIONS_QUERY = """
SELECT
    cluster_name_normalized AS workorder_code_normalized,
    work_date,
    COUNT(*)::int AS duplicate_count
FROM submissions
GROUP BY cluster_name_normalized, work_date
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, workorder_code_normalized, work_date
LIMIT :limit;
"""

_MIXED_REGION_CODES_QUERY = """
SELECT
    cluster_name_normalized AS workorder_code_normalized,
    ARRAY_AGG(DISTINCT zone::text ORDER BY zone::text) AS zones,
    COUNT(*)::int AS row_count
FROM submissions
GROUP BY cluster_name_normalized
HAVING COUNT(DISTINCT zone) > 1
ORDER BY row_count DESC, workorder_code_normalized
LIMIT :limit;
"""

_BLANK_NORMALIZED_CODES_QUERY = """
SELECT
    id::text AS submission_id,
    cluster_name,
    cluster_name_normalized
FROM submissions
WHERE cluster_name_normalized IS NULL OR btrim(cluster_name_normalized) = ''
ORDER BY created_at, id
LIMIT :limit;
"""

_AMBIGUOUS_TOTAL_GRIDS_QUERY = """
SELECT
    cluster_name_normalized AS workorder_code_normalized,
    ARRAY_AGG(DISTINCT number_of_grids ORDER BY number_of_grids) AS legacy_number_of_grids_values,
    COUNT(*)::int AS row_count
FROM submissions
GROUP BY cluster_name_normalized
HAVING COUNT(DISTINCT number_of_grids) > 1 OR MAX(number_of_grids) <= 0
ORDER BY row_count DESC, workorder_code_normalized
LIMIT :limit;
"""

_MULTIPLE_ACTIVE_ATTACHMENTS_QUERY = """
SELECT
    submission_id::text AS submission_id,
    COUNT(*)::int AS active_count
FROM submission_attachments
WHERE is_active IS TRUE
GROUP BY submission_id
HAVING COUNT(*) > 1
ORDER BY active_count DESC, submission_id
LIMIT :limit;
"""


async def _fetch_rows(
    connection: AsyncConnection,
    query: str,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    result = await connection.execute(text(query), {"limit": limit})
    return [dict(row._mapping) for row in result]


async def _fetch_flag(
    connection: AsyncConnection,
    query: str,
    *,
    key: str,
) -> bool:
    result = await connection.execute(text(query))
    row = result.mappings().one()
    return bool(row[key])


def _build_findings(
    *,
    duplicate_daily_submissions: list[dict[str, Any]],
    mixed_region_codes: list[dict[str, Any]],
    blank_normalized_codes: list[dict[str, Any]],
    ambiguous_total_grids_by_code: list[dict[str, Any]],
    submissions_with_multiple_active_attachments: list[dict[str, Any]],
) -> WorkorderCutoverFindings:
    return WorkorderCutoverFindings(
        duplicate_daily_submissions=duplicate_daily_submissions,
        mixed_region_codes=mixed_region_codes,
        blank_normalized_codes=blank_normalized_codes,
        ambiguous_total_grids_by_code=ambiguous_total_grids_by_code,
        submissions_with_multiple_active_attachments=submissions_with_multiple_active_attachments,
    )


def _build_connect_args_from_env() -> tuple[str, dict[str, Any]]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to run cutover guard checks.")

    ssl_mode = os.getenv("DATABASE_SSL_MODE", "disable").strip().lower()
    ssl_root_cert = os.getenv("DATABASE_SSL_ROOT_CERT")

    if ssl_mode == "disable":
        return database_url, {}

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
        raise RuntimeError(
            "DATABASE_SSL_MODE must be one of: disable, require, verify-ca, verify-full."
        )

    return database_url, {"ssl": ssl_context}


async def collect_findings(*, sample_limit: int) -> WorkorderCutoverFindings:
    database_url, connect_args = _build_connect_args_from_env()
    engine = create_async_engine(
        database_url,
        connect_args=connect_args,
    )
    try:
        async with engine.connect() as connection:
            has_submissions = await _fetch_flag(
                connection,
                _HAS_SUBMISSIONS_TABLE_QUERY,
                key="has_submissions",
            )
            has_submission_attachments = await _fetch_flag(
                connection,
                _HAS_ATTACHMENTS_TABLE_QUERY,
                key="has_submission_attachments",
            )

            duplicate_daily_submissions: list[dict[str, Any]] = []
            mixed_region_codes: list[dict[str, Any]] = []
            blank_normalized_codes: list[dict[str, Any]] = []
            ambiguous_total_grids_by_code: list[dict[str, Any]] = []
            submissions_with_multiple_active_attachments: list[dict[str, Any]] = []

            if has_submissions:
                duplicate_daily_submissions = await _fetch_rows(
                    connection,
                    _DUPLICATE_DAILY_SUBMISSIONS_QUERY,
                    limit=sample_limit,
                )
                mixed_region_codes = await _fetch_rows(
                    connection,
                    _MIXED_REGION_CODES_QUERY,
                    limit=sample_limit,
                )
                blank_normalized_codes = await _fetch_rows(
                    connection,
                    _BLANK_NORMALIZED_CODES_QUERY,
                    limit=sample_limit,
                )
                ambiguous_total_grids_by_code = await _fetch_rows(
                    connection,
                    _AMBIGUOUS_TOTAL_GRIDS_QUERY,
                    limit=sample_limit,
                )
            if has_submission_attachments:
                submissions_with_multiple_active_attachments = await _fetch_rows(
                    connection,
                    _MULTIPLE_ACTIVE_ATTACHMENTS_QUERY,
                    limit=sample_limit,
                )

            return _build_findings(
                duplicate_daily_submissions=duplicate_daily_submissions,
                mixed_region_codes=mixed_region_codes,
                blank_normalized_codes=blank_normalized_codes,
                ambiguous_total_grids_by_code=ambiguous_total_grids_by_code,
                submissions_with_multiple_active_attachments=submissions_with_multiple_active_attachments,
            )
    finally:
        await engine.dispose()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-cutover migration guard for submission-only to workorders migration."
        )
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=DEFAULT_SAMPLE_LIMIT,
        help="Max number of sample rows to print for each conflict category.",
    )
    return parser.parse_args(argv)


async def _run(sample_limit: int) -> int:
    findings = await collect_findings(sample_limit=sample_limit)
    print(format_cutover_report(findings, sample_limit=sample_limit))
    return 1 if findings.has_blocking_conflicts else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(_run(sample_limit=args.sample_limit))


if __name__ == "__main__":
    raise SystemExit(main())
