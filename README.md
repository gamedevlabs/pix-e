# pix:e Minimal Starter

Look at the wiki once we have one

## Setup

1. Copy the `.env.example` file inside the `infra` folder and paste it as `.env`.
2. Start Docker on your device
3. Run the following commands to start up the application
```bash
cd infra
docker compose up
```
4. Open your browser on https://localhost/. If you get a certificate error notice,
   then ignore it, as it is expected to show up when running the application locally.

For more information about the current Docker and Reverse Proxy setup, check out
[the infrastructure README.md](infra/README.md)

## Deprecation notice
npm support is still available, but will be removed after the pipeline switch has
been completed. To ensure consistency, it is not recommended to use npm to start
the application anymore, but rather launch it via Docker as described above.