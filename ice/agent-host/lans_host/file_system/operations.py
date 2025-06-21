"""
File System Operations for LANS ICE

Provides safe file system operations with appropriate security controls
and integration with the existing LANS security framework.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union
import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)


class FileOperations:
    """Safe file system operations for LANS ICE"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.allowed_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.txt', '.rst', '.log', '.sql', '.sh', '.bat',
            '.dockerfile', '.gitignore', '.env', '.example'
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
    
    def _is_safe_path(self, path: Union[str, Path]) -> bool:
        """Check if a path is safe to access (no directory traversal)"""
        try:
            resolved_path = Path(path).resolve()
            base_resolved = self.base_path.resolve()
            
            # Check if the path is within the base directory
            return str(resolved_path).startswith(str(base_resolved))
        except (OSError, ValueError):
            return False
    
    def _is_allowed_file(self, path: Union[str, Path]) -> bool:
        """Check if a file type is allowed"""
        file_path = Path(path)
        
        # Allow files without extensions (like Dockerfile, Makefile)
        if not file_path.suffix:
            return True
        
        return file_path.suffix.lower() in self.allowed_extensions
    
    async def read_file(self, path: str) -> Optional[str]:
        """Safely read a file's contents"""
        if not self._is_safe_path(path) or not self._is_allowed_file(path):
            logger.warning(f"Unsafe or disallowed file access attempt: {path}")
            return None
        
        try:
            file_path = Path(path)
            
            # Check file size
            if file_path.exists():
                size = await aiofiles.os.path.getsize(str(file_path))
                if size > self.max_file_size:
                    logger.warning(f"File too large: {path} ({size} bytes)")
                    return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return content
                
        except (OSError, UnicodeDecodeError, PermissionError) as e:
            logger.error(f"Error reading file {path}: {e}")
            return None
    
    async def write_file(self, path: str, content: str) -> bool:
        """Safely write content to a file"""
        if not self._is_safe_path(path) or not self._is_allowed_file(path):
            logger.warning(f"Unsafe or disallowed file write attempt: {path}")
            return False
        
        try:
            file_path = Path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > self.max_file_size:
                logger.warning(f"Content too large for {path}: {content_size} bytes")
                return False
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                return True
                
        except (OSError, PermissionError) as e:
            logger.error(f"Error writing file {path}: {e}")
            return False
    
    async def list_directory(self, path: str = ".") -> Optional[List[Dict[str, Union[str, int, bool]]]]:
        """List directory contents with metadata"""
        if not self._is_safe_path(path):
            logger.warning(f"Unsafe directory access attempt: {path}")
            return None
        
        try:
            dir_path = Path(path)
            if not dir_path.exists() or not dir_path.is_dir():
                return None
            
            items = []
            for item in dir_path.iterdir():
                try:
                    stat = await aiofiles.os.stat(str(item))
                    items.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else 0,
                        'modified': stat.st_mtime,
                        'is_hidden': item.name.startswith('.'),
                        'is_allowed': self._is_allowed_file(item) if item.is_file() else True
                    })
                except (OSError, PermissionError):
                    # Skip items we can't access
                    continue
            
            # Sort: directories first, then files, alphabetically
            items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            return items
            
        except (OSError, PermissionError) as e:
            logger.error(f"Error listing directory {path}: {e}")
            return None
    
    async def create_directory(self, path: str) -> bool:
        """Create a directory"""
        if not self._is_safe_path(path):
            logger.warning(f"Unsafe directory creation attempt: {path}")
            return False
        
        try:
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError) as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False
    
    async def delete_file(self, path: str) -> bool:
        """Delete a file"""
        if not self._is_safe_path(path) or not self._is_allowed_file(path):
            logger.warning(f"Unsafe or disallowed file deletion attempt: {path}")
            return False
        
        try:
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                await aiofiles.os.remove(str(file_path))
                return True
            return False
        except (OSError, PermissionError) as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False
    
    async def delete_directory(self, path: str) -> bool:
        """Delete a directory and its contents"""
        if not self._is_safe_path(path):
            logger.warning(f"Unsafe directory deletion attempt: {path}")
            return False
        
        try:
            dir_path = Path(path)
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(str(dir_path))
                return True
            return False
        except (OSError, PermissionError) as e:
            logger.error(f"Error deleting directory {path}: {e}")
            return False
    
    async def move_file(self, src_path: str, dest_path: str) -> bool:
        """Move/rename a file"""
        if (not self._is_safe_path(src_path) or not self._is_safe_path(dest_path) or
            not self._is_allowed_file(src_path) or not self._is_allowed_file(dest_path)):
            logger.warning(f"Unsafe file move attempt: {src_path} -> {dest_path}")
            return False
        
        try:
            src = Path(src_path)
            dest = Path(dest_path)
            
            if src.exists():
                # Create parent directory if needed
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                return True
            return False
        except (OSError, PermissionError) as e:
            logger.error(f"Error moving file {src_path} -> {dest_path}: {e}")
            return False
    
    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        """Copy a file"""
        if (not self._is_safe_path(src_path) or not self._is_safe_path(dest_path) or
            not self._is_allowed_file(src_path) or not self._is_allowed_file(dest_path)):
            logger.warning(f"Unsafe file copy attempt: {src_path} -> {dest_path}")
            return False
        
        try:
            src = Path(src_path)
            dest = Path(dest_path)
            
            if src.exists() and src.is_file():
                # Check file size
                size = await aiofiles.os.path.getsize(str(src))
                if size > self.max_file_size:
                    logger.warning(f"File too large to copy: {src_path} ({size} bytes)")
                    return False
                
                # Create parent directory if needed
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dest))
                return True
            return False
        except (OSError, PermissionError) as e:
            logger.error(f"Error copying file {src_path} -> {dest_path}: {e}")
            return False
    
    async def get_file_info(self, path: str) -> Optional[Dict[str, Union[str, int, bool]]]:
        """Get detailed information about a file or directory"""
        if not self._is_safe_path(path):
            logger.warning(f"Unsafe file info request: {path}")
            return None
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return None
            
            stat = await aiofiles.os.stat(str(file_path))
            
            return {
                'name': file_path.name,
                'path': str(file_path),
                'type': 'directory' if file_path.is_dir() else 'file',
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'permissions': oct(stat.st_mode)[-3:],
                'is_hidden': file_path.name.startswith('.'),
                'is_allowed': self._is_allowed_file(file_path) if file_path.is_file() else True,
                'extension': file_path.suffix if file_path.is_file() else None
            }
            
        except (OSError, PermissionError) as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return None
