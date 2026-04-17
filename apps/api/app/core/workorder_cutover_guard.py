from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkorderCutoverFindings:
    duplicate_daily_submissions: list[dict[str, Any]] = field(default_factory=list)
    mixed_region_codes: list[dict[str, Any]] = field(default_factory=list)
    blank_normalized_codes: list[dict[str, Any]] = field(default_factory=list)
    ambiguous_total_grids_by_code: list[dict[str, Any]] = field(default_factory=list)
    submissions_with_multiple_active_attachments: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_blocking_conflicts(self) -> bool:
        return self.blocking_conflict_count > 0

    @property
    def blocking_conflict_count(self) -> int:
        return sum(
            1
            for items in (
                self.duplicate_daily_submissions,
                self.mixed_region_codes,
                self.blank_normalized_codes,
                self.ambiguous_total_grids_by_code,
                self.submissions_with_multiple_active_attachments,
            )
            if items
        )


def format_cutover_report(findings: WorkorderCutoverFindings, *, sample_limit: int) -> str:
    lines: list[str] = []
    lines.append("Workorder cutover preflight report")
    lines.append("--------------------------------")
    lines.append(f"Sample limit per conflict query: {sample_limit}")

    if not findings.has_blocking_conflicts:
        lines.append("No blocking conflicts found.")
        lines.append("Environment is safe to proceed with migration cutover.")
        return "\n".join(lines)

    lines.append("Blocking conflicts detected.")

    if findings.duplicate_daily_submissions:
        lines.append("")
        lines.append("1) duplicate daily submissions for the same normalized workorder and date")
        for row in findings.duplicate_daily_submissions:
            lines.append(
                " - code={code}, work_date={work_date}, duplicate_count={count}".format(
                    code=row.get("workorder_code_normalized"),
                    work_date=row.get("work_date"),
                    count=row.get("duplicate_count"),
                )
            )

    if findings.mixed_region_codes:
        lines.append("")
        lines.append("2) mixed regions for the same normalized code")
        for row in findings.mixed_region_codes:
            lines.append(
                " - code={code}, zones={zones}, row_count={count}".format(
                    code=row.get("workorder_code_normalized"),
                    zones=row.get("zones"),
                    count=row.get("row_count"),
                )
            )

    if findings.blank_normalized_codes:
        lines.append("")
        lines.append("3) blank normalized workorder codes")
        for row in findings.blank_normalized_codes:
            lines.append(
                " - submission_id={submission_id}, cluster_name={cluster_name}, normalized={normalized}".format(
                    submission_id=row.get("submission_id"),
                    cluster_name=row.get("cluster_name"),
                    normalized=row.get("cluster_name_normalized"),
                )
            )

    if findings.ambiguous_total_grids_by_code:
        lines.append("")
        lines.append("4) ambiguous legacy total_grids candidates")
        for row in findings.ambiguous_total_grids_by_code:
            lines.append(
                " - code={code}, legacy_number_of_grids_values={values}, row_count={count}".format(
                    code=row.get("workorder_code_normalized"),
                    values=row.get("legacy_number_of_grids_values"),
                    count=row.get("row_count"),
                )
            )

    if findings.submissions_with_multiple_active_attachments:
        lines.append("")
        lines.append("5) multiple active attachments for a single submission")
        for row in findings.submissions_with_multiple_active_attachments:
            lines.append(
                " - submission_id={submission_id}, active_count={count}".format(
                    submission_id=row.get("submission_id"),
                    count=row.get("active_count"),
                )
            )

    lines.append("")
    lines.append("Resolve all blocking conflicts before production cutover.")
    return "\n".join(lines)
