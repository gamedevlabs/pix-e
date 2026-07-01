FROM node:22-alpine AS base

WORKDIR /app
COPY package*.json ./
RUN npm install

################################################################################################
#                     Stage: Development (For local hot-reload support)                        #
################################################################################################
FROM base AS development
RUN apk add --no-cache git && git config --global --add safe.directory '*'
CMD ["npm", "run", "dev"]

################################################################################################
#                           Stage: Builder (For production stage)                              #
################################################################################################
FROM base AS builder
ARG NUXT_PUBLIC_VERSION
ARG NUXT_PUBLIC_GIT_HASH
ENV NUXT_PUBLIC_VERSION=$NUXT_PUBLIC_VERSION
ENV NUXT_PUBLIC_GIT_HASH=$NUXT_PUBLIC_GIT_HASH
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