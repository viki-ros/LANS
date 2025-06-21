# LANS - Large Artificial Neural System

**Universal AI Software Generation Platform**

A sophisticated AI system that transforms natural language requests into complete software projects. LANS uses multi-agent architecture with persistent memory to generate any type of software - from simple scripts to complex applications.

## 🚀 What is LANS?

LANS is a **general-purpose AI software generation platform** that can create:

- **Web Applications** (React, Vue, Next.js, Flask, FastAPI)
- **CLI Tools** (Python, Node.js, Rust, Go)
- **Desktop Applications** (Electron, Tkinter, PyQt)
- **APIs and Microservices** (REST, GraphQL, gRPC)
- **Mobile Apps** (React Native, Flutter basics)
- **Games** (Pygame, JavaScript canvas)
- **Data Science Projects** (Jupyter notebooks, analysis scripts)
- **Simple Utilities** (calculators, file processors, converters)

## ✨ Key Features

### 🧠 Multi-Agent Intelligence
- **Planning Agent**: Analyzes requirements and creates project architecture
- **Coding Agent**: Generates production-ready code with best practices
- **Coordinator**: Orchestrates workflow and handles error recovery

### 🔄 Autonomous Generation
```bash
# Simple folder creation
lans "create folder my_project"

# File creation with content
lans "create file hello.py with a simple greeting"

# Complete application
lans "create a calculator app with GUI"

# Web application
lans "create a todo app with React and FastAPI backend"
```

### 🧠 Persistent Memory System
- **Global Memory**: Learns from every project and improves over time
- **Pattern Recognition**: Remembers successful architectures and solutions
- **Cross-Project Learning**: Knowledge transfers between different types of projects

### 🔐 Secure Execution
- **Sandboxed Environment**: Safe code execution and testing
- **MCP Protocol**: Secure file operations and command execution
- **Error Recovery**: Automatic detection and fixing of issues

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  LANS Core System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Planning   │◄──►│ Coordinator │◄──►│   Coding    │    │
│  │   Agent     │    │             │    │   Agent     │    │
│  │             │    │ Orchestrates│    │             │    │
│  │ • Analyzes  │    │ workflow &  │    │ • Generates │    │
│  │ • Plans     │    │ manages     │    │ • Implements│    │
│  │ • Designs   │    │ state       │    │ • Tests     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │         │
│         └───────────────────┼───────────────────┘         │
│                             │                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              MCP Server (Security Layer)           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │  │
│  │  │   File      │ │   Command   │ │   Project   │   │  │
│  │  │ Operations  │ │ Execution   │ │   Build     │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
│                             │                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Global Memory System                     │  │
│  │     Persistent Learning & Knowledge Base           │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LANS.git
cd LANS

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install LANS
pip install -e .
```

### 2. Setup Local LLM (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models
ollama pull deepseek-coder:6.7b
ollama pull codellama:7b
```

### 3. Start LANS

```bash
# Start the MCP server
lans-server

# In another terminal, use LANS
lans "create a simple calculator app"
```

## 📖 Usage Examples

### Simple File Operations
```bash
# Create folders
lans "create folder my_new_project"

# Create files with content
lans "create file config.json with basic settings"

# Create Python scripts
lans "create a Python script to process CSV files"
```

### Web Development
```bash
# Frontend applications
lans "create a React todo app with local storage"
lans "create a Vue.js weather dashboard"

# Backend APIs
lans "create a FastAPI service for user management"
lans "create a Flask blog API with SQLite"

# Full-stack applications
lans "create a todo app with React frontend and Node.js backend"
```

### Desktop Applications
```bash
# GUI applications
lans "create a Python GUI calculator with Tkinter"
lans "create an Electron text editor app"

# CLI tools
lans "create a command-line file organizer in Python"
lans "create a Rust CLI tool for JSON processing"
```

### Data Science & Analysis
```bash
# Analysis projects
lans "create a Jupyter notebook for stock price analysis"
lans "create a Python script for data visualization with matplotlib"

# Machine learning
lans "create a simple image classifier with TensorFlow"
```

## 🔧 Advanced Features

### Project Templates
LANS includes built-in templates for common project types:

- **web_app**: Modern web applications with best practices
- **api**: RESTful APIs with documentation
- **cli_tool**: Command-line utilities with argument parsing
- **desktop_app**: Cross-platform desktop applications
- **library**: Reusable code libraries with proper packaging
- **game**: Simple games with graphics and interaction
- **data_science**: Analysis projects with proper structure

### Intelligent Code Generation
- **Language Detection**: Automatically chooses the best language for the task
- **Framework Selection**: Picks appropriate frameworks and libraries
- **Best Practices**: Follows industry standards and patterns
- **Error Handling**: Includes proper exception handling and logging
- **Testing**: Generates unit tests and validation code

### Continuous Learning
- **Success Patterns**: Remembers what works well for different project types
- **Error Solutions**: Learns from mistakes and applies fixes automatically
- **User Preferences**: Adapts to your coding style and preferences
- **Knowledge Sharing**: Benefits from the collective experience of all users

## 🧠 Global Memory System

LANS includes a revolutionary **Global Memory MCP Server** that provides persistent, shared memory capabilities for AI agents across sessions and systems.

### Key Features

- **Episodic Memory**: Stores experiences, conversations, and events
- **Semantic Memory**: Stores facts, concepts, and relationships  
- **Procedural Memory**: Stores skills, methods, and how-to knowledge
- **Cross-Agent Knowledge Sharing**: Agents can learn from each other
- **Persistent Storage**: Memory survives across sessions
- **Intelligent Retrieval**: Vector-based semantic search
- **Global Accessibility**: Any AI model can access the memory system

### Quick Start with Global Memory

```bash
# Start the Global Memory server (requires PostgreSQL)
./scripts/start_global_memory.sh

# Or use Docker Compose
docker-compose -f docker-compose.global-memory.yml up -d
```

### Using Global Memory in Your Code

```python
from global_mcp_server.api import GMCPClient, LANSMemoryIntegration

# Basic client usage
client = GMCPClient("http://localhost:8001")
client.configure_agent("my_agent")

# Store memories
await client.store_memory(
    memory_type="episodic",
    content="Successfully created a Python web application with FastAPI",
    metadata={"project": "web_app", "framework": "fastapi", "success": True}
)

# Retrieve memories
memories = await client.retrieve_memories(
    query="web application development",
    memory_types=["episodic", "procedural"],
    max_results=5
)
```

## 📁 Project Structure

```
LANS/
├── agent_core/              # Core multi-agent system
│   ├── agents/              # AI agents (planning, coding, coordinator)
│   ├── models/              # Data models and schemas
│   ├── llm/                 # LLM integration and utilities
│   └── cli.py               # Command-line interface
├── mcp_server/              # Model Context Protocol server
│   ├── handlers/            # File and command handlers
│   ├── security/            # Sandboxing and validation
│   └── main.py              # Server entry point
├── global_mcp_server/       # Global memory system
│   ├── api/                 # Memory API endpoints
│   ├── core/                # Memory management logic
│   └── storage/             # Persistent storage layer
├── scripts/                 # Utility scripts
├── tests/                   # Comprehensive test suite
└── docs/                    # Documentation
```

## 🔄 How LANS Works

1. **Natural Language Input**: You describe what you want in plain English
2. **Intelligent Planning**: Planning agent analyzes requirements and creates a project plan
3. **Code Generation**: Coding agent implements the plan with production-ready code
4. **Automatic Testing**: Built-in validation and error detection
5. **Error Recovery**: Autonomous fixing of issues and optimization
6. **Knowledge Storage**: Every successful project improves LANS for future requests

## 🛠️ Development & Configuration

### Environment Variables
```bash
# Optional: Configure LLM settings
export LANS_MODEL="deepseek-coder:6.7b"
export LANS_OLLAMA_BASE_URL="http://localhost:11434"

# Optional: Memory system
export LANS_MEMORY_ENABLED="true"
export LANS_MEMORY_DB_URL="postgresql://localhost/lans_memory"
```

### Custom Templates
Create your own project templates in `~/.lans/templates/`:

```python
# ~/.lans/templates/my_template.py
def generate_project(spec):
    return {
        "files": {
            "main.py": "# Your custom template",
            "requirements.txt": "# Dependencies"
        },
        "commands": ["pip install -r requirements.txt"]
    }
```

## 🚨 Security & Safety

- **Sandboxed Execution**: All code runs in isolated environments
- **Safe Defaults**: Conservative settings prevent system damage
- **Command Validation**: Dangerous operations require explicit confirmation
- **File System Protection**: Restricted access to system directories
- **Network Isolation**: Optional network access controls

## 📊 Performance & Capabilities

- **Speed**: Simple projects generated in seconds
- **Complexity**: Handles multi-file, multi-language projects
- **Accuracy**: High success rate with automatic error correction
- **Scalability**: Efficient resource usage for large projects
- **Offline**: Works completely offline with local LLMs

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/yourusername/LANS.git
cd LANS
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black .
ruff check --fix .
```

## 📋 Roadmap

- **IDE Integration**: VS Code extension and other editor plugins
- **Cloud Deployment**: Remote LANS instances with web interface
- **Team Collaboration**: Multi-user projects and shared knowledge
- **Advanced Languages**: Expanded support for more programming languages
- **Mobile Development**: Enhanced mobile app generation capabilities

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- **Ollama** for local LLM inference
- **FastAPI** for the MCP server
- **PostgreSQL** for persistent memory storage
- **Model Context Protocol** for secure agent operations

---

**Ready to transform your ideas into code? Start with LANS today!**
