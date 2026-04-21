# Admin Web Frontend Environment

## Recommended Stack
Use this stack for `apps/admin-web`:

- Next.js with App Router
- React
- TypeScript
- Tailwind CSS
- pnpm workspaces
- TanStack Query for API data fetching and caching
- Zod for form validation and API payload validation at UI boundaries
- Supabase Auth client for frontend login/session handling
- Lucide React for icons
- Radix UI primitives where needed for dialogs, dropdowns, popovers, tabs, and drawers
- Playwright for browser smoke tests after the app is scaffolded

Use a restrained operations-console design. Prioritize dense tables, filters, status badges, clear drill-downs, and low-friction review flows.

## Current Repo State
At the time this file was written:

- `apps/admin-web` is not scaffolded.
- The root repo does not yet have frontend package metadata.
- A static prototype exists under `docs/ui-mockups/adminui`.
- Docker is already used for backend-oriented local development.

The first frontend implementation slice should add the frontend workspace files.

## Official Dev Path
Use Docker as the official dev path.

The frontend agent should add or update:

```text
package.json
pnpm-workspace.yaml
apps/admin-web/package.json
apps/admin-web/Dockerfile
docker-compose.yml
```

If a compose service already exists when you work on this, preserve it and extend it conservatively.

The intended compose service should run the admin app in dev mode and expose:

```text
http://localhost:3000
```

Suggested service name:

```text
admin-web
```

Suggested container working directory:

```text
/app/apps/admin-web
```

Suggested Docker behavior:

- Install dependencies with pnpm.
- Mount source for local development.
- Preserve `node_modules` in a container volume.
- Run `pnpm dev`.

## Optional Local Dev Path
Local Node is optional for faster frontend iteration.

Recommended local prerequisites:

- Node.js LTS
- pnpm

Recommended versions:

```text
node >= 20
pnpm >= 9
```

Install pnpm if needed:

```bash
corepack enable
corepack prepare pnpm@latest --activate
```

Install dependencies from repo root:

```bash
pnpm install
```

Run admin web:

```bash
pnpm --filter admin-web dev
```

Run frontend checks:

```bash
pnpm --filter admin-web lint
pnpm --filter admin-web typecheck
pnpm --filter admin-web test
```

Use the exact script names that are added during scaffold. If the script names differ, update this file in the same change.

## Environment Variables
Add an environment example for admin web:

```text
apps/admin-web/.env.example
```

Expected frontend variables:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

Do not commit real secrets.

Frontend code may use public Supabase anon key values as intended by Supabase, but real project values should live in local `.env.local` or deployment configuration, not source-controlled files.

The API env may already contain `SUPABASE_URL`; use the same value for `NEXT_PUBLIC_SUPABASE_URL` in the admin web env.

Do not use `SUPABASE_SERVICE_ROLE_KEY` in admin web. The frontend needs the Supabase anon key only:

```text
NEXT_PUBLIC_SUPABASE_ANON_KEY=<supabase anon public key>
```

If the anon key is not present in existing local env files, request it from the project owner before wiring real login.

## Backend Dependency
The admin web talks to the FastAPI backend under:

```text
/api/v1
```

Default local backend URL:

```text
http://localhost:8000/api/v1
```

The backend currently owns:

- Auth validation
- Role/account status enforcement
- Workorder rules
- Daily submission rules
- Attachment rules
- Audit logs
- CSV export

Do not duplicate backend business rules in the frontend beyond user-facing validation and helpful warnings.

## Supabase Auth
The frontend should use Supabase Auth for login/session retrieval, then send the JWT to the backend:

```text
Authorization: Bearer <access_token>
```

Admin web access rule:

- Allow only current app users with approved role `ADMIN` and account status `APPROVED`.
- Show access denied or redirect state for `DRIVE_TESTER`, pending, rejected, or suspended users.

Use `GET /api/v1/me` after login to determine app role and account state.

Build a simple real login shell during the auth phase. Until API/auth wiring is complete, keep the admin pages reviewable with mock data.

## Package Choices
Recommended dependencies:

```text
next
react
react-dom
typescript
tailwindcss
postcss
autoprefixer
@tanstack/react-query
zod
@supabase/supabase-js
lucide-react
@radix-ui/react-dialog
@radix-ui/react-dropdown-menu
@radix-ui/react-popover
@radix-ui/react-tabs
```

Recommended dev dependencies:

```text
eslint
eslint-config-next
prettier
@types/node
@types/react
@types/react-dom
playwright
@playwright/test
vitest
@testing-library/react
@testing-library/jest-dom
jsdom
```

Use only what is needed for the current slice. Do not add large UI frameworks without approval.

## Scaffold Expectations
The first frontend slice should produce:

```text
apps/admin-web/
  app/
    layout.tsx
    page.tsx
    providers.tsx
    dashboard/
    daily-submissions/
    workorders/
    users/
    no-submission-yet/
    reports/
  components/
  lib/
  styles/
  public/
  package.json
  tsconfig.json
  next.config.ts
  tailwind.config.ts
  postcss.config.mjs
  .env.example
```

Exact folder structure can adapt to Next.js conventions, but keep reusable UI out of route files.

Recommended source boundaries:

- `components/layout`: shell, sidebar, topbar, page structure.
- `components/ui`: small reusable primitives such as badges, alerts, buttons, tables, drawers, dialogs, form fields.
- `components/features`: feature-specific composed components for submissions, workorders, users, reports, and dashboard.
- `lib/api`: typed API client and endpoint functions.
- `lib/query`: query keys and TanStack Query helpers.
- `lib/mock`: temporary mock data only.
- `lib/format`: labels, dates, numbers, percentages, status helpers.
- `lib/config`: public environment parsing and defaults.

Mock data should not live inside route components.

## Static Prototype Assets
The admin mockup uses:

```text
docs/ui-mockups/adminui/assets/ml-technologies-logo.jpeg
```

When building the real app, copy an approved logo into:

```text
apps/admin-web/public/
```

Do not reference files from `docs/ui-mockups` at runtime in the real app.

## Verification Expectations
For each frontend slice, run the checks that exist at that point:

```bash
pnpm --filter admin-web lint
pnpm --filter admin-web typecheck
pnpm --filter admin-web test
```

If Docker is set up:

```bash
docker compose up admin-web
```

When the API is needed for integration work, run API and admin web together through Docker Compose when possible, keeping API on port `8000` and admin web on port `3000`.

Once Playwright is added:

```bash
pnpm --filter admin-web test:e2e
```

If a check cannot run because the app is not scaffolded yet or dependencies are not installed, state that clearly in the final handoff.
