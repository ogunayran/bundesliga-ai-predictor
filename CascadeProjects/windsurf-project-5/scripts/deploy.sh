#!/bin/bash

# Grocery Dynamic Pricing - Quick Deploy Script
# Usage: ./scripts/deploy.sh [dev|prod]

set -e

MODE=${1:-dev}
PROJECT_NAME="grocery-pricing"

echo "🚀 Deploying Grocery Dynamic Pricing System..."
echo "📦 Mode: $MODE"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p data logs backups nginx/ssl

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration before continuing.${NC}"
    read -p "Press enter to continue after editing .env..."
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Build the image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker-compose build

# Start services based on mode
if [ "$MODE" = "prod" ]; then
    echo -e "${YELLOW}🌐 Starting production services (with Nginx)...${NC}"
    docker-compose --profile production up -d
else
    echo -e "${YELLOW}💻 Starting development services...${NC}"
    docker-compose up -d
fi

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check if app is running
if docker ps | grep -q "$PROJECT_NAME-app"; then
    echo -e "${GREEN}✅ Application is running!${NC}"
    
    # Show container status
    echo ""
    echo -e "${GREEN}📊 Container Status:${NC}"
    docker-compose ps
    
    echo ""
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo ""
    echo "📱 Access the application:"
    if [ "$MODE" = "prod" ]; then
        echo "   🌐 Dashboard: http://localhost"
        echo "   📊 Analytics: http://localhost/analytics.html"
        echo "   🔌 API: http://localhost/api"
    else
        echo "   🌐 Dashboard: http://localhost:3000"
        echo "   📊 Analytics: http://localhost:3000/analytics.html"
        echo "   🔌 API: http://localhost:3000/api"
    fi
    echo ""
    echo "📝 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop: docker-compose down"
    echo "   Restart: docker-compose restart"
    echo "   Backup DB: docker exec $PROJECT_NAME-app sqlite3 /app/data/grocery.db \".backup /app/data/backup.db\""
    echo ""
else
    echo -e "${RED}❌ Deployment failed. Check logs with: docker-compose logs${NC}"
    exit 1
fi
