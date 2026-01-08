FROM python:3.10.1-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install sqlite3
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

COPY . .

# initialize the database with schema and seed data
RUN sqlite3 database.db < schema.sql
RUN sqlite3 database.db < seed.sql

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]