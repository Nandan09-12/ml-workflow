# Mobile App

Shared React Native application for Android and iOS using Expo.

## Stack

- Expo
- React Native
- Expo Router
- TypeScript
- TanStack Query
- React Hook Form
- Zod
- Supabase JS

## Screens scaffolded

- `/` splash / brand screen
- `/(auth)/login`
- `/pending-approval`
- `/(tabs)/projects`
- `/(tabs)/chats`
- `/(tabs)/offline`
- `/(tabs)/notifications`
- `/(tabs)/settings`

The projects screen is intentionally limited to four project tiles to match the current product scope.

## Environment

Use Expo public env vars for client-safe configuration:

- `EXPO_PUBLIC_API_BASE_URL`
- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`

Optional EAS build linkage values for a shared or pre-existing Expo project:

- `EXPO_OWNER`
- `EAS_PROJECT_ID`

These are not runtime API/auth values. They are only used when Expo resolves the app config for EAS builds.

Without Supabase env vars, the app falls back to a mock auth flow so UI work can continue in parallel.
Using an email containing `pending` in mock mode routes to the pending-approval screen.

## Docker

The repo includes an optional Docker Compose profile for the Expo dev server:

```bash
docker compose --profile mobile up --build mobile
```

This uses `apps/mobile/.env` for Expo public env values and exposes:

- Metro / Expo dev server on `localhost:8082` by default
- Expo auxiliary ports `19000`, `19001`, and `19002`

The Dockerized mobile service defaults to Expo localhost mode for simulator and emulator testing.

Recommended local flow:

```bash
docker compose up -d db app
docker compose --profile mobile up --build mobile
```

Then open the same frontend three ways:

- Web: `http://localhost:8082`
- iOS Simulator with Expo Go: `exp://127.0.0.1:8082`
- Android Emulator with Expo Go: run `adb reverse tcp:8082 tcp:8082`, then open `exp://127.0.0.1:8082`

For Android API calls, this repo already uses `EXPO_PUBLIC_API_BASE_URL_ANDROID=http://10.0.2.2:8000` in the local mobile env, so no extra API reverse step is needed.

If you later want a physical phone on Wi-Fi instead of simulators, override the Docker host mode back to LAN:

```bash
EXPO_DEV_HOST=lan docker compose --profile mobile up --build mobile
```

## Native Simulator Workflow

If you do not want Expo Go in the middle, use a native dev build on your Mac and keep Docker only for the backend:

```bash
pnpm mobile:backend
pnpm mobile:ios
pnpm mobile:android
```

What each command does:

- `pnpm mobile:backend` starts the API and database in Docker
- `pnpm mobile:ios` builds and installs your app into the iOS Simulator
- `pnpm mobile:android` builds and installs your app into the Android Emulator

After the app is installed once, use this daily parallel workflow:

```bash
pnpm mobile:native
pnpm mobile:web
```

- `pnpm mobile:native` starts Metro in dev-client mode for the installed simulator apps instead of routing through Expo Go
- `pnpm mobile:web` runs the same `apps/mobile` code in the browser

If Expo CLI misbehaves while auto-starting Metro during `run:ios`, use the split flow:

```bash
pnpm mobile:native
pnpm mobile:ios:install
```

That keeps Metro on a fixed port and installs the app into the simulator without asking Expo to manage the bundler.

On the first native build, Expo will generate local `apps/mobile/ios` and `apps/mobile/android` folders.
Those folders are gitignored in this repo because they are build outputs for the local simulator workflow.

Environment values for this workflow:

- `EXPO_PUBLIC_API_BASE_URL=http://localhost:8000` for web
- `EXPO_PUBLIC_API_BASE_URL_IOS=http://127.0.0.1:8000` for iOS Simulator
- `EXPO_PUBLIC_API_BASE_URL_ANDROID=http://10.0.2.2:8000` for Android Emulator

`REACT_NATIVE_PACKAGER_HOSTNAME` is only needed for the Dockerized Expo server or physical-device LAN testing. It is not needed for host-native simulator installs.
