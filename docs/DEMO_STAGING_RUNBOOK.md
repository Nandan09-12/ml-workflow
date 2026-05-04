# Demo Staging Runbook

This runbook is the fastest practical path to give a remote manager a self-serve demo by tomorrow morning.

Goal:

- Android APK for the drive-tester mobile app
- Public staging API
- Public staging admin web UI
- No paid domain purchase

## Recommended Architecture

- One AWS EC2 instance in `us-east-1`
- One AWS Elastic IP attached to that instance
- Docker Compose on EC2 for:
  - Postgres
  - API
  - Admin web
- HTTPS reverse proxy using `sslip.io` hostnames
- Android APK built with Expo EAS internal distribution

Public URLs:

- API: `https://api.<elastic-ip-as-dashes>.sslip.io`
- Admin web: `https://admin.<elastic-ip-as-dashes>.sslip.io`

Example:

- Elastic IP: `54.210.12.34`
- API URL: `https://api.54-210-12-34.sslip.io`
- Admin URL: `https://admin.54-210-12-34.sslip.io`

## What Is Already Good Enough

- `apps/api` is Dockerized and can run in Compose.
- `apps/admin-web` is Dockerized and can run in Compose.
- `apps/mobile` is only Dockerized as an Expo dev server, which is fine for local development.

Important:

- You do not need to "fully dockerize" mobile to create an APK.
- Android delivery is done by building an APK, not by deploying the mobile app in Docker.

## What You Need From Your Side

1. AWS account access
2. Expo account
3. Your current working local env values from:
   - `apps/api/.env`
   - `apps/admin-web/.env.local`
   - `apps/mobile/.env`
4. Two demo accounts:
   - one drive tester
   - one admin

## Recommended Timeline

Do these in order:

1. Create Expo account
2. Launch EC2 instance
3. Allocate and attach Elastic IP
4. Deploy API + admin + DB to EC2
5. Put HTTPS in front using `sslip.io`
6. Update mobile env to use the public API URL
7. Build Android APK with Expo EAS
8. Test from your own Android if possible
9. Send manager:
   - APK install link
   - admin web URL
   - demo credentials

## EC2 Setup

Recommended instance:

- Ubuntu 24.04 LTS
- `t3.small` minimum
- `t3.medium` preferred if you want extra headroom
- 20 GB disk is enough for a short demo environment

Security group inbound rules:

- `22` from your IP only
- `80` from anywhere
- `443` from anywhere

Do not open these to the public internet:

- `3000`
- `5432`
- `8000`

The reverse proxy will handle public traffic on `80` and `443`.

## Elastic IP Setup

1. Allocate one Elastic IP in `us-east-1`
2. Associate it to your EC2 instance
3. Write down the IP

Convert dots to dashes for the hostname:

- `54.210.12.34` becomes `54-210-12-34`

Then define:

- `API_HOST=api.54-210-12-34.sslip.io`
- `ADMIN_HOST=admin.54-210-12-34.sslip.io`

## Install Docker On EC2

SSH into the instance and install Docker Engine plus Compose.

If you want the quickest standard Ubuntu path, use Docker's official Linux install docs:

- https://docs.docker.com/engine/install/ubuntu/

After install:

```bash
docker --version
docker compose version
```

## Get The Repo Onto EC2

Use either:

- `git clone ...`
- or upload a zip/archive

Place it somewhere simple, for example:

```bash
~/ml-workflow
```

## Staging Env Values

Reuse your current local env values where possible, but change the public URLs.

### API env

Start from `apps/api/.env`.

Important values for staging:

```dotenv
APP_ENV=development
DEBUG=false
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+asyncpg://devuser:devpass@db:5432/devdb
DATABASE_SSL_MODE=disable
CORS_ALLOWED_ORIGINS=https://admin.<elastic-ip-as-dashes>.sslip.io
SUPABASE_URL=<from your current working local env>
SUPABASE_JWKS_URL=<leave blank if your current local setup leaves it blank>
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_SERVICE_ROLE_KEY=<from your current working local env>
SUPABASE_STORAGE_BUCKET=attachments
BOOTSTRAP_ADMIN_EMAILS=<comma-separated admin email list>
```

Notes:

- Keep the database host as `db` because Compose uses the service name.
- `CORS_ALLOWED_ORIGINS` must include the public admin URL.
- Mobile APK calls the API natively, so browser CORS is mainly for admin web.

### Admin web env

Start from `apps/admin-web/.env.local`.

Set:

```dotenv
NEXT_PUBLIC_API_BASE_URL=https://api.<elastic-ip-as-dashes>.sslip.io/api/v1
NEXT_PUBLIC_SUPABASE_URL=<from your current working local env>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<from your current working local env>
```

### Mobile env

Start from `apps/mobile/.env`.

Set:

```dotenv
EXPO_PUBLIC_API_BASE_URL=https://api.<elastic-ip-as-dashes>.sslip.io
EXPO_PUBLIC_API_BASE_URL_IOS=https://api.<elastic-ip-as-dashes>.sslip.io
EXPO_PUBLIC_API_BASE_URL_ANDROID=https://api.<elastic-ip-as-dashes>.sslip.io
EXPO_PUBLIC_SUPABASE_URL=<from your current working local env>
EXPO_PUBLIC_SUPABASE_ANON_KEY=<from your current working local env>
```

Notes:

- For this demo, use the same public API URL for all mobile targets.
- `REACT_NATIVE_PACKAGER_HOSTNAME` is not needed for the APK build path.

## Start The Docker Stack On EC2

From repo root:

```bash
docker compose up --build -d
```

Then verify:

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f admin-web
```

Quick health check from the EC2 host:

```bash
curl http://localhost:8000/api/v1/health
```

## HTTPS Without Buying A Domain

Use `sslip.io` plus Caddy.

Why:

- `sslip.io` maps hostnames containing your IP back to that IP
- It lets you use normal hostnames without registering a domain
- Caddy can automatically provision Let's Encrypt certificates

Reference:

- https://sslip.io/

### Create A Caddyfile On EC2

Create a file named `Caddyfile` next to the repo or in your home directory:

```caddy
api.<elastic-ip-as-dashes>.sslip.io {
    reverse_proxy localhost:8000
}

admin.<elastic-ip-as-dashes>.sslip.io {
    reverse_proxy localhost:3000
}
```

Example:

```caddy
api.54-210-12-34.sslip.io {
    reverse_proxy localhost:8000
}

admin.54-210-12-34.sslip.io {
    reverse_proxy localhost:3000
}
```

### Run Caddy In Docker

From the directory containing `Caddyfile`:

```bash
docker run -d \
  --name caddy \
  --restart unless-stopped \
  --network host \
  -v "$(pwd)/Caddyfile:/etc/caddy/Caddyfile" \
  -v caddy_data:/data \
  -v caddy_config:/config \
  caddy:2
```

Then verify:

```bash
docker logs -f caddy
```

What success looks like:

- `https://api.<elastic-ip-as-dashes>.sslip.io/api/v1/health` responds
- `https://admin.<elastic-ip-as-dashes>.sslip.io` opens in browser

## Expo Account And APK Build

Yes, you can do all of this from your PC.

### Install And Log In

From your PC:

```bash
npm install -g eas-cli
eas login
```

### Configure EAS For This App

Go to the mobile app directory:

```bash
cd apps/mobile
```

Because this repo does not currently have an `eas.json`, initialize EAS build config:

```bash
eas build:configure
```

Choose Android when prompted.

For a manager demo, create or update `eas.json` so there is a profile that builds an APK for internal distribution.

Recommended shape:

```json
{
  "build": {
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    }
  }
}
```

### Build The APK

From `apps/mobile`:

```bash
eas build -p android --profile preview
```

When the build finishes, Expo gives you a shareable install URL.

Send that URL to your manager.

## Demo Accounts

Recommended:

- Create one dedicated drive-tester demo user
- Create one dedicated admin demo user
- Use easy-to-recognize names like:
  - `demo.tester@...`
  - `demo.admin@...`

Do not use your own personal login for the demo.

## What To Test Before Sending

### Admin web

Open:

- `https://admin.<elastic-ip-as-dashes>.sslip.io`

Verify:

- login works
- dashboard loads
- workorders page loads
- users page loads

### API

Open:

- `https://api.<elastic-ip-as-dashes>.sslip.io/api/v1/health`

Verify:

- health endpoint returns success

### Mobile APK

Install on Android and verify:

- app opens
- login works
- drive tester home/projects screen loads
- submissions screen loads
- any key demo flow you plan to show works

## What To Send Your Manager

Send one short message with:

1. APK install link
2. Admin web URL
3. Drive tester credentials
4. Admin credentials
5. A tiny demo script

Example:

```text
Drive tester Android app:
<apk-link>

Admin web:
https://admin.<elastic-ip-as-dashes>.sslip.io

Drive tester login:
<email>
<password>

Admin login:
<email>
<password>

Suggested flow:
1. Install the APK and sign in as drive tester
2. Open Projects and DT Check-in
3. Open the admin URL in Chrome and sign in as admin
4. Review dashboard, users, and workorders
```

## Fastest Fallbacks If Something Blocks You

If APK build is delayed:

- still deploy API + admin web
- send admin web link
- record a short mobile screen capture for backup

If HTTPS is blocked:

- do not switch to plain `http` for the Android APK path unless you intentionally configure Android cleartext traffic
- fix HTTPS first

If admin is working but mobile auth is not:

- verify mobile env uses the public HTTPS API URL
- verify Supabase public values in `apps/mobile/.env`
- verify API can validate tokens using the staging API env values

## Final Recommendation

For tomorrow morning, optimize for a stable demo, not perfect infrastructure.

The winning setup is:

- EC2 for API + admin + DB
- `sslip.io` + Caddy for HTTPS
- Expo EAS APK for Android
- dedicated demo accounts
