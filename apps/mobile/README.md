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

Without Supabase env vars, the app falls back to a mock auth flow so UI work can continue in parallel.
Using an email containing `pending` in mock mode routes to the pending-approval screen.
