#!/bin/bash
set -e

# Server setup script for autoapply-be deployment
# Run this script once on a fresh server to prepare it for deployment

echo "🔧 Setting up server for autoapply-be deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Please don't run this script as root. Run as your regular user (lukas)${NC}"
    exit 1
fi

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

# Install Docker
echo -e "${YELLOW}🐳 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed successfully${NC}"
    echo -e "${YELLOW}⚠️  Please log out and log back in for Docker group membership to take effect${NC}"
else
    echo -e "${GREEN}✅ Docker is already installed${NC}"
fi

# Install Docker Compose
echo -e "${YELLOW}🐳 Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker Compose is already installed${NC}"
fi

# Configure firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5433/tcp  # PostgreSQL (if you want external access)
echo -e "${GREEN}✅ Firewall configured${NC}"

# Create project directory
echo -e "${YELLOW}📁 Creating project directory...${NC}"
mkdir -p ~/autoapply-be
echo -e "${GREEN}✅ Project directory created: ~/autoapply-be${NC}"

# Create directories for SSL certificates (optional, for Let's Encrypt)
echo -e "${YELLOW}📁 Creating SSL certificate directories...${NC}"
mkdir -p ~/autoapply-be/certbot/conf
mkdir -p ~/autoapply-be/certbot/www
echo -e "${GREEN}✅ SSL directories created${NC}"

# Display Docker version
echo -e "${YELLOW}📋 Installed versions:${NC}"
docker --version
docker-compose --version

echo -e "${GREEN}✅ Server setup completed!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Log out and log back in (or run: newgrp docker)"
echo "2. Clone or upload your project to ~/autoapply-be"
echo "3. Create .env file from .env.production template"
echo "4. Run: cd ~/autoapply-be && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo -e "${YELLOW}For CI/CD deployment:${NC}"
echo "1. Add GitHub secrets in your repository settings"
echo "2. Push to main/master branch to trigger automatic deployment"

