FROM python:3.12-slim
LABEL authors="Werner Richter, Alexander Wudy"

ARG DJANGO_PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn[standard]  # Async ASGI server

COPY . ./backend

WORKDIR /backend

RUN python ./manage.py collectstatic --noinput

EXPOSE ${DJANGO_PORT}

# run migrations and start the ASGI server with multiple workers for better performance
CMD python manage.py migrate --noinput && \
    uvicorn api.asgi:application --host 0.0.0.0 --port ${DJANGO_PORT} --workers 4