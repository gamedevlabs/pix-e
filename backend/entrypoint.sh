#!/bin/sh
set -e

# run migrations and start the ASGI server with multiple workers for better performance
python manage.py migrate --noinput
exec uvicorn api.asgi:application --host 0.0.0.0 --port 8000 --workers 4