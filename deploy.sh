#!/bin/bash

# Deploy script
# Usage: ./deploy.sh

set -e

echo "Starting deployment..."

echo "Pulling latest Docker images..."
docker-compose pull

echo "Restarting services..."
docker-compose up -d --remove-orphans

echo "Deployment completed successfully!"
