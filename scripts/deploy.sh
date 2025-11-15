#!/bin/bash
set -e

# Deployment script for autoapply-be
# This script should be run on the server

echo "🚀 Starting deployment..."

# Configuration
PROJECT_DIR="$HOME/autoapply-be"
DOCKER_COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Please don't run this script as root${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo -e "${YELLOW}Install with: sudo apt-get install docker-compose-plugin${NC}"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
}

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. Please create it from .env.production template${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Pulling latest images...${NC}"
$DOCKER_COMPOSE_CMD pull

echo -e "${YELLOW}🛑 Stopping old containers...${NC}"
$DOCKER_COMPOSE_CMD down

echo -e "${YELLOW}🚀 Starting new containers...${NC}"
$DOCKER_COMPOSE_CMD up -d

echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

echo -e "${YELLOW}🔄 Running database migrations...${NC}"
$DOCKER_COMPOSE_CMD exec -T web python manage.py migrate

echo -e "${YELLOW}📁 Collecting static files...${NC}"
$DOCKER_COMPOSE_CMD exec -T web python manage.py collectstatic --noinput

echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker image prune -af --filter "until=24h"

echo -e "${YELLOW}🏥 Running health check...${NC}"
sleep 5
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment successful! Application is healthy.${NC}"
else
    echo -e "${RED}❌ Health check failed. Please check the logs.${NC}"
    echo -e "${YELLOW}View logs with: $DOCKER_COMPOSE_CMD logs${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${YELLOW}View logs: $DOCKER_COMPOSE_CMD logs -f${NC}"
echo -e "${YELLOW}Check status: $DOCKER_COMPOSE_CMD ps${NC}"

