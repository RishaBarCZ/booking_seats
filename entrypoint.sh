#!/bin/bash

set -eu

while ! nc -z "$POSTGRES_SERVER" "$POSTGRES_PORT"; do
  echo "Waiting for postgres to start..."
  sleep 3
done
echo 'Postgres started'

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000
