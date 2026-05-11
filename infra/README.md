# Infrastructure Configuration
This directory provides the configuration for the whole configuration on multiple, different runtime environments.

## Caddy Configuration
There are two different Caddyfiles, `Caddyfile` and `Caddyfile.local`.
The first is used to configure the reverse proxy for the development and production environment.
The latter defines the reverse proxy for local runtime.

## Environment files
The `.env.example` file provides a template for environment configuration. To enable local development,
copy the file and rename it to `.env`. The development and production environment have their own
environment files, which are configured on the server themselves to ensure security.

## Docker Compose
To enable simple and unified local development, you should use Docker Compose to run the project.
Using the `docker-compose.yml`, a baseline for the setup is given. This file defines the way the
application runs on the development and the release environment. To enable local development on
this configuration as well, an additional `docker-compose.override.yml` is defined. This file uses
[Docker Compose's "Merge"](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/) feature
to replace or expand the declared paths with new or additional values.