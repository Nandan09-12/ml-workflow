# Admin Web

Next.js admin console for ML Workflow DT Check-in.

## Docker

From repo root:

```bash
docker compose up admin-web
```

Admin web runs at http://localhost:3000.

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
