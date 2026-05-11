FROM node:22-alpine AS builder

LABEL authors="Werner Richter, Alexander Wudy"

################################################################################################
#                              Step 1: Build the Nuxt static site                              #
################################################################################################
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# CRITICAL: We use generate, NOT build, to produce a truly static dist/
RUN npm run generate  # Outputs static files to .output/public


################################################################################################
#                          Step 2: Provide site via Caddy web server                           #
################################################################################################
FROM caddy:2-alpine
COPY --from=builder /app/.output/public /www
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 80