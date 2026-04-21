# Admin Web API Integration

## Purpose
This file maps Admin Web pages and actions to backend API endpoints.

Source API contract:

```text
docs/API_SPEC.md
```

Base path:

```text
/api/v1
```

Default local base URL:

```text
http://localhost:8000/api/v1
```

## Auth
All business endpoints require:

```text
Authorization: Bearer <supabase_access_token>
```

Frontend flow:

1. Sign in with Supabase Auth.
2. Read Supabase session.
3. Call `GET /api/v1/me`.
4. Allow admin app only if current app user has:
   - `approved_role = ADMIN`
   - `account_status = APPROVED`

Block all other users from admin pages.

## Response Envelope
JSON success responses use:

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

JSON errors use:

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

Do not assume this envelope for file streams or `204` responses.

Centralize response parsing in the API client layer.

## Pagination
List endpoint defaults:

```text
page = 1
page_size = 20
max page_size = 100
```

Frontend tables should expose pagination controls and should not request page sizes above 100.

## URL Query Mapping
List-page filters should be represented in URL search params and mapped directly to backend query parameters where possible.

Rules:

- Omit empty filters instead of sending empty strings.
- Keep `page` and `page_size` in the URL for paginated pages.
- Reset `page` to `1` when filters change.
- Debounce free-text filters before sending API requests.
- Do not invent unsupported backend query parameters without adding a backend/API follow-up.
- Dashboard drill-down links should prefill the target list page query params.

## Dashboard
Page:

```text
/dashboard
```

Endpoint:

```text
GET /api/v1/admin/dashboard/summary
```

Query parameters:

- Date or date range, based on backend implementation.
- Region if supported.

Use for:

- Active workorders count.
- Completed workorders count.
- In-progress daily submissions count.
- Checked-out daily submissions count.
- Completed daily submissions count.
- Aggregate workorder progress metrics.

No Submission Yet dashboard widget:

```text
GET /api/v1/admin/dashboard/no-submission-yet
```

Query parameters:

- Selected date.

## Daily Submissions List
Page:

```text
/daily-submissions
```

Endpoint:

```text
GET /api/v1/admin/submissions
```

Supported filters from API spec:

- `work_date`
- `date_from`
- `date_to`
- `tester`
- `region`
- `shift`
- `submission_status`
- `workorder_status`
- `workorder_code`
- `ticket_number`
- `file_submission_pending`
- `page`
- `page_size`

Response items include:

- Daily submission fields.
- `file_submission_pending`.
- Nested workorder summary with aggregate progress values.

Frontend notes:

- Show `file_submission_pending` as "File Pending".
- Show remaining grids from nested workorder summary when available.
- Row click opens `/daily-submissions/[submissionId]`.

## Daily Submission Detail
Page:

```text
/daily-submissions/[submissionId]
```

Endpoint:

```text
GET /api/v1/admin/submissions/{submission_id}
```

Use for:

- Full daily submission fields.
- `file_submission_pending`.
- Nested workorder summary.

Audit endpoint:

```text
GET /api/v1/admin/submissions/{submission_id}/audit
```

Attachment history endpoint:

```text
GET /api/v1/admin/submissions/{submission_id}/attachments/history
```

Active attachment listing may use:

```text
GET /api/v1/submissions/{submission_id}/attachments
```

Only use tester-owned endpoint variants from admin web if backend permission rules allow admin access. Prefer admin-specific endpoints when they exist.

Integration checkpoint:

- First verify whether `GET /api/v1/admin/submissions/{submission_id}` already includes active attachment metadata.
- If it does, render active attachment state from the detail response.
- If it does not, verify admin access to `GET /api/v1/submissions/{submission_id}/attachments`.
- If neither path returns active attachment metadata for admins, create a backend/API follow-up before finalizing the attachment section.

## Edit Daily Submission
Action:

```text
PATCH /api/v1/admin/submissions/{submission_id}
```

Rules:

- Admin can edit any daily submission, including `COMPLETED`.
- Aggregate workorder totals after edit must not exceed parent `total_grids`.
- Child edit may move parent workorder between `ACTIVE` and `COMPLETED`.

Frontend behavior:

- Use edit drawer from detail page.
- Show backend validation errors.
- Invalidate submission detail, submissions list, workorder detail, and dashboard queries after success.

## Reopen Daily Submission
Action:

```text
POST /api/v1/admin/submissions/{submission_id}/reopen
```

Rules:

- Reopens completed daily submission back to `CHECKED_OUT`.
- Parent workorder may move back to `ACTIVE`.

Frontend behavior:

- Require confirmation.
- Explain parent workorder may reopen.
- Refresh affected detail/list/dashboard queries after success.

## Workorders List
Page:

```text
/workorders
```

Endpoint:

```text
GET /api/v1/admin/workorders
```

Supported filters:

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

## Workorder Detail
Page:

```text
/workorders/[workorderId]
```

Endpoint:

```text
GET /api/v1/admin/workorders/{workorder_id}
```

Response includes:

- Parent workorder fields.
- Aggregate progress values.
- Child daily submission list.

## Edit Workorder
Action:

```text
PATCH /api/v1/admin/workorders/{workorder_id}
```

Patchable fields in V1:

- `workorder_code`
- `region`
- `total_grids`

Rules:

- Normalized workorder code must remain globally unique.
- `total_grids` cannot be reduced below aggregate completed plus skipped.

Frontend behavior:

- Use edit drawer from detail page.
- Show guardrail warning before save.
- Show backend validation errors.
- Invalidate workorder detail, workorders list, submissions list, and dashboard queries after success.

## Users
Page:

```text
/users
```

Endpoint:

```text
GET /api/v1/admin/users
```

User detail:

```text
GET /api/v1/admin/users/{user_id}
```

Approval history:

```text
GET /api/v1/admin/users/{user_id}/approval-history
```

Suspend:

```text
POST /api/v1/admin/users/{user_id}/suspend
```

Frontend behavior:

- Show role and account status filters.
- Confirm before suspend.

## Pending Users
Page:

```text
/users/pending
```

Endpoint:

```text
GET /api/v1/admin/users/pending
```

Approve:

```text
POST /api/v1/admin/users/{user_id}/approve
```

Reject:

```text
POST /api/v1/admin/users/{user_id}/reject
```

Frontend behavior:

- Confirm reject.
- Admin requests should visually signal higher review risk.
- Refresh pending users and users list after mutation.

## No Submission Yet
Page:

```text
/no-submission-yet
```

Endpoint:

```text
GET /api/v1/admin/dashboard/no-submission-yet
```

Required query parameter:

- Selected date.

Important UI language:

- This means no daily submission record exists for selected date.
- This is not assignment-based in V1.

## Reports And Export
Page:

```text
/reports
```

Endpoint:

```text
GET /api/v1/admin/reports/submissions/export
```

Exports filtered daily submissions as CSV in V1.

Filters should mirror `GET /api/v1/admin/submissions` where supported.

Frontend behavior:

- Send filters as query parameters.
- Treat response as file/blob or text CSV, not JSON envelope.
- Use a meaningful filename such as:

```text
daily-submissions-YYYY-MM-DD.csv
```

## Attachment Download
To download a file:

```text
POST /api/v1/attachments/{attachment_id}/download-url
```

Response returns a signed download URL after permission checks.

Frontend behavior:

- Do not expose bucket/object paths as direct public URLs.
- Open signed URL after successful response.
- Show expiration or retry messaging if backend exposes it.

## Query Key Suggestions
Use stable query keys:

```text
["me"]
["dashboard", filters]
["daily-submissions", filters]
["daily-submission", submissionId]
["daily-submission-audit", submissionId]
["daily-submission-attachments-history", submissionId]
["workorders", filters]
["workorder", workorderId]
["users", filters]
["pending-users", filters]
["no-submission-yet", date]
```

Include normalized filter objects in list query keys. Avoid using raw `URLSearchParams` instances directly as query-key items.

## Error Handling
Show friendly messages for common backend error codes:

- `UNAUTHORIZED`
- `FORBIDDEN`
- `ACCOUNT_NOT_APPROVED`
- `ADMIN_ONLY`
- `VALIDATION_ERROR`
- `CONFLICT`
- `WORKORDER_CODE_ALREADY_EXISTS`
- `WORKORDER_PROGRESS_EXCEEDS_TOTAL`
- `SUBMISSION_NOT_COMPLETED`
- `SUBMISSION_NOT_CHECKED_OUT`
- `ATTACHMENT_REQUIRED_FOR_COMPLETION`
- `ACTIVE_ATTACHMENT_ALREADY_EXISTS`
- `UNSUPPORTED_FILE_TYPE`

Keep detailed backend error data available for field-level display when `details` is present.
