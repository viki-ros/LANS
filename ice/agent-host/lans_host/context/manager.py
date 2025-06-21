"""
Context Manager for LANS ICE

Handles attachment and management of context items including files, URLs,
and text snippets for use in agent conversations and command execution.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import httpx
import aiofiles
from bs4 import BeautifulSoup
import markdown

from ..file_system.operations import FileOperations

logger = logging.getLogger(__name__)


class ContextItem:
    """Represents a single context item"""
    
    def __init__(self, item_type: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())
        self.type = item_type  # "file", "url", "text"
        self.content = content
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.summary: Optional[str] = None
        self.processed_content: Optional[str] = None
        self.size_bytes = len(content.encode('utf-8'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "summary": self.summary,
            "processed_content": self.processed_content,
            "size_bytes": self.size_bytes
        }


class ContextManager:
    """Manages context attachments for LANS ICE"""
    
    def __init__(self, max_items: int = 50, max_total_size: int = 50 * 1024 * 1024):
        self.items: Dict[str, ContextItem] = {}
        self.max_items = max_items
        self.max_total_size = max_total_size  # 50MB total
        self.file_ops = FileOperations()
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    async def attach(self, item_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Attach a new context item"""
        try:
            # Validate input
            if item_type not in ["file", "url", "text"]:
                raise ValueError(f"Invalid context type: {item_type}")
            
            # Process the content based on type
            if item_type == "file":
                processed_item = await self._process_file(content, metadata)
            elif item_type == "url":
                processed_item = await self._process_url(content, metadata)
            else:  # text
                processed_item = await self._process_text(content, metadata)
            
            # Check size limits
            await self._enforce_size_limits(processed_item)
            
            # Store the item
            self.items[processed_item.id] = processed_item
            
            logger.info(f"Context attached: {item_type} ({processed_item.size_bytes} bytes)")
            return processed_item.id
            
        except Exception as e:
            logger.error(f"Error attaching context {item_type}: {e}")
            raise
    
    async def _process_file(self, file_path: str, metadata: Optional[Dict[str, Any]]) -> ContextItem:
        """Process a file attachment"""
        try:
            # Read file content
            content = await self.file_ops.read_file(file_path)
            if content is None:
                raise ValueError(f"Could not read file: {file_path}")
            
            # Get file info
            file_info = await self.file_ops.get_file_info(file_path)
            
            # Create context item
            item = ContextItem("file", content, metadata)
            item.metadata.update({
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "file_extension": Path(file_path).suffix,
                "file_size": file_info.get("size", 0) if file_info else 0,
                "file_modified": file_info.get("modified", 0) if file_info else 0
            })
            
            # Generate summary
            item.summary = await self._generate_file_summary(file_path, content)
            
            # Process content for better readability
            item.processed_content = await self._process_file_content(content, Path(file_path).suffix)
            
            return item
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    async def _process_url(self, url: str, metadata: Optional[Dict[str, Any]]) -> ContextItem:
        """Process a URL attachment"""
        try:
            # Fetch URL content
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            content = response.text
            content_type = response.headers.get("content-type", "").lower()
            
            # Create context item
            item = ContextItem("url", content, metadata)
            item.metadata.update({
                "url": url,
                "content_type": content_type,
                "status_code": response.status_code,
                "response_size": len(content)
            })
            
            # Process content based on type
            if "text/html" in content_type:
                item.processed_content = await self._extract_html_content(content)
                item.summary = await self._generate_html_summary(item.processed_content)
            elif "application/json" in content_type:
                item.processed_content = content
                item.summary = f"JSON data from {url} ({len(content)} characters)"
            else:
                item.processed_content = content[:10000]  # Limit to first 10KB
                item.summary = f"Content from {url} ({content_type})"
            
            return item
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            raise
    
    async def _process_text(self, text: str, metadata: Optional[Dict[str, Any]]) -> ContextItem:
        """Process a text attachment"""
        try:
            # Create context item
            item = ContextItem("text", text, metadata)
            item.metadata.update({
                "text_length": len(text),
                "line_count": text.count('\n') + 1
            })
            
            # Generate summary
            item.summary = await self._generate_text_summary(text)
            
            # Processed content is the same as original for text
            item.processed_content = text
            
            return item
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            raise
    
    async def _generate_file_summary(self, file_path: str, content: str) -> str:
        """Generate a summary for a file"""
        try:
            file_name = Path(file_path).name
            extension = Path(file_path).suffix
            line_count = content.count('\n') + 1
            char_count = len(content)
            
            if extension in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                # Count functions/classes for code files
                function_count = content.count('def ') + content.count('function ')
                class_count = content.count('class ')
                return f"{file_name}: {line_count} lines, {function_count} functions, {class_count} classes"
            
            elif extension in ['.md', '.txt', '.rst']:
                # Word count for text files
                word_count = len(content.split())
                return f"{file_name}: {line_count} lines, {word_count} words"
            
            else:
                return f"{file_name}: {line_count} lines, {char_count} characters"
                
        except Exception:
            return f"File: {Path(file_path).name}"
    
    async def _generate_html_summary(self, content: str) -> str:
        """Generate a summary for HTML content"""
        try:
            lines = content.strip().split('\n')
            first_line = lines[0] if lines else "HTML content"
            
            word_count = len(content.split())
            return f"Web page: {first_line[:100]}... ({word_count} words)"
            
        except Exception:
            return "HTML content"
    
    async def _generate_text_summary(self, text: str) -> str:
        """Generate a summary for text content"""
        try:
            lines = text.strip().split('\n')
            first_line = lines[0] if lines else ""
            
            word_count = len(text.split())
            
            if len(first_line) > 100:
                first_line = first_line[:100] + "..."
            
            return f"Text: {first_line} ({word_count} words)"
            
        except Exception:
            return "Text content"
    
    async def _process_file_content(self, content: str, extension: str) -> str:
        """Process file content for better readability"""
        try:
            if extension == '.md':
                # Convert markdown to HTML for better display
                return markdown.markdown(content)
            else:
                # Return as-is for other file types
                return content
                
        except Exception:
            return content
    
    async def _extract_html_content(self, html: str) -> str:
        """Extract readable content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception:
            # If HTML parsing fails, return raw content
            return html
    
    async def _enforce_size_limits(self, new_item: ContextItem):
        """Enforce context size limits"""
        # Check individual item size (max 10MB per item)
        max_item_size = 10 * 1024 * 1024
        if new_item.size_bytes > max_item_size:
            raise ValueError(f"Context item too large: {new_item.size_bytes} bytes (max: {max_item_size})")
        
        # Check total size
        current_total = sum(item.size_bytes for item in self.items.values())
        if current_total + new_item.size_bytes > self.max_total_size:
            # Remove oldest items until we have space
            await self._cleanup_old_items(new_item.size_bytes)
        
        # Check item count
        if len(self.items) >= self.max_items:
            # Remove oldest item
            oldest_id = min(self.items.keys(), key=lambda k: self.items[k].created_at)
            del self.items[oldest_id]
            logger.info(f"Removed oldest context item to make space")
    
    async def _cleanup_old_items(self, needed_space: int):
        """Remove old items to make space"""
        current_total = sum(item.size_bytes for item in self.items.values())
        target_total = self.max_total_size - needed_space
        
        if current_total <= target_total:
            return
        
        # Sort by creation time (oldest first)
        sorted_items = sorted(self.items.items(), key=lambda x: x[1].created_at)
        
        for item_id, item in sorted_items:
            del self.items[item_id]
            current_total -= item.size_bytes
            logger.info(f"Removed context item {item_id} to free space")
            
            if current_total <= target_total:
                break
    
    def get_item(self, item_id: str) -> Optional[ContextItem]:
        """Get a context item by ID"""
        return self.items.get(item_id)
    
    def get_all_items(self) -> List[ContextItem]:
        """Get all context items"""
        # Sort by creation time (newest first)
        return sorted(self.items.values(), key=lambda x: x.created_at, reverse=True)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove a context item"""
        if item_id in self.items:
            del self.items[item_id]
            logger.info(f"Removed context item {item_id}")
            return True
        return False
    
    def clear_all(self):
        """Clear all context items"""
        count = len(self.items)
        self.items.clear()
        logger.info(f"Cleared {count} context items")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get context summary"""
        total_size = sum(item.size_bytes for item in self.items.values())
        type_counts = {}
        
        for item in self.items.values():
            type_counts[item.type] = type_counts.get(item.type, 0) + 1
        
        return {
            "total_items": len(self.items),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "type_counts": type_counts,
            "size_limit_mb": round(self.max_total_size / 1024 / 1024, 2),
            "usage_percent": round((total_size / self.max_total_size) * 100, 1)
        }
    
    async def close(self):
        """Close the context manager and cleanup resources"""
        await self.http_client.aclose()
        self.clear_all()
