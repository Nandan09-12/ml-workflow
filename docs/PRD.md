# Product Requirements Document

## Product Name
ML Workflow

## V1 Module
DT Check-in

## Problem Statement
Drive testers currently submit operational progress manually through Google Sheets. This process is hard to manage, difficult to audit, error-prone, and not designed for structured reporting, approval, or field workflows that evolve across multiple days.

## Goal
Build a structured workflow application where drive testers create daily closeout submissions under multi-day workorders, while admins can review workorders, audit submissions, filter activity, edit records, and export operational data.

## Primary Users

### Drive Tester
Can:
- sign up
- request Drive Tester role
- log in
- wait for approval
- start a daily submission for a workorder
- update progress on the current day's submission
- end drive / check out the current day's submission
- upload or replace the daily CSV/XLSX closeout file
- complete the daily submission after receiving end-of-day counts
- continue the same workorder on a later day by creating a new daily submission under the same workorder
- view own daily submissions and statuses

### Admin
Can:
- sign up and request Admin role
- approve/reject/suspend users
- view all workorders
- view all daily submissions
- filter by date, tester, region, shift, workorder code, ticket, workorder status, and submission status
- view audit history
- edit workorders and daily submissions
- reopen completed daily submissions back to checked-out state
- view attachment history, including inactive file metadata
- export submission data
- view approved drive testers with no submission yet for a selected date

## V1 Scope

### Drive Tester Features
- email/password signup via Supabase Auth
- requested role selection during signup
- pending approval state after signup
- create daily submission through `Start Drive`
- manually enter `workorder_code`
- attach to an existing active workorder automatically when the code already exists
- create a new workorder automatically when the code does not exist yet
- update own `IN_PROGRESS` and `CHECKED_OUT` daily submission data
- update cumulative `completed_grids` during the day for that day only
- end drive / check out own daily submission
- upload or replace exactly one active CSV/XLSX closeout file per daily submission
- complete the daily submission after final daily data + file are ready
- view own daily submission history
- update own full name only in profile

### Admin Features
- approve, reject, or suspend users
- see pending users list
- see all workorders
- see all daily submissions
- see `ACTIVE` and `COMPLETED` workorders
- see `IN_PROGRESS`, `CHECKED_OUT`, and `COMPLETED` daily submissions
- see approved testers with no submission yet for selected date
- see attachment metadata and download files
- see inactive attachment metadata history
- see submission audit history
- edit workorders
- edit daily submissions
- reopen completed daily submissions to checked-out state
- export filtered daily submissions

## Workorder vs Daily Submission Model

### Workorder
A workorder is the parent business record that can stay open across multiple days and different drivers.

Workorder fields:
- Workorder Code
- Region
- Total Grids
- Workorder Status

### Daily Submission
A daily submission is the child record for one workorder on one work date.

Daily submission fields:
- Name (auto-filled snapshot)
- Email (auto-filled snapshot)
- Date
- Team Number
- Ticket Number
- Shift
- Completed Grids
- Skipped Grids
- Force Tested Grids
- Started At
- Ended At
- Submission Status
- Daily Closeout File

Derived / computed workorder values:
- Workorder Completed Grids
- Workorder Skipped Grids
- Workorder Remaining Grids
- Workorder Progress Percent
- File Submission Pending

## Allowed Values

### Region
Backend canonical values:
- `NE_UP`
- `CENTRAL`
- `SOUTH_FLORIDA`

Suggested UI labels:
- `NE-UP`
- `Central`
- `South/Florida`

### Shift
- `AM`
- `PM`

### Workorder Status
- `ACTIVE`
- `COMPLETED`

### Daily Submission Status
- `IN_PROGRESS`
- `CHECKED_OUT`
- `COMPLETED`

## V1 Daily Submission Lifecycle
1. Tester enters `workorder_code` and start-drive fields.
2. Backend normalizes the code.
3. If an active workorder already exists for that normalized code, backend attaches the daily submission to it.
4. If no active workorder exists, backend creates a new parent workorder using the entered `region` and grand `total_grids`.
5. Backend creates the daily submission in `IN_PROGRESS` and stamps `started_at`.
6. During the day, tester updates cumulative `completed_grids` for that one day.
7. Tester presses `End Drive`.
8. Backend stamps `ended_at` and moves the daily submission to `CHECKED_OUT`.
9. At end of day, tester receives the daily CSV/XLSX file and final `skipped_grids` / `force_tested_grids`.
10. Tester uploads the file and completes the daily submission.

## V1 Workorder Lifecycle
1. Day 1 creates the parent workorder.
2. Same driver or different driver on a later day enters the same `workorder_code`.
3. Backend attaches that day's daily submission to the same active workorder.
4. Aggregate workorder progress is computed from all child daily submissions.
5. When aggregate `completed_grids + skipped_grids = total_grids`, backend marks the parent workorder `COMPLETED`.
6. A later child reopen or last-file removal may move the parent workorder back to `ACTIVE` until the final daily closeout is complete again.

## V1 File + Completion Requirement
Each daily submission requires exactly one active closeout attachment in v1.

Daily completion rules:
- daily submission status must be `CHECKED_OUT`
- there must be exactly one active CSV/XLSX attachment on that daily submission
- end-of-day daily values must be present
- aggregate workorder totals must not exceed the parent workorder `total_grids`

Attachment behavior:
- one active file per daily submission
- Day 2's file may include Day 1 + Day 2 data; it is still the authoritative Day 2 closeout file
- files may be replaced after completion by deactivating the old file and uploading a new one
- inactive attachment metadata remains available to admins for history/review
- if the last active attachment is removed from a completed daily submission, that daily submission moves back to `CHECKED_OUT`
- if that daily submission was keeping the parent fully closed out, the parent workorder moves back to `ACTIVE`

Computed API indicator:
- expose `file_submission_pending` in daily submission list/detail responses
- `true` when daily submission is `CHECKED_OUT` and has zero active attachments
- `false` otherwise
- do not persist as a DB column in v1

Attachment constraints:
- exactly `1` active file per daily submission
- allowed extensions: `.csv`, `.xlsx`
- `.xls` is out of scope for v1

## Validation Requirements
- `workorder_code` is the real business identifier across days
- `workorder_code` is globally unique by normalized value
- normalization must preserve `-`
- whitespace is ignored during normalization
- one daily submission is allowed per `workorder + work_date`
- `region` belongs to the parent workorder and stays fixed across days
- `total_grids` belongs to the parent workorder and is the grand total across all days
- `completed_grids`, `skipped_grids`, and `force_tested_grids` on a daily submission are that day's contribution only
- `skipped_grids` are permanent for the workorder
- aggregate workorder progress cannot exceed `total_grids`
- future work dates are not allowed based on region-local date
- pagination defaults: `page=1`, `page_size=20`, max `page_size=100`

## Offline Requirement
Offline support is required for the tester app in the product vision. Initial web-first development is acceptable, but the architecture must support offline-first mobile sync later.

## Out of Scope for V1
- roster / assignment management
- edit approval workflow
- file content parsing or semantic validation
- backend-managed 4-hour reminder scheduling
- structured 4-hour checkpoint history table
- notifications by email/push
- workorder master-data management UI beyond automatic create/find by code
- team master-data management UI
- multi-client support
- multiple backend microservices

## Success Criteria
- users can sign up and be approved
- testers can submit daily data without Google Sheets
- testers can close out each day with required file + daily counts
- same workorder can continue across multiple days and drivers
- admins can review both workorders and daily submissions in one console
- completed workorders reflect aggregate child progress correctly
- checked-out daily submissions expose missing-file state via `file_submission_pending`
- all key changes are audit logged
- first admin bootstrap works safely and only once
