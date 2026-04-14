# API Spec

## Base Path
`/api/v1`

## Authentication
All business endpoints require a valid Supabase JWT in the Authorization header.

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
PATCH /api/v1/me
Updates editable profile data.
Admin Users
GET /api/v1/admin/users/pending
List pending users.
GET /api/v1/admin/users
List all app users.
GET /api/v1/admin/users/{user_id}
Get one user.
POST /api/v1/admin/users/{user_id}/approve
Approve pending user.
POST /api/v1/admin/users/{user_id}/reject
Reject pending user.
POST /api/v1/admin/users/{user_id}/suspend
Suspend approved user.
GET /api/v1/admin/users/{user_id}/approval-history
Get approval history.
Submissions
POST /api/v1/submissions
Create a new submission. Status should effectively be created as ONGOING.
GET /api/v1/submissions
List my submissions.
Query params may include: - work_date - date_from - date_to - status - zone - shift - page - page_size
GET /api/v1/submissions/{submission_id}
Get my submission detail.
PATCH /api/v1/submissions/{submission_id}
Update my ongoing submission. Must include version_number for optimistic concurrency.
POST /api/v1/submissions/{submission_id}/complete
Complete an ongoing submission. Requirements: - active attachment exists - pending_grids = 0
Admin Submissions
GET /api/v1/admin/submissions
Admin list of all submissions. Supports filtering by date, tester, zone, shift, status, cluster, ticket number, etc.
GET /api/v1/admin/submissions/{submission_id}
Admin detail view.
PATCH /api/v1/admin/submissions/{submission_id}
Admin edits any submission.
POST /api/v1/admin/submissions/{submission_id}/reopen
Admin reopens completed submission.
GET /api/v1/admin/submissions/{submission_id}/audit
Get full audit history.
Attachments
POST /api/v1/submissions/{submission_id}/attachments
Upload CSV/XLSX file. Uses multipart/form-data.
GET /api/v1/submissions/{submission_id}/attachments
List submission attachments.
GET /api/v1/attachments/{attachment_id}
Get attachment metadata.
POST /api/v1/attachments/{attachment_id}/download-url
Returns signed download URL.
DELETE /api/v1/attachments/{attachment_id}
Soft remove attachment.
Dashboard / Reporting
GET /api/v1/admin/dashboard/summary
Returns dashboard counts for a date or date range.
GET /api/v1/admin/dashboard/no-submission-yet
Returns approved drive testers with no submission for selected date. Response must clearly state this is not assignment-based.
GET /api/v1/admin/reports/submissions/export
Exports filtered submissions as CSV in v1.
Mobile Sync
GET /api/v1/mobile/bootstrap
Returns reference data and current user state.
POST /api/v1/mobile/sync
Batch sync endpoint for future offline support.
Standard Error Codes
•	ACCOUNT_NOT_APPROVED
•	ADMIN_ONLY
•	SUBMISSION_ALREADY_EXISTS
•	INVALID_GRID_MATH
•	VERSION_CONFLICT
•	ATTACHMENT_REQUIRED_BEFORE_COMPLETE
•	PENDING_GRIDS_MUST_BE_ZERO
•	SUBMISSION_ALREADY_COMPLETED
•	SUBMISSION_NOT_COMPLETED
•	NOT_OWNER
•	UNSUPPORTED_FILE_TYPE
HTTP Status Guidance
•	200 OK
•	201 Created
•	204 No Content
•	400 Bad Request
•	401 Unauthorized
•	403 Forbidden
•	404 Not Found
•	409 Conflict
•	422 Unprocessable Entity
