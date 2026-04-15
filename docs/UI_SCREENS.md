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

### 3. My Submissions List
- list my submissions
- filters by date and status
- show `file_submission_pending` indicator for completed submissions with no active file
- create new submission button

### 4. Submission Form
- create or edit submission
- date picker defaulting to today
- zone dropdown
- shift dropdown
- numeric input fields
- save as ongoing
- block future dates by zone-local date rule

### 5. Submission Detail
- show all submission values
- show status
- show `file_submission_pending` warning when status is completed and no active attachment exists
- show attachment list
- upload attachment action
- complete submission action when `pending_grids = 0`
- show validation errors when attachment/type/size/count rules fail

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
- counts for approved testers, ongoing, completed, no submission yet
- date filter

### 4. Submissions Table
- filters: date, zone, shift, status, tester, cluster, ticket number, `file_submission_pending`
- pagination defaults: page 1, page size 20
- page size max 100
- export action

### 5. Submission Detail Page
- full submission info
- show `file_submission_pending` state
- attachment list with download buttons
- audit timeline
- admin edit action
- reopen action if completed

### 6. No Submission Yet Page
- approved drive testers with no submission for selected date
- note: not assignment-based

## Common UI States
- loading
- empty
- validation error
- permission denied
- success toast / confirmation
