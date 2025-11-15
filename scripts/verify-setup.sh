#!/bin/bash

# Verification script to check if all deployment files are present
# Run this before attempting deployment

echo "🔍 Verifying deployment setup..."
echo ""

ERRORS=0
WARNINGS=0

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check function
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        ((ERRORS++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
    else
        echo -e "${RED}✗${NC} $1/ (MISSING)"
        ((ERRORS++))
    fi
}

echo "📦 Checking Docker configuration..."
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file "docker-compose.prod.yml"
check_file ".dockerignore"
echo ""

echo "🌐 Checking Nginx configuration..."
check_dir "nginx"
check_file "nginx/nginx.conf"
check_file "nginx/conf.d/autoapply.conf"
echo ""

echo "🤖 Checking CI/CD configuration..."
check_dir ".github/workflows"
check_file ".github/workflows/deploy.yml"
echo ""

echo "📜 Checking deployment scripts..."
check_dir "scripts"
check_file "scripts/setup-server.sh"
check_file "scripts/deploy.sh"
check_file "scripts/rollback.sh"
check_file "scripts/local-deploy-test.ps1"
echo ""

echo "📄 Checking configuration files..."
check_file "env.production.template"
check_file "requirements.txt"
echo ""

echo "📚 Checking documentation..."
check_file "DEPLOYMENT.md"
check_file "QUICK_START_DEPLOY.md"
check_file "DOCKER_CHEATSHEET.md"
check_file "DEPLOYMENT_SUMMARY.md"
echo ""

# Check if requirements.txt has gunicorn
if grep -q "gunicorn" requirements.txt; then
    echo -e "${GREEN}✓${NC} gunicorn in requirements.txt"
else
    echo -e "${RED}✗${NC} gunicorn not in requirements.txt"
    ((ERRORS++))
fi

# Check Docker Compose files use V2 syntax (docker compose)
if grep -q "docker compose" docker-compose.prod.yml; then
    echo -e "${GREEN}✓${NC} Docker Compose V2 syntax (docker compose)"
else
    echo -e "${YELLOW}⚠${NC}  Using old Docker Compose V1 syntax (docker-compose)"
    ((WARNINGS++))
fi
echo ""

# Optional checks
echo "⚠️  Optional checks..."

if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  .env file exists (should not be committed to git)"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} No .env file in repo (good)"
fi

if [ -f "env.example" ]; then
    echo -e "${GREEN}✓${NC} env.example exists"
else
    echo -e "${YELLOW}⚠${NC}  env.example not found (not critical)"
    ((WARNINGS++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All required files are present!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review DEPLOYMENT_SUMMARY.md"
    echo "2. Follow QUICK_START_DEPLOY.md for deployment"
    echo "3. Configure GitHub secrets for CI/CD"
else
    echo -e "${RED}❌ Found $ERRORS missing files!${NC}"
    echo "Please ensure all required files are present before deploying."
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warnings (review recommended)${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

