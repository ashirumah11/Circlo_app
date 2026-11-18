#!/bin/sh
set -e

echo "==> Circlo container starting..."

# Wait for PostgreSQL
if [ -n "$POSTGRES_HOST" ]; then
    echo "==> Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    while ! nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
        sleep 0.5
    done
    echo "==> PostgreSQL is ready!"
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed -e 's|^redis://||' -e 's|/.*$||' -e 's|:.*$||')
    REDIS_PORT=$(echo "$REDIS_URL" | sed -e 's|^redis://||' -e 's|/.*$||' -e 's|^.*:||')
    REDIS_PORT=${REDIS_PORT:-6379}

    if [ -n "$REDIS_HOST" ]; then
        echo "==> Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
        while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
            sleep 0.5
        done
        echo "==> Redis is ready!"
    fi
fi

# Apply database migrations if executing the web service
if [ "$1" = "daphne" ] || [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "runserver" ]; then
    echo "==> Applying database migrations..."
    python manage.py migrate --noinput

    echo "==> Collecting static files..."
    python manage.py collectstatic --noinput --clear || true
fi

echo "==> Launching service: $@"
exec "$@"
