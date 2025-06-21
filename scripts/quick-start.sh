#!/bin/bash
# LANS Development Quick Start Script

set -e

echo "🚀 LANS Quick Development Setup"

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Please run this script from the LANS root directory"
    exit 1
fi

# Set resource-efficient defaults
export LANS_PARALLEL_WORKERS=${LANS_PARALLEL_WORKERS:-2}
export LANS_MAX_MEMORY_GB=${LANS_MAX_MEMORY_GB:-2}
export LANS_BUILD_TIMEOUT=${LANS_BUILD_TIMEOUT:-180}

echo "⚙️  Resource configuration:"
echo "   - Parallel workers: $LANS_PARALLEL_WORKERS"
echo "   - Memory limit: ${LANS_MAX_MEMORY_GB}GB"
echo "   - Build timeout: ${LANS_BUILD_TIMEOUT}s"

# Quick health check
echo "🔍 Running quick health check..."

# Test basic imports
echo "   - Testing Python imports..."
python -c "
import agent_core
import mcp_server
print('✓ Core imports working')
" || {
    echo "❌ Import test failed. Run 'pip install -e .' first"
    exit 1
}

# Test basic functionality
echo "   - Testing basic functionality..."
python -m pytest tests/test_simple.py::test_simple -q --tb=no || {
    echo "❌ Basic tests failed"
    exit 1
}

echo ""
echo "✅ LANS is ready for development!"
echo ""
echo "🎯 Quick commands:"
echo "   make test-fast     # Run fast tests (~15s)"
echo "   make quick         # Lint + fast tests (~20s)"
echo "   make dev           # Start development environment"
echo ""
echo "📊 Performance monitoring:"
echo "   make monitor-resources  # Monitor system resources"
echo "   make diagnose          # System diagnostics"
echo ""
echo "📖 More commands: make help"
