#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding demo users (skipped if already present)..."
python -m app.db.seed

echo "Loading knowledge corpus..."
python -m app.rag.ingest

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
