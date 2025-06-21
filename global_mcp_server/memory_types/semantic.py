"""
Semantic Memory - Stores facts, concepts, and knowledge.
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
class SemanticMemoryItem:
    """Semantic memory item representing knowledge and concepts."""
    id: str
    concept: str
    definition: str
    domain: str
    relations: Dict[str, Any]
    confidence_score: float = 0.5
    source_count: int = 1
    contributors: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    embedding: Optional[List[float]] = None


class SemanticMemory:
    """
    Semantic memory stores factual knowledge, concepts, and their relationships.
    This represents the "what" knowledge that agents accumulate over time.
    """
    
    def __init__(self, db_manager: DatabaseManager, embedding_generator: EmbeddingGenerator):
        self.db_manager = db_manager
        self.embedding_generator = embedding_generator
        self.table_name = "semantic_memories"
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize semantic memory storage (tables already created by DatabaseManager)."""
        # Skip individual memory type initialization to avoid SQL syntax issues
        self.logger.info(f"Semantic memory initialized (using database tables)")
        pass
    
    async def store_knowledge(
        self,
        concept: str,
        definition: str,
        domain: str,
        relations: Optional[Dict[str, Any]] = None,
        contributor: Optional[str] = None,
        confidence_score: float = 0.5
    ) -> str:
        """Store or update knowledge in semantic memory."""
        
        # Check if concept already exists
        existing = await self.get_concept(concept, domain)
        
        if existing:
            # Update existing concept
            return await self._update_concept(
                existing['id'], definition, relations, contributor, confidence_score
            )
        else:
            # Create new concept
            return await self._create_concept(
                concept, definition, domain, relations, contributor, confidence_score
            )
    
    async def _create_concept(
        self,
        concept: str,
        definition: str,
        domain: str,
        relations: Optional[Dict[str, Any]],
        contributor: Optional[str],
        confidence_score: float
    ) -> str:
        """Create a new semantic memory concept."""
        
        # Generate embedding for the concept and definition
        content_for_embedding = f"{concept}: {definition}"
        embedding = await self.embedding_generator.generate_embedding(content_for_embedding)
        
        # Prepare data
        data = {
            'concept': concept,
            'definition': definition,
            'domain': domain,
            'relations': json.dumps(relations or {}),
            'confidence_score': confidence_score,
            'source_count': 1,
            'contributors': json.dumps([contributor] if contributor else []),
            'embedding': json.dumps(embedding) if embedding else None  # Serialize embedding for TEXT storage
        }
        
        # Insert into database
        concept_id = await self.db_manager.insert(self.table_name, data)
        
        return concept_id
    
    async def _update_concept(
        self,
        concept_id: str,
        definition: str,
        relations: Optional[Dict[str, Any]],
        contributor: Optional[str],
        confidence_score: float
    ) -> str:
        """Update existing semantic memory concept."""
        
        # Get existing concept
        existing = await self.db_manager.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE id = ?", concept_id
        )
        
        if not existing:
            raise ValueError(f"Concept with ID {concept_id} not found")
        
        # Merge relations
        existing_relations = json.loads(existing['relations'] or '{}')
        if relations:
            existing_relations.update(relations)
        
        # Update contributors
        existing_contributors = json.loads(existing['contributors'] or '[]')
        if contributor and contributor not in existing_contributors:
            existing_contributors.append(contributor)
        
        # Calculate new confidence score (weighted average)
        new_source_count = existing['source_count'] + 1
        new_confidence = (
            (existing['confidence_score'] * existing['source_count'] + confidence_score) 
            / new_source_count
        )
        
        # Regenerate embedding with updated definition
        content_for_embedding = f"{existing['concept']}: {definition}"
        embedding = await self.embedding_generator.generate_embedding(content_for_embedding)
        
        # Update data
        update_data = {
            'definition': definition,
            'relations': json.dumps(existing_relations),
            'confidence_score': new_confidence,
            'source_count': new_source_count,
            'contributors': json.dumps(existing_contributors),
            'updated_at': datetime.utcnow(),
            'embedding': embedding
        }
        
        # Update in database
        await self.db_manager.update(
            self.table_name, update_data, "id = $1", concept_id
        )
        
        return concept_id
    
    async def get_concept(self, concept: str, domain: Optional[str] = None) -> Optional[Dict]:
        """Retrieve a specific concept."""
        query = f"SELECT * FROM {self.table_name} WHERE concept = ?"
        args = [concept]
        
        if domain:
            query += " AND domain = ?"
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
        
        # Add query text search (SQLite uses LIKE instead of ILIKE)
        if query_text:
            where_conditions.append("(concept LIKE ? OR definition LIKE ?)")
            params.extend([f"%{query_text}%", f"%{query_text}%"])
        
        # Note: For SQLite, we'll use simple JSON string search instead of jsonb operations
        if filters.get("agent_id"):
            where_conditions.append("contributors LIKE ?")
            params.append(f'%"{filters["agent_id"]}"%')
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Prepare pagination parameters
        actual_limit = limit if limit is not None else max_results
        
        query = f"""
            SELECT id, concept, definition, domain, relations, contributors, 
                   confidence_score, created_at as timestamp
            FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY confidence_score DESC, created_at DESC
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
                memory_type="semantic",
                content=f"{row['concept']}: {row['definition']}",
                metadata={
                    "concept": row["concept"],
                    "definition": row["definition"],
                    "domain": row["domain"],
                    "relations": row["relations"],
                    "contributors": row["contributors"],
                    "confidence_score": row["confidence_score"]
                },
                timestamp=row["timestamp"],
                embedding=None,  # Not retrieved in this query
                importance_score=row["confidence_score"],
                access_count=row["access_count"],
                last_accessed=row["last_accessed"],
                relevance_score=row["similarity_score"]
            )
            memory_items.append(memory_item)
            
        return memory_items
    
    async def search_knowledge(
        self,
        query: str,
        domain: Optional[str] = None,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """Search for knowledge using semantic similarity."""
        
        # Generate embedding for the query
        query_embedding = await self.embedding_generator.generate_embedding(query)
        
        # Build additional filters
        additional_filters = None
        filter_args = []
        
        if domain:
            additional_filters = "domain = $1"
            filter_args.append(domain)
        
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
    
    async def get_related_concepts(
        self,
        concept: str,
        relation_type: Optional[str] = None,
        max_results: int = 20
    ) -> List[Dict]:
        """Get concepts related to a given concept."""
        
        # First get the concept
        base_concept = await self.get_concept(concept)
        if not base_concept:
            return []
        
        relations = json.loads(base_concept['relations'] or '{}')
        
        if relation_type and relation_type in relations:
            # Get specific relation type
            related_concepts = relations[relation_type]
            if not isinstance(related_concepts, list):
                related_concepts = [related_concepts]
        else:
            # Get all related concepts
            related_concepts = []
            for rel_list in relations.values():
                if isinstance(rel_list, list):
                    related_concepts.extend(rel_list)
                else:
                    related_concepts.append(rel_list)
        
        # Fetch details for related concepts
        if not related_concepts:
            return []
        
        placeholders = ','.join([f"${i+1}" for i in range(len(related_concepts))])
        query = f"SELECT * FROM {self.table_name} WHERE concept IN ({placeholders}) LIMIT {max_results}"
        
        return await self.db_manager.fetch(query, *related_concepts)
    
    async def add_relation(
        self,
        concept1: str,
        concept2: str,
        relation_type: str,
        bidirectional: bool = True
    ) -> bool:
        """Add a relationship between two concepts."""
        
        # Add relation from concept1 to concept2
        success1 = await self._add_single_relation(concept1, concept2, relation_type)
        
        if bidirectional:
            # Add reverse relation
            success2 = await self._add_single_relation(concept2, concept1, relation_type)
            return success1 and success2
        
        return success1
    
    async def _add_single_relation(self, from_concept: str, to_concept: str, relation_type: str) -> bool:
        """Add a single directional relation."""
        
        concept = await self.get_concept(from_concept)
        if not concept:
            return False
        
        relations = json.loads(concept['relations'] or '{}')
        
        if relation_type not in relations:
            relations[relation_type] = []
        
        if not isinstance(relations[relation_type], list):
            relations[relation_type] = [relations[relation_type]]
        
        if to_concept not in relations[relation_type]:
            relations[relation_type].append(to_concept)
        
        # Update in database
        update_data = {
            'relations': json.dumps(relations),
            'updated_at': datetime.utcnow()
        }
        
        affected_rows = await self.db_manager.update(
            self.table_name, update_data, "id = $1", concept['id']
        )
        
        return affected_rows > 0
    
    async def get_domain_knowledge(self, domain: str, limit: int = 100) -> List[Dict]:
        """Get all knowledge for a specific domain."""
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE domain = $1 
            ORDER BY confidence_score DESC, source_count DESC 
            LIMIT {limit}
        """
        
        return await self.db_manager.fetch(query, domain)
    
    async def get_top_concepts(self, limit: int = 50) -> List[Dict]:
        """Get the most confident and well-sourced concepts."""
        query = f"""
            SELECT * FROM {self.table_name} 
            ORDER BY confidence_score DESC, source_count DESC 
            LIMIT {limit}
        """
        
        return await self.db_manager.fetch(query)
    
    async def forget_concept(self, concept: str, domain: Optional[str] = None) -> bool:
        """Remove a concept from semantic memory."""
        if domain:
            # Delete by concept and domain
            where_clause = "concept = $1 AND domain = $2"
            args = [concept, domain]
        else:
            # Delete by concept only
            where_clause = "concept = $1"
            args = [concept]
        affected_rows = await self.db_manager.delete(self.table_name, where_clause, *args)
        return affected_rows > 0
