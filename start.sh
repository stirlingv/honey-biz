#!/usr/bin/env bash
# Startup script for Render deployment
# Runs at each deploy when the persistent disk IS mounted

set -o errexit  # Exit on error

# Create data directory if it doesn't exist (for SQLite on persistent disk)
mkdir -p /opt/render/project/src/data

# Run database migrations
python manage.py migrate

# Start the web server
exec gunicorn bearcreek.wsgi:application
