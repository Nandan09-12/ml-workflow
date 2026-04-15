# User Flows

## Drive Tester Signup Flow
1. user signs up via Supabase Auth
2. user selects requested role = `DRIVE_TESTER`
3. app calls bootstrap endpoint
4. app user record is created in `PENDING_APPROVAL`
5. user can log in
6. user sees waiting-for-approval state until approved

## Admin Signup Flow
1. user signs up via Supabase Auth
2. user selects requested role = `ADMIN`
3. app calls bootstrap endpoint
4. if no approved admins exist and user email is in `BOOTSTRAP_ADMIN_EMAILS`, user is auto-approved
5. otherwise app user record is created in `PENDING_APPROVAL`
6. existing approved admin reviews and approves/rejects/suspends

## Admin User Approval Flow
1. admin opens pending users page
2. admin reviews user request
3. admin approves or rejects
4. approval audit record is created
5. user account status updates accordingly

## Profile Update Flow
1. user opens profile
2. user edits `full_name`
3. user saves
4. system updates full name only

## Submission Create Flow
1. drive tester opens create submission form
2. date defaults to today
3. tester fills fields
4. backend normalizes cluster name into `cluster_name_normalized`
5. backend validates no future date by zone timezone
6. tester saves submission
7. submission is created as `ONGOING`
8. audit record is created

## Submission Edit Flow
1. tester opens one of their `ONGOING` submissions
2. tester edits values
3. tester saves changes
4. system validates grid math
5. system validates optimistic version
6. version increments
7. audit record is created

## Attachment Upload Flow
1. tester opens submission detail
2. tester uploads CSV/XLSX file
3. backend validates extension + MIME, size <= 25 MB, active attachment count <= 5
4. file is stored in Supabase Storage
5. metadata is stored in `submission_attachments`
6. audit record is created

## Complete Submission Flow
1. tester opens `ONGOING` submission
2. tester confirms values
3. tester clicks complete
4. backend checks `pending_grids = 0`
5. status becomes `COMPLETED`
6. system computes `file_submission_pending` from status + active attachment count
7. if `file_submission_pending = true`, tester UI shows warning to upload CSV/XLSX
8. audit record is created

## Admin Review Flow
1. admin opens submissions table
2. admin filters by date, zone, shift, status, tester, cluster, ticket, or `file_submission_pending`
3. admin opens submission detail page
4. admin reviews values, attachments, and audit history

## Admin Reopen Flow
1. admin opens completed submission
2. admin clicks reopen
3. system changes status to `ONGOING`
4. reopen metadata is saved
5. audit record is created

## No Submission Yet Flow
1. admin selects date
2. system compares approved drive testers to users with at least one submission on that date
3. admin sees users with no submission yet
4. UI clearly states this is not assignment-based
