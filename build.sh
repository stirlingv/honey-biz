#!/usr/bin/env bash
# Build script for Render deployment
# https://render.com/docs/deploy-django

set -o errexit  # Exit on error

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Create data directory if it doesn't exist (for SQLite on persistent disk)
mkdir -p /opt/render/project/src/data

# Run database migrations
python manage.py migrate

echo "Build completed successfully!"
