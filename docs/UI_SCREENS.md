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
- create new submission button

### 4. Submission Form
- create or edit submission
- date picker defaulting to today
- zone dropdown
- shift dropdown
- numeric input fields
- save as ongoing

### 5. Submission Detail
- show all submission values
- show status
- show attachment list
- upload attachment action
- complete submission action if valid
- audit summary if desired later

## Admin Web Screens

### 1. Pending Users Page
- list pending users
- filters by requested role
- approve / reject actions

### 2. All Users Page
- list all users
- filter by role and account status
- user detail link

### 3. Dashboard Summary Page
- counts for approved testers, ongoing, completed, no submission yet
- date filter

### 4. Submissions Table
- filters: date, zone, shift, status, tester, cluster, ticket number
- pagination
- export action

### 5. Submission Detail Page
- full submission info
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
