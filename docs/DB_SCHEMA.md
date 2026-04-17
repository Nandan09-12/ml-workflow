# Database Schema

## Core Tables
1. `app_users`
2. `user_approval_audit`
3. `workorders`
4. `submissions`
5. `submission_attachments`
6. `submission_audit_logs`

## Relationship Overview
- one app user can own many daily submissions
- one workorder can have many daily submissions
- one daily submission belongs to one workorder
- one daily submission can have many attachment rows, but only one active attachment in v1
- one daily submission can have many audit logs
- one app user can have many approval audit records

## app_users

Fields:
- `id` (uuid, pk)
- `auth_user_id` (uuid, unique, maps to Supabase `auth.users.id`)
- `full_name` (varchar)
- `email` (varchar, unique)
- `requested_role` (enum)
- `approved_role` (enum, nullable)
- `account_status` (enum)
- `approved_at` (timestamptz, nullable)
- `approved_by_user_id` (uuid, nullable, fk -> `app_users.id`)
- `last_login_at` (timestamptz, nullable)
- `created_at` (timestamptz)
- `updated_at` (timestamptz)

## user_approval_audit

Fields:
- `id` (uuid, pk)
- `user_id` (uuid, fk -> `app_users.id`)
- `requested_role` (enum)
- `decision` (enum)
- `reviewed_by_user_id` (uuid, fk -> `app_users.id`, nullable)
- `reviewed_at` (timestamptz, nullable)
- `review_notes` (text, nullable)
- `created_at` (timestamptz)

Notes:
- bootstrap auto-admin flow writes audit rows with `reviewed_by_user_id = null` and `review_notes = BOOTSTRAP_ADMIN_AUTO_APPROVED`

## workorders

Fields:
- `id` (uuid, pk)
- `workorder_code` (varchar)
- `workorder_code_normalized` (varchar)
- `region` (enum)
- `total_grids` (int)
- `status` (enum)
- `created_at` (timestamptz)
- `created_by_user_id` (uuid, fk -> `app_users.id`)
- `updated_at` (timestamptz)
- `updated_by_user_id` (uuid, fk -> `app_users.id`)
- `completed_at` (timestamptz, nullable)
- `completed_by_user_id` (uuid, fk -> `app_users.id`, nullable)

Unique constraint:
- `(workorder_code_normalized)`

Notes:
- `workorder_code` is the stable business identifier across days
- `workorder_code` is stored as entered for display
- `workorder_code_normalized` is used for matching/search/uniqueness
- `region` belongs to the parent workorder and stays fixed across days
- `total_grids` is the grand total for the whole workorder across all days
- a workorder is not owned by one tester because different drivers may work it on different days

## submissions

Fields:
- `id` (uuid, pk)
- `client_generated_id` (uuid, unique)
- `workorder_id` (uuid, fk -> `workorders.id`)
- `owner_user_id` (uuid, fk -> `app_users.id`)
- `submitter_name_snapshot` (varchar)
- `submitter_email_snapshot` (varchar)
- `work_date` (date)
- `shift` (enum)
- `team_number` (varchar, nullable)
- `ticket_number` (varchar)
- `completed_grids` (int)
- `skipped_grids` (int)
- `force_tested_grids` (int)
- `status` (enum)
- `started_at` (timestamptz)
- `ended_at` (timestamptz, nullable)
- `created_at` (timestamptz)
- `created_by_user_id` (uuid, fk -> `app_users.id`)
- `updated_at` (timestamptz)
- `updated_by_user_id` (uuid, fk -> `app_users.id`)
- `completed_at` (timestamptz, nullable)
- `completed_by_user_id` (uuid, fk -> `app_users.id`, nullable)
- `reopened_at` (timestamptz, nullable)
- `reopened_by_user_id` (uuid, fk -> `app_users.id`, nullable)
- `version_number` (int)

Unique constraint:
- `(workorder_id, work_date)`

Notes:
- one daily submission exists per workorder per day
- same driver or different driver may create the next day's daily submission under the same active workorder
- `shift` remains useful for reporting but does not define identity
- `completed_grids`, `skipped_grids`, and `force_tested_grids` are contribution counts for that one day only
- `skipped_grids` are permanent for the parent workorder

## submission_attachments

Fields:
- `id` (uuid, pk)
- `submission_id` (uuid, fk -> `submissions.id`)
- `file_name` (varchar)
- `bucket_name` (varchar)
- `object_path` (varchar)
- `mime_type` (varchar)
- `file_extension` (varchar)
- `file_size_bytes` (bigint)
- `uploaded_by_user_id` (uuid, fk -> `app_users.id`)
- `uploaded_at` (timestamptz)
- `is_active` (boolean)

Notes:
- exactly one active attachment is allowed per daily submission in v1
- attachment rows are soft-retained for admin-only history even after a tester removes or replaces a file

## submission_audit_logs

Fields:
- `id` (uuid, pk)
- `submission_id` (uuid, fk -> `submissions.id`)
- `action_type` (enum)
- `actor_user_id` (uuid, fk -> `app_users.id`)
- `actor_role` (enum or varchar)
- `source` (enum)
- `changed_fields_json` (jsonb, nullable)
- `before_snapshot_json` (jsonb, nullable)
- `after_snapshot_json` (jsonb, nullable)
- `created_at` (timestamptz)

Notes:
- audit logs remain the mutation trail for v1
- workorder create/attach/complete/reopen effects are recorded in the related daily submission audit trail in v1
- audit logs are not the same thing as a future structured 4-hour progress history table

## Enums

### requested_role / approved_role
- `DRIVE_TESTER`
- `ADMIN`

### account_status
- `PENDING_APPROVAL`
- `APPROVED`
- `REJECTED`
- `SUSPENDED`

### region
- `NE_UP`
- `CENTRAL`
- `SOUTH_FLORIDA`

UI labels:
- `NE-UP`
- `Central`
- `South/Florida`

### shift
- `AM`
- `PM`

### workorder_status
- `ACTIVE`
- `COMPLETED`

### submission_status
- `IN_PROGRESS`
- `CHECKED_OUT`
- `COMPLETED`

### approval_decision
- `PENDING`
- `APPROVED`
- `REJECTED`

### audit_action_type
- `CREATED`
- `UPDATED`
- `STATUS_CHANGED`
- `COMPLETED`
- `REOPENED`
- `FILE_UPLOADED`
- `FILE_REMOVED`

### audit_source
- `MOBILE`
- `WEB`
- `ADMIN_CONSOLE`
- `SYNC`

## Validation Constraints
- `workorders.total_grids` is a positive integer
- `workorder_code_normalized` is unique
- all daily submission grid counts are non-negative integers
- `force_tested_grids` is informational only

## Service-Layer Rules
These are enforced in backend services in addition to DB constraints:
- `Start Drive` normalizes `workorder_code` and finds or creates the parent workorder transactionally
- if a matching active workorder already exists, backend reuses the stored parent `region` and `total_grids`
- if the request includes parent fields while attaching to an existing workorder, those values must match the existing parent or the request is rejected
- if no matching active workorder exists, `region` and `total_grids` are required to create the new parent workorder
- no new daily submission may be created for a `COMPLETED` workorder
- drive tester can edit only own `IN_PROGRESS` or `CHECKED_OUT` daily submission
- drive tester cannot edit `COMPLETED` daily submission data
- drive tester may still upload, replace, or remove files after completion
- tester progress updates use cumulative `completed_grids` for the current day only
- aggregate `sum(child completed_grids) + sum(child skipped_grids)` cannot exceed parent `workorders.total_grids`
- `End Drive` stamps `ended_at` and changes daily submission status to `CHECKED_OUT`
- daily completion requires submission status `CHECKED_OUT`
- daily completion requires exactly one active CSV/XLSX attachment
- daily completion records end-of-day `skipped_grids` and `force_tested_grids`
- a workorder becomes `COMPLETED` automatically when aggregate child `completed_grids + skipped_grids = total_grids` and the triggering daily submission is completed
- if a completed child daily submission is reopened or loses its last active file, the parent workorder may move back to `ACTIVE`
- admin can view and edit any workorder and any daily submission, including `COMPLETED` ones
- admin can reopen `COMPLETED` daily submissions back to `CHECKED_OUT`
- `workorder_code` normalization algorithm is applied before lookup/search/uniqueness checks
- work_date cannot be future relative to the parent workorder region timezone
- pagination defaults and limits are enforced at API boundary
- attachment limits are enforced:
  - exactly 1 active attachment per daily submission
  - extension + MIME validation
- inactive attachment history is admin-only in v1

## Computed API Fields (Not Persisted)
- `file_submission_pending` is computed from daily submission status and active attachment count
- rule:
  - `true` when daily submission status is `CHECKED_OUT` and active attachment count is `0`
  - `false` otherwise
- workorder aggregate fields are computed from all child daily submissions:
  - `workorder_completed_grids = sum(child completed_grids)`
  - `workorder_skipped_grids = sum(child skipped_grids)`
  - `workorder_remaining_grids = total_grids - (completed + skipped)`
  - `workorder_progress_percent = (completed + skipped) / total_grids * 100`
- these are read-model fields, not new DB columns in v1
