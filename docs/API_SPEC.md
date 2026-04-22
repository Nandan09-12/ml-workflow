# API Spec

## Base Path
`/api/v1`

## Authentication
All business endpoints require a valid Supabase JWT in the `Authorization: Bearer <token>` header.

## Standard Response Envelope
Use envelope responses for all JSON endpoints except file streams and `204 No Content` responses.

### Success Envelope
```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

### Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable summary",
    "details": {}
  },
  "meta": {}
}
```

## Pagination Standard
For list endpoints that support pagination:
- `page` default: `1`
- `page_size` default: `20`
- `page_size` max: `100`
- invalid values return `422 Unprocessable Entity`

## Endpoint Groups
- me / profile
- admin users
- workorders
- submissions
- admin workorders
- admin submissions
- attachments
- dashboard / reporting
- mobile sync

## Me / Profile

### GET /api/v1/me
Returns current app user state.

### POST /api/v1/me/bootstrap
Creates app user record after Supabase signup.

Request:
```json
{
  "full_name": "John Doe",
  "requested_role": "DRIVE_TESTER"
}
```

Behavior:
- idempotent by authenticated user identity (`auth_user_id`)
- if zero approved admins exist and caller email is allowlisted in `BOOTSTRAP_ADMIN_EMAILS`, and requested role is `ADMIN`, auto-approve as admin
- bootstrap auto-approval must write `user_approval_audit` with:
  - `reviewed_by_user_id = null`
  - `review_notes = "BOOTSTRAP_ADMIN_AUTO_APPROVED"`
- bootstrap auto-approval path is disabled once any approved admin exists
- bootstrap write logic must be atomic/transactional

### PATCH /api/v1/me
Updates editable profile data.

Request:
```json
{
  "full_name": "Updated Name"
}
```

Rules:
- only `full_name` is editable in v1

## Admin Users

### GET /api/v1/admin/users/pending
List pending users.

### GET /api/v1/admin/users
List all app users.

### GET /api/v1/admin/users/{user_id}
Get one user.

### POST /api/v1/admin/users/{user_id}/approve
Approve pending user.

### POST /api/v1/admin/users/{user_id}/reject
Reject pending user.

### POST /api/v1/admin/users/{user_id}/suspend
Suspend approved user.

### GET /api/v1/admin/users/{user_id}/approval-history
Get approval history.

## Workorders

### GET /api/v1/workorders/lookup
Resolve an active workorder by `workorder_code`.

Use case:
- tester enters the workorder code manually on `Start Drive`
- frontend can check whether this is a continuation of an existing active workorder

Query params:
- `workorder_code`

Response includes:
- `workorder_code`
- `region`
- `total_grids`
- `status`
- aggregate workorder progress fields

Rules:
- lookup uses normalized workorder code
- if no active workorder exists for that code, return `404`

## Submissions

### POST /api/v1/submissions
Start a new daily submission. Daily submission status is created as `IN_PROGRESS`.

Request fields:
- `workorder_code`
- `work_date`
- `shift`
- `team_number`
- `ticket_number`
- `region` when creating a brand-new workorder
- `total_grids` when creating a brand-new workorder

Rules:
- normalize `workorder_code` and search parent workorders by normalized value
- if no active workorder exists, create the parent workorder and the daily submission in one transaction
- if an active workorder exists, attach the new daily submission to it
- if attaching to an existing workorder, request `region` / `total_grids` are optional but must match if supplied
- enforce uniqueness by `(workorder_id, work_date)`
- enforce work date is not in the future by parent region timezone mapping
- backend stamps `started_at`
- backend initializes:
  - `completed_grids = 0`
  - `skipped_grids = 0`
  - `force_tested_grids = 0`

Response includes:
- daily submission fields
- nested workorder summary with aggregate progress values

### GET /api/v1/submissions
List current user's daily submissions.

Response items include:
- daily submission fields
- `file_submission_pending`
- nested workorder summary:
  - `workorder_code`
  - `workorder_status`
  - `workorder_total_grids`
  - `workorder_completed_grids`
  - `workorder_skipped_grids`
  - `workorder_remaining_grids`
  - `workorder_progress_percent`

Query params may include:
- `work_date`
- `date_from`
- `date_to`
- `submission_status`
- `shift`
- `ticket_number`
- `workorder_code`
- `workorder_status`
- `page`
- `page_size`

### GET /api/v1/submissions/{submission_id}
Get current user's daily submission detail.

Response includes:
- daily submission fields
- `file_submission_pending`
- nested workorder summary with aggregate progress values

### PATCH /api/v1/submissions/{submission_id}
Update current user's `IN_PROGRESS` or `CHECKED_OUT` daily submission.

Rules:
- must include `version_number` for optimistic concurrency
- returns `VERSION_CONFLICT` on stale version
- tester progress updates use cumulative `completed_grids` for that day
- aggregate workorder progress cannot exceed parent `total_grids`
- drive testers may not edit daily submission data once status is `COMPLETED`

Patchable fields in v1:
- `completed_grids`
- `skipped_grids`
- `force_tested_grids`
- `team_number`
- `ticket_number`
- `shift`

### POST /api/v1/submissions/{submission_id}/end-drive
End active field work for a daily submission.

Requirements:
- current status must be `IN_PROGRESS`
- backend stamps `ended_at`
- status changes to `CHECKED_OUT`

### POST /api/v1/submissions/{submission_id}/complete
Complete a checked-out daily submission.

Requirements:
- current status must be `CHECKED_OUT`
- there must be exactly one active attachment
- end-of-day `completed_grids`, `skipped_grids`, and `force_tested_grids` values must be present
- aggregate workorder totals after this closeout must not exceed parent `total_grids`
- if aggregate workorder totals reach parent `total_grids`, parent workorder becomes `COMPLETED`

## Admin Workorders

### GET /api/v1/admin/workorders
Admin list of all workorders.

Supports filters by:
- `workorder_code`
- `region`
- `status`
- `date_from`
- `date_to`
- `page`
- `page_size`

Response items include computed fields:
- `workorder_completed_grids`
- `workorder_skipped_grids`
- `workorder_remaining_grids`
- `workorder_progress_percent`

### GET /api/v1/admin/workorders/{workorder_id}
Admin workorder detail view.

Response includes:
- parent workorder fields
- aggregate workorder progress values
- child daily submission list

Error semantics:
- `404` when `workorder_id` is a valid UUID but no workorder exists.
- `422` when `workorder_id` is not a valid UUID.

### PATCH /api/v1/admin/workorders/{workorder_id}
Admin edits workorder fields.

Patchable fields in v1:
- `workorder_code`
- `region`
- `total_grids`

Rules:
- normalized code must remain globally unique
- `total_grids` cannot be reduced below aggregate child `completed_grids + skipped_grids`

## Admin Submissions

### GET /api/v1/admin/submissions
Admin list of all daily submissions.

Supports filters by date, tester, region, shift, submission status, workorder code, workorder status, ticket number, `file_submission_pending`, and pagination.

Response items include:
- daily submission fields
- `file_submission_pending`
- nested workorder summary with aggregate progress values

### GET /api/v1/admin/submissions/{submission_id}
Admin daily submission detail view.

Response includes:
- daily submission fields
- `file_submission_pending`
- nested workorder summary with aggregate progress values

Error semantics:
- `404` when `submission_id` is a valid UUID but no submission exists.
- `422` when `submission_id` is not a valid UUID.

### PATCH /api/v1/admin/submissions/{submission_id}
Admin edits any daily submission, including `COMPLETED` submissions.

Rules:
- aggregate workorder totals after edit must not exceed parent `total_grids`
- a child edit may move the parent workorder between `ACTIVE` and `COMPLETED`

### POST /api/v1/admin/submissions/{submission_id}/reopen
Admin reopens completed daily submission back to `CHECKED_OUT`.

Rules:
- if the parent workorder had been `COMPLETED`, reopening the child may move the parent back to `ACTIVE`

### GET /api/v1/admin/submissions/{submission_id}/audit
Get full daily submission audit history.

Response shape:
- `items`: array of audit entries
- `count`: number of audit entries

Each audit item includes:
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

### GET /api/v1/admin/submissions/{submission_id}/attachments/history
Get attachment history, including inactive attachment records.

Rules:
- admin-only in v1
- intended for file replacement/removal visibility and audit support

## Attachments

### POST /api/v1/submissions/{submission_id}/attachments
Upload attachment using `multipart/form-data`.

Validation:
- max active attachments per daily submission: `1`
- allowed extensions: `.csv`, `.xlsx`
- `.xls` is not allowed in v1
- allowed MIME types:
  - `text/csv`
  - `application/csv`
  - `application/vnd.ms-excel`
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- extension and MIME must both be valid

Rules:
- uploads are allowed in `IN_PROGRESS`, `CHECKED_OUT`, and `COMPLETED`
- if an active file already exists, upload returns a conflict until the active file is replaced/removed
- testers can replace or upload files after completion

### GET /api/v1/submissions/{submission_id}/attachments
List active daily submission attachments for the tester flow.

### GET /api/v1/attachments/{attachment_id}
Get attachment metadata.

### POST /api/v1/attachments/{attachment_id}/download-url
Returns signed download URL.

### DELETE /api/v1/attachments/{attachment_id}
Soft remove attachment.

Rules:
- remove should mark `is_active = false`
- attachment metadata remains available for admin-only history
- if the deleted attachment was the last active file on a `COMPLETED` daily submission, backend changes that daily submission back to `CHECKED_OUT`
- if that daily submission was keeping the parent workorder fully closed out, the parent workorder changes back to `ACTIVE`

## Dashboard / Reporting

### GET /api/v1/admin/dashboard/summary
Returns dashboard counts for a date or date range.

Dashboard read models may include:
- active workorders
- completed workorders
- in-progress daily submissions
- checked-out daily submissions
- completed daily submissions
- aggregate workorder progress metrics

### GET /api/v1/admin/dashboard/no-submission-yet
Returns approved drive testers with no daily submission for selected date.

Response must clearly state this is not assignment-based.

### GET /api/v1/admin/reports/submissions/export
Exports filtered daily submissions as CSV in v1.

## Mobile Sync

### GET /api/v1/mobile/bootstrap
Returns reference data and current user state.

Response contract:
- `contract_version = "v1"`
- `offline_sync_enabled = false` in v1 placeholder
- includes current `app_users` state and enum reference data (`regions`, `shifts`, `workorder_statuses`, `submission_statuses`)

### POST /api/v1/mobile/sync
Batch sync endpoint for future offline support.

V1 placeholder behavior:
- validates request contract
- does not persist operations yet
- returns status payload with:
  - `status = "NOT_IMPLEMENTED"`
  - operation counters (`received`, `processed`, `rejected`)

## Workorder Normalization Contract
Normalization for `workorder_code_normalized`:
1. Unicode NFKC normalization
2. trim leading/trailing whitespace
3. uppercase
4. remove all whitespace
5. preserve `-`

## Future Date Validation Contract
A tester cannot create or update a daily submission with `work_date` in the future relative to the parent workorder region local date.

Region timezone mapping:
- `NE_UP -> America/New_York`
- `SOUTH_FLORIDA -> America/New_York`
- `CENTRAL -> America/Chicago`

UI labels:
- `NE-UP`
- `South/Florida`
- `Central`

## Computed Field Contract
`file_submission_pending` is computed (not persisted) as:
- `true` when `submission_status = CHECKED_OUT` and active attachment count is `0`
- `false` otherwise

Workorder aggregate read-model fields are computed as:
- `workorder_completed_grids = sum(child completed_grids)`
- `workorder_skipped_grids = sum(child skipped_grids)`
- `workorder_remaining_grids = total_grids - (completed + skipped)`
- `workorder_progress_percent = (completed + skipped) / total_grids * 100`

Notes:
- do not add DB columns for these computed fields in v1
- compute in service/read layer and expose in workorder detail, admin workorder list, and nested submission summaries

## Standard Error Codes
- `BAD_REQUEST`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `NOT_FOUND`
- `CONFLICT`
- `VALIDATION_ERROR`
- `NOT_IMPLEMENTED`
- `INTERNAL_SERVER_ERROR`
- `ACCOUNT_NOT_APPROVED`
- `ADMIN_ONLY`
- `INVALID_ACCOUNT_STATE`
- `WORKORDER_NOT_FOUND`
- `WORKORDER_ALREADY_COMPLETED`
- `WORKORDER_FIELDS_REQUIRED`
- `WORKORDER_CODE_ALREADY_EXISTS`
- `WORKORDER_PROGRESS_EXCEEDS_TOTAL`
- `SUBMISSION_ALREADY_EXISTS`
- `VERSION_CONFLICT`
- `SUBMISSION_ALREADY_COMPLETED`
- `SUBMISSION_NOT_COMPLETED`
- `SUBMISSION_NOT_CHECKED_OUT`
- `ATTACHMENT_REQUIRED_FOR_COMPLETION`
- `ACTIVE_ATTACHMENT_ALREADY_EXISTS`
- `NOT_OWNER`
- `UNSUPPORTED_FILE_TYPE`

## HTTP Status Guidance
- `200 OK`
- `201 Created`
- `204 No Content`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `409 Conflict`
- `501 Not Implemented`
- `422 Unprocessable Entity`
