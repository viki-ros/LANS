#!/bin/bash

# AgentROS Development Setup Script
# Optimized for local development with resource efficiency

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 AgentROS Development Setup${NC}"
echo "Setting up optimized local development environment..."

# Check system requirements
check_requirements() {
    echo -e "\n${YELLOW}📋 Checking system requirements...${NC}"
    
    # Check Python version
    if ! python3 --version | grep -E "3\.(9|10|11|12)" > /dev/null; then
        echo -e "${RED}❌ Python 3.9+ required${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python version OK${NC}"
    
    # Check available memory (should have at least 4GB)
    memory_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    memory_gb=$((memory_kb / 1024 / 1024))
    
    if [ $memory_gb -lt 4 ]; then
        echo -e "${YELLOW}⚠️  Warning: Low memory (${memory_gb}GB). Consider closing other applications.${NC}"
    else
        echo -e "${GREEN}✓ Memory OK (${memory_gb}GB)${NC}"
    fi
    
    # Check CPU cores
    cores=$(nproc)
    echo -e "${GREEN}✓ CPU cores: ${cores}${NC}"
    
    # Adjust parallel workers based on available resources
    if [ $cores -gt 4 ]; then
        export AGENTROS_PARALLEL_WORKERS=4
    else
        export AGENTROS_PARALLEL_WORKERS=$((cores))
    fi
    
    echo -e "${BLUE}🔧 Setting parallel workers to: ${AGENTROS_PARALLEL_WORKERS}${NC}"
}

# Setup Python environment
setup_python_env() {
    echo -e "\n${YELLOW}🐍 Setting up Python environment...${NC}"
    
    # Check if conda is available
    if command -v conda &> /dev/null; then
        echo "Using conda for environment management"
        
        # Create or activate environment
        if conda env list | grep -q "agentros"; then
            echo "AgentROS conda environment already exists"
            source "$(conda info --base)/etc/profile.d/conda.sh"
            conda activate agentros
        else
            echo "Creating new conda environment..."
            conda create -n agentros python=3.10 -y
            source "$(conda info --base)/etc/profile.d/conda.sh"
            conda activate agentros
        fi
    else
        echo "Using venv for environment management"
        
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
    fi
    
    # Install dependencies with optimizations
    echo "Installing Python dependencies..."
    
    # Install with reduced verbosity for faster setup
    pip install -e ".[dev]" --quiet --disable-pip-version-check
    
    echo -e "${GREEN}✓ Python environment ready${NC}"
}

# Setup Ollama with optimized models
setup_ollama() {
    echo -e "\n${YELLOW}🦙 Setting up Ollama LLM server...${NC}"
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo -e "${GREEN}✓ Ollama already installed${NC}"
    fi
    
    # Start Ollama service if not running
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting Ollama service..."
        ollama serve &
        sleep 3
    fi
    
    # Pull optimized models for local development
    echo "Setting up AI models (this may take a while)..."
    
    # Use smaller models for faster local development
    echo "Pulling DeepSeek Coder 6.7B (planning agent)..."
    ollama pull deepseek-coder:6.7b
    
    echo "Pulling Devstral (coding agent)..."
    ollama pull devstral:latest
    
    echo -e "${GREEN}✓ Ollama and models ready${NC}"
}

# Create optimized development configuration
create_dev_config() {
    echo -e "\n${YELLOW}⚙️  Creating development configuration...${NC}"
    
    # Create .env file for development
    cat > .env << EOF
# AgentROS Development Configuration
# Optimized for local development

# LLM Settings
OLLAMA_URL=http://localhost:11434
AGENTROS_USE_CACHE=true
AGENTROS_CACHE_TTL=3600

# MCP Server Settings  
MCP_SERVER_URL=http://localhost:8000
MCP_SANDBOX_ROOT=/tmp/agentros_sandbox

# Resource Optimization
AGENTROS_PARALLEL_WORKERS=${AGENTROS_PARALLEL_WORKERS:-2}
AGENTROS_MAX_MEMORY_GB=2
AGENTROS_BUILD_TIMEOUT=300
AGENTROS_RETRY_LIMIT=3

# Development Features
AGENTROS_DEBUG=true
AGENTROS_LOG_LEVEL=INFO
AGENTROS_FAST_MODE=true

# ROS 2 Settings (if available)
ROS_DOMAIN_ID=42
EOF
    
    # Create pytest configuration for efficient testing
    cat > pytest.ini << EOF
[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    --strict-markers 
    --strict-config 
    --disable-warnings
    -x
    --tb=short
    --maxfail=3
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests  
    unit: marks tests as unit tests
    llm: marks tests that require LLM
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
EOF

    echo -e "${GREEN}✓ Development configuration created${NC}"
}

# Setup development tools
setup_dev_tools() {
    echo -e "\n${YELLOW}🛠️  Setting up development tools...${NC}"
    
    # Setup pre-commit hooks for code quality
    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    fi
    
    # Create useful development scripts
    mkdir -p scripts
    
    # Quick test script
    cat > scripts/quick_test.sh << 'EOF'
#!/bin/bash
# Quick test script for development
echo "🧪 Running quick tests..."
pytest tests/ -m "unit and not slow" --maxfail=1 -q
EOF
    
    # Performance test script  
    cat > scripts/perf_test.sh << 'EOF'
#!/bin/bash
# Performance monitoring for development
echo "📊 Running performance tests..."
pytest tests/ -m "unit" --durations=10 -v
EOF
    
    # Local development server script
    cat > scripts/dev_server.sh << 'EOF'
#!/bin/bash
# Start development servers
echo "🚀 Starting AgentROS development servers..."

# Start MCP server in background
echo "Starting MCP server..."
agentros server --host localhost --port 8000 &
MCP_PID=$!

# Wait for server to start
sleep 2

echo "✓ MCP Server running (PID: $MCP_PID)"
echo "✓ Ollama should be running on port 11434"
echo ""
echo "Ready for development! 🎉"
echo "Use 'agentros status' to check system status"
echo "Use 'kill $MCP_PID' to stop MCP server"
EOF
    
    chmod +x scripts/*.sh
    
    echo -e "${GREEN}✓ Development tools ready${NC}"
}

# Optimize system for development
optimize_system() {
    echo -e "\n${YELLOW}⚡ Applying system optimizations...${NC}"
    
    # Set memory overcommit for better resource usage
    if [ -w /proc/sys/vm/overcommit_memory ]; then
        echo 1 | sudo tee /proc/sys/vm/overcommit_memory > /dev/null
        echo -e "${GREEN}✓ Memory overcommit optimized${NC}"
    fi
    
    # Increase file watch limits for development
    if [ -w /proc/sys/fs/inotify/max_user_watches ]; then
        echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches > /dev/null
        echo -e "${GREEN}✓ File watch limits increased${NC}"
    fi
    
    # Setup swap if needed (for memory efficiency)
    if [ ! -f /swapfile ] && [ $(free -m | awk '/^Mem:/{print $2}') -lt 8192 ]; then
        echo -e "${YELLOW}⚠️  Consider adding swap space for better memory management${NC}"
        echo "Run: sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 && sudo mkswap /swapfile && sudo swapon /swapfile"
    fi
}

# Create workspace structure
create_workspace() {
    echo -e "\n${YELLOW}📁 Creating workspace structure...${NC}"
    
    # Initialize workspace if not already done
    if [ ! -d "examples" ]; then
        agentros init . --examples
    fi
    
    echo -e "${GREEN}✓ Workspace ready${NC}"
}

# Run setup validation
validate_setup() {
    echo -e "\n${YELLOW}✅ Validating setup...${NC}"
    
    # Check that all services are accessible
    echo "Checking Ollama..."
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo -e "${GREEN}✓ Ollama accessible${NC}"
    else
        echo -e "${RED}❌ Ollama not accessible${NC}"
    fi
    
    # Run a quick test
    echo "Running quick validation test..."
    if python -c "import agent_core; print('✓ AgentROS package imports OK')" 2>/dev/null; then
        echo -e "${GREEN}✓ Python package OK${NC}"
    else
        echo -e "${RED}❌ Python package import failed${NC}"
    fi
    
    echo -e "\n${GREEN}🎉 Setup complete! Ready for development.${NC}"
    echo -e "\n${BLUE}Quick start:${NC}"
    echo "  1. Start servers: ./scripts/dev_server.sh"
    echo "  2. Check status: agentros status"
    echo "  3. Generate package: agentros generate 'Create a simple publisher node'"
    echo "  4. Run tests: ./scripts/quick_test.sh"
}

# Main setup flow
main() {
    check_requirements
    setup_python_env
    setup_ollama
    create_dev_config
    setup_dev_tools
    optimize_system
    create_workspace
    validate_setup
}

# Handle script arguments
case "${1:-setup}" in
    setup)
        main
        ;;
    quick)
        echo -e "${BLUE}🚀 Quick setup (skipping system optimizations)${NC}"
        setup_python_env
        create_dev_config
        setup_dev_tools
        create_workspace
        ;;
    validate)
        validate_setup
        ;;
    *)
        echo "Usage: $0 [setup|quick|validate]"
        echo "  setup   - Full development setup (default)"
        echo "  quick   - Quick setup without system changes"  
        echo "  validate - Validate existing setup"
        exit 1
        ;;
esac
