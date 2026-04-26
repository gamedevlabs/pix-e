FROM python:3.12-slim
LABEL authors="richterw"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn[standard]  # Async ASGI server

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Entry point for Uvicorn (api.asgi)
CMD ["uvicorn", "api.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]