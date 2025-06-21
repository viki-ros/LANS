"""
MCP Server - Model Context Protocol Server for LANS

Provides secure, sandboxed operations for AI agents:
- run_cmd: Execute shell commands safely
- read_file: Read file contents
- write_file: Write/create files
"""

__version__ = "0.1.0"

from .main import MCPServer
from .handlers.file_operations import FileHandler
from .handlers.command_execution import CommandHandler
from .security.sandbox import SandboxManager

__all__ = [
    "MCPServer",
    "FileHandler", 
    "CommandHandler",
    "SandboxManager",
]
