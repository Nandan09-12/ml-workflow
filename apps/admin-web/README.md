# Admin Web

Next.js admin console for ML Workflow DT Check-in.

## Docker

From repo root:

```bash
docker compose up --build
```

Admin web runs at `http://localhost:3000`.

This stack expects:

- `apps/admin-web/.env.local`
- `apps/api/.env`

For first-time setup, copy the examples:

```bash
copy apps\api\.env.example apps\api\.env
copy apps\admin-web\.env.example apps\admin-web\.env.local
```

If the API is already running and you only want the frontend container:

```bash
docker compose up admin-web
```

## Local pnpm

From repo root:

```bash
pnpm install
pnpm --filter admin-web dev
```

Checks:

```bash
pnpm --filter admin-web lint
pnpm --filter admin-web typecheck
pnpm --filter admin-web test
```

For the full teammate onboarding flow, see [docs/DOCKER_SETUP.md](../../docs/DOCKER_SETUP.md).
