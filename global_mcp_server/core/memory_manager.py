"""
Global Memory Manager - Core orchestrator for all memory types.
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import json
import numpy as np
import sys
import os

# Use relative imports for proper package structure
from ..memory_types.episodic import EpisodicMemory
from ..memory_types.semantic import SemanticMemory  
from ..memory_types.procedural import ProceduralMemory
from ..storage.database import DatabaseManager
from ..storage.sqlite_database import SQLiteDatabaseManager
from ..utils.embeddings import EmbeddingGenerator
from .overfitting_prevention import OverfittingPreventionManager, OverfittingConfig

# Import AIL memory formatter with better error handling
try:
    # Try relative import first
    from ...ail_memory_formatter import AILMemoryFormatter
except ImportError:
    try:
        # Try absolute import as fallback
        from ail_memory_formatter import AILMemoryFormatter
    except ImportError as e:
        # Create a stub formatter if unavailable
        import logging
        logging.getLogger(__name__).warning(f"AIL memory formatter not available: {e}")
        
        class AILMemoryFormatter:
            def format_memory_as_ail(self, **kwargs):
                return kwargs.get('content', '')


@dataclass
@dataclass
class MemoryQuery:
    """Query structure for memory retrieval with pagination and streaming support."""
    query_text: str
    memory_types: Optional[List[str]] = field(default_factory=lambda: None)  # ["episodic", "semantic", "procedural"]
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    time_range: Optional[tuple] = None
    max_results: int = 10
    # Pagination support
    offset: int = 0
    page_size: int = 10
    # Streaming support
    streaming: bool = False
    # Search parameters
    similarity_threshold: float = 0.1
    # Metadata control
    return_metadata: bool = False
    
    def __post_init__(self):
        """Validate query parameters after initialization."""
        if not self.query_text or not self.query_text.strip():
            raise ValueError("Query text cannot be empty or whitespace-only")
        
        if self.max_results < 0:
            raise ValueError("max_results cannot be negative")
            
        if self.offset < 0:
            raise ValueError("offset cannot be negative")
            
        if self.page_size <= 0:
            raise ValueError("page_size must be positive")
            
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")


@dataclass 
class MemoryQueryResult:
    """Result structure for paginated memory queries."""
    memories: List['MemoryItem']
    total_count: int
    offset: int
    page_size: int
    has_more: bool
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_time_ms: float = 0.0


@dataclass
class MemoryItem:
    """Universal memory item structure."""
    id: str
    memory_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    embedding: Optional[List[float]] = None
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_score: float = 0.0


class GlobalMemoryManager:
    """
    Core manager that orchestrates all memory types and provides
    a unified interface for storing and retrieving memories.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize storage and utilities
        # Handle both nested and flat database config
        if "database" in config:
            database_config = config["database"]
        else:
            # Build database config from flat structure
            database_config = {
                "type": config.get("database_type", "sqlite"),
                "url": config.get("database_url", "sqlite:///lans_memory.db"),
                "database_url": config.get("database_url", "sqlite:///lans_memory.db")
            }
        
        # Determine database type and initialize appropriate manager
        database_type = database_config.get("type", "sqlite").lower()
        database_url = database_config.get("url", database_config.get("database_url", ""))
        
        if database_type == "sqlite" or database_url.startswith("sqlite:"):
            self.logger.info("Initializing SQLite database manager for local operation")
            self.db_manager = SQLiteDatabaseManager(database_config)
        else:
            self.logger.info(f"Initializing PostgreSQL database manager for {database_type}")
            self.db_manager = DatabaseManager(database_config)
            
        self.embedding_generator = EmbeddingGenerator(config.get("embeddings", {}))
        
        # Initialize AIL memory formatter
        self.ail_formatter = AILMemoryFormatter()
        
        # Initialize overfitting prevention
        overfitting_config = OverfittingConfig()
        if "overfitting_prevention" in config:
            # Override with user config
            prevention_config = config["overfitting_prevention"]
            for key, value in prevention_config.items():
                if hasattr(overfitting_config, key):
                    setattr(overfitting_config, key, value)
        
        self.overfitting_prevention = OverfittingPreventionManager(overfitting_config)
        
        # Initialize memory types
        self.episodic_memory = EpisodicMemory(self.db_manager, self.embedding_generator)
        self.semantic_memory = SemanticMemory(self.db_manager, self.embedding_generator)
        self.procedural_memory = ProceduralMemory(self.db_manager, self.embedding_generator)
        
        # Memory type mapping
        self.memory_handlers = {
            "episodic": self.episodic_memory,
            "semantic": self.semantic_memory,
            "procedural": self.procedural_memory
        }
        
        # Statistics tracking
        self.stats = {
            "total_memories": 0,
            "queries_processed": 0,
            "cross_agent_shares": 0,
            "memory_consolidations": 0,
            "overfitting_rejections": 0,
            "knowledge_audits": 0
        }
    
    def _validate_memory_metadata(self, memory_type: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Validate metadata requirements for specific memory types."""
        if not metadata:
            metadata = {}
        
        if memory_type == "semantic":
            # Semantic memory requires concept
            if "concept" not in metadata:
                self.logger.warning("Semantic memory metadata missing 'concept' field")
                return False
        elif memory_type == "procedural":
            # Procedural memory requires skill_name
            if "skill_name" not in metadata:
                self.logger.warning("Procedural memory metadata missing 'skill_name' field")
                return False
        elif memory_type == "episodic":
            # Episodic memory can work with minimal metadata
            pass
        
        return True
    
    async def initialize(self):
        """Initialize the global memory system."""
        try:
            await self.db_manager.initialize()
            self.logger.info("Database manager initialized successfully")
            
            try:
                await self.embedding_generator.initialize()
                self.logger.info("Embedding generator initialized successfully")
            except Exception as e:
                self.logger.warning(f"Embedding generator initialization failed: {e}")
                # Continue without embeddings
            
            # Initialize each memory type with error handling
            initialized_memory_types = []
            for memory_name, memory_type in self.memory_handlers.items():
                try:
                    await memory_type.initialize()
                    initialized_memory_types.append(memory_name)
                    self.logger.info(f"{memory_name} memory initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize {memory_name} memory: {e}")
                    # Continue with other memory types
            
            if initialized_memory_types:
                self.logger.info(f"Memory system initialized with: {initialized_memory_types}")
            else:
                self.logger.warning("No memory types were successfully initialized - running in degraded mode")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory system: {e}")
            # Don't raise - allow the system to work without memory
            self.logger.info("Memory system will run in fallback mode")
            
            # Load existing memory statistics
            await self._load_statistics()
            
            self.logger.info("Global Memory Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Global Memory Manager: {e}")
            raise
    
    async def store_memory(
        self, 
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        importance_score: float = 0.5,
        store_as_ail: bool = True  # New parameter to control AIL formatting
    ) -> str:
        """Store a memory item in the appropriate memory type with overfitting prevention."""
        try:
            # Enhanced input validation
            if memory_type not in self.memory_handlers:
                raise ValueError(f"Unknown memory type: {memory_type}. Available types: {list(self.memory_handlers.keys())}")
            
            if not content or not content.strip():
                raise ValueError("Content cannot be empty or whitespace-only")
            
            # Validate required metadata for specific memory types
            if not self._validate_memory_metadata(memory_type, metadata):
                raise ValueError(f"Invalid metadata for memory type '{memory_type}'")
            
            # Convert content to AIL format if requested (default)
            original_content = content
            if store_as_ail:
                try:
                    ail_content = self.ail_formatter.format_memory_as_ail(
                        memory_type=memory_type,
                        content=content,
                        context=metadata or {},
                        agent_id=agent_id or "unknown",
                        importance=importance_score
                    )
                    content = ail_content
                    self.logger.debug(f"Converted memory to AIL format: {memory_type}")
                except Exception as e:
                    self.logger.warning(f"Failed to convert to AIL format, storing as natural language: {e}")
                    # Continue with original content if AIL conversion fails
            
            # Prepare memory for overfitting prevention analysis
            memory_data = {
                'memory_type': memory_type,
                'content': content,  # Now potentially in AIL format
                'original_content': original_content,  # Keep original for analysis
                'metadata': metadata or {},
                'agent_id': agent_id,
                'user_id': user_id,
                'importance_score': importance_score,
                'timestamp': datetime.now(),
                'is_ail_formatted': store_as_ail
            }
            
            # Generate embedding for overfitting analysis (use original content for embedding)
            try:
                embedding = await self.embedding_generator.generate_embedding(original_content)
                memory_data['embedding'] = embedding
            except Exception as e:
                self.logger.error(f"Failed to generate embedding: {e}")
                # Continue without embedding for now
                memory_data['embedding'] = None
            
            # Apply overfitting prevention
            try:
                should_store, prevention_results = await self.overfitting_prevention.process_memory_storage(memory_data)
            except Exception as e:
                self.logger.warning(f"Overfitting prevention failed, allowing storage: {e}")
                should_store, prevention_results = True, {}
            
            if not should_store:
                # Log rejection reason
                rejection_reason = prevention_results.get('final_decision', 'unknown')
                self.logger.info(f"Memory rejected by overfitting prevention: {rejection_reason}")
                self.stats["overfitting_rejections"] += 1
                await self._update_statistics()
                
                # Return empty ID to indicate rejection
                return ""
            
            # Use adjusted importance score from overfitting prevention
            final_importance = memory_data.get('importance_score', importance_score)
            
            handler = self.memory_handlers[memory_type]
            
            # Store based on memory type with error handling
            if memory_type == "episodic":
                memory_id = await handler.store_experience(
                    agent_id=agent_id or "unknown",
                    user_id=user_id,
                    session_id=metadata.get("session_id", str(uuid.uuid4())),
                    content=content,
                    context=metadata or {},
                    importance_score=final_importance
                )
            elif memory_type == "semantic":
                memory_id = await handler.store_knowledge(
                    concept=metadata.get("concept", "unknown_concept"),
                    definition=content,
                    domain=metadata.get("domain", "general"),
                    relations=metadata.get("relations"),
                    contributor=agent_id,
                    confidence_score=final_importance
                )
            elif memory_type == "procedural":
                memory_id = await handler.store_skill(
                    skill_name=metadata.get("skill_name", "unknown_skill"),
                    domain=metadata.get("domain", "general"),
                    procedure=content,
                    steps=metadata.get("steps"),
                    prerequisites=metadata.get("prerequisites"),
                    contributor=agent_id,
                    success_rate=final_importance
                )
            else:
                raise ValueError(f"Unsupported memory type: {memory_type}")
            
            # Update statistics
            self.stats["total_memories"] += 1
            await self._update_statistics()
            
            self.logger.info(f"Stored {memory_type} memory with ID: {memory_id} (importance: {final_importance:.3f})")
            return memory_id
                
        except Exception as db_error:
            self.logger.error(f"Database error storing {memory_type} memory: {db_error}")
            # Generate a fallback ID to indicate storage attempt
            fallback_id = str(uuid.uuid4())
            self.logger.warning(f"Memory storage failed, returning fallback ID: {fallback_id}")
            return fallback_id

    async def retrieve_memories(self, query: MemoryQuery) -> Union[List[MemoryItem], MemoryQueryResult]:
        """
        Retrieve memories based on query parameters with pagination and streaming support.
        
        Args:
            query: MemoryQuery with search parameters
            
        Returns:
            List[MemoryItem] for backward compatibility or MemoryQueryResult for pagination
        """
        start_time = datetime.now()
        
        try:
            # Input validation
            if not query.query_text or not query.query_text.strip():
                raise ValueError("Query text cannot be empty")
            
            if query.max_results <= 0:
                raise ValueError("max_results must be positive")
            
            if query.offset < 0:
                raise ValueError("offset must be non-negative")
            
            if query.page_size <= 0:
                raise ValueError("page_size must be positive")
            
            # Generate query embedding with retry logic
            query_embedding = None
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    query_embedding = await self.embedding_generator.generate_embedding(query.query_text)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.logger.error(f"Failed to generate embedding after {max_retries} attempts: {e}")
                        raise
                    self.logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
            # Determine which memory types to search
            memory_types = query.memory_types or ["episodic", "semantic", "procedural"]
            
            # Validate memory types
            valid_types = set(self.memory_handlers.keys())
            invalid_types = set(memory_types) - valid_types
            if invalid_types:
                raise ValueError(f"Invalid memory types: {invalid_types}. Valid types: {valid_types}")
            
            all_results = []
            total_found = 0
            
            # Search each memory type with error handling
            for memory_type in memory_types:
                try:
                    handler = self.memory_handlers[memory_type]
                    
                    # Enhanced search with pagination support
                    results = await handler.search(
                        query_embedding=query_embedding,
                        query_text=query.query_text,
                        filters={
                            "agent_id": query.agent_id,
                            "user_id": query.user_id,
                            "time_range": query.time_range
                        },
                        max_results=query.max_results * 2,  # Get more results for better sorting
                        similarity_threshold=query.similarity_threshold,
                        offset=query.offset if not query.streaming else 0,
                        limit=query.page_size if not query.streaming else query.max_results
                    )
                    
                    all_results.extend(results)
                    total_found += len(results)
                    
                except Exception as e:
                    self.logger.error(f"Failed to search {memory_type} memory: {e}")
                    # Continue with other memory types instead of failing completely
                    continue
            
            # Calculate relevance scores with error handling
            scored_results = []
            for memory in all_results:
                try:
                    relevance_score = await self._calculate_relevance_score(memory, query)
                    memory.relevance_score = relevance_score
                    scored_results.append(memory)
                except Exception as e:
                    self.logger.warning(f"Failed to calculate relevance score for memory {memory.id}: {e}")
                    # Use default score and continue
                    memory.relevance_score = 0.5
                    scored_results.append(memory)
            
            # Sort by relevance and importance
            scored_results.sort(
                key=lambda x: (x.importance_score * 0.5 + 
                              getattr(x, 'relevance_score', 0.5) * 0.5),
                reverse=True
            )
            
            # Apply pagination if not streaming
            if query.streaming:
                final_results = scored_results[:query.max_results]
            else:
                start_idx = query.offset
                end_idx = start_idx + query.page_size
                final_results = scored_results[start_idx:end_idx]
            
            # Update access statistics asynchronously to avoid blocking
            asyncio.create_task(self._update_access_stats(final_results))
            
            # Update query statistics
            self.stats["queries_processed"] += 1
            asyncio.create_task(self._update_statistics())
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.info(f"Retrieved {len(final_results)} memories for query in {execution_time:.1f}ms")
            
            # Return paginated result or simple list for backward compatibility
            if query.streaming or hasattr(query, 'return_metadata') and query.return_metadata:
                return MemoryQueryResult(
                    memories=final_results,
                    total_count=len(scored_results),
                    offset=query.offset,
                    page_size=query.page_size,
                    has_more=(query.offset + len(final_results)) < len(scored_results),
                    execution_time_ms=execution_time
                )
            else:
                # Backward compatibility: return just the list
                return final_results
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"Failed to retrieve memories after {execution_time:.1f}ms: {e}")
            raise
    
    async def share_knowledge(
        self, 
        source_agent_id: str,
        target_agent_id: str,
        knowledge_domain: str,
        max_items: int = 50
    ) -> List[MemoryItem]:
        """Share knowledge between agents."""
        try:
            shared_memories = []
            
            # Get top knowledge from source agent
            semantic_knowledge = await self.semantic_memory.get_domain_knowledge(
                domain=knowledge_domain, limit=max_items // 2
            )
            
            procedural_knowledge = await self.procedural_memory.get_domain_skills(
                domain=knowledge_domain, limit=max_items // 2
            )
            
            # Convert to MemoryItem format and add target agent context
            for item in semantic_knowledge + procedural_knowledge:
                memory_item = MemoryItem(
                    id=str(uuid.uuid4()),
                    memory_type="semantic" if item in semantic_knowledge else "procedural",
                    content=item.get("definition") or item.get("procedure", ""),
                    metadata={
                        "shared_from": source_agent_id,
                        "shared_to": target_agent_id,
                        "domain": knowledge_domain,
                        "original_id": item["id"]
                    },
                    timestamp=datetime.utcnow(),
                    importance_score=item.get("confidence_score") or item.get("success_rate", 0.5)
                )
                shared_memories.append(memory_item)
            
            # Update sharing statistics
            self.stats["cross_agent_shares"] += len(shared_memories)
            await self._update_statistics()
            
            self.logger.info(f"Shared {len(shared_memories)} memories from {source_agent_id} to {target_agent_id}")
            return shared_memories
            
        except Exception as e:
            self.logger.error(f"Failed to share knowledge: {e}")
            raise

    async def _calculate_relevance_score(self, memory: MemoryItem, query: MemoryQuery) -> float:
        """Calculate relevance score for a memory item based on query context."""
        score = 0.0
        
        # Time relevance (more recent = higher score)
        if query.time_range:
            time_diff = datetime.utcnow() - memory.timestamp
            max_time_diff = query.time_range[1] - query.time_range[0]
            time_score = 1.0 - (time_diff.total_seconds() / max_time_diff.total_seconds())
            score += time_score * 0.3
        
        # Agent/user relevance
        if query.agent_id and memory.metadata.get("agent_id") == query.agent_id:
            score += 0.2
        if query.user_id and memory.metadata.get("user_id") == query.user_id:
            score += 0.2
        
        # Access frequency (higher access = higher relevance)
        if memory.access_count > 0:
            score += min(memory.access_count / 10.0, 0.3)
        
        return min(score, 1.0)

    async def _update_memory_access(self, memory_id: str):
        """Update access statistics for a memory item."""
        # This would be implemented by each memory handler
        pass

    async def _load_statistics(self):
        """Load existing statistics from database."""
        try:
            stats_row = await self.db_manager.fetchrow(
                "SELECT * FROM memory_statistics WHERE metric_name = 'global_stats' ORDER BY timestamp DESC LIMIT 1"
            )
            
            if stats_row:
                metadata = json.loads(stats_row.get('metadata', '{}'))
                self.stats.update(metadata)
            
        except Exception as e:
            self.logger.warning(f"Could not load existing statistics: {e}")

    async def _update_statistics(self):
        """Update memory system statistics in database."""
        try:
            # Check if database connection is available
            if hasattr(self.db_manager, 'connection') and self.db_manager.connection:
                await self.db_manager.insert("memory_statistics", {
                    "metric_name": "global_stats",
                    "metric_value": float(self.stats["total_memories"]),
                    "metadata": json.dumps(self.stats),
                    "timestamp": datetime.utcnow()
                })
            else:
                self.logger.debug("Database connection closed, skipping statistics update")
        except Exception as e:
            self.logger.warning(f"Could not update statistics: {e}")

    async def consolidate_memories(self, agent_id: Optional[str] = None):
        """Consolidate and optimize stored memories."""
        try:
            # Consolidate each memory type
            for memory_type, handler in self.memory_handlers.items():
                if hasattr(handler, 'consolidate'):
                    consolidated_count = await handler.consolidate(agent_id=agent_id)
                    self.stats["memory_consolidations"] += consolidated_count
            
            # Clean up old, low-importance memories
            await self._cleanup_old_memories()
            
            await self._update_statistics()
            self.logger.info(f"Memory consolidation completed for agent: {agent_id or 'all'}")
            
        except Exception as e:
            self.logger.error(f"Failed to consolidate memories: {e}")
            raise

    async def _cleanup_old_memories(self):
        """Clean up old, low-importance memories to manage storage."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=730)  # 2 years
            
            # Clean up each memory type
            for table in ["episodic_memories", "semantic_memories", "procedural_memories"]:
                await self.db_manager.execute(
                    f"DELETE FROM {table} WHERE created_at < $1 AND importance_score < 0.2",
                    cutoff_date
                )
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")

    async def close(self):
        """Clean shutdown of the memory manager."""
        try:
            await self.db_manager.close()
            self.logger.info("Global Memory Manager closed successfully")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def _schedule_knowledge_audit(self):
        """Schedule a knowledge audit to prevent overfitting."""
        try:
            self.logger.info("Performing scheduled knowledge audit")
            audit_results = await self.overfitting_prevention.perform_knowledge_audit(self)
            
            # Update statistics
            self.stats["knowledge_audits"] += 1
            await self._update_statistics()
            
            # Log audit results
            self.logger.info(f"Knowledge audit completed: {audit_results}")
            
        except Exception as e:
            self.logger.error(f"Knowledge audit failed: {e}")

    async def get_overfitting_metrics(self) -> Dict[str, Any]:
        """Get comprehensive overfitting prevention metrics."""
        try:
            base_metrics = {
                "overfitting_risk_score": self.overfitting_prevention.get_overfitting_risk_score(),
                "total_rejections": self.stats.get("overfitting_rejections", 0),
                "knowledge_audits": self.stats.get("knowledge_audits", 0),
                "total_memories": self.stats.get("total_memories", 0)
            }
            
            # Add diversity metrics
            diversity_tracker = self.overfitting_prevention.diversity_tracker
            diversity_metrics = {
                "domain_distribution": dict(diversity_tracker.domain_distribution),
                "pattern_frequency": dict(list(diversity_tracker.pattern_frequency.items())[:10]),  # Top 10
                "total_memories_tracked": diversity_tracker.total_memories,
                "rejections_by_type": dict(diversity_tracker.rejections)
            }
            
            # Add importance scorer metrics
            importance_scorer = self.overfitting_prevention.importance_scorer
            importance_metrics = {
                "success_rates": dict(importance_scorer.success_rates),
                "domain_performance": dict(importance_scorer.domain_performance),
                "avg_importance_score": np.mean(importance_scorer.importance_history) if importance_scorer.importance_history else 0.0,
                "importance_std": np.std(importance_scorer.importance_history) if importance_scorer.importance_history else 0.0
            }
            
            return {
                **base_metrics,
                "diversity_metrics": diversity_metrics,
                "importance_metrics": importance_metrics,
                "audit_history": self.overfitting_prevention.audit_results[-5:]  # Last 5 audits
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get overfitting metrics: {e}")
            return {"error": str(e)}

    async def update_memory_performance(self, memory_id: str, success: bool, domain: str = "general", cross_domain_used: bool = False):
        """Update memory performance metrics for overfitting prevention."""
        try:
            await self.overfitting_prevention.importance_scorer.update_performance_metrics(
                memory_id, success, domain, cross_domain_used
            )
            self.logger.debug(f"Updated performance for memory {memory_id}: success={success}")
            
        except Exception as e:
            self.logger.error(f"Failed to update memory performance: {e}")

    async def force_knowledge_audit(self) -> Dict[str, Any]:
        """Force a knowledge audit regardless of schedule."""
        try:
            self.logger.info("Forcing knowledge audit")
            audit_results = await self.overfitting_prevention.perform_knowledge_audit(self)
            
            # Update statistics
            self.stats["knowledge_audits"] += 1
            await self._update_statistics()
            
            return audit_results
            
        except Exception as e:
            self.logger.error(f"Forced knowledge audit failed: {e}")
            return {"error": str(e)}

    async def get_memory_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory system health report including overfitting analysis."""
        try:
            # Basic memory stats
            total_memories = self.stats.get("total_memories", 0)
            queries_processed = self.stats.get("queries_processed", 0)
            
            # Overfitting metrics
            overfitting_metrics = await self.get_overfitting_metrics()
            
            # Domain distribution analysis
            domain_dist = overfitting_metrics.get("diversity_metrics", {}).get("domain_distribution", {})
            domain_balance_score = self._calculate_domain_balance_score(domain_dist, total_memories)
            
            # Memory efficiency metrics
            rejection_rate = (overfitting_metrics.get("total_rejections", 0) / max(total_memories + overfitting_metrics.get("total_rejections", 0), 1)) * 100
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_health": {
                    "total_memories": total_memories,
                    "queries_processed": queries_processed,
                    "memory_efficiency": {
                        "rejection_rate_percent": round(rejection_rate, 2),
                        "domain_balance_score": round(domain_balance_score, 3),
                        "overfitting_risk": round(overfitting_metrics.get("overfitting_risk_score", 0), 3)
                    }
                },
                "overfitting_prevention": overfitting_metrics,
                "recommendations": self._generate_health_recommendations(overfitting_metrics, domain_balance_score, rejection_rate)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate health report: {e}")
            return {"error": str(e)}

    def _calculate_domain_balance_score(self, domain_dist: Dict[str, int], total_memories: int) -> float:
        """Calculate a score representing how balanced the domain distribution is."""
        if total_memories == 0 or not domain_dist:
            return 1.0
        
        # Calculate entropy for domain distribution
        domain_ratios = [count / total_memories for count in domain_dist.values()]
        entropy = -sum(ratio * np.log2(ratio) if ratio > 0 else 0 for ratio in domain_ratios)
        
        # Normalize by maximum possible entropy (uniform distribution)
        max_entropy = np.log2(len(domain_dist)) if len(domain_dist) > 1 else 1.0
        
        return entropy / max_entropy if max_entropy > 0 else 1.0

    def _generate_health_recommendations(self, overfitting_metrics: Dict[str, Any], domain_balance: float, rejection_rate: float) -> List[str]:
        """Generate recommendations based on memory system health."""
        recommendations = []
        
        # High rejection rate
        if rejection_rate > 15:
            recommendations.append(f"High memory rejection rate ({rejection_rate:.1f}%). Consider adjusting overfitting prevention thresholds.")
        
        # Poor domain balance
        if domain_balance < 0.6:
            recommendations.append(f"Domain distribution is imbalanced (score: {domain_balance:.2f}). Encourage diverse knowledge storage.")
        
        # High overfitting risk
        overfitting_risk = overfitting_metrics.get("overfitting_risk_score", 0)
        if overfitting_risk > 0.7:
            recommendations.append(f"High overfitting risk ({overfitting_risk:.2f}). Consider running knowledge audit.")
        
        # No recent audits
        audit_count = overfitting_metrics.get("knowledge_audits", 0)
        if audit_count == 0:
            recommendations.append("No knowledge audits performed yet. Consider running initial audit.")
        
        # Success rate analysis
        importance_metrics = overfitting_metrics.get("importance_metrics", {})
        avg_success = np.mean(list(importance_metrics.get("success_rates", {1.0}).values()))
        if avg_success < 0.6:
            recommendations.append(f"Memory success rate is low ({avg_success:.2f}). Review memory quality and validation.")
        
        if not recommendations:
            recommendations.append("Memory system health is good. No immediate actions required.")
        
        return recommendations

    def _convert_db_result_to_memory_item(self, row: Dict, memory_type: str) -> MemoryItem:
        """Convert database row to standardized MemoryItem object."""
        # Convert UUID to string if needed
        memory_id = str(row.get('id', ''))
        
        # Extract common fields
        content = row.get('content', '')
        timestamp = row.get('timestamp') or row.get('created_at', datetime.now())
        importance_score = row.get('importance_score', 0.5)
        
        # Memory-type specific metadata extraction
        if memory_type == "episodic":
            metadata = {
                "agent_id": row.get('agent_id'),
                "user_id": row.get('user_id'),
                "session_id": row.get('session_id'),
                "context": row.get('context', {}),
                "emotion": row.get('emotion'),
                "outcome": row.get('outcome')
            }
        elif memory_type == "semantic":
            metadata = {
                "concept": row.get('concept'),
                "definition": row.get('definition'),
                "domain": row.get('domain'),
                "relations": row.get('relations', {}),
                "contributors": row.get('contributors', []),
                "confidence_score": row.get('confidence_score', 0.5)
            }
        elif memory_type == "procedural":
            metadata = {
                "skill_name": row.get('skill_name'),
                "domain": row.get('domain'),
                "procedure": row.get('procedure'),
                "steps": row.get('steps', []),
                "prerequisites": row.get('prerequisites', []),
                "contributors": row.get('contributors', []),
                "success_rate": row.get('success_rate', 0.5)
            }
        else:
            metadata = {}
        
        return MemoryItem(
            id=memory_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            timestamp=timestamp,
            embedding=row.get('embedding'),
            importance_score=importance_score,
            access_count=row.get('access_count', 0),
            last_accessed=row.get('last_accessed'),
            relevance_score=row.get('similarity_score', 0.5)
        )

    def calculate_similarity_score(self, query_embedding: List[float], 
                                   memory_embedding: List[float]) -> float:
        """Calculate semantic similarity between query and memory."""
        try:
            # Ensure embeddings are valid
            if not query_embedding or not memory_embedding:
                return 0.0
            
            # Convert to numpy arrays
            query_vec = np.array(query_embedding, dtype=np.float32)
            memory_vec = np.array(memory_embedding, dtype=np.float32)
            
            # Validate dimensions
            if query_vec.shape != memory_vec.shape:
                return 0.0
            
            # Calculate cosine similarity
            dot_product = np.dot(query_vec, memory_vec)
            query_norm = np.linalg.norm(query_vec)
            memory_norm = np.linalg.norm(memory_vec)
            
            if query_norm == 0 or memory_norm == 0:
                return 0.0
                
            similarity = dot_product / (query_norm * memory_norm)
            
            # Ensure similarity is in [0, 1] range
            similarity = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
            
            return float(similarity)
            
        except Exception as e:
            self.logger.warning(f"Error calculating similarity: {e}")
            return 0.0

    async def share_memory_with_agent(self, memory_id: str, target_agent: str) -> bool:
        """Share a memory with another agent."""
        try:
            # Get the memory
            memory = await self.get_memory_by_id(memory_id)
            if not memory:
                return False
            
            # Mark as shared
            memory.metadata = memory.metadata or {}
            memory.metadata['shared_with'] = memory.metadata.get('shared_with', [])
            memory.metadata['shared_with'].append(target_agent)
            memory.metadata['is_shared'] = True
            
            # Update cross-agent share count
            self.stats['cross_agent_shares'] = self.stats.get('cross_agent_shares', 0) + 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sharing memory with agent: {e}")
            return False

    async def get_collaborative_memories(self, agent_id: str, topic: str) -> List[Dict[str, Any]]:
        """Get memories relevant for collaboration on a topic."""
        try:
            # Query for memories related to the topic
            results = await self.query_memories(
                query_text=f"collaboration {topic} shared knowledge",
                max_results=20,
                similarity_threshold=0.6
            )
            
            # Filter for collaborative memories
            collaborative_memories = []
            for result in results:
                metadata = result.get('metadata', {})
                if (metadata.get('is_shared') or 
                    metadata.get('collaboration_enabled') or
                    'shared' in result.get('content', '').lower()):
                    collaborative_memories.append(result)
            
            return collaborative_memories
            
        except Exception as e:
            self.logger.error(f"Error getting collaborative memories: {e}")
            return []

    async def enable_memory_collaboration(self, memory_id: str) -> bool:
        """Enable a memory for cross-agent collaboration."""
        try:
            memory = await self.get_memory_by_id(memory_id)
            if not memory:
                return False
            
            # Mark as collaboration-enabled
            memory.metadata = memory.metadata or {}
            memory.metadata['collaboration_enabled'] = True
            memory.metadata['collaboration_timestamp'] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling memory collaboration: {e}")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics."""
        try:
            # Get current statistics
            current_stats = self.stats.copy()
            
            # Get overfitting prevention metrics
            overfitting_metrics = self.overfitting_prevention.get_prevention_status()
            
            # Calculate additional metrics
            total_memories = current_stats.get("total_memories", 0)
            domain_dist = current_stats.get("domain_distribution", {})
            domain_balance = self._calculate_domain_balance_score(domain_dist, total_memories)
            
            # Calculate rejection rate
            rejected = current_stats.get("rejected_memories", 0)
            rejection_rate = (rejected / total_memories * 100) if total_memories > 0 else 0
            
            # Generate health recommendations
            recommendations = self._generate_health_recommendations(
                overfitting_metrics, domain_balance, rejection_rate
            )
            
            # Compile comprehensive statistics
            comprehensive_stats = {
                "basic_stats": current_stats,
                "overfitting_prevention": overfitting_metrics,
                "domain_balance_score": domain_balance,
                "rejection_rate_percent": rejection_rate,
                "health_recommendations": recommendations,
                "last_updated": datetime.now().isoformat(),
                "system_status": "healthy" if domain_balance > 0.6 and rejection_rate < 15 else "needs_attention"
            }
            
            return comprehensive_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {
                "error": str(e),
                "basic_stats": self.stats,
                "last_updated": datetime.now().isoformat(),
                "system_status": "error"
            }

    async def get_ail_memory_content(self, memory_id: str, memory_type: str) -> Optional[str]:
        """Retrieve memory content in AIL format."""
        try:
            handler = self.memory_handlers.get(memory_type)
            if not handler:
                raise ValueError(f"Unknown memory type: {memory_type}")
            
            # Get memory by ID
            memories = await handler.search(
                query_text="",
                filters={"id": memory_id},
                max_results=1,
                similarity_threshold=0.0
            )
            
            if memories:
                return memories[0].content
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get AIL memory content: {e}")
            return None
    
    async def convert_memory_to_natural_language(self, ail_content: str) -> str:
        """Convert AIL memory content back to natural language for display."""
        try:
            # Parse the AIL content to extract the natural language components
            parsed_data = self.ail_formatter.parse_ail_memory(ail_content)
            
            if parsed_data:
                # Extract the core content based on memory type
                if "experience" in parsed_data:
                    return parsed_data["experience"].get("content", ail_content)
                elif "knowledge" in parsed_data:
                    concept = parsed_data["knowledge"].get("concept", "")
                    definition = parsed_data["knowledge"].get("definition", "")
                    return f"{concept}: {definition}" if concept and definition else ail_content
                elif "skill" in parsed_data:
                    return parsed_data["skill"].get("procedure", ail_content)
            
            # If parsing fails, return the original content
            return ail_content
            
        except Exception as e:
            self.logger.warning(f"Failed to convert AIL to natural language: {e}")
            return ail_content
    
    async def store_natural_language_memory(
        self, 
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        importance_score: float = 0.5
    ) -> str:
        """Store a memory without AIL formatting (legacy support)."""
        return await self.store_memory(
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            agent_id=agent_id,
            user_id=user_id,
            importance_score=importance_score,
            store_as_ail=False  # Disable AIL formatting
        )

    async def get_memory_format_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory formats (AIL vs natural language)."""
        try:
            # Query the database to count memories by format
            ail_count = 0
            nl_count = 0
            
            for memory_type in ["episodic", "semantic", "procedural"]:
                handler = self.memory_handlers[memory_type]
                # Get all memories for this type
                all_memories = await handler.search(
                    query_text="",
                    filters={},
                    max_results=1000,
                    similarity_threshold=0.0
                )
                
                for memory in all_memories:
                    content = memory.content
                    # Check if content looks like AIL (starts with recognized AIL operations)
                    if content.startswith(("(ANALYZE", "(PLAN", "(EXECUTE", "(REFLECT")):
                        ail_count += 1
                    else:
                        nl_count += 1
            
            return {
                "total_memories": ail_count + nl_count,
                "ail_formatted": ail_count,
                "natural_language": nl_count,
                "ail_percentage": (ail_count / (ail_count + nl_count) * 100) if (ail_count + nl_count) > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get memory format statistics: {e}")
            return {"error": str(e)}

    async def _update_access_stats(self, memories: List[MemoryItem]) -> None:
        """Update memory access statistics asynchronously."""
        try:
            tasks = []
            for memory in memories:
                tasks.append(self._update_memory_access(memory.id))
            
            # Update all access stats concurrently
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            self.logger.warning(f"Failed to update access statistics: {e}")
    
    async def retrieve_memories_streaming(self, query: MemoryQuery) -> AsyncIterator[MemoryItem]:
        """
        Stream memories one by one for large result sets.
        
        Args:
            query: MemoryQuery with streaming=True
            
        Yields:
            MemoryItem: Individual memory items as they're processed
        """
        query.streaming = True
        batch_size = min(query.page_size, 50)  # Process in reasonable batches
        
        try:
            offset = 0
            
            while True:
                batch_query = MemoryQuery(
                    query_text=query.query_text,
                    memory_types=query.memory_types,
                    agent_id=query.agent_id,
                    user_id=query.user_id,
                    time_range=query.time_range,
                    max_results=query.max_results,
                    offset=offset,
                    page_size=batch_size,
                    streaming=False,  # Get batch result
                    similarity_threshold=query.similarity_threshold
                )
                
                result = await self.retrieve_memories(batch_query)
                
                if isinstance(result, MemoryQueryResult):
                    memories = result.memories
                    has_more = result.has_more
                else:
                    memories = result
                    has_more = len(memories) == batch_size
                
                # Yield each memory individually
                for memory in memories:
                    yield memory
                
                # Check if we should continue
                if not has_more or len(memories) < batch_size:
                    break
                    
                offset += len(memories)
                
                # Prevent infinite loops
                if offset > query.max_results:
                    break
                    
        except Exception as e:
            self.logger.error(f"Streaming retrieval failed: {e}")
            raise
    
    async def retrieve_memories_paginated(self, query: MemoryQuery) -> MemoryQueryResult:
        """
        Retrieve memories with explicit pagination metadata.
        
        Args:
            query: MemoryQuery with pagination parameters
            
        Returns:
            MemoryQueryResult: Paginated result with metadata
        """
        query.return_metadata = True  # Ensure we get MemoryQueryResult
        result = await self.retrieve_memories(query)
        
        if isinstance(result, MemoryQueryResult):
            return result
        else:
            # Fallback for backward compatibility
            return MemoryQueryResult(
                memories=result,
                total_count=len(result),
                offset=query.offset,
                page_size=query.page_size,
                has_more=False
            )
