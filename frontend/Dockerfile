FROM node:22-alpine AS base

WORKDIR /app
COPY package*.json ./
RUN npm install

################################################################################################
#                     Stage: Development (For local hot-reload support)                        #
################################################################################################
FROM base AS development
CMD ["npm", "run", "dev"]

################################################################################################
#                           Stage: Builder (For production stage)                              #
################################################################################################
FROM base AS builder
COPY . .
# CRITICAL: We use generate, NOT build, to produce a truly static dist/
RUN npm run generate

################################################################################################
#                          Stage: Production (Caddy Web Server)                                #
################################################################################################
FROM caddy:2-alpine AS production
COPY --from=builder /app/.output/public /www
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 80