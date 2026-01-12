#!/bin/bash
echo "Starting XYZ Corp Agentic Call Center..."

# 1. Build Containers
echo "Building containers..."
docker-compose build

# 2. Start Services (Postgres, Redis, Chroma)
echo "Starting database services..."
docker-compose up -d postgres redis chromadb

# Wait for healthy
echo "Waiting for services to be ready..."
sleep 10

# 3. Seed SQL Data
echo "Seeding SQL data..."
# Run script inside the app container context or locally if python is set up
# We'll assume we run it via docker-compose run for isolation
docker-compose run --rm app python scripts/seed_mock_db.py

# 4. Ingest Vector Data
echo "Ingesting vector data..."
docker-compose run --rm app python scripts/ingest.py

# 5. Start App
echo "Starting Application..."
docker-compose up app
