"""
File Manager Agent - Handles file and directory operations
"""

import asyncio
import aiofiles
from pathlib import Path
from typing import Optional

class FileManager:
    """Manages file and directory operations"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
    
    async def create_file(self, file_path: Path, content: str):
        """Create a file with the given content"""
        # Ensure the file path is within workspace
        if not self._is_safe_path(file_path):
            raise ValueError(f"File path {file_path} is outside workspace")
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
    
    async def create_directory(self, dir_path: Path):
        """Create a directory"""
        if not self._is_safe_path(dir_path):
            raise ValueError(f"Directory path {dir_path} is outside workspace")
        
        dir_path.mkdir(parents=True, exist_ok=True)
    
    async def read_file(self, file_path: Path) -> str:
        """Read file content"""
        if not self._is_safe_path(file_path):
            raise ValueError(f"File path {file_path} is outside workspace")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    async def file_exists(self, file_path: Path) -> bool:
        """Check if file exists"""
        return file_path.exists() and file_path.is_file()
    
    async def directory_exists(self, dir_path: Path) -> bool:
        """Check if directory exists"""
        return dir_path.exists() and dir_path.is_dir()
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is safe (within workspace)"""
        try:
            # Resolve both paths to handle relative paths and symlinks
            resolved_path = path.resolve()
            resolved_workspace = self.workspace.resolve()
            
            # Check if the path is within the workspace
            return str(resolved_path).startswith(str(resolved_workspace))
        except (OSError, ValueError):
            return False