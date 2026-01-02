#!/usr/bin/env bash
# Build script for Render deployment
# https://render.com/docs/deploy-django

set -o errexit  # Exit on error

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Note: Migrations run at startup (in startCommand) because the persistent disk
# is only mounted at runtime, not during build

echo "Build completed successfully!"
