```md
# Business Rules

## User / Access Rules
- users sign up through Supabase Auth
- users choose requested role during signup
- roles in v1: DRIVE_TESTER, ADMIN
- new users start in PENDING_APPROVAL
- pending users can log in but cannot use module features
- only approved admins can approve, reject, or suspend users

## Submission Ownership Rules
- a drive tester can create only their own submissions
- a drive tester can edit only their own submissions
- a drive tester can edit only while submission status is ONGOING
- a drive tester cannot edit a COMPLETED submission
- an admin can view and edit any submission
- an admin can reopen a COMPLETED submission back to ONGOING

## Submission Uniqueness Rule
A submission is unique by:
- owner_user_id
- work_date
- shift
- cluster_name_normalized

## Grid Math Rules
- all numeric fields must be non-negative
- completed_grids + pending_grids + skipped_grids = number_of_grids
- skipped_grids cannot exceed number_of_grids
- pending_grids cannot exceed number_of_grids
- completed_grids cannot exceed number_of_grids
- force_tested_grids is informational only

## Completion Rules
A submission cannot be marked COMPLETED unless:
- at least one active attachment exists
- pending_grids = 0

## Attachment Rules
- allowed file types in v1: CSV and XLSX
- actual file stored in Supabase Storage
- metadata stored in submission_attachments
- private bucket required
- signed download URL should be generated after permission check

## Date Rules
- frontend should default work_date to today
- frontend should use a date picker rather than free-text entry
- drive testers should not be allowed to set future dates

## Admin Reporting Rules
- admin can view ONGOING submissions
- admin can view COMPLETED submissions
- admin can view approved drive testers with no submission yet for a selected date
- no-submission-yet view is best-effort only and not roster-based

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
