# Admin Web API Truth Gaps - Execution Plan

Last updated: 2026-04-22
Owner: Admin Web + API
Status: In Progress

## Goal
Ensure every business-facing Admin Web control is truly API-backed, DB-backed, and contract-aligned.

## Suggested Execution Order
1. Fix filter functionality gap (daily submissions).
2. Wire or remove non-functional dashboard region control.
3. Resolve integration contract mismatches (404 vs 422, audit field mismatch).
4. Re-run full validation and capture evidence.

## Task 1 - Daily Submissions Filter Gap
Priority: P0
Status: Completed (2026-04-22)

### Problem
Admin Web sends region/workorder_code/tester filters, but backend list endpoint currently does not support those query params.

### Current Frontend Call Sites
- apps/admin-web/lib/hooks/use-admin-submissions.ts
- apps/admin-web/components/features/daily-submissions-page.tsx

### Current Backend Endpoint
- apps/api/app/api/v1/routers/admin_submissions.py

### Options
- Option A (recommended): Add backend query params and repository filtering for region, workorder_code, and tester (name/email/ticket strategy must be defined).
- Option B: Temporarily remove/disable those filters from UI until backend supports them.

### Acceptance Criteria
- Filtering by region works end-to-end.
- Filtering by workorder code works end-to-end.
- Filtering by tester works with documented behavior (exact/contains and which fields).
- Integration tests include these filters.
- UI labels and API params stay aligned.

### Closure Notes (2026-04-22)
- Implemented optional query params on admin submissions list endpoint: region, workorder_code, tester.
- Preserved backward compatibility: params default to None and are only applied when present.
- Tester behavior is case-insensitive contains against submission submitter name snapshot OR email snapshot.
- Workorder code behavior is case-insensitive contains against workorder_code.
- Region behavior is exact enum match.

Code refs:
- apps/api/app/api/v1/routers/admin_submissions.py
- apps/api/app/services/submission_service.py
- apps/api/app/repositories/submission_repository.py

Test evidence:
- apps/api/tests/api/test_admin_submissions_api.py (16 passed)
- apps/api/tests/unit/test_submission_service.py (52 passed)
- apps/api/tests/integration/test_submission_service_integration.py -k "region_workorder_code_and_tester_filters or file_submission_pending_filter" (2 passed)

## Task 2 - Dashboard Region Dropdown Not Wired
Priority: P1
Status: Completed (2026-04-22)

### Problem
Dashboard region dropdown is currently presentational and does not affect API requests/state.

### Frontend File
- apps/admin-web/components/features/dashboard-page.tsx

### Options
- Option A (recommended): Wire region into dashboard and related list queries where business-valid.
- Option B: Remove region dropdown until there is a clear backend/filter behavior.

### Acceptance Criteria
- Region selection changes data queries and results, or
- Control is removed and no misleading UI remains.

### Closure Notes (2026-04-22)
- Implemented Option A: wired region selection into dashboard widgets and related navigation links where backend filters are supported.
- Region now filters:
	- recent workorders widget query
	- recent submissions widget query
	- file-pending widget query/count
	- "View all" and "Open table" links for workorders/submissions
- Added an explicit info banner when a region filter is active to make scope clear.
- Kept summary metrics behavior unchanged (date-driven dashboard summary endpoint) while ensuring filtered widgets visibly reflect selected region.

Code refs:
- apps/admin-web/components/features/dashboard-page.tsx
- apps/admin-web/tests/unit/components/features/dashboard-page.test.tsx

Test evidence:
- `pnpm --filter admin-web exec vitest run tests/unit/components/features/dashboard-page.test.tsx --reporter=dot` -> pass (9 tests)
- `pnpm --filter admin-web typecheck` -> pass
- `pnpm --filter admin-web lint` -> pass
- `pnpm --filter admin-web test` -> pass (213 tests, 37 files)

## Task 3 - Integration Contract Mismatches
Priority: P0
Status: Completed (2026-04-22)

### Confirmed Mismatches
1. GET /admin/submissions/{id} returns 422 for non-existent id where test expects 404.
2. GET /admin/workorders/{id} returns 422 for non-existent id where test expects 404.
3. Submission audit response missing changed_by_user_id expected by integration contract.

### Decision Needed
- Are these API behaviors correct and tests wrong?
- Or should API behavior be changed to match contract expectations?

### Decision (2026-04-22)
- GET /admin/submissions/{id}: backend behavior is correct. `404` applies when the path contains a valid UUID that does not exist. `422` applies when the path value is not a valid UUID.
- GET /admin/workorders/{id}: backend behavior is correct. `404` applies when the path contains a valid UUID that does not exist. `422` applies when the path value is not a valid UUID.
- Submission audit response: backend behavior is correct and already matches the real admin-web consumer. The stale contract test expected old field names.

Root cause:
- The failing contract test used malformed IDs like `non-existent-id-000`, which trigger FastAPI UUID validation and correctly return `422` before any DB lookup occurs.
- The audit contract test expected obsolete fields (`changed_by_user_id`, `changed_at`, `change_type`, `before_snapshot`, `after_snapshot`) that are not used by the current admin-web hook/UI.

Correct audit payload fields in current contract:
- `id`
- `submission_id`
- `action_type`
- `actor_user_id`
- `actor_role`
- `source`
- `changed_fields_json`
- `before_snapshot_json`
- `after_snapshot_json`
- `created_at`

Execution notes:
- Updated `apps/admin-web/tests/integration/api-contract.test.ts` to use valid random UUIDs for missing-resource checks.
- Updated the same contract test to assert the current audit payload fields consumed by admin-web.
- Re-ran the integration contract file with a fresh token in the same shell as the test process.
- Task 3 cases passed; remaining failures in that file are unrelated `500` errors from the export endpoint.

Closure notes:
- The 404/422 mismatch was caused by malformed UUIDs in the contract test, not incorrect backend behavior.
- The audit mismatch was caused by stale expected field names in the contract test, not incorrect backend behavior.
- Task 3 is resolved by aligning the contract test and docs to the real API/frontend contract.

Code refs:
- apps/admin-web/tests/integration/api-contract.test.ts
- apps/api/app/api/v1/routers/admin_submissions.py
- apps/api/app/api/v1/routers/admin_workorders.py
- apps/api/app/services/submission_service.py
- apps/api/app/services/workorder_service.py
- apps/api/app/schemas/submissions.py
- apps/admin-web/lib/types/domain.ts
- apps/admin-web/lib/hooks/use-submission-audit.ts
- apps/admin-web/components/features/daily-submission-detail-page.tsx

Test evidence:
- `pnpm --filter admin-web exec vitest run --config vitest.config.integration.ts tests/integration/api-contract.test.ts --reporter=dot`
- Intermediate result: 53 passed, 2 failed (export endpoint 500s)
- Final result after export hotfix: 55 passed, 0 failed
- Export endpoint regression covered by backend integration test: `apps/api/tests/integration/test_reporting_repository_integration.py` (3 passed)

### Acceptance Criteria
- Contract and implementation are consistent.
- tests/integration/api-contract.test.ts passes for the affected cases.
- Any schema/response-field changes are documented in API docs.

## Task 4 - Verification Gate (No Fabrication Rule)
Priority: P0
Status: Completed (2026-04-22)

### Validation Commands
- pnpm --filter admin-web typecheck
- pnpm --filter admin-web lint
- pnpm --filter admin-web test
- pnpm --filter admin-web test:integration (with INTEGRATION_API_TOKEN)

### Acceptance Criteria
- All admin-web runtime business data is API-backed.
- No runtime mock fallback in apps/admin-web/app, apps/admin-web/components, apps/admin-web/lib.
- Integration checks pass for admin endpoints in scope.
- Any intentional placeholders are explicitly documented.

### Closure Notes (2026-04-22)
- Verification gate executed end-to-end after Task 3 and export hotfix.
- All required admin-web checks passed.
- Integration contract file passed fully with a freshly refreshed token in the same shell as test execution.

Test evidence:
- `pnpm --filter admin-web typecheck` -> pass
- `pnpm --filter admin-web lint` -> pass
- `pnpm --filter admin-web test` -> pass (37 files, 212 tests)
- `pnpm --filter admin-web test:integration` -> pass (55 tests)

## Working Notes
- Keep this file as the single source of truth for closure status.
- Close each task with: code refs, test evidence, and behavior notes.

## Post-Closure Hardening (2026-04-22)
Status: Completed (scoped refactor)

### Item 3 Completion
- Replaced private cross-repository helper usage with a public shared utility for admin submission filtering.
- Reporting repository no longer calls `SubmissionRepository._apply_admin_filters` directly.

Code refs:
- apps/api/app/repositories/submission_filters.py
- apps/api/app/repositories/submission_repository.py
- apps/api/app/repositories/reporting_repository.py

Validation evidence:
- `d:/ml-workflow/apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests/integration/test_submission_service_integration.py -k "region_workorder_code_and_tester_filters or file_submission_pending_filter" -q` -> pass (2)
- `d:/ml-workflow/apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests/integration/test_reporting_repository_integration.py -q` -> pass (3)
- `d:/ml-workflow/apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests/api/test_admin_submissions_api.py -q` -> pass (16)
- `d:/ml-workflow/apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests/api/test_reporting_api.py -q` -> pass (6)
