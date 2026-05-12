FROM node:26-bookworm-slim AS base

WORKDIR /app

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV EXPO_NO_TELEMETRY=1
ENV EXPO_DEV_HOST=localhost
ENV EXPO_DEV_PORT=8082
ENV EXPO_DEVTOOLS_LISTEN_ADDRESS=0.0.0.0

RUN corepack enable


FROM base AS deps

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/mobile/package.json apps/mobile/package.json
COPY packages/api-client/package.json packages/api-client/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json

RUN pnpm install --frozen-lockfile


FROM deps AS dev

COPY apps/mobile apps/mobile
COPY packages/api-client packages/api-client
COPY packages/shared-types packages/shared-types

WORKDIR /app/apps/mobile

EXPOSE 8082 19000 19001 19002

CMD ["sh", "-c", "pnpm install --offline --frozen-lockfile --filter @ml-workflow/mobile... && pnpm exec expo start --host \"$EXPO_DEV_HOST\" --port \"$EXPO_DEV_PORT\""]
