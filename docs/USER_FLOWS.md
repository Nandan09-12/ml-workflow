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

## Start Drive / Workorder Resolve Flow
1. approved drive tester opens `Start Drive`
2. tester enters `workorder_code`
3. backend normalizes the code
4. if an active workorder exists:
   - system returns the existing parent workorder
   - UI reuses the stored `region` and grand `total_grids`
5. if no active workorder exists:
   - tester provides `region` and grand `total_grids`
   - backend creates the parent workorder
6. tester enters daily fields:
   - `work_date`
   - `shift`
   - `team_number`
   - `ticket_number`
7. tester presses `Start Drive`
8. daily submission is created as `IN_PROGRESS`
9. backend stamps `started_at`
10. audit record is created

## Daily Progress Update Flow
1. tester opens one of their `IN_PROGRESS` daily submissions
2. tester is prompted during the day to enter the latest cumulative `completed_grids` for that day
3. tester saves changes
4. backend validates optimistic version
5. backend validates aggregate workorder totals do not exceed parent `total_grids`
6. version increments
7. audit record is created

## End Drive Flow
1. tester opens an `IN_PROGRESS` daily submission
2. tester presses `End Drive`
3. backend stamps `ended_at`
4. daily submission status changes to `CHECKED_OUT`
5. audit record is created

## Daily File Upload Flow
1. tester opens daily submission detail
2. tester uploads the daily CSV/XLSX file
3. backend validates extension + MIME and exactly-one-active-file rule
4. file is stored in Supabase Storage
5. metadata is stored in `submission_attachments`
6. audit record is created

## Complete Daily Submission Flow
1. tester opens `CHECKED_OUT` daily submission
2. tester enters final `completed_grids`, `skipped_grids`, and `force_tested_grids`
3. tester confirms the daily closeout file is attached
4. tester clicks `Complete Submission`
5. backend validates exactly one active attachment exists
6. backend validates aggregate child totals do not exceed parent `total_grids`
7. daily submission status becomes `COMPLETED`
8. if aggregate workorder totals now equal grand `total_grids`, parent workorder becomes `COMPLETED`
9. audit record is created

## Next Day Continuation Flow
1. same driver or different driver opens `Start Drive` on a later day
2. tester enters the same `workorder_code`
3. backend finds the same active parent workorder by normalized code
4. backend creates a new daily submission for the new `work_date`
5. the previous day's submission remains completed; it does not stay open overnight

## Completed Daily File Change Flow
1. tester opens a `COMPLETED` daily submission
2. tester may remove the active file and upload a replacement
3. backend keeps inactive file metadata for admin-only history
4. if the active file is removed, daily submission status changes back to `CHECKED_OUT`
5. if that daily submission was keeping the parent workorder fully closed out, the parent workorder changes back to `ACTIVE`
6. tester cannot directly edit completed daily submission data fields
7. if data changes are needed, tester coordinates with admin

## Admin Workorder Review Flow
1. admin opens workorders table
2. admin filters by workorder code, region, status, or date range
3. admin opens workorder detail page
4. admin reviews parent workorder fields, aggregate progress, child daily submissions, and related audit context

## Admin Daily Submission Review Flow
1. admin opens daily submissions table
2. admin filters by date, region, shift, tester, workorder code, submission status, workorder status, ticket, or `file_submission_pending`
3. admin opens daily submission detail page
4. admin reviews daily values, active attachment, inactive attachment history, and audit history

## Admin Edit Flow
1. admin opens any workorder or daily submission
2. admin updates fields as needed
3. system writes audit records for the admin edit
4. parent workorder progress/status is recomputed if child totals changed
5. testers can see the updated result but do not edit completed daily data directly

## Admin Reopen Daily Submission Flow
1. admin opens completed daily submission
2. admin clicks reopen
3. system changes daily submission status to `CHECKED_OUT`
4. reopen metadata is saved
5. if the parent workorder had been fully complete, it may move back to `ACTIVE`
6. audit record is created

## No Submission Yet Flow
1. admin selects date
2. system compares approved drive testers to users with at least one daily submission on that date
3. admin sees users with no daily submission yet
4. UI clearly states this is not assignment-based
