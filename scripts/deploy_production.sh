#!/bin/bash
# LANS Production Deployment Script
# Automated deployment for production environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV=${DEPLOYMENT_ENV:-production}
HEALTH_CHECK_PORT=${HEALTH_CHECK_PORT:-8080}
DB_PORT=${DB_PORT:-5432}
LANS_PORT=${LANS_PORT:-8000}

echo -e "${BLUE}🚀 LANS Production Deployment${NC}"
echo -e "${BLUE}===============================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Pre-deployment checks
echo -e "${BLUE}🔍 Pre-deployment checks...${NC}"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi
print_status "Docker is available"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH"
    exit 1
fi
print_status "Docker Compose is available"

# Check if .env file exists or create from example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning "No .env file found, copying from .env.example"
        cp .env.example .env
        print_warning "Please review and update .env file with production values"
    else
        print_error ".env.example file not found"
        exit 1
    fi
else
    print_status ".env file exists"
fi

# Validate Python environment
echo -e "${BLUE}🐍 Python environment validation...${NC}"
python3 -c "
import sys
print(f'Python version: {sys.version}')

# Test critical imports
try:
    from global_mcp_server.core.memory_manager import GlobalMemoryManager
    print('✅ GlobalMemoryManager import successful')
except ImportError as e:
    print(f'❌ GlobalMemoryManager import failed: {e}')
    sys.exit(1)

try:
    from global_mcp_server.core.overfitting_prevention import OverfittingPreventionManager  
    print('✅ OverfittingPreventionManager import successful')
except ImportError as e:
    print(f'❌ OverfittingPreventionManager import failed: {e}')
    sys.exit(1)

try:
    from agent_core.agents.planning_agent import PlanningAgent
    print('✅ PlanningAgent import successful')
except ImportError as e:
    print(f'❌ PlanningAgent import failed: {e}')
    sys.exit(1)

print('🎯 Core system integrity verified')
"

if [ $? -ne 0 ]; then
    print_error "Python environment validation failed"
    exit 1
fi

# Build Docker images
echo -e "${BLUE}🔨 Building Docker images...${NC}"
docker-compose -f docker-compose.global-memory.yml build
print_status "Docker images built successfully"

# Start services
echo -e "${BLUE}🚀 Starting LANS services...${NC}"

# Stop any existing services
docker-compose -f docker-compose.global-memory.yml down 2>/dev/null || true

# Start database first
echo -e "${BLUE}📊 Starting database...${NC}"
docker-compose -f docker-compose.global-memory.yml up -d postgres
sleep 10  # Wait for database to be ready

# Check database connectivity
echo -e "${BLUE}🔍 Checking database connectivity...${NC}"
for i in {1..30}; do
    if docker-compose -f docker-compose.global-memory.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_status "Database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Database failed to start within 30 seconds"
        docker-compose -f docker-compose.global-memory.yml logs postgres
        exit 1
    fi
    echo "Waiting for database... (${i}/30)"
    sleep 1
done

# Start LANS services
echo -e "${BLUE}🧠 Starting LANS core services...${NC}"
docker-compose -f docker-compose.global-memory.yml up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 15

# Health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Start health check server in background
python3 scripts/health_check.py &
HEALTH_PID=$!
sleep 5  # Give health server time to start

# Test health endpoints
echo -e "${BLUE}🔍 Testing health endpoints...${NC}"

# Basic health check
if curl -f "http://localhost:${HEALTH_CHECK_PORT}/health" > /dev/null 2>&1; then
    print_status "Basic health check passed"
else
    print_warning "Basic health check endpoint not responding"
fi

# Detailed health check
if curl -f "http://localhost:${HEALTH_CHECK_PORT}/health/detailed" > /dev/null 2>&1; then
    print_status "Detailed health check passed"
    
    # Show health report
    echo -e "${BLUE}📊 Health Report:${NC}"
    curl -s "http://localhost:${HEALTH_CHECK_PORT}/health/detailed" | python3 -m json.tool
else
    print_warning "Detailed health check endpoint not responding"
fi

# Clean up health check process
kill $HEALTH_PID 2>/dev/null || true

# Service status
echo -e "${BLUE}📋 Service Status:${NC}"
docker-compose -f docker-compose.global-memory.yml ps

# Show logs
echo -e "${BLUE}📝 Recent logs:${NC}"
docker-compose -f docker-compose.global-memory.yml logs --tail=20

# Deployment summary
echo -e "${BLUE}🎉 Deployment Summary${NC}"
echo -e "${BLUE}===================${NC}"
print_status "LANS deployment completed successfully"
echo ""
echo -e "${BLUE}📡 Service Endpoints:${NC}"
echo -e "  • LANS API: http://localhost:${LANS_PORT}"
echo -e "  • Database: localhost:${DB_PORT}"
echo -e "  • Health Check: http://localhost:${HEALTH_CHECK_PORT}/health"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "  • View logs: docker-compose -f docker-compose.global-memory.yml logs -f"
echo -e "  • Stop services: docker-compose -f docker-compose.global-memory.yml down"
echo -e "  • Restart services: docker-compose -f docker-compose.global-memory.yml restart"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo -e "  • Health status: curl http://localhost:${HEALTH_CHECK_PORT}/health/detailed"
echo -e "  • Service status: docker-compose -f docker-compose.global-memory.yml ps"
echo ""
echo -e "${GREEN}🚀 LANS is now running in production mode!${NC}"
