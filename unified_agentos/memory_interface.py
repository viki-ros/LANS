"""
Unified Memory Interface - Phase 1 Foundation
============================================

A unified memory interface that addresses the critical memory fragmentation
issues identified in the architectural analysis. This provides a single,
consistent interface for all agent memory operations.

Key improvements:
- Single interface for all memory operations
- Consistent memory access patterns across all agents
- Integration with the new unified GMCP architecture
- Optimized caching and performance
- Cross-agent memory sharing capabilities
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Memory types supported by the unified interface"""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


@dataclass
class MemoryItem:
    """Unified memory item structure"""
    memory_id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    relationships: Dict[str, str] = field(default_factory=dict)


@dataclass
class MemoryQuery:
    """Unified memory query structure"""
    query_text: str
    agent_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    session_id: Optional[str] = None
    max_results: int = 10
    similarity_threshold: float = 0.7
    time_range: Optional[tuple] = None
    tags: Optional[Set[str]] = None
    include_cross_agent: bool = False


@dataclass
class MemoryStats:
    """Memory statistics"""
    total_memories: int
    memories_by_type: Dict[MemoryType, int]
    memories_by_agent: Dict[str, int]
    average_importance: float
    last_updated: datetime


class MemoryCache:
    """Intelligent memory caching for performance optimization"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (item, timestamp)
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Any:
        """Get item from cache"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            item, timestamp = self._cache[key]
            
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                self._remove_key(key)
                return None
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            return item
    
    async def put(self, key: str, value: Any):
        """Put item in cache"""
        async with self._lock:
            # Remove old entry if exists
            if key in self._cache:
                self._remove_key(key)
            
            # Add new entry
            self._cache[key] = (value, time.time())
            self._access_order.append(key)
            
            # Evict if over size limit
            while len(self._cache) > self.max_size:
                oldest_key = self._access_order.pop(0)
                self._cache.pop(oldest_key, None)
    
    async def invalidate(self, key: str):
        """Invalidate cache entry"""
        async with self._lock:
            self._remove_key(key)
    
    async def clear(self):
        """Clear entire cache"""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def _remove_key(self, key: str):
        """Remove key from cache and access order"""
        self._cache.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)


class UnifiedMemoryInterface:
    """
    Unified memory interface that addresses memory fragmentation issues.
    Provides a single, consistent interface for all agent memory operations.
    """
    
    def __init__(self, gmcp_config: Dict[str, Any]):
        self.config = gmcp_config
        self._cache = MemoryCache()
        self._stats = MemoryStats(
            total_memories=0,
            memories_by_type={t: 0 for t in MemoryType},
            memories_by_agent={},
            average_importance=0.0,
            last_updated=datetime.utcnow()
        )
        
        # Initialize backend storage - using class-level storage for persistence
        if not hasattr(UnifiedMemoryInterface, '_global_memory_store'):
            UnifiedMemoryInterface._global_memory_store = {}
            UnifiedMemoryInterface._global_agent_memories = {}
        
        self._memory_store = UnifiedMemoryInterface._global_memory_store
        self._agent_memories = UnifiedMemoryInterface._global_agent_memories
        
        logger.info("UnifiedMemoryInterface initialized")
    
    def _initialize_backend(self):
        """Initialize the backend storage system"""
        # This method is no longer needed as we use class-level storage
        pass
    
    async def store_memory_item(self, memory_item: MemoryItem) -> str:
        """
        Store a pre-constructed MemoryItem.
        Returns the memory ID.
        """
        try:
            # Store in backend
            await self._store_to_backend(memory_item)
            
            # Update cache
            cache_key = f"memory_{memory_item.memory_id}"
            await self._cache.put(cache_key, memory_item)
            
            # Update statistics
            await self._update_stats_after_store(memory_item)
            
            logger.debug(f"Stored memory item {memory_item.memory_id} for agent {memory_item.agent_id}")
            return memory_item.memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory item: {e}")
            raise

    async def store_memory(
        self,
        agent_id: str,
        memory_type: MemoryType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
        session_id: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ) -> str:
        """
        Store a memory item.
        Returns the memory ID.
        """
        try:
            # Create memory item
            memory_item = MemoryItem(
                memory_id=f"mem_{int(time.time() * 1000)}_{agent_id}",
                agent_id=agent_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
                importance_score=importance_score,
                session_id=session_id,
                tags=tags or set()
            )
            
            # Store in backend
            await self._store_to_backend(memory_item)
            
            # Update cache
            cache_key = f"memory_{memory_item.memory_id}"
            await self._cache.put(cache_key, memory_item)
            
            # Update statistics
            await self._update_stats_after_store(memory_item)
            
            logger.debug(f"Stored memory {memory_item.memory_id} for agent {agent_id}")
            return memory_item.memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_memories(self, query: MemoryQuery) -> List[MemoryItem]:
        """
        Retrieve memories based on query.
        Returns list of matching memory items.
        """
        try:
            # Check cache first for exact queries
            cache_key = self._get_query_cache_key(query)
            cached_result = await self._cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Retrieved {len(cached_result)} memories from cache")
                return cached_result
            
            # Query backend storage
            memories = await self._query_backend(query)
            
            # Cache result
            await self._cache.put(cache_key, memories)
            
            logger.debug(f"Retrieved {len(memories)} memories for query")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID"""
        try:
            # Check cache first
            cache_key = f"memory_{memory_id}"
            memory = await self._cache.get(cache_key)
            if memory is not None:
                return memory
            
            # Query backend
            memory = await self._get_from_backend(memory_id)
            if memory:
                await self._cache.put(cache_key, memory)
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None
    
    async def delete_memory(self, memory_id: str, agent_id: str) -> bool:
        """Delete a memory (only by the owning agent)"""
        try:
            # Get memory to check ownership
            memory = await self.get_memory(memory_id)
            if not memory or memory.agent_id != agent_id:
                logger.warning(f"Agent {agent_id} cannot delete memory {memory_id}")
                return False
            
            # Delete from backend
            await self._delete_from_backend(memory_id)
            
            # Invalidate cache
            cache_key = f"memory_{memory_id}"
            await self._cache.invalidate(cache_key)
            
            # Update statistics
            await self._update_stats_after_delete(memory)
            
            logger.debug(f"Deleted memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    
    async def update_memory(
        self,
        memory_id: str,
        agent_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a memory (only by the owning agent)"""
        try:
            # Get memory to check ownership
            memory = await self.get_memory(memory_id)
            if not memory or memory.agent_id != agent_id:
                logger.warning(f"Agent {agent_id} cannot update memory {memory_id}")
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            # Update in backend
            await self._update_in_backend(memory)
            
            # Update cache
            cache_key = f"memory_{memory_id}"
            await self._cache.put(cache_key, memory)
            
            logger.debug(f"Updated memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
    
    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get memories for a specific agent"""
        query = MemoryQuery(
            query_text="",
            agent_id=agent_id,
            memory_types=[memory_type] if memory_type else None,
            session_id=session_id,
            max_results=limit,
            similarity_threshold=0.0  # Get all matches
        )
        
        return await self.retrieve_memories(query)
    
    async def get_cross_agent_memories(
        self,
        query_text: str,
        requesting_agent_id: str,
        memory_types: Optional[List[MemoryType]] = None,
        max_results: int = 50
    ) -> List[MemoryItem]:
        """Get memories from other agents (cross-agent access)"""
        query = MemoryQuery(
            query_text=query_text,
            memory_types=memory_types,
            max_results=max_results,
            include_cross_agent=True
        )
        
        memories = await self.retrieve_memories(query)
        
        # Filter out memories from the requesting agent
        cross_agent_memories = [
            m for m in memories if m.agent_id != requesting_agent_id
        ]
        
        logger.debug(f"Retrieved {len(cross_agent_memories)} cross-agent memories")
        return cross_agent_memories
    
    async def get_statistics(self) -> MemoryStats:
        """Get memory system statistics"""
        # Update stats from backend
        await self._refresh_stats()
        return self._stats
    
    async def clear_agent_memories(self, agent_id: str) -> int:
        """Clear all memories for an agent (for cleanup)"""
        try:
            memories = await self.get_agent_memories(agent_id)
            count = 0
            
            for memory in memories:
                if await self.delete_memory(memory.memory_id, agent_id):
                    count += 1
            
            logger.info(f"Cleared {count} memories for agent {agent_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear memories for agent {agent_id}: {e}")
            return 0
    
    # Backend storage methods (to be implemented based on actual backend)
    
    async def _store_to_backend(self, memory_item: MemoryItem):
        """Store memory item to backend storage"""
        self._memory_store[memory_item.memory_id] = memory_item
        
        # Index by agent
        if memory_item.agent_id not in self._agent_memories:
            self._agent_memories[memory_item.agent_id] = []
        self._agent_memories[memory_item.agent_id].append(memory_item.memory_id)
    
    async def _query_backend(self, query: MemoryQuery) -> List[MemoryItem]:
        """Query backend storage for memories"""
        results = []
        
        # Simple filtering based on query parameters
        for memory_item in self._memory_store.values():
            # Filter by agent if specified
            if query.agent_id and memory_item.agent_id != query.agent_id:
                continue
            
            # Filter by memory types if specified
            if query.memory_types and memory_item.memory_type not in query.memory_types:
                continue
            
            # Filter by session if specified
            if query.session_id and memory_item.session_id != query.session_id:
                continue
            
            # Simple text matching (in production, this would be semantic search)
            if query.query_text:
                content_lower = memory_item.content.lower()
                query_lower = query.query_text.lower()
                if query_lower not in content_lower:
                    continue
            
            results.append(memory_item)
        
        # Sort by timestamp (most recent first) and limit results
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:query.max_results]
    
    async def _get_from_backend(self, memory_id: str) -> Optional[MemoryItem]:
        """Get memory from backend by ID"""
        return self._memory_store.get(memory_id)
    
    async def _delete_from_backend(self, memory_id: str):
        """Delete memory from backend"""
        if memory_id in self._memory_store:
            memory_item = self._memory_store[memory_id]
            del self._memory_store[memory_id]
            
            # Remove from agent index
            if memory_item.agent_id in self._agent_memories:
                if memory_id in self._agent_memories[memory_item.agent_id]:
                    self._agent_memories[memory_item.agent_id].remove(memory_id)
    
    async def _update_in_backend(self, memory_item: MemoryItem):
        """Update memory in backend"""
        self._memory_store[memory_item.memory_id] = memory_item
    
    # Helper methods
    
    def _get_query_cache_key(self, query: MemoryQuery) -> str:
        """Generate cache key for query"""
        key_parts = [
            f"query_{hash(query.query_text)}",
            f"agent_{query.agent_id or 'all'}",
            f"types_{','.join([t.value for t in query.memory_types or []])}",
            f"session_{query.session_id or 'any'}",
            f"limit_{query.max_results}",
            f"threshold_{query.similarity_threshold}"
        ]
        return "_".join(key_parts)
    
    async def _update_stats_after_store(self, memory_item: MemoryItem):
        """Update statistics after storing a memory"""
        self._stats.total_memories += 1
        self._stats.memories_by_type[memory_item.memory_type] += 1
        
        if memory_item.agent_id not in self._stats.memories_by_agent:
            self._stats.memories_by_agent[memory_item.agent_id] = 0
        self._stats.memories_by_agent[memory_item.agent_id] += 1
        
        # Update average importance (simple running average)
        total = self._stats.total_memories
        current_avg = self._stats.average_importance
        self._stats.average_importance = (
            (current_avg * (total - 1) + memory_item.importance_score) / total
        )
        
        self._stats.last_updated = datetime.utcnow()
    
    async def _update_stats_after_delete(self, memory_item: MemoryItem):
        """Update statistics after deleting a memory"""
        self._stats.total_memories = max(0, self._stats.total_memories - 1)
        self._stats.memories_by_type[memory_item.memory_type] = max(
            0, self._stats.memories_by_type[memory_item.memory_type] - 1
        )
        
        if memory_item.agent_id in self._stats.memories_by_agent:
            self._stats.memories_by_agent[memory_item.agent_id] = max(
                0, self._stats.memories_by_agent[memory_item.agent_id] - 1
            )
        
        self._stats.last_updated = datetime.utcnow()
    
    async def _refresh_stats(self):
        """Refresh statistics from backend"""
        # Calculate stats from in-memory store
        self._stats.total_memories = len(self._memory_store)
        
        # Reset type and agent counts
        self._stats.memories_by_type = {t: 0 for t in MemoryType}
        self._stats.memories_by_agent = {}
        
        total_importance = 0.0
        for memory_item in self._memory_store.values():
            # Count by type
            self._stats.memories_by_type[memory_item.memory_type] += 1
            
            # Count by agent
            if memory_item.agent_id not in self._stats.memories_by_agent:
                self._stats.memories_by_agent[memory_item.agent_id] = 0
            self._stats.memories_by_agent[memory_item.agent_id] += 1
            
            # Sum importance
            total_importance += memory_item.importance_score
        
        # Calculate average importance
        if self._stats.total_memories > 0:
            self._stats.average_importance = total_importance / self._stats.total_memories
        else:
            self._stats.average_importance = 0.0
        
        self._stats.last_updated = datetime.utcnow()


# Global memory interface instance
_global_memory_interface = None


async def get_memory_interface(config: Optional[Dict[str, Any]] = None) -> UnifiedMemoryInterface:
    """Get the global memory interface"""
    global _global_memory_interface
    
    if _global_memory_interface is None:
        if config is None:
            config = {"type": "sqlite", "url": "sqlite:///unified_memory.db"}
        _global_memory_interface = UnifiedMemoryInterface(config)
    
    return _global_memory_interface


async def store_memory(
    agent_id: str,
    memory_type: MemoryType,
    content: str,
    **kwargs
) -> str:
    """Convenience function to store a memory"""
    interface = await get_memory_interface()
    return await interface.store_memory(agent_id, memory_type, content, **kwargs)


async def retrieve_memories(query: MemoryQuery) -> List[MemoryItem]:
    """Convenience function to retrieve memories"""
    interface = await get_memory_interface()
    return await interface.retrieve_memories(query)
