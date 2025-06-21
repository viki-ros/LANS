"""
Global Memory MCP Server (GMCP) - Core Package

A revolutionary persistent memory system that provides human-like memory
capabilities for AI agents across sessions and models.

Features:
- Episodic memory (experiences, conversations, events)
- Semantic memory (facts, concepts, relationships)  
- Procedural memory (skills, patterns, methods)
- Cross-agent knowledge sharing
- Persistent storage with intelligent retrieval
- Global accessibility for any AI model
"""

__version__ = "0.1.0"
__author__ = "LANS Team"

from .core.memory_manager import GlobalMemoryManager
from .core.server import GlobalMCPServer
from .memory_types.episodic import EpisodicMemory
from .memory_types.semantic import SemanticMemory
from .memory_types.procedural import ProceduralMemory
from .api.client import GMCPClient
from .api.agentos_integration import AgentOSIntegration

__all__ = [
    "GlobalMemoryManager",
    "GlobalMCPServer", 
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "GMCPClient",
    "LANSMemoryIntegration"
]
