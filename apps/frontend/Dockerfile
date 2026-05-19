FROM node:22-slim AS build

WORKDIR /app

# Railway injects service variables during `docker build`; declare ARG/ENV so Astro
# inlines PUBLIC_* values at build time.
ARG PUBLIC_AGENTOS_API_BASE_URL
ARG PUBLIC_AUTH0_DOMAIN
ARG PUBLIC_AUTH0_CLIENT_ID
ARG PUBLIC_AUTH0_AUDIENCE
ENV PUBLIC_AGENTOS_API_BASE_URL=$PUBLIC_AGENTOS_API_BASE_URL
ENV PUBLIC_AUTH0_DOMAIN=$PUBLIC_AUTH0_DOMAIN
ENV PUBLIC_AUTH0_CLIENT_ID=$PUBLIC_AUTH0_CLIENT_ID
ENV PUBLIC_AUTH0_AUDIENCE=$PUBLIC_AUTH0_AUDIENCE

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-slim

WORKDIR /app

ENV HOST=0.0.0.0
ENV NODE_ENV=production

COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

EXPOSE 4321

CMD ["sh", "-c", "exec node ./dist/server/entry.mjs"]
