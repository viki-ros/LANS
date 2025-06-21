"""
Permission Manager for LANS ICE

Extends the existing LANS security framework with desktop-specific
permission controls and security policies.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import stat

# Add LANS modules to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)


class PermissionManager:
    """Manages permissions and security policies for LANS ICE"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.allowed_paths: Set[str] = set()
        self.blocked_paths: Set[str] = set()
        self.allowed_commands: Set[str] = set()
        self.blocked_commands: Set[str] = set()
        
        # Initialize with default policies
        self._initialize_default_policies()
        
        # Try to integrate with existing LANS security
        self.lans_sandbox = None
        self._initialize_lans_security()
    
    def _initialize_default_policies(self):
        """Initialize default security policies"""
        # Default allowed paths (within project)
        self.allowed_paths.update([
            str(self.base_path),
            str(self.base_path / "src"),
            str(self.base_path / "tests"),
            str(self.base_path / "docs"),
            str(self.base_path / "scripts"),
            str(self.base_path / "config"),
            "/tmp",  # Temporary files
            os.path.expanduser("~/.cache"),  # Cache directory
        ])
        
        # Default blocked paths (system critical)
        self.blocked_paths.update([
            "/etc/passwd",
            "/etc/shadow",
            "/etc/ssh",
            "/root",
            "/sys",
            "/proc",
            "/dev",
            "/boot",
            "/usr/bin/sudo",
            "/usr/bin/su"
        ])
        
        # Default allowed commands (safe development tools)
        self.allowed_commands.update([
            "ls", "cat", "grep", "find", "head", "tail", "wc",
            "git", "npm", "pip", "python", "python3", "node",
            "make", "cmake", "cargo", "go", "java", "javac",
            "curl", "wget", "ssh", "scp", "rsync",
            "echo", "printf", "date", "pwd", "whoami",
            "mkdir", "rmdir", "touch", "cp", "mv", "rm",
            "chmod", "chown", "diff", "patch",
            "ps", "top", "htop", "kill", "killall",
            "test", "pytest", "jest", "mocha", "phpunit"
        ])
        
        # Default blocked commands (dangerous system operations)
        self.blocked_commands.update([
            "sudo", "su", "passwd", "chpasswd",
            "fdisk", "mkfs", "fsck", "mount", "umount",
            "iptables", "ufw", "firewall-cmd",
            "systemctl", "service", "init",
            "crontab", "at", "batch",
            "dd", "shred", "wipefs",
            "nc", "netcat", "nmap", "tcpdump",
            "chroot", "jail", "docker", "podman"
        ])
    
    def _initialize_lans_security(self):
        """Initialize integration with existing LANS security"""
        try:
            from mcp_server.security.sandbox import SandboxManager
            self.lans_sandbox = SandboxManager()
            logger.info("Integrated with LANS security framework")
        except ImportError:
            logger.warning("LANS security framework not available, using standalone security")
        except Exception as e:
            logger.error(f"Error initializing LANS security: {e}")
    
    def check_file_access(self, file_path: str, operation: str = "read") -> bool:
        """Check if file access is allowed"""
        try:
            path = Path(file_path).resolve()
            path_str = str(path)
            
            # Check if path is explicitly blocked
            for blocked_path in self.blocked_paths:
                if path_str.startswith(blocked_path):
                    logger.warning(f"File access denied (blocked path): {file_path}")
                    return False
            
            # Check if path is within allowed directories
            allowed = False
            for allowed_path in self.allowed_paths:
                if path_str.startswith(allowed_path):
                    allowed = True
                    break
            
            if not allowed:
                logger.warning(f"File access denied (not in allowed paths): {file_path}")
                return False
            
            # Check file permissions
            if not self._check_file_permissions(path, operation):
                logger.warning(f"File access denied (insufficient permissions): {file_path}")
                return False
            
            # Use LANS sandbox if available
            if self.lans_sandbox:
                return self.lans_sandbox.is_path_allowed(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking file access for {file_path}: {e}")
            return False
    
    def _check_file_permissions(self, path: Path, operation: str) -> bool:
        """Check file system permissions"""
        try:
            if not path.exists():
                # For write operations, check parent directory
                if operation in ["write", "create", "delete"]:
                    return self._check_file_permissions(path.parent, "write")
                return False
            
            file_stat = path.stat()
            mode = file_stat.st_mode
            
            # Check if we own the file or have appropriate permissions
            if operation == "read":
                return bool(mode & stat.S_IRUSR)
            elif operation in ["write", "create", "delete"]:
                return bool(mode & stat.S_IWUSR)
            elif operation == "execute":
                return bool(mode & stat.S_IXUSR)
            
            return False
            
        except (OSError, PermissionError):
            return False
    
    def check_command_execution(self, command: str) -> bool:
        """Check if command execution is allowed"""
        try:
            # Extract command name (first word)
            command_name = command.strip().split()[0] if command.strip() else ""
            
            # Remove path if present
            if "/" in command_name:
                command_name = Path(command_name).name
            
            # Check if command is explicitly blocked
            if command_name in self.blocked_commands:
                logger.warning(f"Command execution denied (blocked): {command_name}")
                return False
            
            # Check if command is in allowed list
            if command_name not in self.allowed_commands:
                logger.warning(f"Command execution denied (not allowed): {command_name}")
                return False
            
            # Use LANS sandbox if available
            if self.lans_sandbox:
                return self.lans_sandbox.is_command_allowed(command)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking command execution for '{command}': {e}")
            return False
    
    def add_allowed_path(self, path: str):
        """Add a path to the allowed list"""
        try:
            resolved_path = str(Path(path).resolve())
            self.allowed_paths.add(resolved_path)
            logger.info(f"Added allowed path: {resolved_path}")
        except Exception as e:
            logger.error(f"Error adding allowed path {path}: {e}")
    
    def remove_allowed_path(self, path: str):
        """Remove a path from the allowed list"""
        try:
            resolved_path = str(Path(path).resolve())
            self.allowed_paths.discard(resolved_path)
            logger.info(f"Removed allowed path: {resolved_path}")
        except Exception as e:
            logger.error(f"Error removing allowed path {path}: {e}")
    
    def add_blocked_path(self, path: str):
        """Add a path to the blocked list"""
        try:
            resolved_path = str(Path(path).resolve())
            self.blocked_paths.add(resolved_path)
            logger.info(f"Added blocked path: {resolved_path}")
        except Exception as e:
            logger.error(f"Error adding blocked path {path}: {e}")
    
    def add_allowed_command(self, command: str):
        """Add a command to the allowed list"""
        self.allowed_commands.add(command)
        logger.info(f"Added allowed command: {command}")
    
    def add_blocked_command(self, command: str):
        """Add a command to the blocked list"""
        self.blocked_commands.add(command)
        logger.info(f"Added blocked command: {command}")
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security configuration summary"""
        return {
            "base_path": str(self.base_path),
            "allowed_paths_count": len(self.allowed_paths),
            "blocked_paths_count": len(self.blocked_paths),
            "allowed_commands_count": len(self.allowed_commands),
            "blocked_commands_count": len(self.blocked_commands),
            "lans_integration": self.lans_sandbox is not None,
            "allowed_paths": sorted(list(self.allowed_paths)),
            "blocked_paths": sorted(list(self.blocked_paths)),
            "allowed_commands": sorted(list(self.allowed_commands)),
            "blocked_commands": sorted(list(self.blocked_commands))
        }
    
    def validate_websocket_origin(self, origin: str) -> bool:
        """Validate WebSocket connection origin"""
        # For development, allow localhost connections
        allowed_origins = [
            "http://localhost:1420",  # Tauri dev server
            "https://tauri.localhost",  # Tauri production
            "http://127.0.0.1:1420",
            "null"  # For file:// protocol in development
        ]
        
        return origin in allowed_origins
    
    def get_file_safety_level(self, file_path: str) -> str:
        """Get safety level for a file"""
        try:
            path = Path(file_path)
            
            # Check extension safety
            extension = path.suffix.lower()
            
            if extension in ['.exe', '.bat', '.cmd', '.sh', '.ps1']:
                return "dangerous"
            elif extension in ['.py', '.js', '.ts', '.java', '.cpp', '.c']:
                return "code"
            elif extension in ['.txt', '.md', '.json', '.yaml', '.yml', '.toml']:
                return "safe"
            elif extension in ['.jpg', '.png', '.gif', '.svg', '.pdf']:
                return "media"
            else:
                return "unknown"
                
        except Exception:
            return "unknown"
    
    def scan_for_security_issues(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scan file content for potential security issues"""
        issues = []
        
        try:
            lines = content.split('\n')
            
            # Check for common security patterns
            security_patterns = [
                ("password", "Potential password in plaintext"),
                ("api_key", "Potential API key"),
                ("secret", "Potential secret"),
                ("token", "Potential token"),
                ("eval(", "Use of eval() function"),
                ("exec(", "Use of exec() function"),
                ("shell=True", "Shell execution with shell=True"),
                ("os.system(", "Direct system command execution"),
                ("subprocess.shell", "Shell subprocess execution")
            ]
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                for pattern, description in security_patterns:
                    if pattern in line_lower:
                        issues.append({
                            "line": line_num,
                            "issue": description,
                            "content": line.strip(),
                            "severity": "medium"
                        })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error scanning file for security issues: {e}")
            return []
