# Active Tasks - Admin Web UI

## Purpose
This is the active execution task list for building the V1 DT Check-in Admin Web UI.

Agents working from this file should behave like veteran frontend developers: protect the product model, choose maintainable architecture over quick mockup ports, keep user workflows clear, and leave the app easier for the next engineer to extend.

Backend/project-wide historical tasks are kept in:

```text
docs/BACKENDTASKS.md
```

Frontend context and specs are kept in:

```text
docs/ADMIN_WEB_FRONTEND_HANDOFF.md
docs/ADMIN_WEB_FRONTEND_ENVIRONMENT.md
docs/ADMIN_WEB_UI_SPEC.md
docs/ADMIN_WEB_API_INTEGRATION.md
docs/ADMIN_WEB_COMPONENTS.md
docs/ADMIN_WEB_FRONTEND_TASKS.md
docs/ui-mockups/adminui/index.html
```

If this file conflicts with `docs/ADMIN_WEB_FRONTEND_TASKS.md`, use this file as the active implementation tracker and update the other doc afterward.

## Current Frontend State
At the time this file was written:

- `apps/admin-web` is scaffolded as a Next.js App Router TypeScript app.
- Shared layout, route shell, mock-data pages, and reusable UI primitives are in place.
- URL-driven filter and pagination state is implemented for Daily Submissions, Workorders, and Users.
- Mock-data detail surfaces use shared definition-list and timeline primitives.
- Unit coverage includes route smoke tests, layout behavior, detail-page rendering, and URL-state behavior for the current list pages.
- Static admin UI mockups exist under `docs/ui-mockups/adminui`.
- Admin web default port is `3000`.
- API default base URL is `http://localhost:8000/api/v1`.
- Official frontend dev path is Docker-first.
- Optional local dev path is Node.js LTS plus pnpm.
- `SUPABASE_URL` exists in the API env and can be mirrored as `NEXT_PUBLIC_SUPABASE_URL`.
- The frontend also needs `NEXT_PUBLIC_SUPABASE_ANON_KEY`; do not use the API service role key in frontend code or env.
- Repo-level GitHub Actions checks now include an `admin-web-checks` job for lint, typecheck, unit tests, and production build.

## Implementation Checkpoint

- Wave 1 and Wave 2 foundation work is complete for the frontend mock/review layer.
- Completed scope includes scaffold, Docker/workspace integration, shared shell, all required routes, mock-data review pages, shared UI primitives, and URL-driven list-state foundations for Daily Submissions, Workorders, and Users.
- Current verification baseline is `pnpm --filter admin-web test`, `pnpm --filter admin-web typecheck`, `pnpm --filter admin-web lint`, and `pnpm --filter admin-web build` all passing.
- Remaining work begins at real auth, API integration, mutations, and export wiring. Treat that as the next wave of implementation, not unfinished scaffold work.

## Product Guardrails
Agents must follow these rules:

- Admin web is only for approved `ADMIN` users.
- `DRIVE_TESTER` users do not access admin web in V1.
- Do not add a `VIEWER` role in V1.
- Do not build drive tester screens inside `apps/admin-web`.
- Do not build teams/kits management in V1.
- Do not build assignment or roster planning in V1.
- Do not use legacy `cluster` terminology in new admin UI.
- Treat legacy cluster as `workorder_code`.
- Do not expose `pending_grids` as editable UI state.
- Show remaining grids as computed: `total_grids - (completed_grids + skipped_grids)`.
- Keep `No Submission Yet` separate from `File Pending`.
- `No Submission Yet` means no daily submission record exists for the selected date.
- `File Pending` means a checked-out daily submission exists with no active attachment.
- Use detail pages and edit drawers for admin edits, not inline table editing.
- Reopen is a separate explicit action from edit.

## Frontend Architecture Guardrails
Build the admin web as a maintainable production app, not a static port of the mockup.

- Use Next.js App Router.
- Keep route files thin. Put reusable UI in `components/` and data/API logic in `lib/`.
- Prefer server components for static layout and shell structure.
- Use client components only for interactivity, auth/session state, filters, drawers, dialogs, and TanStack Query.
- Keep all mock data in one obvious location such as `lib/mock/`; do not bury mock arrays inside page components.
- Make table filters and pagination URL-driven with search params so admin drill-downs and shared links preserve state.
- Do not add client-side sorting/filtering that conflicts with backend pagination. If backend does not support a filter/sort, mark it as UI-only mock or defer it.
- Centralize API calls in a typed client. Page components should not call `fetch` directly.
- Centralize status labels, status colors, region labels, date formatting, and error mapping.
- Do not expose service role secrets or backend-only env vars to client code.
- Keep the app reviewable with mock data before API wiring, but make it easy to remove or bypass mock data later.

## Required Routes
Build these real Next.js routes:

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

The root route `/` must redirect to `/dashboard`.

## Phase 0 - Read And Confirm Context
- Read `docs/ADMIN_WEB_FRONTEND_HANDOFF.md`.
- Read `docs/ADMIN_WEB_FRONTEND_ENVIRONMENT.md`.
- Read `docs/ADMIN_WEB_UI_SPEC.md`.
- Read `docs/ADMIN_WEB_API_INTEGRATION.md`.
- Read `docs/ADMIN_WEB_COMPONENTS.md`.
- Review static mockup at `docs/ui-mockups/adminui/index.html`.
- Confirm `apps/admin-web` current state before editing.
- Confirm port `3000` availability or document alternate dev port if occupied.

Acceptance:

- Agent can explain the workorder/daily-submission model.
- Agent can explain the difference between `No Submission Yet` and `File Pending`.
- Agent knows Docker is the official dev path and pnpm is the package manager.

## Phase 1 - Workspace And Docker Scaffold
- Add root `package.json` if missing.
- Add `pnpm-workspace.yaml` if missing.
- Scaffold `apps/admin-web` as a Next.js App Router TypeScript app.
- Add `apps/admin-web/package.json`.
- Add `apps/admin-web/tsconfig.json`.
- Add `apps/admin-web/next.config.ts`.
- Add Tailwind CSS config.
- Add PostCSS config.
- Add ESLint config.
- Add app-level README or setup note if useful.
- Add `apps/admin-web/.env.example`.
- Add `apps/admin-web/Dockerfile`.
- Add `admin-web` service to `docker-compose.yml`.
- Expose `3000:3000` for admin web.
- Keep the API service on port `8000`.
- Configure the dev command to run `pnpm dev`.
- Preserve local source mounting for fast iteration.
- Preserve container `node_modules` through a volume.
- Add scripts for `dev`, `build`, `lint`, `typecheck`, `test`, and later `test:e2e`.
- Add a basic `README.md` inside `apps/admin-web` with Docker and local pnpm commands.

Acceptance:

- `pnpm install` works from repo root.
- `pnpm --filter admin-web dev` starts admin web locally.
- `pnpm --filter admin-web lint` runs.
- `pnpm --filter admin-web typecheck` runs.
- `docker compose up admin-web` starts admin web in Docker.
- API and admin web can be run together through Docker Compose for integration work.
- The app renders on `http://localhost:3000`.
- `.env.example` includes `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

## Phase 1.5 - Project Structure And Frontend Boundaries
- Create a clear app structure before building screens.
- Use route folders for the required routes.
- Use `app/page.tsx` only to redirect `/` to `/dashboard`.
- Add a provider boundary for client-only providers such as TanStack Query and Supabase session state.
- Add `lib/api/` for typed API functions.
- Add `lib/types/` or `types/` for shared frontend types.
- Add `lib/mock/` for mock data.
- Add `lib/format/` for labels, dates, numbers, and status formatting.
- Add `lib/config/` for public env handling.
- Add `components/layout/`, `components/ui/`, and `components/features/` or similarly clear folders.

Suggested structure:

```text
apps/admin-web/
  app/
    page.tsx
    layout.tsx
    providers.tsx
    dashboard/
    daily-submissions/
    workorders/
    users/
    no-submission-yet/
    reports/
  components/
    layout/
    ui/
    features/
  lib/
    api/
    config/
    format/
    mock/
    query/
    types/
  public/
```

Acceptance:

- Route files stay small.
- Mock data has one clear home.
- API code has one clear home.
- Client-only providers are isolated from server component layout where practical.

## Phase 2 - Static Assets And Theme Foundation
- Copy approved ML Technologies logo into `apps/admin-web/public`.
- Do not reference files from `docs/ui-mockups` at runtime.
- Implement Tailwind theme tokens for colors, spacing, borders, and status colors.
- Keep the style close to the static mockup.
- Add global CSS.
- Add base page metadata.

Acceptance:

- Logo renders in the admin sidebar.
- Theme supports dense tables, status badges, panels, filters, and drawers.
- UI does not depend on external image URLs.

## Phase 3 - Shared Components
Implement reusable components before building pages:

- `AdminShell`
- `Sidebar`
- `Topbar`
- `PageHeader`
- `Panel`
- `StatusBadge`
- `MetricCard`
- `ProgressBar`
- `DataTable`
- `TableToolbar`
- `Pagination`
- `FilterBar`
- `DateFilter`
- `DateRangeFilter`
- `RegionFilter`
- `ShiftFilter`
- `SubmissionStatusFilter`
- `WorkorderStatusFilter`
- `FilePendingFilter`
- `SearchInput`
- `Alert`
- `EmptyState`
- `LoadingState`
- `ErrorState`
- `EditDrawer`
- `ConfirmationDialog`
- `Timeline`
- `DefinitionList`

Acceptance:

- Components are typed.
- Components use canonical backend status values.
- Icon-only buttons have accessible labels.
- No page duplicates table, badge, drawer, or alert styling.
- Data table, filter, drawer, and dialog components are controlled and reusable.
- Components do not import mock data directly unless they are story/demo wrappers.

## Phase 4 - Routing And App Shell
- Create route groups or folders for all required routes.
- Redirect `/` to `/dashboard`.
- Implement the shared admin layout.
- Add sidebar navigation.
- Add active route styling.
- Add topbar with page title and current admin display placeholder.
- Add responsive behavior for desktop, tablet, and narrow screens.

Acceptance:

- All required routes render.
- `/` redirects to `/dashboard`.
- Navigation works without page errors.
- Layout is usable at desktop and tablet widths.
- Mobile/narrow width remains readable even if the primary admin target is desktop.

## Phase 5 - Mock Data Pages
Build all pages using local mock data before backend integration.

Dashboard:

- Summary metric cards.
- Workorder progress list.
- Admin queue for file pending, pending users, and no submission yet.
- Recent daily submissions table.
- Drill-down links into list pages.

Daily Submissions:

- Dense operations table.
- Filters for date, region, shift, tester/search, workorder code, ticket, submission status, workorder status, and file pending.
- Export button placeholder.
- Row action to detail page.
- Store filters and pagination in the URL query string.

Daily Submission Detail:

- Header with tester, workorder, date, shift, ticket, and badges.
- Daily values section.
- Parent workorder summary.
- Active attachment section.
- Attachment history section.
- Audit timeline.
- File pending warning.
- Edit drawer.
- Reopen confirmation placeholder.

Workorders:

- Parent workorder table.
- Filters for workorder code, region, status, date from, and date to.
- Aggregate completed/skipped/remaining/progress.
- Row action to detail page.
- Store filters and pagination in the URL query string.

Workorder Detail:

- Parent summary.
- Progress bar.
- Child daily submissions table.
- Edit drawer.
- Guardrail notes.
- Audit context.

Users:

- Users table.
- Role filter.
- Account status filter.
- Suspend placeholder action.
- Store filters and pagination in the URL query string when useful.

Pending Users:

- Pending approval table or cards.
- Approve and reject placeholders.
- Role filter.

No Submission Yet:

- Date filter.
- Explanation that this is not assignment-based.
- Table of approved drive testers with no daily submission record.

Reports:

- Export filters.
- CSV export placeholder.
- Export column summary.
- EOD snapshot.

Acceptance:

- The real app visually and structurally matches the static mockup direction.
- All pages are reviewable without API connectivity.
- No page uses unsupported roles or legacy editable `pending_grids`.
- Mock data lives outside route/page files.
- Drill-down links preserve intended filters through URL search params.

## Phase 6 - Supabase Auth And Admin Guard
- Add Supabase browser client.
- Build a simple real login shell.
- Add login/session flow.
- Read Supabase access token.
- Call `GET /api/v1/me` after auth.
- Allow access only when:
  - `approved_role = ADMIN`
  - `account_status = APPROVED`
- Block `DRIVE_TESTER`, pending, rejected, and suspended users.
- Add loading state while checking session.
- Add access denied state.
- Add sign-out action.
- Keep session/token handling in one auth boundary or hook.
- Avoid reading private server-only env vars from client components.

Acceptance:

- Admin-only guard is centralized.
- Unauthorized users cannot view admin pages.
- Backend JWT is available to API requests.

## Phase 7 - API Client And Types
- Add typed API client wrapper.
- Centralize JSON response envelope parsing.
- Centralize error response parsing.
- Add file/CSV download helper that does not expect JSON envelope.
- Add TanStack Query provider.
- Add stable query keys.
- Add TypeScript types for:
  - current user
  - app users
  - approval history
  - workorders
  - workorder summaries
  - daily submissions
  - submission attachments
  - attachment history
  - audit logs
  - dashboard summary
  - no-submission-yet response
- Add status/region label helpers.
- Add date/time formatting helpers.
- Add remaining-grid display helper where backend does not already provide the computed value.
- Add request helpers for query-string construction so filters map consistently to backend names.
- Add safe handling for empty string filters so the frontend does not send meaningless query params.

Acceptance:

- Page components do not call `fetch` directly.
- API base URL comes from `NEXT_PUBLIC_API_BASE_URL`.
- API errors surface useful messages from backend envelopes.
- CSV/file downloads bypass JSON envelope parsing.
- Types are shared between list/detail/edit surfaces instead of redefined per page.

## Phase 8 - Dashboard API Integration
- Wire `GET /api/v1/admin/dashboard/summary`.
- Wire no-submission-yet count/list where needed.
- Add date/date-range query parameters according to the actual backend route contract before wiring.
- Add loading, empty, and error states.
- Add dashboard drill-down links with filters.

Acceptance:

- Dashboard reflects API data.
- Summary cards drill into the right pages.
- Dashboard does not fabricate backend-only metrics that are not available.

## Phase 9 - Users API Integration
- Wire `GET /api/v1/admin/users`.
- Wire `GET /api/v1/admin/users/pending`.
- Wire `GET /api/v1/admin/users/{user_id}` if a user detail surface is built.
- Wire `GET /api/v1/admin/users/{user_id}/approval-history` where shown.
- Wire approve action.
- Wire reject action.
- Wire suspend action.
- Add confirmation dialogs for reject and suspend.
- Refresh affected queries after mutation.

Acceptance:

- Pending users can be approved/rejected from UI.
- Users can be suspended from UI if action is exposed.
- Backend validation and permission errors display cleanly.

## Phase 10 - Daily Submissions API Integration
- Wire `GET /api/v1/admin/submissions`.
- Map filters to backend query parameters.
- Wire pagination.
- Wire `GET /api/v1/admin/submissions/{submission_id}`.
- Wire `GET /api/v1/admin/submissions/{submission_id}/audit`.
- Wire `GET /api/v1/admin/submissions/{submission_id}/attachments/history`.
- Confirm how active attachment metadata is exposed:
  - Prefer active attachment data from submission detail if present.
  - Otherwise verify admin access to `GET /api/v1/submissions/{submission_id}/attachments`.
  - If neither provides active attachment data for admin detail, create a backend/API follow-up before final wiring.
- Wire attachment download through `POST /api/v1/attachments/{attachment_id}/download-url`.
- Debounce text search filters where appropriate.

Acceptance:

- Daily Submissions list uses real API data.
- Daily Submission Detail shows real record data.
- File pending warning follows `file_submission_pending`.
- Attachment history is admin-only and visible when returned.
- Active attachment download uses signed URL flow.

## Phase 11 - Workorders API Integration
- Wire `GET /api/v1/admin/workorders`.
- Map filters to backend query parameters.
- Wire pagination.
- Wire `GET /api/v1/admin/workorders/{workorder_id}`.
- Render child daily submissions on detail page.
- Use backend aggregate fields:
  - `workorder_completed_grids`
  - `workorder_skipped_grids`
  - `workorder_remaining_grids`
  - `workorder_progress_percent`
- Debounce text search filters where appropriate.

Acceptance:

- Workorders list uses real API data.
- Workorder Detail uses real API data.
- Remaining grids and progress match backend read model.

## Phase 12 - Admin Edit Mutations
Daily submission edit:

- Wire `PATCH /api/v1/admin/submissions/{submission_id}`.
- Use detail-page edit drawer.
- Validate non-negative daily grid counts with Zod.
- Warn that edits can recompute parent workorder progress/status.
- Send only backend-supported fields.
- Do not send a UI-only admin note unless the backend contract supports it.
- Refresh submission detail, submissions list, workorder detail, and dashboard queries after success.

Daily submission reopen:

- Wire `POST /api/v1/admin/submissions/{submission_id}/reopen`.
- Use explicit confirmation dialog.
- Explain parent workorder may move back to `ACTIVE`.
- Refresh affected queries after success.

Workorder edit:

- Wire `PATCH /api/v1/admin/workorders/{workorder_id}`.
- Use detail-page edit drawer.
- Validate required fields.
- Warn that total grids cannot go below aggregate completed plus skipped.
- Send only backend-supported fields.
- Refresh workorder detail, workorders list, submissions list, and dashboard queries after success.

Acceptance:

- Admin edits work from detail pages.
- Inline table editing is not introduced.
- Backend validation errors are visible and useful.
- Mutations invalidate the correct query keys.

## Phase 13 - Reports And CSV Export
- Wire `GET /api/v1/admin/reports/submissions/export`.
- Mirror Daily Submissions filters where supported.
- Treat response as CSV/file response, not JSON envelope.
- Generate useful local filename.
- Add loading and error states around export.
- Keep PDF export out of scope.

Acceptance:

- Admin can export filtered submissions CSV.
- Export respects visible filters where backend supports them.
- Failed export shows backend or network error clearly.

## Phase 14 - UI Polish And Accessibility
- Verify text does not overflow buttons, badges, cards, filters, or table controls.
- Verify table horizontal scrolling on smaller screens.
- Verify all icon-only buttons have labels.
- Verify drawers/dialogs are keyboard accessible.
- Verify color is not the only status indicator.
- Verify empty states are helpful.
- Verify destructive actions have confirmation.
- Verify admin pages do not include tester-only actions such as `Start Drive`, `End Drive`, or `Complete Submission`.
- Verify URL search params preserve table state on reload.
- Verify loading states do not shift table layout dramatically.
- Verify long emails, workorder codes, and ticket numbers do not break table layout.

Acceptance:

- UI is usable for dense operations review.
- Accessibility basics are covered.
- Admin-only mental model is preserved.

## Phase 15 - Frontend Verification
Run available checks:

```bash
pnpm --filter admin-web lint
pnpm --filter admin-web typecheck
pnpm --filter admin-web test
```

Run Docker dev check:

```bash
docker compose up admin-web
```

When Playwright is added, cover:

- Admin sees dashboard.
- Admin opens Daily Submissions.
- Admin filters Daily Submissions.
- Admin opens Daily Submission Detail.
- Admin opens edit drawer.
- Admin opens Workorders.
- Admin opens Workorder Detail.
- Admin opens Pending Users.
- Admin opens No Submission Yet.
- Admin opens Reports.

Acceptance:

- Checks pass.
- App runs at `http://localhost:3000`.
- Any unavailable check is explicitly documented in the handoff.
- A future agent can run the documented commands without guessing package manager, port, or app path.

## Definition Of Done For Admin Web MVP
- Docker-first frontend app exists.
- Optional local pnpm flow works.
- Admin web route structure is complete.
- Shared UI components are implemented.
- All MVP pages render.
- Admin-only auth guard exists.
- API client layer is centralized.
- Dashboard, users, pending users, workorders, daily submissions, no-submission-yet, and reports are wired.
- Admin edit and reopen actions are wired.
- CSV export is wired.
- File pending and no-submission-yet semantics are correct.
- Remaining grids are computed/displayed correctly.
- No unsupported V1 roles or out-of-scope teams/kits/assignment features are introduced.
