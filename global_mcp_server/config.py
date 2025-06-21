"""
Configuration for Global Memory MCP Server.
"""

import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        "database": {
            "host": os.getenv("GMCP_DATABASE_HOST", "localhost"),
            "port": int(os.getenv("GMCP_DATABASE_PORT", "5432")),
            "database": os.getenv("GMCP_DATABASE_NAME", "global_memory"),
            "username": os.getenv("GMCP_DATABASE_USER", "postgres"),
            "password": os.getenv("GMCP_DATABASE_PASSWORD", "postgres"),
            "max_connections": int(os.getenv("GMCP_DATABASE_MAX_CONNECTIONS", "10"))
        },
        "embeddings": {
            "model": os.getenv("GMCP_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            "device": os.getenv("GMCP_EMBEDDING_DEVICE", "cpu"),
            "batch_size": int(os.getenv("GMCP_EMBEDDING_BATCH_SIZE", "32")),
            "max_seq_length": int(os.getenv("GMCP_EMBEDDING_MAX_SEQ_LENGTH", "512"))
        },
        "server": {
            "host": os.getenv("GMCP_SERVER_HOST", "0.0.0.0"),
            "port": int(os.getenv("GMCP_SERVER_PORT", "8001")),
            "log_level": os.getenv("GMCP_SERVER_LOG_LEVEL", "info")
        },
        "memory": {
            "cleanup_days": int(os.getenv("GMCP_MEMORY_CLEANUP_DAYS", "730")),
            "min_importance": float(os.getenv("GMCP_MEMORY_MIN_IMPORTANCE", "0.2")),
            "consolidation_interval": int(os.getenv("GMCP_MEMORY_CONSOLIDATION_INTERVAL", "24"))
        }
    }


def get_agentos_memory_config() -> Dict[str, Any]:
    """Get memory configuration for AgentOS integration."""
    return {
        "enabled": os.getenv("AGENTOS_MEMORY_ENABLED", "true").lower() == "true",
        "gmcp_url": os.getenv("AGENTOS_GMCP_URL", "http://localhost:8001"),
        "agent_timeout": int(os.getenv("AGENTOS_MEMORY_TIMEOUT", "30"))
    }
