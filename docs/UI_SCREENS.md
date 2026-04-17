# UI Screens

## Tester App Screens

### 1. Login / Signup
- sign in
- sign up
- choose requested role

### 2. Pending Approval Screen
- explain that account is awaiting admin approval
- show current requested role
- optionally allow logout

### 3. My Daily Submissions List
- list my daily submissions
- filters by date and daily submission status
- show workorder code on each row
- show current daily submission status: `IN_PROGRESS`, `CHECKED_OUT`, `COMPLETED`
- show current parent workorder status: `ACTIVE`, `COMPLETED`
- show `file_submission_pending` indicator for checked-out daily submissions with no active file
- show aggregate workorder progress summary
- `Start Drive` button

### 4. Start Drive Form
- start a new daily submission
- workorder code field
- lookup existing active workorder by code
- if workorder exists:
  - show stored region
  - show stored grand total grids
  - show current aggregate workorder progress
- if workorder does not exist:
  - region dropdown
  - total grids input
- date picker defaulting to today
- shift dropdown
- team number field
- ticket number field
- `Start Drive` action
- block future dates by region-local date rule

### 5. Daily Submission Detail
- show daily submission values
- show daily submission status
- show parent workorder summary:
  - workorder code
  - region
  - grand total grids
  - aggregate completed/skipped/remaining/progress
- show `started_at` and `ended_at`
- show active attachment
- upload attachment action
- `End Drive` action when daily status is `IN_PROGRESS`
- `Complete Submission` action when daily status is `CHECKED_OUT` and file requirement is satisfied
- show `file_submission_pending` warning when daily status is `CHECKED_OUT` and no active attachment exists
- show validation errors when attachment/type rules or aggregate workorder limit rules fail
- tester may manage files after daily completion but cannot directly edit completed daily submission data

### 6. Profile Screen
- show profile details
- edit `full_name` only

## Admin Web Screens

### 1. Pending Users Page
- list pending users
- filters by requested role
- approve / reject actions

### 2. All Users Page
- list all users
- filter by role and account status
- user detail link
- suspend action for approved users

### 3. Dashboard Summary Page
- counts for approved testers
- counts for active vs completed workorders
- counts for in-progress / checked-out / completed daily submissions
- date filter
- aggregate workorder progress widgets
- future versions may add progress trend metrics without redesigning the core workorder + daily submission model

### 4. Workorders Table
- filters: workorder code, region, workorder status, date range
- show aggregate completed/skipped/remaining/progress
- pagination defaults: page 1, page size 20
- page size max 100
- workorder detail link

### 5. Workorder Detail Page
- full parent workorder info
- aggregate progress summary
- child daily submissions list
- admin edit action for parent fields
- related audit context

### 6. Daily Submissions Table
- filters: date, region, shift, submission status, workorder status, tester, workorder code, ticket number, `file_submission_pending`
- pagination defaults: page 1, page size 20
- page size max 100
- export action

### 7. Daily Submission Detail Page
- full daily submission info
- parent workorder summary
- show `file_submission_pending` state
- active attachment with download button
- attachment history section for inactive/removed files
- audit timeline
- admin edit action
- reopen action if completed

### 8. No Submission Yet Page
- approved drive testers with no daily submission for selected date
- note: not assignment-based

## Common UI States
- loading
- empty
- validation error
- permission denied
- success toast / confirmation
