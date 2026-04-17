# Backend/API/DB Priority Task Backlog

## Purpose
This document is the execution backlog for backend, API, database, and testing work after moving to the `workorders` (parent) + `submissions` (daily child) architecture.

## Ordering Rule
Tasks are listed in strict descending priority order, highest priority first.

## Priority-Ordered Task List
1. `[P0]` Freeze migration strategy and rollback plan for moving from submission-only semantics to `workorders + daily submissions`.
2. `[P0]` Add new `workorder_status` enum with `ACTIVE` and `COMPLETED`.
3. `[P0]` Create `workorders` table with parent fields (`workorder_code`, normalized code, region, total_grids, status, audit timestamps).
4. `[P0]` Add unique index/constraint on `workorders.workorder_code_normalized` (global uniqueness).
5. `[P0]` Alter `submissions` table to add non-null `workorder_id` foreign key to `workorders`.
6. `[P0]` Add unique constraint on `submissions(workorder_id, work_date)` to enforce one daily submission per workorder per day.
7. `[P0]` Remove legacy uniqueness assumptions tied to owner/date/shift/ticket once new uniqueness is in place.
8. `[P0]` Add/verify DB check constraints for non-negative daily grid contribution fields.
9. `[P0]` Add DB-level one-active-attachment rule with a partial unique index for `submission_attachments(submission_id)` where `is_active = true`.
10. `[P0]` Write data migration to backfill `workorders` from existing submissions and attach every legacy submission to a parent workorder.
11. `[P0]` Add migration validation queries to verify no orphaned submissions, no duplicated normalized codes, and correct foreign-key coverage.
12. `[P0]` Add migration guard script/check for irrecoverable conflicts before production cutover.
13. `[P0]` Implement `workorder_code` normalization utility (`NFKC`, trim, uppercase, remove whitespace, preserve `-`).
14. `[P0]` Add unit tests for normalization behavior, including `WO123 == WO 123` and `WO-123 != WO123`.
15. `[P0]` Implement workorder repository methods for lookup by normalized code, create, update, status transitions, and aggregate reads.
16. `[P0]` Implement submission repository updates to always include parent `workorder_id`.
17. `[P0]` Implement aggregate workorder service for `completed`, `skipped`, `remaining`, and `progress_percent`.
18. `[P0]` Implement transactional `Start Drive` service flow (`find active workorder or create`, then create daily submission).
19. `[P0]` Implement service validation for attach-to-existing behavior where supplied `region`/`total_grids` must match parent if provided.
20. `[P0]` Implement service validation to block new daily submissions for already `COMPLETED` workorders.
21. `[P0]` Implement daily submission progress update service with aggregate cap checks against parent `total_grids`.
22. `[P0]` Implement `End Drive` service transition (`IN_PROGRESS -> CHECKED_OUT`) with `ended_at` stamp.
23. `[P0]` Implement daily completion service requiring `CHECKED_OUT`, end-of-day values, and exactly one active attachment.
24. `[P0]` Implement parent workorder auto-complete when aggregate child `completed + skipped == total_grids`.
25. `[P0]` Implement parent reopen-to-active recalculation when child completion is reversed by reopen or file removal.
26. `[P0]` Update attachment upload service to enforce one active file per daily submission.
27. `[P0]` Update attachment delete/replace service to trigger child and parent status recalculation side effects.
28. `[P0]` Ensure all state transitions are transactional and concurrency-safe (optimistic version checks and atomic updates).
29. `[P0]` Implement/verify strict auth checks: tester ownership, admin overrides, pending-account blocking.
30. `[P0]` Add new domain error codes for workorder and aggregate violations (`WORKORDER_NOT_FOUND`, `WORKORDER_PROGRESS_EXCEEDS_TOTAL`, `ACTIVE_ATTACHMENT_ALREADY_EXISTS`, etc.).

31. `[P0-Test]` Unit tests for `Start Drive` find-vs-create transaction flow and race-safe behavior.
32. `[P0-Test]` Unit tests for attach mismatch cases (`region`/`total_grids` mismatch against existing parent).
33. `[P0-Test]` Unit tests for aggregate cap enforcement during daily edits and completion.
34. `[P0-Test]` Unit tests for status transitions: daily (`IN_PROGRESS`, `CHECKED_OUT`, `COMPLETED`) and parent (`ACTIVE`, `COMPLETED`).
35. `[P0-Test]` Unit tests for file side effects: remove/replace causing child reopen and optional parent reopen.
36. `[P0-Test]` Unit tests for permission matrix (owner tester, non-owner tester, admin, pending user).
37. `[P0-Test]` API tests for `POST /api/v1/submissions` create-new-workorder path.
38. `[P0-Test]` API tests for `POST /api/v1/submissions` attach-existing-workorder path.
39. `[P0-Test]` API tests for duplicate daily submission conflict on `(workorder_id, work_date)`.
40. `[P0-Test]` API tests for `POST /api/v1/submissions/{id}/end-drive` valid and invalid-state transitions.
41. `[P0-Test]` API tests for `POST /api/v1/submissions/{id}/complete` status-code matrix.
42. `[P0-Test]` API tests for one-active-file enforcement and replace/remove behavior.

43. `[P1]` Add tester endpoint `GET /api/v1/workorders/lookup` for manual workorder-code entry assistance.
44. `[P1]` Add/adjust tester list/detail payloads to include nested parent workorder aggregate summary.
45. `[P1]` Add admin workorders list endpoint with filters (`workorder_code`, region, status, date range).
46. `[P1]` Add admin workorder detail endpoint with aggregate summary and child daily submissions.
47. `[P1]` Add admin workorder update endpoint (`workorder_code`, `region`, `total_grids`) with safe aggregate guards.
48. `[P1]` Update admin submissions list/detail endpoints to include parent summary and workorder status.
49. `[P1]` Update admin submission edit endpoint to recalculate parent aggregate/status after edits.
50. `[P1]` Update admin submission reopen endpoint to recalculate parent status when reopening child.
51. `[P1]` Add admin-only endpoint for inactive attachment history on a daily submission.
52. `[P1]` Update dashboard summary endpoints to include workorder-level counts and progress metrics.
53. `[P1]` Update no-submission-yet endpoint to explicitly operate on daily submissions by selected date.
54. `[P1]` Update CSV export endpoint to include parent workorder fields and aggregate progress columns.
55. `[P1]` Update mobile bootstrap/reference data payload to include `workorder_statuses`.

56. `[P1-Test]` API tests for `GET /api/v1/workorders/lookup` found/not-found/auth failures.
57. `[P1-Test]` API tests for admin workorders list/detail/update with role checks.
58. `[P1-Test]` API tests for admin submissions filters including workorder status and `file_submission_pending`.
59. `[P1-Test]` API tests for attachment-history endpoint access control (admin-only).
60. `[P1-Test]` API tests for dashboard and export responses using new workorder aggregates.

61. `[P1-Integration]` Integration test: migrate up/down smoke covering new schema and constraints.
62. `[P1-Integration]` Integration test: data backfill correctness from legacy submissions to parent workorders.
63. `[P1-Integration]` Integration test: uniqueness and FK guarantees (`workorder_code_normalized`, `workorder_id + work_date`, one active attachment).
64. `[P1-Integration]` Integration test: concurrent `Start Drive` requests for same workorder code resolve safely.
65. `[P1-Integration]` Integration test: multi-day continuation (same driver next day, different driver next day).
66. `[P1-Integration]` Integration test: parent completion and parent reopen cascades from child edits/file removal.

67. `[P2]` Add/update factories and fixtures for workorders, daily submissions, and attachment versions.
68. `[P2]` Add query/index tuning for admin heavy filters and export queries.
69. `[P2]` Add audit-log coverage assertions for all mutation endpoints.
70. `[P2]` Add CI checks for migration immutability and new-revision-only policy enforcement.
71. `[P2]` Add CI split for fast suite (unit+API) and opt-in integration suite.
72. `[P2]` Prepare production runbook: preflight checks, migration window steps, post-migration validation, rollback steps.

## Suggested Execution Waves
1. `Wave 1`: Items `1-42` (core DB + core services + core tests).
2. `Wave 2`: Items `43-60` (admin/workorder APIs + contract completion).
3. `Wave 3`: Items `61-72` (integration hardening, performance, rollout readiness).
