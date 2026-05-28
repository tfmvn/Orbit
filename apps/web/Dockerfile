# Build context for this Dockerfile is the monorepo root (see docker/docker-compose.yml),
# since the web app depends on the @orbit/shared workspace package.

FROM node:20-slim AS base
WORKDIR /repo

FROM base AS deps
COPY package.json package-lock.json* ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared/package.json packages/shared/package.json
RUN npm install --workspaces --if-present

FROM base AS build
COPY --from=deps /repo/node_modules ./node_modules
COPY . .
RUN npm run build --workspace=@orbit/web

FROM base AS runner
ENV NODE_ENV=production
WORKDIR /repo/apps/web
COPY --from=build /repo/apps/web/.next ./.next
COPY --from=build /repo/apps/web/public ./public
COPY --from=build /repo/node_modules ./node_modules
COPY --from=build /repo/apps/web/package.json ./package.json

EXPOSE 3000
CMD ["npm", "run", "start"]
