FROM node:20-bookworm-slim

WORKDIR /app

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable

COPY package.json pnpm-workspace.yaml ./
COPY apps/admin-web/package.json apps/admin-web/package.json

RUN pnpm install --no-frozen-lockfile

WORKDIR /app/apps/admin-web

EXPOSE 3000

CMD ["pnpm", "dev"]
