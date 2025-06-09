#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations

# The "$@" command will run the CMD from the Dockerfile.
# In our case, it will be: gunicorn simak.wsgi:application --bind 0.0.0.0:8000
exec "$@"