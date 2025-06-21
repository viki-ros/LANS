# LANS - Large Artificial Neural System

**Advanced Multi-Agent AI Platform with Cognitive Architecture**

LANS is a sophisticated multi-agent AI system that combines cognitive agents, persistent memory, and a desktop interface (ICE) for advanced AI interactions and development workflows.

## 🎯 Current Status

**LANS is currently in active development.** The system includes several working components but is not yet ready for general production use. This README reflects the **actual current state** of the project.

## 🚀 What is LANS?

LANS is a **research-focused AI platform** featuring:

- **🧠 Cognitive Agents**: Advanced AI agents with memory, reasoning, and self-reflection capabilities
- **💾 Global Memory System**: Persistent, shared memory across AI agents and sessions
- **🖥️ ICE Desktop App**: Modern desktop interface for AI interactions
- **🔗 MCP Integration**: Model Context Protocol for secure agent operations
- **🔄 Multi-Agent Architecture**: Coordinated agents for complex tasks

## ✨ Current Features

### 🧠 Cognitive Agent System
- **Memory & Reasoning**: Agents with episodic, semantic, and procedural memory
- **Self-Reflection**: Agents that learn from experiences and improve over time
- **Goal-Oriented Behavior**: Task-focused AI with performance tracking
- **Multi-Model Support**: Integration with various LLMs via Ollama

### 💾 Global Memory MCP Server
- **Persistent Storage**: Knowledge that survives across sessions
- **Cross-Agent Sharing**: Agents can learn from each other's experiences
- **Vector-Based Retrieval**: Intelligent memory search and recall
- **Memory Types**: Episodic (events), Semantic (facts), Procedural (skills)

### �️ ICE Desktop Application
- **Modern UI**: React + Tauri-based desktop application
- **Terminal Integration**: Built-in terminal with xterm.js
- **Code Editor**: Monaco editor integration
- **Real-time Interaction**: Live AI agent communication

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LANS Platform                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Cognitive  │◄──►│    ICE      │◄──►│   Global    │    │
│  │   Agents    │    │  Desktop    │    │   Memory    │    │
│  │             │    │    App      │    │             │    │
│  │ • Memory    │    │ • Terminal  │    │ • Episodic  │    │
│  │ • Reasoning │    │ • Editor    │    │ • Semantic  │    │
│  │ • Learning  │    │ • Chat UI   │    │ • Procedural│    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │         │
│         └───────────────────┼───────────────────┘         │
│                             │                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              MCP Protocol Layer                    │  │
│  │    Secure communication between components         │  │
│  └─────────────────────────────────────────────────────┘  │
│                             │                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                 Ollama LLMs                        │  │
│  │         Local model inference engine               │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+ (for ICE desktop app)
- Ollama (for local LLM inference)
- Git

### 1. Basic Setup

```bash
# Clone the repository
git clone https://github.com/viki-ros/LANS.git
cd LANS

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required Python packages
pip install -r requirements.txt
```

### 2. Setup Ollama (Local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models for LANS
ollama pull deepseek-coder:6.7b
ollama pull llama3.1:8b
ollama pull codellama:7b
```

### 3. Run LANS Components

#### Option A: Use the Fresh Launcher (Recommended)
```bash
# Run the comprehensive launcher
python lans_fresh_launcher.py
```

#### Option B: Use Individual Components
```bash
# Run cognitive agents
python cognitive_agents.py

# Or use the CLI
python -m agent_core.cli
```

### 4. ICE Desktop App (Optional)

```bash
# Navigate to ICE desktop app
cd ice/desktop-app

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📖 Usage Examples

### Cognitive Agent Interaction

The primary way to interact with LANS is through the cognitive agents:

```bash
# Start the fresh launcher for interactive mode
python lans_fresh_launcher.py

# Follow the interactive prompts to:
# - Initialize agents
# - Start global memory server
# - Chat with AI agents
# - Switch between different models
```

### Global Memory System

```python
# Example: Using the global memory system
from global_mcp_server.api import GMCPClient

client = GMCPClient("http://localhost:8080")
await client.store_memory(
    memory_type="episodic",
    content="Successful Python project creation",
    metadata={"project_type": "python", "success": True}
)
```

### ICE Desktop Interface

The ICE desktop app provides a modern GUI for:
- Terminal integration with AI assistance
- Code editing with Monaco editor
- Real-time agent communication
- Memory system visualization

## 🔧 Current Capabilities

### ✅ Working Features

- **Cognitive Agents**: Multi-agent system with memory and reasoning
- **Global Memory**: Persistent knowledge storage and retrieval
- **ICE Desktop**: Modern desktop interface
- **Ollama Integration**: Local LLM support
- **MCP Protocol**: Secure agent communication
- **Interactive Launchers**: Multiple ways to start and interact with the system

### 🚧 In Development

- **CLI Interface**: Command-line tool for direct task execution
- **Package Installation**: Proper Python package setup
- **Advanced Reasoning**: Enhanced cognitive capabilities
- **Plugin System**: Extensible architecture
- **Web Interface**: Browser-based interaction

## 🧠 Global Memory System

LANS includes an advanced **Global Memory MCP Server** that provides persistent, shared memory capabilities for AI agents across sessions and systems.

### Key Features

- **Episodic Memory**: Stores experiences, conversations, and events
- **Semantic Memory**: Stores facts, concepts, and relationships
- **Procedural Memory**: Stores skills, methods, and how-to knowledge
- **Cross-Agent Knowledge Sharing**: Agents can learn from each other
- **Persistent Storage**: Memory survives across sessions
- **Intelligent Retrieval**: Vector-based semantic search
- **Global Accessibility**: Any AI model can access the memory system

### Starting Global Memory

```bash
# Start with the launcher (recommended)
python lans_fresh_launcher.py

# Or start manually
cd scripts
./start_global_memory.sh
```

## 📁 Project Structure

```
LANS/
├── agent_core/              # Core multi-agent system
│   ├── agents/              # AI agents (planning, coding, coordinator)
│   ├── core/                # Core engine and configuration
│   ├── llm/                 # LLM integration (Ollama client)
│   └── cli.py               # Command-line interface
├── cognitive_agents.py      # Enhanced cognitive agent system
├── global_mcp_server/       # Global memory system
│   ├── api/                 # Memory API endpoints
│   ├── core/                # Memory management logic
│   ├── storage/             # Persistent storage layer
│   └── config/              # Configuration files
├── ice/                     # ICE Desktop Application
│   ├── desktop-app/         # Tauri + React desktop app
│   └── agent-host/          # Agent hosting system
├── mcp_server/              # Model Context Protocol server
│   ├── handlers/            # Request handlers
│   └── security/            # Security and validation
├── scripts/                 # Utility and setup scripts
│   ├── start_global_memory.sh
│   ├── setup_dev.sh
│   └── quick-start.sh
├── lans_fresh_launcher.py   # Main interactive launcher
├── lans_cli.py              # CLI interface
└── tests/                   # Test suite
```

## 🔄 How LANS Works

1. **Initialize System**: Start with `lans_fresh_launcher.py` for full system initialization
2. **Agent Interaction**: Cognitive agents with memory, reasoning, and learning capabilities
3. **Memory Integration**: Persistent knowledge storage across sessions
4. **Model Flexibility**: Support for multiple LLMs via Ollama
5. **Desktop Interface**: Optional GUI through ICE desktop app

## 🛠️ Development & Configuration

### Environment Setup

```bash
# Development setup
git clone https://github.com/viki-ros/LANS.git
cd LANS

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black ruff    # Development tools
```

### Configuration

Key configuration files:
- `agent_core/core/config.py` - Core agent configuration
- `global_mcp_server/config/` - Memory system settings
- `scripts/setup_dev.sh` - Development environment setup

### Available Launchers

- **`lans_fresh_launcher.py`** - Comprehensive system launcher (recommended)
- **`cognitive_agents.py`** - Direct cognitive agent interaction
- **`lans_cli.py`** - Command-line interface
- **`demo_launcher.py`** - Demonstration and testing
## 🚨 Security & Safety

- **Local Execution**: Runs entirely on your local machine
- **MCP Protocol**: Secure communication between components
- **Sandboxed Operations**: Safe execution environment
- **No External Dependencies**: No cloud services required
- **Privacy-First**: Your data stays on your system

## 📊 Performance & Requirements

### System Requirements
- **OS**: Linux, macOS, Windows
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum, 16GB recommended (for LLMs)
- **Storage**: 10GB+ for models and workspace
- **GPU**: Optional but recommended for faster inference

### Performance
- **Startup**: ~30 seconds for full system initialization
- **Response Time**: Varies by model and query complexity
- **Memory Usage**: Efficient memory management with optional cleanup
- **Offline**: Full functionality without internet connection

## 🚧 Known Limitations

- **CLI Interface**: Not fully implemented yet
- **Package Installation**: No pip package available currently
- **Documentation**: Some features still need documentation
- **Testing**: Test coverage is incomplete
- **Stability**: Some components are experimental

## 🤝 Contributing

We welcome contributions! The project is actively developed and needs help with:

- **Core Features**: Implementing missing CLI functionality
- **Testing**: Expanding test coverage
- **Documentation**: Improving guides and examples
- **UI/UX**: Enhancing the ICE desktop app
- **Performance**: Optimizing memory and speed

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/LANS.git
cd LANS

# Set up development environment
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh

# Run tests
python -m pytest tests/

# Code formatting
black . && ruff check --fix .
```

## 📋 Roadmap

### Short Term (2025 Q2-Q3)
- [ ] Complete CLI interface implementation
- [ ] Package installation setup (setup.py/pyproject.toml)
- [ ] Comprehensive documentation
- [ ] Expanded test coverage
- [ ] Performance optimizations

### Medium Term (2025 Q4)
- [ ] Web interface for remote access
- [ ] Enhanced cognitive capabilities
- [ ] Plugin system architecture
- [ ] Multi-user support
- [ ] Cloud deployment options

### Long Term (2026+)
- [ ] Advanced reasoning capabilities
- [ ] Enterprise features
- [ ] Mobile applications
- [ ] Integration with other AI platforms
- [ ] Commercial licensing options

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- **Ollama** for local LLM inference
- **React + Tauri** for the ICE desktop application
- **FastAPI** for API services
- **SQLite/PostgreSQL** for data storage
- **Model Context Protocol** for secure agent operations

---

**LANS is under active development. Star the repo to follow progress!**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/viki-ros/LANS).
