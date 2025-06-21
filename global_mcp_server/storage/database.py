"""
Database manager for persistent storage.
"""

import asyncio
import asyncpg
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict


class DatabaseManager:
    """
    Manages PostgreSQL database connections and operations for the global memory system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database connection settings
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 5432)
        self.database = config.get("database", "global_memory")
        self.username = config.get("username", "postgres")
        self.password = config.get("password", "postgres")
        
        # Connection pool
        self.pool = None
        self.max_connections = config.get("max_connections", 10)
        
    async def initialize(self):
        """Initialize database connection pool and create tables."""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=1,
                max_size=max(self.max_connections, 2),  # Ensure max_size >= min_size
                command_timeout=60
            )
            
            self.logger.info("Database connection pool created successfully")
            
            # Create tables
            await self._create_tables()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create all necessary tables for the global memory system."""
        
        # Try to enable pgvector extension for vector operations (optional)
        try:
            await self.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
            """)
            self.logger.info("pgvector extension enabled successfully")
            self.has_pgvector = True
        except Exception as e:
            self.logger.warning(f"pgvector extension not available: {e}")
            self.logger.info("Continuing without vector operations")
            self.has_pgvector = False
        
        # Episodic Memory Table
        embedding_column = "embedding VECTOR(1536)" if self.has_pgvector else "embedding TEXT"
        await self.execute(f"""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(100) NOT NULL,
                user_id VARCHAR(100),
                session_id VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                context JSONB DEFAULT '{{}}',
                emotion VARCHAR(50),
                outcome VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance_score FLOAT DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                {embedding_column}
            );
        """)
        
        # Create indexes for episodic memory
        await self.execute("CREATE INDEX IF NOT EXISTS idx_episodic_agent_id ON episodic_memories(agent_id);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_episodic_user_id ON episodic_memories(user_id);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memories(timestamp);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic_memories(importance_score);")
        
        # Semantic Memory Table
        await self.execute(f"""
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                concept VARCHAR(255) NOT NULL,
                definition TEXT NOT NULL,
                domain VARCHAR(100),
                relations JSONB DEFAULT '{{}}',
                confidence_score FLOAT DEFAULT 0.5,
                source_count INTEGER DEFAULT 1,
                contributors JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                {embedding_column}
            );
        """)
        
        # Create indexes for semantic memory
        await self.execute("CREATE INDEX IF NOT EXISTS idx_semantic_concept ON semantic_memories(concept);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_semantic_domain ON semantic_memories(domain);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_semantic_confidence ON semantic_memories(confidence_score);")
        
        # Procedural Memory Table
        await self.execute(f"""
            CREATE TABLE IF NOT EXISTS procedural_memories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                skill_name VARCHAR(255) NOT NULL,
                domain VARCHAR(100) NOT NULL,
                procedure TEXT NOT NULL,
                steps JSONB DEFAULT '[]',
                prerequisites JSONB DEFAULT '[]',
                success_rate FLOAT DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                contributors JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                {embedding_column}
            );
        """)
        
        # Create indexes for procedural memory
        await self.execute("CREATE INDEX IF NOT EXISTS idx_procedural_skill ON procedural_memories(skill_name);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_procedural_domain ON procedural_memories(domain);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_procedural_success ON procedural_memories(success_rate);")
        
        # Memory Statistics Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS memory_statistics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                metadata JSONB DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for memory statistics
        await self.execute("CREATE INDEX IF NOT EXISTS idx_stats_metric ON memory_statistics(metric_name);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON memory_statistics(timestamp);")
        
        # Agent Registry Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS agent_registry (
                agent_id VARCHAR(100) PRIMARY KEY,
                agent_type VARCHAR(50),
                capabilities JSONB DEFAULT '[]',
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                memory_preferences JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Cognition Execution Log Table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS cognitions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cognition_id VARCHAR(100) NOT NULL,
                agent_id VARCHAR(100),
                user_id VARCHAR(100),
                ail_code TEXT NOT NULL,
                operation_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                result JSONB,
                execution_time_ms FLOAT,
                causality_chain JSONB DEFAULT '[]',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                metadata JSONB DEFAULT '{}'
            );
        """)
        
        # Create indexes for cognitions
        await self.execute("CREATE INDEX IF NOT EXISTS idx_cognitions_agent_id ON cognitions(agent_id);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_cognitions_operation ON cognitions(operation_type);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_cognitions_status ON cognitions(status);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_cognitions_timestamp ON cognitions(timestamp);")
        
        # Variable Storage Table (for LET operations)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS variable_storage (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cognition_id VARCHAR(100) NOT NULL,
                variable_name VARCHAR(255) NOT NULL,
                variable_value JSONB NOT NULL,
                scope_level INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );
        """)
        
        # Event Definitions Table (for EVENT operations)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS event_definitions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_name VARCHAR(255) NOT NULL,
                agent_id VARCHAR(100),
                trigger_condition TEXT NOT NULL,
                handler_ail TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered TIMESTAMP,
                trigger_count INTEGER DEFAULT 0,
                metadata JSONB DEFAULT '{}'
            );
        """)
        
        # Create indexes for events
        await self.execute("CREATE INDEX IF NOT EXISTS idx_events_name ON event_definitions(event_name);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_events_agent ON event_definitions(agent_id);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_events_active ON event_definitions(is_active);")

        self.logger.info("Database tables created successfully")
    
    async def execute(self, query: str, *args) -> Any:
        """Execute a SQL query."""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Fetch multiple rows from a query."""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Fetch a single row from a query."""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value from a query."""
        async with self.pool.acquire() as connection:
            return await connection.fetchval(query, *args)
    
    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert data into a table and return the ID."""
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(data.values())
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING id
        """
        
        async with self.pool.acquire() as connection:
            result = await connection.fetchval(query, *values)
            return str(result)
    
    async def update(self, table: str, data: Dict[str, Any], where_clause: str, *where_args) -> int:
        """Update data in a table."""
        set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(data.keys())]
        values = list(data.values())
        
        query = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE {where_clause}
        """
        
        async with self.pool.acquire() as connection:
            result = await connection.execute(query, *values, *where_args)
            return int(result.split()[-1])  # Extract affected rows count
    
    async def delete(self, table: str, where_clause: str, *where_args) -> int:
        """Delete data from a table."""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        async with self.pool.acquire() as connection:
            result = await connection.execute(query, *where_args)
            return int(result.split()[-1])  # Extract affected rows count
    
    async def vector_search(
        self, 
        table: str, 
        embedding: List[float], 
        limit: int = 10, 
        similarity_threshold: float = 0.7,
        additional_filters: Optional[str] = None,
        filter_args: Optional[List] = None
    ) -> List[Dict]:
        """Perform vector similarity search."""
        
        # Convert embedding to PostgreSQL vector format
        vector_str = f"[{','.join(map(str, embedding))}]"
        
        # Build query with optional filters
        where_clause = f"embedding <-> '{vector_str}' < {1 - similarity_threshold}"
        args = []
        
        if additional_filters:
            where_clause += f" AND {additional_filters}"
            if filter_args:
                args.extend(filter_args)
        
        query = f"""
            SELECT *, (1 - (embedding <-> '{vector_str}')) AS similarity_score
            FROM {table}
            WHERE {where_clause}
            ORDER BY embedding <-> '{vector_str}'
            LIMIT {limit}
        """
        
        return await self.fetch(query, *args)
    
    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
