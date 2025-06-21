# Part II: Technical Architecture Deep Dive

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Memory Type Implementations](#memory-type-implementations)
3. [Core Component Analysis](#core-component-analysis)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Scalability Design](#scalability-design)
6. [Integration Patterns](#integration-patterns)

---

## System Architecture Overview

### High-Level Architecture Principles

The Global Memory MCP Server follows key architectural principles:

1. **Separation of Concerns**: Clear boundaries between memory types, storage, and API layers
2. **Microservices Design**: Independent, loosely-coupled components
3. **Event-Driven Architecture**: Asynchronous processing for optimal performance
4. **Hexagonal Architecture**: Clean interfaces between business logic and external systems
5. **Domain-Driven Design**: Memory types as distinct bounded contexts

### Component Hierarchy

```
GlobalMemoryMCPServer/
├── Core Layer/
│   ├── GlobalMemoryManager (Orchestrator)
│   ├── MemoryQuery (Query Object)
│   └── MemoryItem (Data Transfer Object)
├── Memory Types Layer/
│   ├── EpisodicMemory (Experience Storage)
│   ├── SemanticMemory (Knowledge Storage)
│   └── ProceduralMemory (Skill Storage)
├── Storage Layer/
│   ├── DatabaseManager (PostgreSQL Interface)
│   └── EmbeddingGenerator (Vector Processing)
├── API Layer/
│   ├── FastAPI Server (REST Endpoints)
│   ├── GMCPClient (Integration Library)
│   └── AgentROSIntegration (Specialized Helper)
└── Infrastructure Layer/
    ├── Configuration Management
    ├── Health Monitoring
    └── Security & Authentication
```

### Memory Type Architecture Deep Dive

#### Episodic Memory System

**Purpose**: Store temporal experiences, conversations, and contextual events

**Data Structure**:
```python
@dataclass
class EpisodicMemoryItem:
    id: str                          # Unique identifier
    agent_id: str                    # Source agent
    user_id: Optional[str]           # Associated user
    session_id: str                  # Conversation session
    content: str                     # Memory content
    context: Dict[str, Any]          # Contextual metadata
    emotion: Optional[str]           # Emotional valence
    outcome: Optional[str]           # Result classification
    timestamp: datetime              # Temporal anchor
    importance_score: float          # Significance rating
    embedding: Optional[List[float]] # Semantic vector
```

**Key Features**:
- Temporal ordering with microsecond precision
- Contextual metadata storage using JSONB
- Emotional tagging for enhanced recall
- Outcome classification for success pattern recognition
- Automatic importance scoring based on multiple factors

**Database Schema**:
```sql
CREATE TABLE episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    session_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    emotion VARCHAR(50),
    outcome VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    embedding VECTOR(1536)
);
```

#### Semantic Memory System

**Purpose**: Store factual knowledge, concepts, and their relationships

**Data Structure**:
```python
@dataclass
class SemanticMemoryItem:
    id: str                          # Unique identifier
    concept: str                     # Concept name
    definition: str                  # Concept definition
    domain: str                      # Knowledge domain
    relations: Dict[str, Any]        # Concept relationships
    confidence_score: float          # Knowledge confidence
    source_count: int                # Number of sources
    contributors: List[str]          # Contributing agents
    embedding: Optional[List[float]] # Semantic vector
```

**Relationship Types**:
- **is-a**: Hierarchical relationships (inheritance)
- **part-of**: Compositional relationships
- **related-to**: Associative relationships
- **contradicts**: Conflicting information
- **supports**: Evidence relationships

**Database Schema**:
```sql
CREATE TABLE semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    domain VARCHAR(100),
    relations JSONB DEFAULT '{}',
    confidence_score FLOAT DEFAULT 0.5,
    source_count INTEGER DEFAULT 1,
    contributors JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536)
);
```

#### Procedural Memory System

**Purpose**: Store executable knowledge, skills, and methods

**Data Structure**:
```python
@dataclass
class ProceduralMemoryItem:
    id: str                          # Unique identifier
    skill_name: str                  # Skill identifier
    domain: str                      # Application domain
    procedure: str                   # Step-by-step process
    steps: List[str]                 # Discrete action steps
    prerequisites: List[str]         # Required preconditions
    success_rate: float              # Effectiveness metric
    usage_count: int                 # Application frequency
    contributors: List[str]          # Contributing agents
    embedding: Optional[List[float]] # Semantic vector
```

**Skill Classification**:
- **Cognitive Skills**: Problem-solving patterns
- **Technical Skills**: Implementation methods
- **Communication Skills**: Interaction patterns
- **Meta-Skills**: Learning and adaptation strategies

**Database Schema**:
```sql
CREATE TABLE procedural_memories (
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
    embedding VECTOR(1536)
);
```

## Core Component Analysis

### GlobalMemoryManager: Central Orchestrator

**Responsibilities**:
1. **Memory Coordination**: Unified interface for all memory operations
2. **Query Processing**: Intelligent routing to appropriate memory types
3. **Cross-Memory Search**: Seamless search across memory boundaries
4. **Memory Consolidation**: Automated importance-based optimization
5. **Statistics Tracking**: Performance and usage analytics

**Key Methods**:
```python
class GlobalMemoryManager:
    async def store_memory(self, memory_type: str, content: str, metadata: Dict) -> str
    async def retrieve_memories(self, query: MemoryQuery) -> List[MemoryItem]
    async def share_knowledge(self, source_agent: str, target_agent: str, domain: str) -> List[MemoryItem]
    async def consolidate_memories(self, agent_id: Optional[str] = None) -> None
    async def get_statistics(self) -> Dict[str, Any]
```

**Design Patterns Used**:
- **Facade Pattern**: Simplified interface to complex subsystem
- **Strategy Pattern**: Pluggable memory type implementations
- **Observer Pattern**: Event-driven memory updates
- **Command Pattern**: Encapsulated memory operations

### DatabaseManager: Storage Abstraction

**Advanced Features**:
1. **Connection Pooling**: Efficient resource management with asyncpg
2. **Vector Operations**: Native pgvector integration for similarity search
3. **Transaction Management**: ACID compliance for data integrity
4. **Query Optimization**: Prepared statements and index utilization
5. **Health Monitoring**: Connection status and performance tracking

**Vector Search Implementation**:
```python
async def vector_search(
    self, 
    table: str, 
    embedding: List[float], 
    limit: int = 10, 
    similarity_threshold: float = 0.7,
    additional_filters: Optional[str] = None,
    filter_args: Optional[List] = None
) -> List[Dict]:
    # Convert embedding to PostgreSQL vector format
    vector_str = f"[{','.join(map(str, embedding))}]"
    
    # Cosine distance query with threshold filtering
    query = f"""
        SELECT *, (1 - (embedding <-> '{vector_str}')) AS similarity_score
        FROM {table}
        WHERE embedding <-> '{vector_str}' < {1 - similarity_threshold}
        ORDER BY embedding <-> '{vector_str}'
        LIMIT {limit}
    """
    
    return await self.fetch(query, *args)
```

### EmbeddingGenerator: Semantic Processing

**Model Architecture**:
- **Base Model**: all-MiniLM-L6-v2 (384-dimensional embeddings)
- **Tokenization**: SentencePiece with 512 token limit
- **Normalization**: L2 normalization for consistent similarity calculation
- **Batch Processing**: Configurable batch size for performance optimization

**Advanced Features**:
1. **Text Preprocessing**: Cleaning and tokenization pipeline
2. **Batch Processing**: Efficient multi-text embedding generation
3. **Similarity Calculation**: Optimized cosine similarity computation
4. **Caching Strategy**: Model weight caching for faster initialization

## Data Flow Architecture

### Memory Storage Flow

```
User/Agent Request
        ↓
   API Endpoint
        ↓
 GlobalMemoryManager
        ↓
   Memory Type Handler
   (Episodic/Semantic/Procedural)
        ↓
   EmbeddingGenerator
   (Generate vector representation)
        ↓
   DatabaseManager
   (Store in PostgreSQL)
        ↓
   Response with Memory ID
```

### Memory Retrieval Flow

```
Query Request
        ↓
   API Endpoint
        ↓
 GlobalMemoryManager
        ↓
   EmbeddingGenerator
   (Generate query vector)
        ↓
   Memory Type Handlers
   (Parallel search)
        ↓
   DatabaseManager
   (Vector similarity search)
        ↓
   Result Ranking & Filtering
        ↓
   Formatted Response
```

### Cross-Agent Knowledge Sharing Flow

```
Knowledge Share Request
        ↓
   Source Agent Query
   (Retrieve relevant memories)
        ↓
   Knowledge Filtering
   (Domain-specific selection)
        ↓
   Memory Transformation
   (Adapt to target context)
        ↓
   Target Agent Storage
   (Create shared memories)
        ↓
   Relationship Mapping
   (Track knowledge provenance)
```

## Scalability Design

### Horizontal Scaling Strategies

1. **Database Sharding**: Memory types distributed across database instances
2. **Read Replicas**: Query load distribution across multiple read-only databases
3. **Service Decomposition**: Independent scaling of memory type services
4. **Cache Layers**: Redis for frequently accessed memories
5. **Load Balancing**: Request distribution across multiple server instances

### Vertical Scaling Optimizations

1. **Connection Pooling**: Efficient database connection reuse
2. **Batch Processing**: Optimized embedding generation
3. **Index Optimization**: Multi-dimensional database indexing
4. **Query Optimization**: Prepared statements and query caching
5. **Memory Management**: Efficient object lifecycle management

### Performance Characteristics

**Throughput Metrics**:
- **Memory Storage**: 1,000+ operations/second
- **Memory Retrieval**: 500+ complex queries/second
- **Vector Search**: 100+ similarity searches/second
- **Concurrent Agents**: 100+ simultaneous connections

**Latency Characteristics**:
- **Simple Storage**: <50ms p95
- **Complex Retrieval**: <200ms p95
- **Vector Search**: <300ms p95
- **Cross-Agent Sharing**: <500ms p95

## Integration Patterns

### Universal Client Pattern

**Design Philosophy**: 
Provide a unified interface that abstracts complexity while offering flexibility for different integration scenarios.

```python
# Simple Integration
client = GMCPClient("http://localhost:8001")
client.configure_agent("my_agent")
await client.store_memory("episodic", "I learned something new!")

# Advanced Integration
integration = AgentROSMemoryIntegration(client, "planning_agent", "planning")
await integration.remember_successful_solution(problem, solution)
```

### Event-Driven Integration

**Memory Events**:
- `memory.stored`: New memory created
- `memory.retrieved`: Memory accessed
- `memory.shared`: Knowledge shared between agents
- `memory.consolidated`: Memory importance updated

**Webhook Support**:
```python
@app.post("/webhook/memory-events")
async def handle_memory_event(event: MemoryEvent):
    if event.type == "memory.stored":
        await notify_related_agents(event.memory_id)
```

### Plugin Architecture

**Memory Type Plugins**:
Custom memory types can be implemented by extending base classes:

```python
class CustomMemoryType(BaseMemoryType):
    async def store(self, content: str, metadata: Dict) -> str:
        # Custom storage logic
        pass
    
    async def search(self, query: str, filters: Dict) -> List[Dict]:
        # Custom search logic
        pass
```

**Integration Plugins**:
Framework-specific integrations for popular AI platforms:

- **LangChain Plugin**: Native LangChain memory integration
- **AutoGen Plugin**: Multi-agent conversation memory
- **CrewAI Plugin**: Team-based knowledge sharing
- **Custom Framework Plugin**: Template for new integrations

---

**Next: [Part III - Implementation Analysis & Code Review](./part-iii-implementation-analysis.md)**
