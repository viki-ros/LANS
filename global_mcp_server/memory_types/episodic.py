"""
Episodic Memory - Stores experiences, conversations, and events.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..storage.database import DatabaseManager
from ..utils.embeddings import EmbeddingGenerator


@dataclass
class EpisodicMemoryItem:
    """Episodic memory item with conversation and event context."""
    id: str
    agent_id: str
    user_id: Optional[str]
    session_id: str
    content: str
    context: Dict[str, Any]
    emotion: Optional[str] = None
    outcome: Optional[str] = None  # success, failure, partial, etc.
    timestamp: datetime = None
    importance_score: float = 0.5
    embedding: Optional[List[float]] = None


class EpisodicMemory:
    """
    Episodic memory stores personal experiences, conversations, and events
    that happened to the AI agent. This includes context about interactions,
    decisions made, and outcomes achieved.
    """
    
    def __init__(self, db_manager: DatabaseManager, embedding_generator: EmbeddingGenerator):
        self.db_manager = db_manager
        self.embedding_generator = embedding_generator
        self.table_name = "episodic_memories"
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize episodic memory storage."""
        # Tables are created by the SQLite database manager
        # Skip individual memory type initialization to avoid SQL syntax issues
        self.logger.info(f"Episodic memory initialized (using database tables)")
        pass
    
    async def store(self, memory_item) -> str:
        """Store an episodic memory."""
        # Prepare data for SQLite insertion
        data = {
            'id': memory_item.id,
            'agent_id': memory_item.agent_id,
            'user_id': memory_item.user_id,
            'session_id': memory_item.session_id,
            'content': memory_item.content,
            'context': memory_item.context or {},
            'emotion': memory_item.emotion,
            'outcome': memory_item.outcome,
            'timestamp': memory_item.timestamp.isoformat() if memory_item.timestamp else datetime.utcnow().isoformat(),
            'importance_score': memory_item.importance_score or 0.5,
            'embedding': json.dumps(memory_item.embedding) if memory_item.embedding else None,
            'access_count': 0,
            'last_accessed': None
        }
        
        # Use the SQLite database manager's insert method
        await self.db_manager.insert(self.table_name, data)
        return memory_item.id
    
    async def search(
        self,
        query_embedding: List[float],
        query_text: str,
        filters: Dict[str, Any],
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List:
        """Search episodic memories with semantic similarity."""
        
        # Use simple text search for SQLite
        where_conditions = []
        params = []
        
        # Add query text search (SQLite uses LIKE instead of ILIKE)
        if query_text:
            where_conditions.append("content LIKE ?")
            params.append(f"%{query_text}%")
        
        if filters.get("agent_id"):
            where_conditions.append("agent_id = ?")
            params.append(filters["agent_id"])
        
        if filters.get("user_id"):
            where_conditions.append("user_id = ?")
            params.append(filters["user_id"])
        
        if filters.get("time_range"):
            start_time, end_time = filters["time_range"]
            where_conditions.append("timestamp >= ?")
            params.append(start_time.isoformat() if hasattr(start_time, 'isoformat') else start_time)
            where_conditions.append("timestamp <= ?")
            params.append(end_time.isoformat() if hasattr(end_time, 'isoformat') else end_time)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Prepare pagination parameters
        actual_limit = limit if limit is not None else max_results
        
        query = f"""
            SELECT id, agent_id, user_id, session_id, content, context, emotion, outcome,
                   timestamp, importance_score, embedding, access_count, last_accessed
            FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY importance_score DESC, timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        # Add limit and offset to params
        params.extend([actual_limit, offset])
        
        results = await self.db_manager.fetch(query, *params)
        
        # Convert to memory items
        memory_items = []
        for row in results:
            # Import here to avoid circular imports
            from ..core.memory_manager import MemoryItem
            
            memory_item = MemoryItem(
                id=str(row["id"]),
                memory_type="episodic",
                content=row["content"],
                metadata={
                    "agent_id": row["agent_id"],
                    "user_id": row["user_id"],
                    "session_id": row["session_id"],
                    "context": json.loads(row["context"] or "{}"),
                    "emotion": row["emotion"],
                    "outcome": row["outcome"],
                    "importance_score": row["importance_score"],
                    "access_count": row.get("access_count", 0),
                    "last_accessed": row.get("last_accessed"),
                },
                timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"]
            )
            memory_items.append(memory_item)
        
        return memory_items
    
    async def get_conversation_history(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        days_back: int = 30
    ) -> List[EpisodicMemoryItem]:
        """Get conversation history for context."""
        
        start_time = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        where_conditions = ["agent_id = ?", "timestamp >= ?"]
        params = [agent_id, start_time]
        
        if user_id:
            where_conditions.append("user_id = ?")
            params.append(user_id)
        
        if session_id:
            where_conditions.append("session_id = ?")
            params.append(session_id)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        results = await self.db_manager.fetch(query, *params)
        
        return [self._row_to_memory_item(row) for row in results]
    
    async def get_similar_experiences(
        self,
        current_situation: str,
        agent_id: str,
        max_results: int = 5
    ) -> List[EpisodicMemoryItem]:
        """Find similar past experiences for learning."""
        
        # Use simple text similarity for SQLite
        query = f"""
            SELECT *
            FROM {self.table_name}
            WHERE agent_id = ? AND outcome IS NOT NULL 
            AND content LIKE ?
            ORDER BY importance_score DESC, timestamp DESC
            LIMIT ?
        """
        
        results = await self.db_manager.fetch(query, agent_id, f'%{current_situation}%', max_results)
        
        return [self._row_to_memory_item(row) for row in results]
    
    async def consolidate(self, agent_id: Optional[str] = None) -> int:
        """Consolidate similar episodic memories."""
        # Find duplicate or very similar conversations
        consolidated_count = 0
        
        # Simplified consolidation for SQLite
        where_clause = "WHERE agent_id = ?" if agent_id else ""
        params = [agent_id] if agent_id else []
        
        duplicate_query = f"""
            SELECT content, COUNT(*) as count, MIN(id) as keep_id
            FROM {self.table_name}
            {where_clause}
            GROUP BY content
            HAVING COUNT(*) > 1
        """
        
        duplicates = await self.db_manager.fetch(duplicate_query, *params)
        
        for duplicate in duplicates:
            # Remove duplicates, keeping the first one
            delete_query = f"""
                DELETE FROM {self.table_name} 
                WHERE content = ? AND id != ?
            """
            if agent_id:
                delete_query += " AND agent_id = ?"
                delete_params = [duplicate["content"], duplicate["keep_id"], agent_id]
            else:
                delete_params = [duplicate["content"], duplicate["keep_id"]]
            
            rows_deleted = await self.db_manager.execute(delete_query, *delete_params)
            consolidated_count += rows_deleted
        
        return consolidated_count
    
    async def get_memory_count(
        self, 
        agent_id: Optional[str] = None,
        time_range: Optional[tuple] = None
    ) -> int:
        """Get count of episodic memories."""
        where_conditions = []
        params = []
        
        if agent_id:
            where_conditions.append("agent_id = ?")
            params.append(agent_id)
        
        if time_range:
            start_time, end_time = time_range
            where_conditions.append("timestamp >= ?")
            params.append(start_time.isoformat() if hasattr(start_time, 'isoformat') else start_time)
            where_conditions.append("timestamp <= ?")
            params.append(end_time.isoformat() if hasattr(end_time, 'isoformat') else end_time)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"SELECT COUNT(*) as count FROM {self.table_name} {where_clause}"
        
        result = await self.db_manager.fetchrow(query, *params)
        
        return result["count"] if result else 0
    
    async def store_experience(
        self,
        agent_id: str,
        user_id: Optional[str],
        session_id: str,
        content: str,
        context: Dict[str, Any],
        importance_score: float = 0.5
    ) -> str:
        """Store an episodic experience (wrapper for store method)."""
        # Create EpisodicMemoryItem
        memory_item = EpisodicMemoryItem(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            content=content,
            context=context,
            importance_score=importance_score,
            timestamp=datetime.now()
        )
        
        # Use the store method
        return await self.store(memory_item)

    async def store_skill(
        self,
        skill_name: str,
        domain: str,
        procedure: str,
        steps: Optional[List[str]],
        prerequisites: Optional[List[str]],
        contributor: str,
        success_rate: float = 0.5
    ) -> str:
        """Store a skill/procedure (compatibility method for procedural memory interface)."""
        # Create a simplified episodic entry for skills
        memory_item = EpisodicMemoryItem(
            id=str(uuid.uuid4()),
            agent_id=contributor,
            user_id=None,
            session_id=f"skill_learning_{skill_name}",
            content=f"Learned skill: {skill_name}\nProcedure: {procedure}",
            context={
                "type": "skill_acquisition",
                "skill_name": skill_name,
                "domain": domain,
                "steps": steps or [],
                "prerequisites": prerequisites or [],
                "success_rate": success_rate
            },
            importance_score=success_rate,
            timestamp=datetime.now()
        )
        
        return await self.store(memory_item)

    def _row_to_memory_item(self, row: Dict[str, Any]) -> EpisodicMemoryItem:
        """Convert database row to EpisodicMemoryItem."""
        return EpisodicMemoryItem(
            id=row["id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            content=row["content"],
            context=json.loads(row["context"] or "{}"),
            emotion=row["emotion"],
            outcome=row["outcome"],
            timestamp=row["timestamp"],
            importance_score=row["importance_score"],
            embedding=row["embedding"]
        )
