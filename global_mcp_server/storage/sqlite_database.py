"""
SQLite Database manager for local storage.
"""

import asyncio
import aiosqlite
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path


class SQLiteDatabaseManager:
    """
    Simple SQLite database manager for local LANS storage.
    No PostgreSQL dependencies, no pgvector warnings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # SQLite database settings
        self.database_path = config.get("database_url", "sqlite:///lans_memory.db")
        if self.database_path.startswith("sqlite:///"):
            self.database_path = self.database_path[10:]  # Remove sqlite:/// prefix
        
        # Ensure database directory exists
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.connection = None
        
    async def initialize(self):
        """Initialize SQLite database and create tables."""
        try:
            self.connection = await aiosqlite.connect(self.database_path)
            self.connection.row_factory = aiosqlite.Row  # Enable dict-like access
            
            self.logger.info(f"SQLite database connected: {self.database_path}")
            
            # Create tables
            await self._create_tables()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite database: {e}")
            raise
    
    async def _create_tables(self):
        """Create all necessary tables for the memory system."""
        
        # Episodic Memory Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT DEFAULT '{}',
                emotion TEXT,
                outcome TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                embedding TEXT
            );
        """)
        
        # Create indexes for episodic memory
        await self.execute("CREATE INDEX IF NOT EXISTS idx_episodic_agent_id ON episodic_memories(agent_id);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memories(timestamp);")
        
        # Semantic Memory Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id TEXT PRIMARY KEY,
                concept TEXT NOT NULL,
                definition TEXT NOT NULL,
                domain TEXT,
                relations TEXT DEFAULT '{}',
                confidence_score REAL DEFAULT 0.5,
                source_count INTEGER DEFAULT 1,
                contributors TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                embedding TEXT
            );
        """)
        
        # Create indexes for semantic memory
        await self.execute("CREATE INDEX IF NOT EXISTS idx_semantic_concept ON semantic_memories(concept);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_semantic_domain ON semantic_memories(domain);")
        
        # Procedural Memory Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS procedural_memories (
                id TEXT PRIMARY KEY,
                skill_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                procedure TEXT NOT NULL,
                steps TEXT DEFAULT '[]',
                prerequisites TEXT DEFAULT '[]',
                success_rate REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                contributors TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                embedding TEXT
            );
        """)
        
        # Create indexes for procedural memory
        await self.execute("CREATE INDEX IF NOT EXISTS idx_procedural_skill ON procedural_memories(skill_name);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_procedural_domain ON procedural_memories(domain);")
        
        # Memory Statistics Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS memory_statistics (
                id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                metric_value TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for memory statistics
        await self.execute("CREATE INDEX IF NOT EXISTS idx_stats_metric ON memory_statistics(metric_name);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON memory_statistics(timestamp);")
        
        self.logger.info("SQLite database tables created successfully")
    
    async def execute(self, query: str, *args) -> Any:
        """Execute a SQL query."""
        async with self.connection.execute(query, args) as cursor:
            await self.connection.commit()
            return cursor.rowcount
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Fetch multiple rows from a query."""
        async with self.connection.execute(query, args) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Fetch a single row from a query."""
        async with self.connection.execute(query, args) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value from a query."""
        async with self.connection.execute(query, args) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert data into a table and return the ID."""
        import uuid
        
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        values = list(data.values())
        
        # Convert complex objects to JSON strings
        for i, value in enumerate(values):
            if isinstance(value, (dict, list)):
                values[i] = json.dumps(value)
            elif isinstance(value, datetime):
                values[i] = value.isoformat()
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        await self.execute(query, *values)
        return data['id']
    
    async def update(self, table: str, data: Dict[str, Any], where_clause: str, *where_args) -> int:
        """Update data in a table."""
        set_clauses = [f"{col} = ?" for col in data.keys()]
        values = list(data.values())
        
        # Convert complex objects to JSON strings
        for i, value in enumerate(values):
            if isinstance(value, (dict, list)):
                values[i] = json.dumps(value)
            elif isinstance(value, datetime):
                values[i] = value.isoformat()
        
        query = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE {where_clause}
        """
        
        return await self.execute(query, *values, *where_args)
    
    async def delete(self, table: str, where_clause: str, *where_args) -> int:
        """Delete data from a table."""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        return await self.execute(query, *where_args)
    
    async def close(self):
        """Close the database connection."""
        if self.connection:
            await self.connection.close()
