# AgentROS Development Session Guide

This document helps maintain development context and progress across sessions.

## 🎯 Project Status

**Current Status:** ✅ MVP Core Complete  
**Last Updated:** June 12, 2025  
**Next Milestone:** First ROS 2 package generation

### ✅ Completed Components

1. **Multi-Agent Architecture**
   - ✅ Planning Agent (requirement analysis, task planning)
   - ✅ Coding Agent (implementation, code generation)  
   - ✅ Coordinator (orchestration, communication)
   - ✅ LLM integration with Ollama (local inference)

2. **MCP Server (Model Context Protocol)**
   - ✅ Secure sandbox environment
   - ✅ File operations (read/write/list)
   - ✅ Command execution with safety validation
   - ✅ Resource optimization for local development

3. **Development Infrastructure**
   - ✅ Test suite with unit/integration/performance tests
   - ✅ Makefile with optimized workflows
   - ✅ Resource monitoring and performance tracking
   - ✅ Pre-commit hooks and code quality tools

### 🚧 Next Steps

1. **Immediate (Next Session)**
   - [ ] Test end-to-end package generation
   - [ ] Create sample ROS 2 packages for validation
   - [ ] Optimize LLM prompt engineering
   - [ ] Add error recovery workflows

2. **Short Term (This Week)**
   - [ ] GUI development (React/Vite frontend)
   - [ ] CI/CD pipeline setup
   - [ ] Documentation completion
   - [ ] Performance benchmarking

3. **Medium Term (Next Week)**
   - [ ] Advanced ROS 2 templates (navigation, perception)
   - [ ] Learning from generated packages
   - [ ] Integration with ROS 2 ecosystem tools

## 🛠️ Quick Development Commands

```bash
# Start development session
make dev

# Run fast tests
make test-fast

# Generate a test package
agentros generate "Create a simple publisher node"

# Monitor performance
make monitor-resources

# Check system health
make diagnose
```

## 📊 Architecture Overview

```
User Request → Planning Agent → Task Breakdown
     ↓                           ↓
Coordinator ← → Coding Agent → Implementation
     ↓                           ↓
MCP Server ← → File System + Commands → ROS 2 Package
```

## 🔧 Key Configuration Files

- **`pyproject.toml`** - Dependencies and project metadata
- **`Makefile`** - Development workflows
- **`OPTIMIZATION.md`** - Performance tuning guide
- **`tests/conftest.py`** - Test configuration
- **`agent_core/`** - Core multi-agent system
- **`mcp_server/`** - Secure operations server

## 🧠 Memory for AI Assistants

If working with a new AI assistant, they should:

1. **Read this file first** to understand project status
2. **Run `make diagnose`** to check system health
3. **Review `TODO.md`** for outstanding tasks
4. **Check `tests/`** to understand testing patterns
5. **Read `OPTIMIZATION.md`** for performance context

## 🎨 Development Patterns

### Typical Workflow
1. Make changes to agent code
2. Run `make quick` (lint + fast tests, ~15s)
3. Test with `agentros generate "test prompt"`
4. Run `make test-unit` for broader validation
5. Commit with `make commit-ready`

### Performance Testing
- **Unit tests**: < 15 seconds
- **Integration**: < 60 seconds  
- **Memory usage**: < 4GB total
- **Package generation**: < 30 seconds (simple)

### Debugging Tips
- Use `--mock-llm` for faster testing
- Check `make monitor-resources` for bottlenecks
- Review logs in sandbox `/tmp/agentros_sandbox/logs/`
- Test individual agents with unit tests

## 📝 Code Quality Standards

- **Type hints** on all functions
- **Docstrings** for public APIs
- **Unit tests** for core functionality
- **Resource limits** for local development
- **Error handling** with graceful degradation

## 🚀 Optimization Notes

**For Local Development:**
- Uses smaller LLM models (6.7B vs 34B)
- Configurable parallel workers
- Smart test selection with markers
- Build caching and incremental compilation
- Mocked LLM responses for speed

**Resource Targets:**
- Cold start: < 30s
- Hot reload: < 5s
- Memory: < 4GB
- Test suite: < 2min

## 🔍 Troubleshooting

**Common Issues:**
1. **Tests failing**: Check if Ollama is running, use `--mock-llm`
2. **Memory issues**: Reduce `AGENTROS_PARALLEL_WORKERS`
3. **Slow tests**: Use `pytest -m "not slow"`
4. **Import errors**: Run `pip install -e .`

**Health Checks:**
```bash
make diagnose                    # System diagnostics
curl http://localhost:11434/api/tags  # Check Ollama
pytest --collect-only           # Validate test discovery
```

## 📈 Success Metrics

**Development Velocity:**
- [ ] Can generate simple ROS 2 package in < 30s
- [ ] Test suite runs in < 2 minutes
- [ ] Error recovery works within 3 attempts
- [ ] Memory usage stays < 4GB

**Code Quality:**
- [ ] 90%+ test coverage on core components
- [ ] No flake8/ruff violations
- [ ] All type hints pass mypy
- [ ] Documentation is up-to-date

---

## 💡 For New AI Assistants

**First Actions:**
1. Read this file completely
2. Run `make diagnose` to check system health
3. Review recent git commits: `git log --oneline -10`
4. Check test status: `make test-fast`
5. Understand current blockers in `TODO.md`

**Context Files to Review:**
- `README.md` - Project overview
- `OPTIMIZATION.md` - Performance guide  
- `agent_core/agents/` - Core agent implementations
- `tests/` - Test patterns and fixtures

This ensures continuity across development sessions!
