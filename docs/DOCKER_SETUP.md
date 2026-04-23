# Docker Setup Guide

Use this guide when you pull the repo on a new PC and want to run the local stack.

## What You Are Running

This repo uses separate containers for separate services:

- Postgres database
- FastAPI backend (`apps/api`)
- Next.js admin web (`apps/admin-web`)

They run together through one shared Docker Compose stack.

Docker source of truth in this repo:

- API image definition: `apps/api/Dockerfile`
- Admin web image definition: `apps/admin-web/Dockerfile`

Mobile is intentionally not part of this setup guide.

## Prerequisites

Install these first:

- Docker Desktop (or compatible Docker engine) running
- Git

Optional when working outside Docker:

- Node.js 20+
- pnpm 9+
- Python 3.12+

## Clone The Repo

```bash
git clone <your-repo-url>
cd ml-workflow
```

## Create Local Env Files

Windows:

```bash
copy apps\api\.env.example apps\api\.env
copy apps\admin-web\.env.example apps\admin-web\.env.local
```

macOS/Linux:

```bash
cp apps/api/.env.example apps/api/.env
cp apps/admin-web/.env.example apps/admin-web/.env.local
```

Never commit these local env files.

## Required Environment Values

### Admin Web

Edit `apps/admin-web/.env.local`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=<ask repo owner>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<ask repo owner>
```

### API

Edit `apps/api/.env`.

Minimum values you must set or confirm:

```dotenv
SUPABASE_URL=<ask repo owner>
SUPABASE_SERVICE_ROLE_KEY=<ask repo owner if file upload/storage flows are needed>
SUPABASE_STORAGE_BUCKET=<ask repo owner>
BOOTSTRAP_ADMIN_EMAILS=<admin email list>
```

## Database Mode: Choose One

The API supports two valid local modes.

### Option A: Local Docker Postgres (recommended for most teammates)

Use the default values from `apps/api/.env.example`:

```dotenv
DATABASE_URL=postgresql+asyncpg://devuser:devpass@db:5432/devdb
DATABASE_SSL_MODE=disable
```

Why this is recommended:

- avoids depending on shared cloud database state
- safer for local development
- works well with Docker Compose

### Option B: Supabase Postgres

If you need parity with the hosted database, replace the database settings in `apps/api/.env` with your Supabase pooler URL and matching SSL mode.

Use this only when intentionally working against the hosted database.

## Start The Full Local Stack

From repo root:

```bash
docker compose up --build
```

This starts:

- DB on `localhost:5432`
- API on `localhost:8000`
- Admin web on `localhost:3000`

## Start Only Part Of The Stack

API + DB only:

```bash
docker compose up --build db app
```

Admin web only, if API is already running:

```bash
docker compose up --build admin-web
```

## Verify It Works

1. Open `http://localhost:3000`
2. Open `http://localhost:8000/api/v1/health`
3. Confirm admin web loads without API connection errors
4. Sign in with a valid account provided by the repo owner

## Common Commands

Stop the stack:

```bash
docker compose down
```

Rebuild after Docker-related changes:

```bash
docker compose up --build
```

View logs:

```bash
docker compose logs -f app
docker compose logs -f admin-web
docker compose logs -f db
```

Reset local database volume:

```bash
docker compose down -v
docker compose up --build
```

## Production-Ready Image Builds

These images are deployment-ready in the sense that they can be built and run cleanly, but this repo does not yet include server deployment manifests.

Build the API image:

```bash
docker build -f apps/api/Dockerfile -t ml-workflow-api:prod .
```

Build the admin web production image:

```bash
docker build \
  -f apps/admin-web/Dockerfile \
  --target prod \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url> \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key> \
  -t ml-workflow-admin-web:prod .
```

Run the API image:

```bash
docker run --rm -p 8000:8000 --env-file apps/api/.env ml-workflow-api:prod
```

Run the admin web production image:

```bash
docker run --rm -p 3000:3000 ml-workflow-admin-web:prod
```

## Troubleshooting

### Port already in use

Another local service is already using `3000`, `5432`, or `8000`.

Fix:

- stop the conflicting process, or
- change the host-side port mapping in `docker-compose.yml`

### Admin web cannot reach API

Check:

- API container is running
- `NEXT_PUBLIC_API_BASE_URL` in `apps/admin-web/.env.local` is `http://localhost:8000/api/v1`
- browser can open `http://localhost:8000/api/v1/health`

### Login works badly or auth is broken

Check:

- `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set in `apps/admin-web/.env.local`
- `SUPABASE_URL` is set in `apps/api/.env`

### API DB connection is wrong

Check whether you are using:

- local Docker Postgres settings, or
- Supabase Postgres settings

Do not mix them accidentally.

### Container builds are large or slow

This repo now ignores local env files, virtual environments, node_modules, and build artifacts from Docker build context. If builds still feel stale, rebuild with `--build`.

## Recommended Team Workflow

1. Use Docker Compose for API + DB + admin web locally.
2. Keep mobile Docker work separate.
3. Default to local Docker Postgres for most development.
4. Use Supabase-backed DB only when you intentionally need hosted-data parity.