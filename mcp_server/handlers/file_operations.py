"""
File operation handlers for MCP server.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
import aiofiles
import logging

from ..security.sandbox import SandboxManager


class FileHandler:
    """Handles secure file operations for agents."""
    
    def __init__(self, sandbox_manager: SandboxManager):
        self.sandbox = sandbox_manager
        self.logger = logging.getLogger(__name__)
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents safely."""
        try:
            validated_path = self.sandbox.validate_path(path, "read")
            
            if not validated_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            if not validated_path.is_file():
                raise IsADirectoryError(f"Path is not a file: {path}")
            
            async with aiofiles.open(validated_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            self.logger.info(f"Read file: {validated_path}")
            
            return {
                "path": str(validated_path),
                "content": content,
                "size": validated_path.stat().st_size,
                "encoding": "utf-8"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read file {path}: {e}")
            raise
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file contents safely."""
        try:
            validated_path = self.sandbox.validate_path(path, "write")
            
            # Create parent directories if needed
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(validated_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            self.logger.info(f"Wrote file: {validated_path}")
            
            return {
                "path": str(validated_path),
                "size": len(content.encode('utf-8')),
                "encoding": "utf-8",
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to write file {path}: {e}")
            raise
    
    async def list_files(self, path: str = ".") -> Dict[str, Any]:
        """List files and directories safely."""
        try:
            validated_path = self.sandbox.validate_path(path, "read")
            
            if not validated_path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not validated_path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {path}")
            
            items = []
            for item in validated_path.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": stat.st_mtime
                    })
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue
            
            # Sort by type (directories first) then name
            items.sort(key=lambda x: (x["type"] != "directory", x["name"]))
            
            self.logger.info(f"Listed directory: {validated_path}")
            
            return {
                "path": str(validated_path),
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to list directory {path}: {e}")
            raise
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory safely."""
        try:
            validated_path = self.sandbox.validate_path(path, "create")
            
            validated_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Created directory: {validated_path}")
            
            return {
                "path": str(validated_path),
                "success": True,
                "created": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            raise
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete file safely (within sandbox only)."""
        try:
            validated_path = self.sandbox.validate_path(path, "write")
            
            if not str(validated_path).startswith(str(self.sandbox.root)):
                raise PermissionError("Can only delete files within sandbox")
            
            if validated_path.exists():
                if validated_path.is_file():
                    validated_path.unlink()
                elif validated_path.is_dir():
                    validated_path.rmdir()  # Only remove empty directories
                else:
                    raise ValueError(f"Cannot delete: {path}")
            
            self.logger.info(f"Deleted: {validated_path}")
            
            return {
                "path": str(validated_path),
                "success": True,
                "deleted": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete {path}: {e}")
            raise
