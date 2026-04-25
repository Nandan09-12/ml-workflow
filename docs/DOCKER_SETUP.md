# Docker Setup Guide

Use this guide when you pull the repo on a new PC and want to run the local stack.

## What You Are Running

This repo uses separate containers for separate services:

- Postgres database
- FastAPI backend (`apps/api`)
- Next.js admin web (`apps/admin-web`)
- Optional Expo mobile dev server (`apps/mobile`) via Docker Compose profile

They run together through one shared Docker Compose stack.

Docker source of truth in this repo:

- API image definition: `apps/api/Dockerfile`
- Admin web image definition: `apps/admin-web/Dockerfile`
- Mobile image definition: `apps/mobile/Dockerfile`

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
copy apps\mobile\.env.example apps\mobile\.env
```

macOS/Linux:

```bash
cp apps/api/.env.example apps/api/.env
cp apps/admin-web/.env.example apps/admin-web/.env.local
cp apps/mobile/.env.example apps/mobile/.env
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

## Start The Mobile Expo Dev Server In Docker

The mobile app runs as an optional Compose profile so it does not change the default `docker compose up --build` flow.

Start it with:

```bash
docker compose --profile mobile up --build mobile
```

This will also start the API dependency automatically.

Exposed mobile ports:

- Expo / Metro on `localhost:8082` by default
- Expo helper ports on `localhost:19000`, `localhost:19001`, and `localhost:19002`

The Dockerized mobile service defaults to Expo localhost mode for simulator and emulator testing.

Use it like this:

```bash
docker compose up -d db app
docker compose --profile mobile up --build mobile
```

Then test the same frontend in parallel:

- Web: open `http://localhost:8082`
- iOS Simulator: open Expo Go and load `exp://127.0.0.1:8082`
- Android Emulator: run `adb reverse tcp:8082 tcp:8082`, then open Expo Go and load `exp://127.0.0.1:8082`

The local mobile env already uses `EXPO_PUBLIC_API_BASE_URL_ANDROID=http://10.0.2.2:8000`, so Android API traffic can still reach the Dockerized backend without extra reverse rules.

If `8082` is already in use on your machine, override it temporarily:

```bash
EXPO_DEV_PORT=8083 docker compose --profile mobile up --build mobile
```

If you want to test on a physical phone over Wi-Fi instead of simulators, override back to LAN mode:

```bash
EXPO_DEV_HOST=lan docker compose --profile mobile up --build mobile
```

## Run The Mobile App Without Expo Go

If you want the app installed directly in the iOS Simulator or Android Emulator, do not use the Dockerized mobile profile for that step.
Keep Docker for the backend and run the mobile native build on your host machine instead.

From repo root:

```bash
pnpm mobile:backend
pnpm mobile:ios
pnpm mobile:android
```

This gives you:

- API + DB in Docker
- iOS Simulator running your installed app
- Android Emulator running your installed app

After the first install, use this daily parallel workflow:

```bash
pnpm mobile:native
pnpm mobile:web
```

- `pnpm mobile:native` starts Metro in dev-client mode for the installed simulator apps and keeps Expo Go out of the flow
- `pnpm mobile:web` runs the same `apps/mobile` codebase in the browser

If `expo run:ios` hits a Metro port-detection issue on your machine, use:

```bash
pnpm mobile:native
pnpm mobile:ios:install
```

This starts Metro separately on a fixed port and installs the iOS app without letting Expo re-manage the bundler.

The first native build may generate local `apps/mobile/ios` and `apps/mobile/android` folders.
They are intentionally gitignored in this repo because they are local native build outputs.

Use these mobile env values for the host-native workflow:

```dotenv
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_API_BASE_URL_IOS=http://127.0.0.1:8000
EXPO_PUBLIC_API_BASE_URL_ANDROID=http://10.0.2.2:8000
```

Notes:

- iOS Simulator reaches the host API at `127.0.0.1`
- Android Emulator reaches the host API at `10.0.2.2`
- `REACT_NATIVE_PACKAGER_HOSTNAME` is only needed when Metro itself is running in Docker or when testing on a physical device over LAN

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
docker compose --profile mobile logs -f mobile
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
2. Use the optional `mobile` profile when you want Expo running in Docker.
3. Default to local Docker Postgres for most development.
4. Use Supabase-backed DB only when you intentionally need hosted-data parity.
