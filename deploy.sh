#!/usr/bin/env bash
set -e

LOGFILE="/var/log/deploy.log"

{
    echo "=== 🚀 Deploy started at $(date) ==="
    cd /var/www/sehatiapps

    echo "🔄 Pulling latest code..."
    git fetch origin main
    git reset --hard origin/main

    echo "📦 Installing dependencies via Poetry..."
    export PATH="$HOME/.local/bin:$PATH"
    set -a
    source .env
    set +a
    poetry install --no-root --only main

    echo "📜 Applying Alembic migrations..."
    poetry run alembic upgrade head

    echo "🚀 Restarting FastAPI service..."
    sudo systemctl restart sehati

    echo "✅ Deploy completed at $(date)"
    echo
} >> "$LOGFILE" 2>&1
