#!/bin/bash
set -e

# Rollback script for autoapply-be
# This script rolls back to the previous Docker image version

echo "⏪ Rolling back deployment..."

# Configuration
PROJECT_DIR="$HOME/autoapply-be"
DOCKER_COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
}

echo -e "${YELLOW}🛑 Stopping current containers...${NC}"
$DOCKER_COMPOSE_CMD down

echo -e "${YELLOW}📋 Available Docker images:${NC}"
docker images | grep autoapply-be

read -p "Enter the image tag to rollback to (e.g., sha-abc123): " IMAGE_TAG

if [ -z "$IMAGE_TAG" ]; then
    echo -e "${RED}❌ No image tag provided${NC}"
    exit 1
fi

# Update docker-compose to use specific tag
echo -e "${YELLOW}🔄 Updating configuration to use tag: $IMAGE_TAG${NC}"
export IMAGE_TAG=$IMAGE_TAG

echo -e "${YELLOW}🚀 Starting containers with previous version...${NC}"
$DOCKER_COMPOSE_CMD up -d

echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

echo -e "${YELLOW}🏥 Running health check...${NC}"
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Rollback successful! Application is healthy.${NC}"
else
    echo -e "${RED}❌ Health check failed after rollback.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Rollback completed successfully!${NC}"

