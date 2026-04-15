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

## Submission Ownership Rules
- a drive tester can create only their own submissions
- a drive tester can edit only their own submissions
- a drive tester can edit only while submission status is `ONGOING`
- a drive tester cannot edit a `COMPLETED` submission
- an admin can view and edit any submission
- an admin can reopen a `COMPLETED` submission back to `ONGOING`

## Submission Uniqueness Rule
A submission is unique by:
- `owner_user_id`
- `work_date`
- `shift`
- `cluster_name_normalized`

## Cluster Normalization Rule
`cluster_name_normalized` is derived by:
1. Unicode NFKC normalization
2. trim
3. replace `-` and `_` with space
4. collapse repeated whitespace
5. uppercase

## Grid Math Rules
- all numeric fields must be non-negative
- `completed_grids + pending_grids + skipped_grids = number_of_grids`
- `skipped_grids <= number_of_grids`
- `pending_grids <= number_of_grids`
- `completed_grids <= number_of_grids`
- `force_tested_grids` is informational only

## Completion Rules
A submission cannot be marked `COMPLETED` unless:
- `pending_grids = 0`
- attachment is not required for completion

## Attachment Rules
- allowed file types in v1: `.csv`, `.xlsx`
- `.xls` is not allowed in v1
- allowed MIME types:
  - `text/csv`
  - `application/csv`
  - `application/vnd.ms-excel`
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- validate both extension and MIME type
- max size per file: `25 MB`
- max active attachments per submission: `5`
- attachments may be uploaded after completion
- actual file stored in Supabase Storage
- metadata stored in `submission_attachments`
- private bucket required
- signed download URL generated only after permission checks

## File Submission Pending Indicator Rules
- expose computed boolean `file_submission_pending` in submission list/detail responses
- `file_submission_pending = true` when:
  - submission `status = COMPLETED`
  - active attachment count = `0`
- otherwise `file_submission_pending = false`
- do not store this as a DB column in v1; compute at read time

## Date Rules
- frontend defaults `work_date` to today
- frontend uses a date picker rather than free-text input
- drive testers cannot set future dates
- backend enforces `work_date <= current date` based on zone timezone mapping:
  - `NORTHEAST -> America/New_York`
  - `SOUTH_FLORIDA -> America/New_York`
  - `CENTRAL -> America/Chicago`

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
- admin can view `ONGOING` submissions
- admin can view `COMPLETED` submissions
- admin can filter submissions by `file_submission_pending`
- admin can view approved drive testers with no submission yet for a selected date
- no-submission-yet view is best-effort and not roster-based

## Audit Rules
All of the following must create audit records:
- submission create
- submission update
- status change
- completion
- reopen
- file upload
- file remove
- user approval
- user rejection
- admin edits
- bootstrap admin auto-approval
