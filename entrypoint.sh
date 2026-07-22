#!/bin/sh
set -e

echo "Starting PromptGuard..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-1}"
