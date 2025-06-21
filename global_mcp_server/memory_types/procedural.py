"""
Procedural Memory - Stores skills, methods, and how-to knowledge.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from ..storage.database import DatabaseManager
from ..utils.embeddings import EmbeddingGenerator


@dataclass
class ProceduralMemoryItem:
    """Procedural memory item representing skills and methods."""
    id: str
    skill_name: str
    domain: str
    procedure: str
    steps: List[str]
    prerequisites: List[str]
    success_rate: float = 0.5
    usage_count: int = 0
    last_used: Optional[datetime] = None
    contributors: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    embedding: Optional[List[float]] = None


class ProceduralMemory:
    """
    Procedural memory stores "how-to" knowledge - skills, methods, and procedures
    that agents can learn and share with each other.
    """
    
    def __init__(self, db_manager: DatabaseManager, embedding_generator: EmbeddingGenerator):
        self.db_manager = db_manager
        self.embedding_generator = embedding_generator
        self.table_name = "procedural_memories"
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize procedural memory storage (tables already created by DatabaseManager)."""
        # Skip individual memory type initialization to avoid SQL syntax issues
        self.logger.info(f"Procedural memory initialized (using database tables)")
        pass
    
    async def store_skill(
        self,
        skill_name: str,
        domain: str,
        procedure: str,
        steps: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        contributor: Optional[str] = None,
        success_rate: float = 0.5
    ) -> str:
        """Store or update a skill in procedural memory."""
        
        # Check if skill already exists
        existing = await self.get_skill(skill_name, domain)
        
        if existing:
            # Update existing skill
            return await self._update_skill(
                existing['id'], procedure, steps, prerequisites, contributor, success_rate
            )
        else:
            # Create new skill
            return await self._create_skill(
                skill_name, domain, procedure, steps, prerequisites, contributor, success_rate
            )
    
    async def _create_skill(
        self,
        skill_name: str,
        domain: str,
        procedure: str,
        steps: Optional[List[str]],
        prerequisites: Optional[List[str]],
        contributor: Optional[str],
        success_rate: float
    ) -> str:
        """Create a new procedural memory skill."""
        
        # Generate embedding for the skill and procedure
        content_for_embedding = f"{skill_name} in {domain}: {procedure}"
        if steps:
            content_for_embedding += " Steps: " + " -> ".join(steps)
        
        embedding = await self.embedding_generator.generate_embedding(content_for_embedding)
        
        # Prepare data
        data = {
            'skill_name': skill_name,
            'domain': domain,
            'procedure': procedure,
            'steps': json.dumps(steps or []),
            'prerequisites': json.dumps(prerequisites or []),
            'success_rate': success_rate,
            'usage_count': 0,
            'contributors': json.dumps([contributor] if contributor else []),
            'embedding': json.dumps(embedding) if embedding else None  # Serialize embedding for TEXT storage
        }
        
        # Insert into database
        skill_id = await self.db_manager.insert(self.table_name, data)
        
        return skill_id
    
    async def _update_skill(
        self,
        skill_id: str,
        procedure: str,
        steps: Optional[List[str]],
        prerequisites: Optional[List[str]],
        contributor: Optional[str],
        success_rate: float
    ) -> str:
        """Update existing procedural memory skill."""
        
        # Get existing skill
        existing = await self.db_manager.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE id = $1", skill_id
        )
        
        if not existing:
            raise ValueError(f"Skill with ID {skill_id} not found")
        
        # Update contributors
        existing_contributors = json.loads(existing['contributors'] or '[]')
        if contributor and contributor not in existing_contributors:
            existing_contributors.append(contributor)
        
        # Calculate weighted success rate
        total_usage = existing['usage_count'] if existing['usage_count'] > 0 else 1
        new_success_rate = (
            (existing['success_rate'] * total_usage + success_rate) / (total_usage + 1)
        )
        
        # Regenerate embedding with updated procedure
        content_for_embedding = f"{existing['skill_name']} in {existing['domain']}: {procedure}"
        if steps:
            content_for_embedding += " Steps: " + " -> ".join(steps)
        
        embedding = await self.embedding_generator.generate_embedding(content_for_embedding)
        
        # Update data
        update_data = {
            'procedure': procedure,
            'steps': json.dumps(steps or json.loads(existing['steps'] or '[]')),
            'prerequisites': json.dumps(prerequisites or json.loads(existing['prerequisites'] or '[]')),
            'success_rate': new_success_rate,
            'contributors': json.dumps(existing_contributors),
            'updated_at': datetime.utcnow(),
            'embedding': embedding
        }
        
        # Update in database
        await self.db_manager.update(
            self.table_name, update_data, "id = $1", skill_id
        )
        
        return skill_id
    
    async def get_skill(self, skill_name: str, domain: Optional[str] = None) -> Optional[Dict]:
        """Retrieve a specific skill."""
        query = f"SELECT * FROM {self.table_name} WHERE skill_name = $1"
        args = [skill_name]
        
        if domain:
            query += " AND domain = $2"
            args.append(domain)
        
        return await self.db_manager.fetchrow(query, *args)
    
    async def search(
        self,
        query_embedding: List[float],
        query_text: str,
        filters: Dict[str, Any],
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Search method for compatibility with memory manager interface."""
        # Use simple text search for SQLite
        where_conditions = []
        params = []
        
        # Add query text search
        if query_text:
            where_conditions.append("(skill_name LIKE ? OR procedure LIKE ?)")
            params.extend([f"%{query_text}%", f"%{query_text}%"])
        
        if filters.get("agent_id"):
            # For SQLite, we'll use simple JSON search
            where_conditions.append("contributors LIKE ?")
            params.append(f'%"{filters["agent_id"]}"%')
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Prepare pagination parameters
        actual_limit = limit if limit is not None else max_results
        
        query = f"""
            SELECT id, skill_name, domain, procedure, steps, prerequisites, contributors,
                   success_rate, success_rate as performance_score, created_at as timestamp, 
                   usage_count as access_count, last_used as last_accessed
            FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY success_rate DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        
        # Add limit and offset to params
        params.extend([actual_limit, offset])
        
        results = await self.db_manager.fetch(query, *params)
        
        # Convert to MemoryItem objects
        memory_items = []
        for row in results:
            from ..core.memory_manager import MemoryItem
            
            memory_item = MemoryItem(
                id=str(row["id"]),  # Convert UUID to string
                memory_type="procedural",
                content=f"{row['skill_name']}: {row['procedure']}",
                metadata={
                    "skill_name": row["skill_name"],
                    "domain": row["domain"],
                    "procedure": row["procedure"],
                    "steps": row["steps"],
                    "prerequisites": row["prerequisites"],
                    "contributors": row["contributors"],
                    "success_rate": row["success_rate"]
                },
                timestamp=row["timestamp"],
                embedding=None,  # Not retrieved in this query
                importance_score=row["success_rate"],
                access_count=row["access_count"],
                last_accessed=row["last_accessed"],
                relevance_score=row["similarity_score"]
            )
            memory_items.append(memory_item)
            
        return memory_items
    
    async def search_skills(
        self,
        query: str,
        domain: Optional[str] = None,
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        min_success_rate: float = 0.0
    ) -> List[Dict]:
        """Search for skills using semantic similarity."""
        
        # Generate embedding for the query
        query_embedding = await self.embedding_generator.generate_embedding(query)
        
        # Build additional filters
        filters = []
        filter_args = []
        
        if domain:
            filters.append(f"domain = ${len(filter_args) + 1}")
            filter_args.append(domain)
        
        if min_success_rate > 0:
            filters.append(f"success_rate >= ${len(filter_args) + 1}")
            filter_args.append(min_success_rate)
        
        additional_filters = " AND ".join(filters) if filters else None
        
        # Perform vector search
        results = await self.db_manager.vector_search(
            table=self.table_name,
            embedding=query_embedding,
            limit=max_results,
            similarity_threshold=similarity_threshold,
            additional_filters=additional_filters,
            filter_args=filter_args
        )
        
        return results
    
    async def use_skill(self, skill_id: str, success: bool = True) -> bool:
        """Record usage of a skill and update success rate."""
        
        # Get existing skill
        existing = await self.db_manager.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE id = $1", skill_id
        )
        
        if not existing:
            return False
        
        # Update usage count
        new_usage_count = existing['usage_count'] + 1
        
        # Update success rate based on outcome
        current_successes = existing['success_rate'] * existing['usage_count']
        new_successes = current_successes + (1 if success else 0)
        new_success_rate = new_successes / new_usage_count
        
        # Update data
        update_data = {
            'usage_count': new_usage_count,
            'success_rate': new_success_rate,
            'last_used': datetime.utcnow()
        }
        
        affected_rows = await self.db_manager.update(
            self.table_name, update_data, "id = $1", skill_id
        )
        
        return affected_rows > 0
    
    async def get_best_skills(
        self,
        domain: Optional[str] = None,
        limit: int = 20,
        min_usage: int = 1
    ) -> List[Dict]:
        """Get the most successful and well-tested skills."""
        
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE usage_count >= $1
        """
        args = [min_usage]
        
        if domain:
            query += f" AND domain = ${len(args) + 1}"
            args.append(domain)
        
        query += f" ORDER BY success_rate DESC, usage_count DESC LIMIT {limit}"
        
        return await self.db_manager.fetch(query, *args)
    
    async def get_domain_skills(self, domain: str, limit: int = 50) -> List[Dict]:
        """Get all skills for a specific domain."""
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE domain = $1 
            ORDER BY success_rate DESC, usage_count DESC 
            LIMIT {limit}
        """
        
        return await self.db_manager.fetch(query, domain)
    
    async def get_skills_by_prerequisite(self, prerequisite: str, limit: int = 20) -> List[Dict]:
        """Find skills that require a specific prerequisite."""
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE prerequisites::text LIKE $1
            ORDER BY success_rate DESC 
            LIMIT {limit}
        """
        
        return await self.db_manager.fetch(query, f'%"{prerequisite}"%')
    
    async def get_skill_progression(self, base_skill: str) -> List[Dict]:
        """Find skills that build upon a base skill (skill appears in prerequisites)."""
        return await self.get_skills_by_prerequisite(base_skill)
    
    async def recommend_skills(
        self,
        agent_skills: List[str],
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Recommend skills based on agent's current skills."""
        
        # Find skills where the agent has most prerequisites
        query = f"""
            SELECT *, 
                   (
                       SELECT COUNT(*)::float / 
                              CASE WHEN jsonb_array_length(prerequisites) = 0 THEN 1 
                                   ELSE jsonb_array_length(prerequisites) 
                              END
                       FROM (
                           SELECT value::text as prereq
                           FROM jsonb_array_elements(prerequisites)
                       ) prereqs
                       WHERE prereq = ANY($1)
                   ) as prerequisite_match_ratio
            FROM {self.table_name}
            WHERE skill_name != ALL($1)
        """
        
        args = [agent_skills]
        
        if domain:
            query += f" AND domain = ${len(args) + 1}"
            args.append(domain)
        
        query += f"""
            ORDER BY prerequisite_match_ratio DESC, success_rate DESC 
            LIMIT {limit}
        """
        
        return await self.db_manager.fetch(query, *args)
    
    async def export_skill(self, skill_id: str) -> Optional[Dict]:
        """Export a skill for sharing with other agents."""
        skill = await self.db_manager.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE id = $1", skill_id
        )
        
        if not skill:
            return None
        
        # Convert to exportable format
        return {
            'skill_name': skill['skill_name'],
            'domain': skill['domain'],
            'procedure': skill['procedure'],
            'steps': json.loads(skill['steps'] or '[]'),
            'prerequisites': json.loads(skill['prerequisites'] or '[]'),
            'success_rate': skill['success_rate'],
            'usage_count': skill['usage_count']
        }
    
    async def import_skill(self, skill_data: Dict[str, Any], contributor: str) -> str:
        """Import a skill from another agent."""
        return await self.store_skill(
            skill_name=skill_data['skill_name'],
            domain=skill_data['domain'],
            procedure=skill_data['procedure'],
            steps=skill_data.get('steps'),
            prerequisites=skill_data.get('prerequisites'),
            contributor=contributor,
            success_rate=skill_data.get('success_rate', 0.5)
        )
    
    async def forget_skill(self, skill_name: str, domain: Optional[str] = None) -> bool:
        """Remove a skill from procedural memory."""
        query_parts = ["skill_name = $1"]
        args = [skill_name]
        
        if domain:
            query_parts.append("domain = $2")
            args.append(domain)
        
        where_clause = " AND ".join(query_parts)
        affected_rows = await self.db_manager.delete(self.table_name, where_clause, *args)
        return affected_rows > 0
