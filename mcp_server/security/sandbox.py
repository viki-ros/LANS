"""
Sandbox manager for secure execution environment.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List
import logging


class SandboxManager:
    """Manages a sandboxed execution environment for agent operations."""
    
    def __init__(self, root: str = "/tmp/agentros_sandbox"):
        self.root = Path(root).resolve()
        self.logger = logging.getLogger(__name__)
        
        # Allowed file extensions for read/write operations
        self.allowed_extensions = {
            ".py", ".cpp", ".hpp", ".h", ".c", ".cc", ".cxx",
            ".xml", ".yaml", ".yml", ".json", ".toml", ".cfg",
            ".txt", ".md", ".rst", ".launch", ".xacro",
            ".msg", ".srv", ".action", ".urdf", ".sdf"
        }
        
        # Blocked directories (security)
        self.blocked_paths = {
            "/etc", "/usr", "/var", "/sys", "/proc", "/dev",
            "/root", "/boot", "/lib", "/lib64", "/bin", "/sbin"
        }
    
    async def initialize(self):
        """Initialize the sandbox environment."""
        try:
            # Create sandbox root if it doesn't exist
            self.root.mkdir(parents=True, exist_ok=True)
            
            # Create standard directories
            (self.root / "workspace").mkdir(exist_ok=True)
            (self.root / "temp").mkdir(exist_ok=True)
            (self.root / "logs").mkdir(exist_ok=True)
            
            self.logger.info(f"Sandbox initialized at: {self.root}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sandbox: {e}")
            raise
    
    async def cleanup(self):
        """Clean up sandbox environment."""
        try:
            if self.root.exists():
                shutil.rmtree(self.root)
            self.logger.info("Sandbox cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup sandbox: {e}")
    
    def validate_path(self, path: str, operation: str = "read") -> Path:
        """Validate that a path is safe for the requested operation."""
        try:
            # Convert to absolute path
            abs_path = Path(path).resolve()
            
            # Check for blocked system directories
            for blocked in self.blocked_paths:
                if str(abs_path).startswith(blocked):
                    raise PermissionError(f"Access denied to system directory: {blocked}")
            
            # For write operations, must be within sandbox
            if operation in ["write", "create"] and not str(abs_path).startswith(str(self.root)):
                abs_path = self.root / "workspace" / Path(path).name
            
            # Check file extension for write operations (only if file has extension)
            if operation == "write" and abs_path.suffix and abs_path.suffix not in self.allowed_extensions:
                raise ValueError(f"File extension {abs_path.suffix} not allowed")
            
            return abs_path
            
        except Exception as e:
            self.logger.error(f"Path validation failed for {path}: {e}")
            raise
    
    def get_safe_working_directory(self, requested_cwd: Optional[str] = None) -> Path:
        """Get a safe working directory for command execution."""
        if requested_cwd:
            try:
                cwd = self.validate_path(requested_cwd, "read")
                if cwd.is_dir():
                    return cwd
            except Exception:
                pass
        
        # Default to sandbox workspace
        return self.root / "workspace"
    
    def get_allowed_commands(self) -> List[str]:
        """Get list of allowed commands for execution."""
        return [
            # ROS 2 build system
            "colcon", "rosdep", "ros2",
            
            # Build tools
            "cmake", "make", "catkin_make",
            
            # Package managers
            "pip", "pip3", "apt", "sudo apt",
            
            # File operations
            "ls", "cd", "pwd", "mkdir", "cp", "mv",
            "cat", "head", "tail", "grep", "find", "sort", "uniq",
            "wc", "du", "df", "file", "basename", "dirname",
            
            # Git operations  
            "git",
            
            # Python and development
            "python", "python3", "pytest", "pip", "npm", "node",
            "java", "javac", "gcc", "g++", "clang",
            
            # System information (agent-friendly)
            "echo", "which", "whereis", "env", "date", "whoami",
            "hostname", "uname", "uptime", "ps", "top", "htop",
            "free", "lscpu", "lsblk", "lsusb", "lspci",
            
            # Text processing
            "awk", "sed", "cut", "tr", "diff", "patch",
            
            # Archive operations
            "tar", "zip", "unzip", "gzip", "gunzip",
            
            # Network tools (safe)
            "curl", "wget", "ping", "nslookup", "dig",
            
            # Docker (if available)
            "docker", "docker-compose",
            
            # Testing and debugging
            "valgrind", "gdb", "strace", "ltrace"
        ]
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to execute."""
        command_parts = command.strip().split()
        if not command_parts:
            return False
        
        base_command = command_parts[0]
        
        # Block explicitly dangerous commands
        dangerous_commands = ["sudo rm", "chmod 777", "chown", "dd", "mkfs", "fdisk", "format"]
        if base_command in dangerous_commands or any(danger in command for danger in dangerous_commands):
            return False
        
        # Block dangerous patterns but allow pipes and redirections for agent use
        dangerous_patterns = ["rm -rf /", ">/dev/null", "&&rm", ";rm", "| rm"]
        for pattern in dangerous_patterns:
            if pattern in command:
                return False
        
        # Allow common shell patterns for agent development
        allowed_shell_patterns = ["|", "&&", ";", ">", ">>", "<", "2>", "2>&1"]
        
        allowed_commands = self.get_allowed_commands()
        
        # Check if base command or any allowed pattern matches
        for allowed in allowed_commands:
            if base_command == allowed or command.startswith(allowed):
                return True
        
        # Special handling for complex commands with pipes/redirections
        if any(pattern in command for pattern in allowed_shell_patterns):
            # Split on shell operators and check each part
            import re
            parts = re.split(r'[|;&><]+', command)
            for part in parts:
                part = part.strip()
                if part and not any(part.startswith(allowed) for allowed in allowed_commands):
                    return False
            return True
        
        return False
