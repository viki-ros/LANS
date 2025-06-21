"""
LANS Configuration Management
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class LANSConfig:
    """Configuration for LANS system"""
    
    # Core settings
    workspace: Path = field(default_factory=lambda: Path.cwd())
    model: Optional[str] = None
    verbose: bool = False
    
    # LLM settings
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "deepseek-coder:6.7b"
    temperature: float = 0.1
    max_tokens: int = 4096
    
    # MCP settings
    mcp_server_url: str = "http://localhost:8000"
    mcp_enabled: bool = True
    
    # Memory settings
    memory_enabled: bool = True
    memory_db_url: Optional[str] = None
    
    # Security settings
    sandbox_enabled: bool = True
    allowed_commands: list = field(default_factory=lambda: [
        "pip", "npm", "yarn", "pnpm", "python", "node", "tsc", "vite"
    ])
    
    def __post_init__(self):
        """Initialize configuration from environment variables"""
        # Override with environment variables if present
        self.model = self.model or os.getenv("LANS_MODEL", self.default_model)
        self.ollama_base_url = os.getenv("LANS_OLLAMA_BASE_URL", self.ollama_base_url)
        self.mcp_server_url = os.getenv("LANS_MCP_SERVER_URL", self.mcp_server_url)
        self.memory_db_url = os.getenv("LANS_MEMORY_DB_URL", self.memory_db_url)
        
        # Convert string booleans from env vars
        if os.getenv("LANS_MEMORY_ENABLED"):
            self.memory_enabled = os.getenv("LANS_MEMORY_ENABLED").lower() == "true"
        if os.getenv("LANS_SANDBOX_ENABLED"):
            self.sandbox_enabled = os.getenv("LANS_SANDBOX_ENABLED").lower() == "true"
        if os.getenv("LANS_VERBOSE"):
            self.verbose = os.getenv("LANS_VERBOSE").lower() == "true"
    
    def validate(self) -> bool:
        """Validate the configuration settings."""
        try:
            # Validate workspace
            if not isinstance(self.workspace, Path):
                return False
            
            # Validate URL formats
            if not self.ollama_base_url.startswith(('http://', 'https://')):
                return False
            
            if not self.mcp_server_url.startswith(('http://', 'https://')):
                return False
            
            # Validate numeric ranges
            if not (0.0 <= self.temperature <= 2.0):
                return False
            
            if self.max_tokens <= 0:
                return False
            
            # Validate allowed commands is a list
            if not isinstance(self.allowed_commands, list):
                return False
            
            return True
            
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "workspace": str(self.workspace),
            "model": self.model,
            "verbose": self.verbose,
            "ollama_base_url": self.ollama_base_url,
            "default_model": self.default_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "mcp_server_url": self.mcp_server_url,
            "mcp_enabled": self.mcp_enabled,
            "memory_enabled": self.memory_enabled,
            "memory_db_url": self.memory_db_url,
            "sandbox_enabled": self.sandbox_enabled,
            "allowed_commands": self.allowed_commands,
        }
    
    @classmethod
    def from_file(cls, config_path: Path) -> "LANSConfig":
        """Load configuration from file"""
        import yaml
        
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def save_to_file(self, config_path: Path):
        """Save configuration to file"""
        import yaml
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)