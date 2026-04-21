# Admin Web Frontend Tasks

## Purpose
This is the supporting ordered frontend backlog for building the DT Check-in Admin Web app.

Agents should execute these tasks with a veteran frontend developer mindset: do not merely recreate screens; build the foundation, boundaries, components, and state model that make the admin web reliable after mock data is replaced by real APIs.

The active implementation tracker is:

```text
docs/TASKS.md
```

If this file conflicts with `docs/TASKS.md`, use `docs/TASKS.md` and update this file afterward.

Follow this file alongside:

- `docs/ADMIN_WEB_FRONTEND_HANDOFF.md`
- `docs/ADMIN_WEB_FRONTEND_ENVIRONMENT.md`
- `docs/ADMIN_WEB_UI_SPEC.md`
- `docs/ADMIN_WEB_API_INTEGRATION.md`
- `docs/ADMIN_WEB_COMPONENTS.md`

## Phase 0 - Confirm Context
- Read the admin mockup at `docs/ui-mockups/adminui/index.html`.
- Read `docs/PRD.md`, `docs/BUSINESS_RULES.md`, and `docs/API_SPEC.md`.
- Confirm that admin web is only for approved `ADMIN` users.
- Confirm that `DRIVE_TESTER` users do not access admin web in V1.
- Confirm that there is no `VIEWER` role in V1.

## Phase 1 - Frontend Workspace Scaffold
- Add root `package.json` if missing.
- Add `pnpm-workspace.yaml` if missing.
- Scaffold `apps/admin-web` as a Next.js App Router TypeScript app.
- Add Tailwind CSS.
- Add lint and typecheck scripts.
- Add `.env.example`.
- Add `apps/admin-web/Dockerfile`.
- Add or update Docker Compose service for admin web.
- Add initial README or setup notes in `apps/admin-web` if useful.

Acceptance:

- `pnpm install` works.
- `pnpm --filter admin-web dev` starts the app locally.
- Docker dev path is documented and works when Docker is available.
- The default route renders a basic admin shell.

## Phase 2 - App Shell And Navigation
- Build sidebar with ML Technologies branding.
- Build topbar with page title, search placeholder, notification button, and current admin chip.
- Add responsive behavior for desktop and smaller screens.
- Add route structure for the MVP pages.
- Add active navigation state.

Routes:

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

Acceptance:

- All routes render.
- Sidebar navigation works.
- Layout is usable at desktop and tablet widths.

## Phase 3 - Shared UI Components
- Implement status badges.
- Implement metric cards.
- Implement filter bars.
- Implement data table wrapper.
- Implement progress bars.
- Implement empty states.
- Implement alerts.
- Implement edit drawer.
- Implement confirmation dialog.
- Implement page header and section panel components.

Acceptance:

- Pages do not duplicate table, badge, alert, or drawer styling.
- Components use canonical status values.
- Components have typed props.

## Phase 4 - Mock Data Pages
Build all MVP pages using local mock data first.

Dashboard:

- Summary cards.
- Workorder progress list.
- Admin queue for file pending, pending users, and no submission yet.
- Recent daily submissions table.

Daily Submissions:

- Dense table.
- Date, region, shift, submission status, file, and workorder filters.
- Export button placeholder.
- Row action to detail page.

Daily Submission Detail:

- Submission header and status.
- File pending alert when relevant.
- Daily values.
- Parent workorder summary.
- Active attachment section.
- Attachment history.
- Audit timeline.
- Edit drawer.
- Reopen confirmation placeholder.

Workorders:

- Workorder table.
- Region, status, code, and date filters.
- Aggregate progress and remaining grids.

Workorder Detail:

- Parent summary.
- Progress bar.
- Child daily submissions table.
- Edit drawer.
- Audit context.

Users:

- Users table.
- Role and account status filters.

Pending Users:

- Approval cards or table.
- Approve/reject placeholders.

No Submission Yet:

- Date filter.
- Clear best-effort explanation.
- Table of approved drive testers with no daily submission record.

Reports:

- Filter controls.
- Export CSV action placeholder.
- Export column summary.
- EOD snapshot.

Acceptance:

- UI matches the structure and spirit of `docs/ui-mockups/adminui`.
- All pages are reviewable without backend connectivity.
- No page uses unsupported roles or legacy `pending_grids`.

## Phase 5 - Auth And Access Guard
- Add Supabase Auth client setup.
- Add login flow if no authenticated user exists.
- Fetch current app user from `GET /api/v1/me`.
- Allow only approved admins.
- Block drive testers, pending users, rejected users, and suspended users.
- Add loading and access denied states.

Acceptance:

- Admin-only access logic is centralized.
- Auth token is available to API client.
- Unauthorized users cannot see admin pages.

## Phase 6 - API Client Layer
- Add typed API client wrapper for the backend response envelope.
- Add standard error mapping.
- Add TanStack Query provider.
- Add query keys.
- Add types for users, workorders, submissions, attachments, audit logs, and dashboard summary.
- Add CSV download helper for export endpoints.

Acceptance:

- API code is not embedded directly in page components.
- JSON envelope handling is centralized.
- File downloads bypass JSON envelope assumptions.

## Phase 7 - Read Endpoint Integration
Wire read flows:

- Dashboard summary.
- Daily submissions list.
- Daily submission detail.
- Daily submission audit.
- Daily submission attachment history.
- Workorders list.
- Workorder detail.
- Users list.
- Pending users list.
- No submission yet.

Acceptance:

- Filters map to backend query parameters.
- Pagination defaults follow backend contract.
- Empty, loading, and error states are present.

## Phase 8 - Mutations
Wire admin actions:

- Approve user.
- Reject user.
- Suspend user.
- Edit workorder.
- Edit daily submission.
- Reopen completed daily submission.
- Request attachment download URL.
- Export filtered submissions CSV.

Acceptance:

- Mutations invalidate or refresh affected queries.
- Destructive or high-impact actions use confirmation dialogs.
- Backend validation errors are shown near the relevant form or page action.

## Phase 9 - Forms And Validation
- Add Zod schemas for admin edit forms.
- Validate non-negative daily grid counts.
- Warn when a submission edit can affect parent aggregate progress.
- Warn when workorder total grids is below aggregate completed plus skipped.
- Do not attempt to enforce every backend rule client-side.

Acceptance:

- Frontend validation catches obvious input mistakes.
- Backend remains source of truth for business rules.

## Phase 10 - Testing And Polish
- Add route smoke tests.
- Add component tests for badges, tables, filters, and edit drawers.
- Add Playwright happy path tests:
  - Admin lands on dashboard.
  - Admin filters daily submissions.
  - Admin opens submission detail.
  - Admin opens edit drawer.
  - Admin opens no-submission-yet page.
- Verify responsive layouts.
- Verify accessible labels for icon-only buttons.

Acceptance:

- Lint, typecheck, and tests pass.
- The app can be reviewed through Docker and optional local pnpm.

## Non-Goals
- Do not build teams/kits management.
- Do not build assignment planning.
- Do not build viewer role.
- Do not build drive tester self-service admin-web pages.
- Do not parse uploaded CSV/XLSX content in frontend.
- Do not add advanced analytics.
