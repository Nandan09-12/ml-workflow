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
- submissions
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

## Submissions

### POST /api/v1/submissions
Create a new submission. Status is created as `ONGOING`.

Rules:
- enforce uniqueness by `(owner_user_id, work_date, shift, cluster_name_normalized)`
- normalize `cluster_name` and store result in `cluster_name_normalized`
- enforce work date is not in the future by zone timezone mapping

### GET /api/v1/submissions
List current user's submissions.

Response items include computed field:
- `file_submission_pending`

Query params may include:
- `work_date`
- `date_from`
- `date_to`
- `status`
- `zone`
- `shift`
- `page`
- `page_size`

### GET /api/v1/submissions/{submission_id}
Get current user's submission detail.

Response includes computed field:
- `file_submission_pending`

### PATCH /api/v1/submissions/{submission_id}
Update current user's ongoing submission.

Rules:
- must include `version_number` for optimistic concurrency
- returns `VERSION_CONFLICT` on stale version

### POST /api/v1/submissions/{submission_id}/complete
Complete an ongoing submission.

Requirements:
- `pending_grids = 0`
- attachment is not required before completion

## Admin Submissions

### GET /api/v1/admin/submissions
Admin list of all submissions.

Supports filters by date, tester, zone, shift, status, cluster, ticket number, `file_submission_pending`, and pagination.

Response items include computed field:
- `file_submission_pending`

### GET /api/v1/admin/submissions/{submission_id}
Admin detail view.

Response includes computed field:
- `file_submission_pending`

### PATCH /api/v1/admin/submissions/{submission_id}
Admin edits any submission.

### POST /api/v1/admin/submissions/{submission_id}/reopen
Admin reopens completed submission.

### GET /api/v1/admin/submissions/{submission_id}/audit
Get full audit history.

## Attachments

### POST /api/v1/submissions/{submission_id}/attachments
Upload attachment using `multipart/form-data`.

Validation:
- max size per file: `25 MB`
- max active attachments per submission: `5`
- allowed extensions: `.csv`, `.xlsx`
- `.xls` is not allowed in v1
- allowed MIME types:
  - `text/csv`
  - `application/csv`
  - `application/vnd.ms-excel`
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- extension and MIME must both be valid

### GET /api/v1/submissions/{submission_id}/attachments
List submission attachments.

### GET /api/v1/attachments/{attachment_id}
Get attachment metadata.

### POST /api/v1/attachments/{attachment_id}/download-url
Returns signed download URL.

### DELETE /api/v1/attachments/{attachment_id}
Soft remove attachment.

## Dashboard / Reporting

### GET /api/v1/admin/dashboard/summary
Returns dashboard counts for a date or date range.

### GET /api/v1/admin/dashboard/no-submission-yet
Returns approved drive testers with no submission for selected date.

Response must clearly state this is not assignment-based.

### GET /api/v1/admin/reports/submissions/export
Exports filtered submissions as CSV in v1.

## Mobile Sync

### GET /api/v1/mobile/bootstrap
Returns reference data and current user state.

Response contract:
- `contract_version = "v1"`
- `offline_sync_enabled = false` in v1 placeholder
- includes current `app_users` state and enum reference data (`zones`, `shifts`, `submission_statuses`)

### POST /api/v1/mobile/sync
Batch sync endpoint for future offline support.

V1 placeholder behavior:
- validates request contract
- does not persist operations yet
- returns status payload with:
  - `status = "NOT_IMPLEMENTED"`
  - operation counters (`received`, `processed`, `rejected`)

## Cluster Normalization Contract
Normalization for `cluster_name_normalized`:
1. Unicode NFKC normalization
2. trim leading/trailing whitespace
3. replace `-` and `_` with space
4. collapse repeated whitespace into single spaces
5. uppercase

## Future Date Validation Contract
A tester cannot create or update a submission with `work_date` in the future relative to zone local date.

Zone timezone mapping:
- `NORTHEAST -> America/New_York`
- `SOUTH_FLORIDA -> America/New_York`
- `CENTRAL -> America/Chicago`

## Computed Field Contract
`file_submission_pending` is computed (not persisted) as:
- `true` when `status = COMPLETED` and active attachment count is `0`
- `false` otherwise

Notes:
- do not add a DB column for this field in v1
- compute in service/read layer and expose in submission detail/list responses

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
- `SUBMISSION_ALREADY_EXISTS`
- `INVALID_GRID_MATH`
- `VERSION_CONFLICT`
- `PENDING_GRIDS_MUST_BE_ZERO`
- `SUBMISSION_ALREADY_COMPLETED`
- `SUBMISSION_NOT_COMPLETED`
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
