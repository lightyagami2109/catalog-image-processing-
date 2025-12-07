#!/usr/bin/env bash
# Safe purge script - runs purge with dry-run first, then actual purge if confirmed

BASE_URL="${1:-http://localhost:10000}"

echo "Running dry-run purge..."
curl -X POST "${BASE_URL}/purge/?dry_run=true"

echo -e "\n\nIf the above looks correct, run:"
echo "curl -X POST \"${BASE_URL}/purge/?dry_run=false\""

