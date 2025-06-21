#!/bin/bash

# Global Memory MCP Server Startup Script

set -e

echo "🧠 Starting Global Memory MCP Server..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on localhost:5432"
    echo "Please start PostgreSQL and create the 'global_memory' database:"
    echo "  sudo systemctl start postgresql"
    echo "  sudo -u postgres createdb global_memory"
    echo "  sudo -u postgres psql -c \"CREATE USER postgres WITH PASSWORD 'postgres';\""
    echo "  sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE global_memory TO postgres;\""
    exit 1
fi

# Check if database exists
if ! psql -h localhost -U postgres -d global_memory -c '\q' >/dev/null 2>&1; then
    echo "📊 Creating global_memory database..."
    createdb -h localhost -U postgres global_memory
fi

# Load environment variables
if [ -f .env ]; then
    echo "📄 Loading environment from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using defaults"
fi

# Install/upgrade required packages
echo "📦 Installing required packages..."
pip install -e . --quiet

# Start the server
echo "🚀 Starting Global Memory MCP Server..."
echo "   URL: http://localhost:${GMCP_SERVER_PORT:-8001}"
echo "   Health Check: http://localhost:${GMCP_SERVER_PORT:-8001}/health"
echo "   API Docs: http://localhost:${GMCP_SERVER_PORT:-8001}/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m global_mcp_server.core.server
