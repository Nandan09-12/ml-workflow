# Admin Web Frontend Handoff

## Purpose
This file gives frontend agents the working context for building the V1 Admin Web console for the DT Check-in module.

Agents should approach this work like veteran frontend developers. Use the mockup and task list as product direction, but make implementation choices that support a real, maintainable admin console: clear boundaries, typed data flow, accessible controls, URL-driven list state, and components that can survive API integration without a rewrite.

The admin web app lives at:

```text
apps/admin-web
```

At the time this handoff was written, `apps/admin-web` has not been scaffolded yet. It only contains `.gitkeep`.

## Source Of Truth
Read these files before implementing:

- `README.md`
- `docs/PRD.md`
- `docs/BUSINESS_RULES.md`
- `docs/API_SPEC.md`
- `docs/DB_SCHEMA.md`
- `docs/USER_FLOWS.md`
- `docs/UI_SCREENS.md`
- `docs/ADMIN_WEB_FRONTEND_ENVIRONMENT.md`
- `docs/ADMIN_WEB_UI_SPEC.md`
- `docs/ADMIN_WEB_API_INTEGRATION.md`
- `docs/ADMIN_WEB_COMPONENTS.md`
- `docs/ui-mockups/adminui/index.html`

The static prototype is the visual and flow reference:

```text
docs/ui-mockups/adminui/index.html
```

## Product Context
ML Workflow V1 includes the DT Check-in module.

The backend domain model has two central records:

- Workorder: parent, multi-day business record.
- Daily Submission: child record for one work date under one workorder.

A workorder can span multiple days and different drive testers. A daily submission belongs to one workorder and one drive tester for one work date.

## Admin Web Audience
Only approved `ADMIN` users access the admin web app in V1.

`DRIVE_TESTER` users do not access the admin web app in V1. They appear inside admin pages as managed users and as owners of daily submissions, but their operational workflow belongs to the tester/mobile app.

Do not add a `VIEWER` role in V1 unless the backend docs and schema are intentionally changed first.

## Core Admin Jobs
The admin web app must help admins:

- Review operational progress for the selected date or date range.
- Review all workorders and their aggregate progress.
- Review all daily submissions and their file state.
- Approve, reject, and suspend users.
- See pending user requests.
- See approved drive testers with no daily submission record for a selected date.
- Edit workorders and daily submissions where necessary.
- Reopen completed daily submissions back to `CHECKED_OUT`.
- View attachment and audit context.
- Export filtered daily submission data.

## Key Terms
Use these terms consistently in UI copy and code:

- Workorder
- Daily Submission
- Drive Tester
- Admin
- Region
- Shift
- Ticket Number
- Completed Grids
- Skipped Grids
- Force Tested Grids
- Remaining Grids
- File Pending
- No Submission Yet

Do not use `cluster` in new admin UI except when explaining legacy data. Legacy `cluster_name` maps to `workorder_code`.

Do not expose `pending_grids` as editable state. In V1, pending-at-EOD is represented by computed remaining grids:

```text
remaining_grids = total_grids - (completed_grids + skipped_grids)
```

## Status Values
Daily Submission statuses:

- `IN_PROGRESS`
- `CHECKED_OUT`
- `COMPLETED`

Workorder statuses:

- `ACTIVE`
- `COMPLETED`

Account statuses:

- `PENDING_APPROVAL`
- `APPROVED`
- `REJECTED`
- `SUSPENDED`

Roles:

- `ADMIN`
- `DRIVE_TESTER`

Frontend display labels may be friendlier, but API payloads and internal types should use canonical values.

## Important Distinctions
No Submission Yet:

- Means an approved drive tester has no daily submission record for the selected date.
- It is not assignment-based in V1 because roster and assignment management are out of scope.

File Pending:

- Means a daily submission exists, has status `CHECKED_OUT`, and has zero active attachments.
- It does not mean no submission exists.

Remaining Grids:

- Computed from parent workorder total minus aggregate completed and skipped grids.
- It should not be typed manually by admins.

## MVP Route Map
Build these admin routes:

```text
/dashboard
/daily-submissions
/daily-submissions/[submissionId]
/workorders
/workorders/[workorderId]
/users
/users/pending
/no-submission-yet
/reports
```

The mockup has single-page hash navigation for discussion only. The real app should use Next.js routes.

The root route `/` should redirect to `/dashboard`.

## MVP Page Set
Dashboard:

- Summary cards and drill-downs for today or selected date range.

Daily Submissions:

- Dense operations table with filters and export action.

Daily Submission Detail:

- Full daily record, parent workorder summary, attachment state, attachment history, audit timeline, edit drawer, and reopen action.

Workorders:

- Parent workorder table with aggregate progress.

Workorder Detail:

- Parent workorder summary and child daily submissions.

Users:

- All app users with role and account-status filters.

Pending Users:

- Approval queue for pending role requests.

No Submission Yet:

- Approved drive testers with no daily submission record for selected date.

Reports:

- Filtered CSV export flow for daily submissions.

## Admin Edit UX Decision
For V1, do not implement inline editing in data tables.

Use detail pages and an edit drawer or modal:

- Daily submission edits happen from Daily Submission Detail.
- Workorder edits happen from Workorder Detail.
- Reopen is a separate explicit action from edit.
- Show warning copy when an edit can affect parent workorder progress or status.
- If an admin note field is not supported by the backend yet, treat it as a future design placeholder and do not send it to unsupported endpoints.

## Out Of Scope For Admin Web V1
Do not build these unless the product scope changes:

- Teams and kits management.
- Assignment or roster planning.
- Viewer role.
- Drive tester self-service web portal.
- Client-facing views.
- Advanced analytics.
- File content parsing.
- Structured checkpoint history.
- Notification scheduling.

## Implementation Approach
Build in layers:

1. Scaffold `apps/admin-web`.
2. Convert static mockup into reusable React components using mock data.
3. Add real route structure.
4. Add auth/session guard for approved admins.
5. Wire read endpoints.
6. Wire mutations.
7. Add smoke tests and UI checks.

Keep mock data available during early UI work so the app remains reviewable before backend integration is complete.

During the auth phase, build a simple real login shell. The admin pages may continue to use mock data until the API client and authenticated reads are wired.

## Frontend Quality Bar
Treat the static mockup as a product/design reference, not as final architecture.

Implementation should:

- Keep page route files thin.
- Keep reusable UI components outside route folders.
- Keep API access in a typed `lib/api` layer.
- Keep mock data in `lib/mock` so it can be replaced cleanly.
- Keep filters and pagination in URL search params for list pages.
- Keep status/region/date formatting in shared helpers.
- Use client components only where interactivity requires them.
- Avoid frontend-only business rules beyond helpful validation and warnings.
- Avoid adding unsupported backend concepts to make the UI easier.

The goal is an admin console that can grow into production code without a second rewrite.
