FROM python:3.12-slim
LABEL authors="richterw"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn[standard]  # Async ASGI server

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

# run migrations and start the ASGI server with multiple workers for better performance
CMD python manage.py migrate --noinput && \
    uvicorn api.asgi:application --host 0.0.0.0 --port 8000 --workers 4