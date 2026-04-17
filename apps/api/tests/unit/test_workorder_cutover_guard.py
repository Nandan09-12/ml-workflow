from app.core.workorder_cutover_guard import WorkorderCutoverFindings, format_cutover_report


def test_findings_are_clean_when_no_conflicts_exist() -> None:
    findings = WorkorderCutoverFindings()

    assert findings.has_blocking_conflicts is False
    assert findings.blocking_conflict_count == 0


def test_findings_are_blocking_when_duplicate_daily_submissions_exist() -> None:
    findings = WorkorderCutoverFindings(
        duplicate_daily_submissions=[
            {
                "workorder_code_normalized": "WO123",
                "work_date": "2026-04-15",
                "duplicate_count": 2,
            }
        ]
    )

    assert findings.has_blocking_conflicts is True
    assert findings.blocking_conflict_count == 1


def test_findings_are_blocking_when_mixed_region_codes_exist() -> None:
    findings = WorkorderCutoverFindings(
        mixed_region_codes=[
            {
                "workorder_code_normalized": "WO123",
                "zones": ["CENTRAL", "NORTHEAST"],
                "row_count": 3,
            }
        ]
    )

    assert findings.has_blocking_conflicts is True
    assert findings.blocking_conflict_count == 1


def test_findings_are_blocking_when_blank_normalized_codes_exist() -> None:
    findings = WorkorderCutoverFindings(
        blank_normalized_codes=[
            {
                "submission_id": "f6fc4dc3-4f8f-473f-befe-b72846253e9f",
                "cluster_name": "Raw",
                "cluster_name_normalized": "",
            }
        ]
    )

    assert findings.has_blocking_conflicts is True
    assert findings.blocking_conflict_count == 1


def test_findings_are_blocking_when_ambiguous_legacy_total_grids_exist() -> None:
    findings = WorkorderCutoverFindings(
        ambiguous_total_grids_by_code=[
            {
                "workorder_code_normalized": "WO123",
                "legacy_number_of_grids_values": [20, 24],
                "row_count": 2,
            }
        ]
    )

    assert findings.has_blocking_conflicts is True
    assert findings.blocking_conflict_count == 1


def test_findings_are_blocking_when_multiple_active_attachments_exist() -> None:
    findings = WorkorderCutoverFindings(
        submissions_with_multiple_active_attachments=[
            {
                "submission_id": "7f0baaf4-40d0-4b00-8f9c-bf375ccb5194",
                "active_count": 2,
            }
        ]
    )

    assert findings.has_blocking_conflicts is True
    assert findings.blocking_conflict_count == 1


def test_report_formatting_for_clean_state() -> None:
    findings = WorkorderCutoverFindings()

    report = format_cutover_report(findings, sample_limit=20)

    assert "No blocking conflicts found." in report
    assert "safe to proceed" in report


def test_report_formatting_includes_all_conflict_sections() -> None:
    findings = WorkorderCutoverFindings(
        duplicate_daily_submissions=[
            {
                "workorder_code_normalized": "WO123",
                "work_date": "2026-04-15",
                "duplicate_count": 2,
            }
        ],
        mixed_region_codes=[
            {
                "workorder_code_normalized": "WO999",
                "zones": ["CENTRAL", "NORTHEAST"],
                "row_count": 4,
            }
        ],
        blank_normalized_codes=[
            {
                "submission_id": "f6fc4dc3-4f8f-473f-befe-b72846253e9f",
                "cluster_name": "Raw",
                "cluster_name_normalized": "",
            }
        ],
        ambiguous_total_grids_by_code=[
            {
                "workorder_code_normalized": "WO124",
                "legacy_number_of_grids_values": [18, 19],
                "row_count": 2,
            }
        ],
        submissions_with_multiple_active_attachments=[
            {
                "submission_id": "7f0baaf4-40d0-4b00-8f9c-bf375ccb5194",
                "active_count": 3,
            }
        ],
    )

    report = format_cutover_report(findings, sample_limit=20)

    assert "duplicate daily submissions" in report
    assert "mixed regions for the same normalized code" in report
    assert "blank normalized workorder codes" in report
    assert "ambiguous legacy total_grids candidates" in report
    assert "multiple active attachments" in report
    assert "Blocking conflicts detected" in report
