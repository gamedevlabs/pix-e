FROM node:22-alpine AS builder

LABEL authors="richterw"

# Stage 1: build the Nuxt static site

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
RUN npm ci
COPY frontend/ .
# CRITICAL: We use generate, NOT build, to produce a truly static dist/
RUN npm run generate  # Outputs static files to .output/public


# Stage 2: Serve with Caddy
FROM caddy:2-alpine
COPY --from=builder /app/.output/public /usr/share/caddy/html
COPY ./Caddyfile /etc/caddy/Caddyfile
EXPOSE 80 443