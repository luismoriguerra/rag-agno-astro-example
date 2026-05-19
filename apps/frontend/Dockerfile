FROM node:22-slim AS build

WORKDIR /app

ARG PUBLIC_AGENTOS_API_BASE_URL
ARG PUBLIC_MOCK_IDENTITY
ENV PUBLIC_AGENTOS_API_BASE_URL=$PUBLIC_AGENTOS_API_BASE_URL
ENV PUBLIC_MOCK_IDENTITY=$PUBLIC_MOCK_IDENTITY

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-slim

WORKDIR /app

RUN npm install -g serve@14

COPY --from=build /app/dist ./dist

ENV HOST=0.0.0.0
EXPOSE 4321

CMD ["sh", "-c", "serve dist -l tcp://0.0.0.0:${PORT:-4321}"]
