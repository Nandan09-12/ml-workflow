# Workorder Migration Strategy And Rollback Plan

## Scope Freeze
This plan freezes the migration path for moving from legacy submission-only semantics to:
- parent `workorders`
- child daily `submissions`

The scope in this wave is split into two DB-only revisions:
- `0002_workorders_parent_daily`
  - bridge migration for workorder parent creation, FK backfill, uniqueness, and attachment guardrails
- `0003_finalize_submission_schema`
  - final cleanup migration for the `submissions` table so column names and enums match the locked docs

## Preconditions
1. Existing Alembic revisions remain immutable (`0001_init_core_tables.py` is not edited).
2. Pre-cutover guard passes:
   - `python scripts/check_workorder_cutover_guard.py`
3. A fresh logical backup/snapshot exists for the target environment immediately before migration.
4. Do not apply `0003_finalize_submission_schema` until the backend submission contract has also been switched off legacy `zone` / `cluster_name` / `number_of_grids` fields.

## Forward Migration Order
### Revision `0002_workorders_parent_daily`
1. Add `workorder_status_enum`.
2. Add `region_enum` with:
   - `NE_UP`
   - `CENTRAL`
   - `SOUTH_FLORIDA`
3. Create `workorders` with:
   - `workorder_code`
   - `workorder_code_normalized`
   - `region`
   - `total_grids`
   - `status`
   - audit timestamps and audit user references
4. Add global uniqueness on `workorders.workorder_code_normalized`.
5. Add nullable `submissions.workorder_id`.
6. Backfill `workorders` from legacy `submissions` using:
   - `submissions.cluster_name -> workorders.workorder_code`
   - `submissions.cluster_name_normalized -> workorders.workorder_code_normalized`
   - legacy `submissions.zone` mapped to new `workorders.region`
7. Backfill `submissions.workorder_id` from normalized code mapping.
8. Add FK and set `submissions.workorder_id` to `NOT NULL`.
9. Add `UNIQUE (workorder_id, work_date)`.
10. Drop legacy uniqueness on `(owner_user_id, work_date, shift, cluster_name_normalized)`.
11. Verify/add non-negative submission grid constraints for daily contribution fields.
12. Add one-active-attachment partial unique index.
13. Run migration validation checks (no orphaned submissions, no duplicated normalized codes, full FK coverage).

### Revision `0003_finalize_submission_schema`
14. Add `submissions.started_at` and backfill from `created_at`.
15. Add `submissions.ended_at` and backfill completed rows from `completed_at`.
16. Convert `submission_status_enum` from:
   - `ONGOING`
   - `COMPLETED`
   to:
   - `IN_PROGRESS`
   - `CHECKED_OUT`
   - `COMPLETED`
17. Drop legacy bridge-only submission columns after parent backfill is already complete:
   - `zone`
   - `cluster_name`
   - `cluster_name_normalized`
   - `number_of_grids`
   - `pending_grids`
18. Drop obsolete legacy grid math constraints tied to removed columns.
19. Validate the final submission contract:
   - no null `started_at`
   - no legacy columns remain on `submissions`
   - `submission_status_enum` exposes the final 3 values

## Irrecoverable Conflict Policy
Migration is blocked if preflight or upgrade detects:
1. Blank normalized workorder code values.
2. Duplicate legacy submissions for same normalized code + work date.
3. Mixed regions for the same normalized code.
4. Conflicting or non-positive legacy `number_of_grids` values for the same normalized code.
5. Multiple active attachments for a single submission.

These must be resolved before cutover.

## Rollback Plan
Rollback is allowed only if there is a functional regression or failed validation after deployment.

### Fast rollback (schema rollback)
1. Stop write traffic.
2. Run Alembic downgrade to previous revision.
   - `0003 -> 0002` restores the bridge-style `submissions` columns from parent `workorders`
   - `0002 -> 0001` removes the parent/child split entirely
3. Re-enable write traffic after smoke checks.

### Data-safe rollback (preferred for production incidents)
1. Stop write traffic.
2. Restore from pre-cutover backup/snapshot.
3. Reconcile delta writes captured during the incident window, if any.
4. Re-enable traffic.

## Post-Migration Validation Checklist
1. `submissions.workorder_id` is non-null for all rows.
2. No orphaned submission FK rows.
3. `workorders.workorder_code_normalized` is globally unique.
4. `submissions(workorder_id, work_date)` uniqueness is enforced.
5. `submission_attachments` enforces one active attachment per submission.
6. `submissions.started_at` is present and non-null.
7. `submissions` no longer contains `zone`, `cluster_name`, `cluster_name_normalized`, `number_of_grids`, or `pending_grids`.
8. `submission_status_enum` values are `IN_PROGRESS`, `CHECKED_OUT`, `COMPLETED`.

## Notes On Existing Guardrails
- Immutable migration guard (`scripts/check_alembic_immutable.py`) remains unchanged.
- Existing-table changes are done through a new revision file only, which is compatible with guardrail policy.
