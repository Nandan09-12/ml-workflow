# User Flows

## Drive Tester Signup Flow
1. user signs up via Supabase Auth
2. user selects requested role = DRIVE_TESTER
3. app calls bootstrap endpoint
4. app user record is created in PENDING_APPROVAL
5. user can log in
6. user sees waiting-for-approval state until approved

## Admin Signup Flow
1. user signs up via Supabase Auth
2. user selects requested role = ADMIN
3. app calls bootstrap endpoint
4. app user record is created in PENDING_APPROVAL
5. existing admin reviews request
6. admin approves or rejects

## Admin User Approval Flow
1. admin opens pending users page
2. admin reviews user request
3. admin approves or rejects
4. audit record is created
5. user account status updates accordingly

## Submission Create Flow
1. drive tester opens create submission form
2. date defaults to today
3. tester fills fields
4. tester saves submission
5. submission is created as ONGOING
6. audit record is created

## Submission Edit Flow
1. tester opens one of their ONGOING submissions
2. tester edits values
3. tester saves changes
4. system validates grid math
5. version increments
6. audit record is created

## Attachment Upload Flow
1. tester opens submission detail
2. tester uploads CSV/XLSX file
3. file is stored in Supabase Storage
4. metadata is stored in submission_attachments
5. audit record is created

## Complete Submission Flow
1. tester opens ONGOING submission
2. tester confirms values
3. tester uploads required file if not already uploaded
4. tester clicks complete
5. backend checks attachment exists
6. backend checks pending_grids = 0
7. status becomes COMPLETED
8. audit record is created

## Admin Review Flow
1. admin opens submissions table
2. admin filters by date, zone, shift, status, or tester
3. admin opens a submission detail page
4. admin reviews values, attachments, and audit history

## Admin Reopen Flow
1. admin opens completed submission
2. admin clicks reopen
3. system changes status to ONGOING
4. reopen metadata is saved
5. audit record is created

## No Submission Yet Flow
1. admin selects date
2. system compares approved drive testers to users with at least one submission on that date
3. admin sees users with no submission yet
4. UI clearly states this is not assignment-based
