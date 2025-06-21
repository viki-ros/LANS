"""
Command execution handlers for MCP server.
"""

import asyncio
import subprocess
import shlex
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from ..security.sandbox import SandboxManager


class CommandHandler:
    """Handles secure command execution for agents."""
    
    def __init__(self, sandbox_manager: SandboxManager):
        self.sandbox = sandbox_manager
        self.logger = logging.getLogger(__name__)
    
    async def run_command(
        self, 
        command: str, 
        cwd: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Execute a command safely within the sandbox."""
        try:
            # Validate command is allowed
            if not self.sandbox.is_command_allowed(command):
                raise PermissionError(f"Command not allowed: {command}")
            
            # Get safe working directory
            working_dir = self.sandbox.get_safe_working_directory(cwd)
            
            # Ensure working directory exists
            working_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Executing command: {command} in {working_dir}")
            
            # Use asyncio subprocess for non-blocking execution
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_safe_environment()
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            result = {
                "command": command,
                "exit_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "cwd": str(working_dir),
                "success": process.returncode == 0
            }
            
            if process.returncode == 0:
                self.logger.info(f"Command succeeded: {command}")
            else:
                self.logger.warning(f"Command failed with exit code {process.returncode}: {command}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute command '{command}': {e}")
            return {
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "cwd": str(working_dir) if 'working_dir' in locals() else "",
                "success": False,
                "error": str(e)
            }
    
    def _get_safe_environment(self) -> Dict[str, str]:
        """Get a safe environment for command execution."""
        import os
        
        # Start with minimal environment
        safe_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.sandbox.root),
            "USER": "agentros",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8"
        }
        
        # Add ROS 2 environment if available
        ros_vars = [
            "ROS_VERSION", "ROS_DISTRO", "AMENT_PREFIX_PATH",
            "CMAKE_PREFIX_PATH", "LD_LIBRARY_PATH", "PKG_CONFIG_PATH",
            "PYTHONPATH", "ROS_PACKAGE_PATH", "COLCON_PREFIX_PATH"
        ]
        
        for var in ros_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]
        
        # Add Python environment
        python_vars = ["VIRTUAL_ENV", "CONDA_DEFAULT_ENV", "CONDA_PREFIX"]
        for var in python_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]
        
        return safe_env
    
    async def run_build_command(self, package_path: str) -> Dict[str, Any]:
        """Run ROS 2 build command for a specific package."""
        try:
            validated_path = self.sandbox.validate_path(package_path, "read")
            
            if not validated_path.exists():
                raise FileNotFoundError(f"Package path not found: {package_path}")
            
            # Determine build command based on package type
            if (validated_path / "setup.py").exists():
                # Python package
                command = f"colcon build --packages-select {validated_path.name}"
            elif (validated_path / "CMakeLists.txt").exists():
                # C++ package
                command = f"colcon build --packages-select {validated_path.name}"
            else:
                raise ValueError(f"Unknown package type at {package_path}")
            
            # Execute build command
            return await self.run_command(command, cwd=str(validated_path.parent), timeout=300)
            
        except Exception as e:
            self.logger.error(f"Failed to build package at {package_path}: {e}")
            raise
    
    async def run_test_command(self, package_path: str) -> Dict[str, Any]:
        """Run tests for a ROS 2 package."""
        try:
            validated_path = self.sandbox.validate_path(package_path, "read")
            
            if not validated_path.exists():
                raise FileNotFoundError(f"Package path not found: {package_path}")
            
            # Run tests
            command = f"colcon test --packages-select {validated_path.name}"
            
            return await self.run_command(command, cwd=str(validated_path.parent), timeout=300)
            
        except Exception as e:
            self.logger.error(f"Failed to test package at {package_path}: {e}")
            raise
