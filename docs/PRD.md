# Product Requirements Document

## Product Name
ML Workflow

## V1 Module
DT Check-in

## Problem Statement
Drive testers currently submit operational progress manually through Google Sheets. This process is hard to manage, difficult to audit, error-prone, and not designed for structured reporting, approval, or offline-first field operations.

## Goal
Build a structured workflow application where drive testers can submit daily cluster/grid work data and admins can review, audit, filter, and export those submissions.

## Primary Users

### Drive Tester
Can:
- sign up
- request Drive Tester role
- log in
- wait for approval
- create submissions
- view own submissions
- edit own ongoing submissions
- upload CSV/XLSX file

### Admin
Can:
- sign up and request Admin role
- approve/reject/suspend users
- view all submissions
- filter by date, tester, zone, shift, cluster, status
- view audit history
- edit submissions
- reopen completed submissions
- export submission data
- view approved drive testers with no submission yet for a selected date

## V1 Scope

### Drive Tester Features
- email/password signup via Supabase Auth
- requested role selection during signup
- pending approval state after signup
- create submission
- update own ongoing submission
- upload CSV/XLSX attachment
- mark submission completed
- view own submission history
- update own full name only in profile

### Admin Features
- approve, reject, or suspend users
- see pending users list
- see all submissions
- see ongoing and completed submissions
- see approved testers with no submission yet for selected date
- see attachment metadata and download files
- see submission audit history
- export filtered submissions
- reopen completed submission

## Submission Fields
- Name (auto-filled snapshot)
- Email (auto-filled snapshot)
- Zone
- Date
- Team Number
- Ticket Number
- Shift
- Cluster Name
- Number of Grids
- Skipped Grids
- Force Tested Grids
- Pending Grids
- Completed Grids
- Status

## Allowed Values

### Zone
- NORTHEAST
- CENTRAL
- SOUTH_FLORIDA

### Shift
- AM
- PM

### Status
- ONGOING
- COMPLETED

## V1 File Upload Requirement
Submission completion does not require an attachment in v1.

Completion rule:
- `pending_grids` must be `0`

Computed API indicator:
- expose `file_submission_pending` in submission list/detail responses
- `true` when submission is `COMPLETED` and has zero active attachments
- `false` otherwise
- do not persist as a DB column in v1

Attachment constraints:
- max 25 MB per file
- max 5 active attachments per submission
- allowed extensions: `.csv`, `.xlsx`
- `.xls` is out of scope for v1

## Validation Requirements
- cluster normalization is required before uniqueness checks
- future work dates are not allowed based on zone-local date
- pagination defaults: `page=1`, `page_size=20`, max `page_size=100`

## Offline Requirement
Offline support is required for the tester app in the product vision. Initial web-first development is acceptable, but the architecture must support offline-first mobile sync later.

## Out of Scope for V1
- roster / assignment management
- edit approval workflow
- file content parsing or semantic validation
- notifications by email/push
- cluster master-data management UI
- team master-data management UI
- multi-client support
- multiple backend microservices

## Success Criteria
- users can sign up and be approved
- testers can submit data without Google Sheets
- admins can review all submissions in one console
- completed records enforce `pending_grids = 0` and expose missing-file state via `file_submission_pending`
- all key changes are audit logged
- first admin bootstrap works safely and only once
