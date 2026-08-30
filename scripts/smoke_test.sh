#!/bin/sh
set -e

echo "Checking API health..."
curl -f http://localhost:8000/health
echo
echo "OK"
