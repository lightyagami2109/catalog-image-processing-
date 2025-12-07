#!/usr/bin/env bash
# Setup script for local PostgreSQL database

echo "Setting up PostgreSQL database for Catalog Image Pipeline..."
echo ""

# Default values (update these if your setup is different)
DB_NAME="${DB_NAME:-catalogdb}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Database configuration:"
echo "  Name: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "Error: psql command not found. Please install PostgreSQL client tools."
    exit 1
fi

# Create database
echo "Creating database '$DB_NAME'..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || {
    echo "Database might already exist, continuing..."
}

echo ""
echo "✓ Database setup complete!"
echo ""
echo "Update your .env file with:"
echo "DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Then run: python -c \"from app.db import init_db; import asyncio; asyncio.run(init_db())\""

