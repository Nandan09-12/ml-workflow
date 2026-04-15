# Database Schema

## Core Tables
1. `app_users`
2. `user_approval_audit`
3. `submissions`
4. `submission_attachments`
5. `submission_audit_logs`

## Relationship Overview
- one app user can own many submissions
- one submission can have many attachments
- one submission can have many audit logs
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

## submissions

Fields:
- `id` (uuid, pk)
- `client_generated_id` (uuid, unique)
- `owner_user_id` (uuid, fk -> `app_users.id`)
- `submitter_name_snapshot` (varchar)
- `submitter_email_snapshot` (varchar)
- `zone` (enum)
- `work_date` (date)
- `shift` (enum)
- `team_number` (varchar, nullable)
- `ticket_number` (varchar, nullable)
- `cluster_name` (varchar)
- `cluster_name_normalized` (varchar)
- `number_of_grids` (int)
- `skipped_grids` (int)
- `force_tested_grids` (int)
- `pending_grids` (int)
- `completed_grids` (int)
- `status` (enum)
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
- `(owner_user_id, work_date, shift, cluster_name_normalized)`

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

## Enums

### requested_role / approved_role
- `DRIVE_TESTER`
- `ADMIN`

### account_status
- `PENDING_APPROVAL`
- `APPROVED`
- `REJECTED`
- `SUSPENDED`

### zone
- `NORTHEAST`
- `CENTRAL`
- `SOUTH_FLORIDA`

### shift
- `AM`
- `PM`

### submission_status
- `ONGOING`
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
- all grid counts are non-negative integers
- `completed + pending + skipped = number_of_grids`
- `skipped <= number_of_grids`
- `pending <= number_of_grids`
- `completed <= number_of_grids`
- completed submissions must have `pending_grids = 0`
- `force_tested_grids` is informational only

## Service-Layer Rules
These are enforced in backend services in addition to DB constraints:
- completion requires `pending_grids = 0`
- completion does not require attachment
- drive tester can edit only own ongoing submission
- drive tester cannot edit completed submission
- admin can reopen completed submission
- cluster normalization algorithm is applied before uniqueness checks
- work_date cannot be future relative to zone timezone
- pagination defaults and limits are enforced at API boundary
- attachment limits are enforced:
  - max 25 MB per file
  - max 5 active attachments per submission
  - extension + MIME validation

## Computed API Fields (Not Persisted)
- `file_submission_pending` is computed from submission status and active attachment count
- rule:
  - `true` when submission status is `COMPLETED` and active attachment count is `0`
  - `false` otherwise
- this is not a table column in v1
