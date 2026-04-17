# Business Rules

## User / Access Rules
- users sign up through Supabase Auth
- users choose requested role during signup
- roles in v1: `DRIVE_TESTER`, `ADMIN`
- new users start in `PENDING_APPROVAL`
- pending users can log in but cannot use module features
- only approved admins can approve, reject, or suspend users

## First Admin Bootstrap Rules
- config key: `BOOTSTRAP_ADMIN_EMAILS`
- value format: comma-separated email allowlist
- on `POST /api/v1/me/bootstrap`, if zero approved admins exist and caller email is allowlisted and requested role is `ADMIN`, auto-approve as admin
- auto-approval must write `user_approval_audit` with:
  - `reviewed_by_user_id = null`
  - `review_notes = "BOOTSTRAP_ADMIN_AUTO_APPROVED"`
- this bootstrap path is disabled once any approved admin exists
- this logic must be atomic/transactional

## Profile Rules
- in v1, `PATCH /api/v1/me` may edit only `full_name`

## Workorder Model Rules
- a workorder is the parent business record
- a workorder may span multiple days
- a workorder may move between different drivers on different days
- `workorder_code` is the real business identifier across days
- `workorder_code` is globally unique by normalized value
- `region` belongs to the workorder and stays fixed across all child daily submissions
- `total_grids` belongs to the workorder and is the grand total across all days
- workorder statuses in v1: `ACTIVE`, `COMPLETED`

## Daily Submission Ownership Rules
- a drive tester can create only their own daily submissions
- a drive tester can edit only their own daily submissions
- a drive tester can edit daily submission data only while submission status is `IN_PROGRESS` or `CHECKED_OUT`
- a drive tester cannot edit a `COMPLETED` daily submission's data fields
- a drive tester may still upload, replace, or remove files after daily completion
- an admin can view and edit any workorder and any daily submission, including `COMPLETED`
- an admin can reopen a `COMPLETED` daily submission back to `CHECKED_OUT`

## Daily Submission Uniqueness Rule
One daily submission is allowed per:
- `workorder_id`
- `work_date`

Notes:
- one driver per workorder per day
- same driver or different driver may create the next day's daily submission
- `shift` is useful for reporting but not part of the identity key

## Workorder Code Normalization Rule
`workorder_code_normalized` is derived by:
1. Unicode NFKC normalization
2. trim
3. uppercase
4. remove all whitespace
5. preserve `-`

Examples:
- `WO 123` and `wo123` normalize to the same code
- `WO-123` remains different from `WO123`

## Daily Grid Contribution Rules
- all numeric fields must be non-negative
- `completed_grids`, `skipped_grids`, and `force_tested_grids` on a daily submission are that day's contribution only
- tester progress updates use cumulative `completed_grids`, not incremental deltas
- `force_tested_grids` is informational only
- `skipped_grids` are permanent for the parent workorder

## Aggregate Workorder Progress Rules
- aggregate workorder completed count is `sum(child completed_grids)`
- aggregate workorder skipped count is `sum(child skipped_grids)`
- aggregate workorder remaining count is `total_grids - (completed + skipped)`
- aggregate workorder progress percent is `(completed + skipped) / total_grids * 100`
- aggregate `completed + skipped` across all child daily submissions must never exceed parent `total_grids`

## Lifecycle Rules
- `Start Drive` finds or creates the parent workorder and creates the daily submission in `IN_PROGRESS`
- backend stamps `started_at` automatically when `Start Drive` succeeds
- `End Drive` stamps `ended_at` automatically and moves the daily submission to `CHECKED_OUT`
- each day must be closed out the same day with final counts and file
- `COMPLETED` on a daily submission means the day is fully closed out
- `COMPLETED` on a workorder means the whole multi-day workorder is fully finished
- when aggregate child `completed_grids + skipped_grids = total_grids`, the parent workorder becomes `COMPLETED`
- if a completed child daily submission is reopened or loses its last active file, the parent workorder may move back to `ACTIVE`

## Daily Completion Rules
A daily submission cannot be marked `COMPLETED` unless:
- current daily status is `CHECKED_OUT`
- there is exactly one active attachment
- end-of-day `completed_grids`, `skipped_grids`, and `force_tested_grids` values are present
- aggregate parent workorder totals after this closeout do not exceed `total_grids`

## Attachment Rules
- allowed file types in v1: `.csv`, `.xlsx`
- `.xls` is not allowed in v1
- allowed MIME types:
  - `text/csv`
  - `application/csv`
  - `application/vnd.ms-excel`
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- validate both extension and MIME type
- exactly one active attachment is allowed per daily submission
- actual file stored in Supabase Storage
- metadata stored in `submission_attachments`
- private bucket required
- signed download URL generated only after permission checks
- file metadata is soft-retained for attachment history after tester removal/replacement
- normal tester attachment listing shows active files only
- inactive attachment history is admin-only in v1
- Day 2's file may contain Day 1 + Day 2 data; it is still the authoritative daily closeout file for Day 2's submission

## File Submission Pending Indicator Rules
- expose computed boolean `file_submission_pending` in daily submission list/detail responses
- `file_submission_pending = true` when:
  - daily submission `status = CHECKED_OUT`
  - active attachment count = `0`
- otherwise `file_submission_pending = false`
- do not store this as a DB column in v1; compute at read time

## Date Rules
- frontend defaults `work_date` to today
- frontend uses a date picker rather than free-text input
- drive testers cannot set future dates
- backend enforces `work_date <= current date` based on the parent workorder region timezone mapping:
  - `NE_UP -> America/New_York`
  - `SOUTH_FLORIDA -> America/New_York`
  - `CENTRAL -> America/Chicago`

## Reminder / Progress Tracking Rules
- v1 supports periodic progress updates by overwriting the latest daily submission row values
- v1 does not yet require a backend-managed 4-hour reminder scheduler
- v1 does not yet require a structured per-checkpoint progress history table
- future v2/v3 can add checkpoint history and reminder compliance tracking without redesigning the core workorder + daily submission model

## Pagination Rules
- default `page = 1`
- default `page_size = 20`
- max `page_size = 100`
- invalid pagination values return `422`

## Response Contract Rules
- JSON success envelope: `{ "success": true, "data": ..., "meta": ... }`
- JSON error envelope: `{ "success": false, "error": { "code", "message", "details" }, "meta": ... }`
- no envelope for file streams or `204` responses

## Admin Reporting Rules
- admin can view `ACTIVE` workorders
- admin can view `COMPLETED` workorders
- admin can view `IN_PROGRESS`, `CHECKED_OUT`, and `COMPLETED` daily submissions
- admin can filter daily submissions by `file_submission_pending`
- admin can view approved drive testers with no daily submission yet for a selected date
- no-submission-yet view is best-effort and not roster-based

## Audit Rules
All of the following must create audit records:
- daily submission create
- daily submission update
- daily submission status change
- daily submission completion
- daily submission reopen
- file upload
- file remove
- workorder create / attach
- workorder auto-complete / reopen effects
- user approval
- user rejection
- admin edits
- bootstrap admin auto-approval

Notes:
- v1 audit logs are mutation-oriented and not a substitute for future structured 4-hour checkpoint history
