#!/usr/bin/env bash
set -e

cd /var/www/sehatiapps

echo "🔄 Pulling latest code..."
git fetch origin main
git reset --hard origin/main

echo "📦 Installing dependencies..."
export PATH="$HOME/.local/bin:$PATH"
poetry install --no-root --only main

echo "📜 Applying Alembic migrations..."
poetry run alembic upgrade head

echo "🚀 Restarting FastAPI service..."
sudo systemctl restart sehati

echo "✅ Deploy completed!"
