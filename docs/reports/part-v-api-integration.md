# Part V: API & Integration Layer Documentation

**Document:** Global Memory MCP Server - Comprehensive Technical Report  
**Part:** V of X - API & Integration Layer Documentation  
**Date:** June 12, 2025  

---

## Table of Contents

1. [API Architecture Overview](#api-architecture-overview)
2. [FastAPI Server Implementation](#fastapi-server-implementation)
3. [RESTful Endpoints Documentation](#restful-endpoints-documentation)
4. [Client Library (GMCPClient)](#client-library-gmcpclient)
5. [AgentROS Integration](#agentros-integration)
6. [Authentication & Security](#authentication--security)
7. [Error Handling & Validation](#error-handling--validation)
8. [Integration Examples](#integration-examples)

---

## API Architecture Overview

### Multi-Protocol Design

The Global Memory MCP Server implements a dual-protocol approach to maximize compatibility and ease of integration:

```
┌─────────────────────────────────────────────────┐
│                API Gateway Layer                │
├─────────────────────────────────────────────────┤
│  ┌─────────────────┬─────────────────────────┐  │
│  │   FastAPI REST  │  Legacy MCP Protocol    │  │
│  │   15 Endpoints  │   (Future Extension)    │  │
│  └─────────────────┴─────────────────────────┘  │
├─────────────────────────────────────────────────┤
│              Request Processing Layer           │
│  ┌─────────────────┬─────────────────────────┐  │
│  │   Validation    │   Authentication        │  │
│  │   (Pydantic)    │   & Authorization       │  │
│  └─────────────────┴─────────────────────────┘  │
├─────────────────────────────────────────────────┤
│               Service Layer                     │
│  ┌─────────────────┬─────────────────────────┐  │
│  │ GlobalMemory    │   Memory Type           │  │
│  │ Manager         │   Handlers              │  │
│  └─────────────────┴─────────────────────────┘  │
├─────────────────────────────────────────────────┤
│               Storage Layer                     │
│  ┌─────────────────┬─────────────────────────┐  │
│  │   PostgreSQL    │   Vector Search         │  │
│  │   Database      │   (pgvector)            │  │
│  └─────────────────┴─────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Design Principles

**RESTful Design**: Following REST architectural constraints for predictable API behavior
**Async-First**: All operations use async/await for high concurrency
**Type Safety**: Full Pydantic model validation for request/response
**Extensibility**: Modular design for easy addition of new endpoints
**Compatibility**: Maintains compatibility with existing MCP protocol expectations

---

## FastAPI Server Implementation

### Server Configuration

**Main Server Setup** (`core/server.py`):
```python
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="Global Memory MCP Server",
    description="AI Memory System with Persistent Storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory manager instance
memory_manager: Optional[GlobalMemoryManager] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the global memory manager on startup."""
    global memory_manager
    config = load_config()
    memory_manager = await create_memory_manager(config)
    logger.info("Global Memory MCP Server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    if memory_manager:
        await memory_manager.close()
    logger.info("Global Memory MCP Server shut down")
```

### Request/Response Models

**Pydantic Models for Type Safety**:
```python
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

class MemoryRequest(BaseModel):
    content: Dict[str, Any] = Field(..., description="Memory content as JSON object")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or v == {}:
            raise ValueError('Content cannot be empty')
        return v

class MemoryResponse(BaseModel):
    id: str = Field(..., description="Unique memory identifier")
    content: Dict[str, Any] = Field(..., description="Memory content")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    memory_type: str = Field(..., description="Type of memory (episodic/semantic/procedural)")
    timestamp: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    similarity_score: Optional[float] = Field(None, description="Similarity score for search results")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    memory_type: Optional[str] = Field(None, description="Filter by memory type")
    agent_id: Optional[str] = Field(None, description="Filter by agent")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    min_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")

class SearchResponse(BaseModel):
    memories: List[MemoryResponse] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database: Dict[str, Any] = Field(..., description="Database health information")
    memory_stats: Dict[str, Any] = Field(..., description="Memory usage statistics")
```

### Middleware & Request Processing

**Custom Middleware**:
```python
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {str(e)} in {process_time:.3f}s")
            raise

app.add_middleware(RequestLoggingMiddleware)
```

**Dependency Injection**:
```python
async def get_memory_manager() -> GlobalMemoryManager:
    """Dependency injection for memory manager."""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    return memory_manager

async def validate_agent_id(agent_id: Optional[str] = None) -> Optional[str]:
    """Validate and normalize agent ID."""
    if agent_id and len(agent_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
    return agent_id.strip() if agent_id else None
```

---

## RESTful Endpoints Documentation

### 1. Memory Storage Endpoints

#### Store Memory
```http
POST /memories/{memory_type}
Content-Type: application/json

{
    "content": {"type": "conversation", "message": "Hello, how are you?"},
    "agent_id": "agent-001",
    "metadata": {"priority": "high", "tags": ["greeting"]}
}
```

**Implementation**:
```python
@app.post("/memories/{memory_type}", response_model=dict)
async def store_memory(
    memory_type: str,
    request: MemoryRequest,
    manager: GlobalMemoryManager = Depends(get_memory_manager),
    agent_id: Optional[str] = Depends(validate_agent_id)
):
    """Store a new memory of specified type."""
    try:
        # Validate memory type
        if memory_type not in ['episodic', 'semantic', 'procedural']:
            raise HTTPException(status_code=400, detail="Invalid memory type")
        
        # Store memory
        memory_id = await manager.store_memory(
            memory_type=memory_type,
            content=request.content,
            agent_id=request.agent_id or agent_id,
            metadata=request.metadata
        )
        
        return {
            "id": memory_id,
            "message": f"{memory_type.title()} memory stored successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Batch Store Memories
```http
POST /memories/batch
Content-Type: application/json

{
    "memories": [
        {
            "memory_type": "episodic",
            "content": {"message": "First message"},
            "agent_id": "agent-001"
        },
        {
            "memory_type": "semantic", 
            "content": {"fact": "The sky is blue"},
            "agent_id": "agent-001"
        }
    ]
}
```

### 2. Memory Retrieval Endpoints

#### Search Memories
```http
GET /memories/search?query=hello&memory_type=episodic&limit=10
```

**Implementation**:
```python
@app.get("/memories/search", response_model=SearchResponse)
async def search_memories(
    query: str,
    memory_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 10,
    min_similarity: float = 0.0,
    manager: GlobalMemoryManager = Depends(get_memory_manager)
):
    """Search memories using vector similarity."""
    start_time = time.time()
    
    try:
        # Validate parameters
        if limit > 100:
            limit = 100
        
        # Perform search
        results = await manager.search_memories(
            query=query,
            memory_type=memory_type,
            agent_id=agent_id,
            limit=limit,
            min_similarity=min_similarity
        )
        
        # Convert to response format
        memory_responses = [
            MemoryResponse(
                id=result['id'],
                content=result['content'],
                agent_id=result['agent_id'],
                memory_type=result['memory_type'],
                timestamp=result['timestamp'],
                metadata=result['metadata'],
                similarity_score=result.get('similarity_score')
            )
            for result in results
        ]
        
        query_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            memories=memory_responses,
            total_count=len(memory_responses),
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Get Memory by ID
```http
GET /memories/{memory_id}
```

#### Get Agent Memories
```http
GET /agents/{agent_id}/memories?memory_type=episodic&limit=50
```

### 3. Memory Management Endpoints

#### Delete Memory
```http
DELETE /memories/{memory_id}
```

#### Update Memory
```http
PUT /memories/{memory_id}
Content-Type: application/json

{
    "content": {"updated": "content"},
    "metadata": {"status": "updated"}
}
```

#### Consolidate Memories
```http
POST /memories/consolidate
Content-Type: application/json

{
    "agent_id": "agent-001",
    "memory_types": ["episodic", "semantic"]
}
```

### 4. System Endpoints

#### Health Check
```http
GET /health
```

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-06-12T10:30:00Z",
    "database": {
        "status": "connected",
        "pool_size": 15,
        "total_memories": 1247
    },
    "memory_stats": {
        "episodic_count": 856,
        "semantic_count": 234,
        "procedural_count": 157
    }
}
```

#### System Statistics
```http
GET /stats
```

#### Server Information
```http
GET /info
```

---

## Client Library (GMCPClient)

### Client Architecture

**Universal Client Implementation** (`api/client.py`):
```python
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import json
import logging

class GMCPClient:
    """Universal client for Global Memory MCP Server integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 timeout: int = 30, max_retries: int = 3):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
```

### Core Client Methods

**Memory Storage**:
```python
async def store_memory(self, memory_type: str, content: Dict[str, Any],
                      agent_id: str = None, metadata: Dict = None) -> str:
    """Store a new memory."""
    url = f"{self.base_url}/memories/{memory_type}"
    payload = {
        "content": content,
        "agent_id": agent_id,
        "metadata": metadata or {}
    }
    
    async with self.session.post(url, json=payload) as response:
        if response.status == 200:
            result = await response.json()
            return result['id']
        else:
            error_text = await response.text()
            raise GMCPClientError(f"Failed to store memory: {error_text}")

async def store_conversation_turn(self, agent_id: str, user_message: str,
                                 assistant_response: str, conversation_id: str,
                                 turn_number: int, metadata: Dict = None) -> str:
    """Store a conversation turn in episodic memory."""
    content = {
        "type": "conversation_turn",
        "user_message": user_message,
        "assistant_response": assistant_response,
        "conversation_id": conversation_id,
        "turn_number": turn_number
    }
    
    return await self.store_memory(
        memory_type="episodic",
        content=content,
        agent_id=agent_id,
        metadata=metadata
    )
```

**Memory Retrieval**:
```python
async def search_memories(self, query: str, memory_type: str = None,
                         agent_id: str = None, limit: int = 10,
                         min_similarity: float = 0.0) -> List[Dict]:
    """Search memories using vector similarity."""
    params = {
        "query": query,
        "limit": limit,
        "min_similarity": min_similarity
    }
    
    if memory_type:
        params["memory_type"] = memory_type
    if agent_id:
        params["agent_id"] = agent_id
    
    url = f"{self.base_url}/memories/search"
    
    async with self.session.get(url, params=params) as response:
        if response.status == 200:
            result = await response.json()
            return result['memories']
        else:
            error_text = await response.text()
            raise GMCPClientError(f"Failed to search memories: {error_text}")

async def get_agent_memories(self, agent_id: str, memory_type: str = None,
                           limit: int = 50) -> List[Dict]:
    """Get all memories for a specific agent."""
    params = {"limit": limit}
    if memory_type:
        params["memory_type"] = memory_type
    
    url = f"{self.base_url}/agents/{agent_id}/memories"
    
    async with self.session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise GMCPClientError(f"Failed to get agent memories: {error_text}")
```

**Memory Management**:
```python
async def consolidate_memories(self, agent_id: str = None,
                              memory_types: List[str] = None) -> Dict[str, int]:
    """Trigger memory consolidation."""
    payload = {}
    if agent_id:
        payload["agent_id"] = agent_id
    if memory_types:
        payload["memory_types"] = memory_types
    
    url = f"{self.base_url}/memories/consolidate"
    
    async with self.session.post(url, json=payload) as response:
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise GMCPClientError(f"Failed to consolidate memories: {error_text}")

async def health_check(self) -> Dict[str, Any]:
    """Check server health status."""
    url = f"{self.base_url}/health"
    
    async with self.session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            return {"status": "unhealthy", "error": await response.text()}
```

### Error Handling & Retry Logic

**Custom Exceptions**:
```python
class GMCPClientError(Exception):
    """Base exception for GMCP client operations."""
    pass

class ConnectionError(GMCPClientError):
    """Connection-related errors."""
    pass

class AuthenticationError(GMCPClientError):
    """Authentication-related errors."""
    pass

class ValidationError(GMCPClientError):
    """Request validation errors."""
    pass
```

**Retry Mechanism**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(ConnectionError)
)
async def _make_request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
    """Make HTTP request with automatic retry."""
    try:
        async with self.session.request(method, url, **kwargs) as response:
            if response.status >= 500:
                raise ConnectionError(f"Server error: {response.status}")
            return response
            
    except aiohttp.ClientError as e:
        raise ConnectionError(f"Connection failed: {e}")
```

---

## AgentROS Integration

### Specialized Integration Helper

**AgentROS Memory Integration** (`api/agentros_integration.py`):
```python
from typing import Dict, List, Optional, Any
import asyncio
import logging

class AgentROSMemoryIntegration:
    """Specialized helper for seamless AgentROS memory enhancement."""
    
    def __init__(self, gmcp_client: GMCPClient):
        self.client = gmcp_client
        self.logger = logging.getLogger(__name__)
    
    async def enhance_agent_with_memory(self, agent_config: Dict) -> Dict:
        """Enhance existing AgentROS agent with memory capabilities."""
        agent_id = agent_config.get('agent_id')
        if not agent_id:
            raise ValueError("Agent configuration must include 'agent_id'")
        
        # Load existing memories for context
        existing_memories = await self.client.get_agent_memories(
            agent_id=agent_id,
            limit=100
        )
        
        # Enhance agent configuration with memory context
        enhanced_config = agent_config.copy()
        enhanced_config['memory_integration'] = {
            'enabled': True,
            'existing_memories_count': len(existing_memories),
            'memory_server_url': self.client.base_url
        }
        
        # Inject memory capabilities into agent prompt
        if 'system_prompt' in enhanced_config:
            memory_context = await self._build_memory_context(existing_memories)
            enhanced_config['system_prompt'] += f"\n\n{memory_context}"
        
        return enhanced_config
```

**AgentROS Workflow Integration**:
```python
async def store_agent_interaction(self, agent_id: str, interaction: Dict) -> str:
    """Store agent interaction in appropriate memory type."""
    interaction_type = interaction.get('type', 'conversation')
    
    if interaction_type == 'conversation':
        return await self.client.store_conversation_turn(
            agent_id=agent_id,
            user_message=interaction['user_message'],
            assistant_response=interaction['assistant_response'],
            conversation_id=interaction.get('conversation_id'),
            turn_number=interaction.get('turn_number', 1),
            metadata=interaction.get('metadata', {})
        )
    
    elif interaction_type == 'skill_execution':
        return await self.client.store_memory(
            memory_type='procedural',
            content={
                'skill_name': interaction['skill_name'],
                'procedure': interaction['procedure'],
                'success': interaction.get('success', True),
                'execution_time': interaction.get('execution_time')
            },
            agent_id=agent_id,
            metadata=interaction.get('metadata', {})
        )
    
    elif interaction_type == 'fact_learning':
        return await self.client.store_memory(
            memory_type='semantic',
            content={
                'fact': interaction['fact'],
                'concept_type': interaction.get('concept_type', 'general'),
                'confidence': interaction.get('confidence', 1.0)
            },
            agent_id=agent_id,
            metadata=interaction.get('metadata', {})
        )
    
    else:
        # Default to episodic memory
        return await self.client.store_memory(
            memory_type='episodic',
            content=interaction,
            agent_id=agent_id
        )

async def get_agent_context(self, agent_id: str, query: str,
                           memory_types: List[str] = None) -> List[Dict]:
    """Get relevant memory context for agent's current task."""
    if memory_types is None:
        memory_types = ['episodic', 'semantic', 'procedural']
    
    all_context = []
    
    for memory_type in memory_types:
        memories = await self.client.search_memories(
            query=query,
            memory_type=memory_type,
            agent_id=agent_id,
            limit=5,
            min_similarity=0.7
        )
        all_context.extend(memories)
    
    # Sort by relevance (similarity score)
    all_context.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    return all_context[:10]  # Return top 10 most relevant memories

async def share_knowledge_between_agents(self, source_agent: str,
                                       target_agent: str, topic: str) -> bool:
    """Share knowledge from source agent to target agent."""
    try:
        # Get relevant knowledge from source agent
        source_knowledge = await self.client.search_memories(
            query=topic,
            agent_id=source_agent,
            memory_type='semantic',
            limit=10,
            min_similarity=0.8
        )
        
        # Transfer high-confidence knowledge to target agent
        transferred_count = 0
        for knowledge in source_knowledge:
            if knowledge.get('confidence', 0) >= 0.8:
                await self.client.store_memory(
                    memory_type='semantic',
                    content=knowledge['content'],
                    agent_id=target_agent,
                    metadata={
                        'source_agent': source_agent,
                        'transfer_topic': topic,
                        'original_confidence': knowledge.get('confidence'),
                        'transferred_at': datetime.utcnow().isoformat()
                    }
                )
                transferred_count += 1
        
        return transferred_count > 0
        
    except Exception as e:
        self.logger.error(f"Failed to share knowledge: {e}")
        return False
```

### Memory-Enhanced Agent Creation

**Agent Factory with Memory**:
```python
class MemoryEnhancedAgentFactory:
    """Factory for creating AgentROS agents with memory capabilities."""
    
    def __init__(self, memory_integration: AgentROSMemoryIntegration):
        self.memory_integration = memory_integration
    
    async def create_planning_agent(self, agent_id: str,
                                   base_config: Dict = None) -> Dict:
        """Create memory-enhanced planning agent."""
        base_config = base_config or {}
        
        # Get existing planning patterns
        planning_memories = await self.memory_integration.client.search_memories(
            query="planning successful pattern strategy",
            agent_id=agent_id,
            memory_type="procedural",
            limit=10
        )
        
        # Build planning context from memories
        planning_context = self._build_planning_context(planning_memories)
        
        agent_config = {
            'agent_id': agent_id,
            'type': 'planning_agent',
            'system_prompt': f"""
You are a memory-enhanced planning agent. You have access to your past planning experiences and successful patterns.

{planning_context}

Use your memory to inform your planning decisions and learn from past successes and failures.
            """,
            'memory_integration': {
                'enabled': True,
                'auto_store_plans': True,
                'learn_from_outcomes': True
            }
        }
        
        # Merge with base configuration
        agent_config.update(base_config)
        
        return await self.memory_integration.enhance_agent_with_memory(agent_config)
```

---

## Authentication & Security

### API Key Authentication

**Security Middleware**:
```python
from fastapi import HTTPException, Header
from functools import wraps

API_KEYS = {
    "gmcp-prod-key-001": {"name": "Production Agent", "permissions": ["read", "write"]},
    "gmcp-read-key-002": {"name": "Read-Only Client", "permissions": ["read"]}
}

async def verify_api_key(x_api_key: str = Header(None)) -> Dict[str, Any]:
    """Verify API key and return permissions."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return API_KEYS[x_api_key]

def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            api_key_info = kwargs.get('api_key_info')
            if not api_key_info or permission not in api_key_info['permissions']:
                raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in endpoints
@app.post("/memories/{memory_type}")
@require_permission("write")
async def store_memory(
    memory_type: str,
    request: MemoryRequest,
    api_key_info: Dict = Depends(verify_api_key),
    manager: GlobalMemoryManager = Depends(get_memory_manager)
):
    # Implementation here
    pass
```

### Rate Limiting

**Redis-Based Rate Limiting**:
```python
import redis.asyncio as redis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_client, default_limit: int = 100, window_seconds: int = 3600):
        self.redis = redis_client
        self.default_limit = default_limit
        self.window_seconds = window_seconds
    
    async def check_rate_limit(self, client_id: str, limit: int = None) -> bool:
        """Check if client has exceeded rate limit."""
        limit = limit or self.default_limit
        window_start = int(datetime.utcnow().timestamp()) // self.window_seconds
        key = f"rate_limit:{client_id}:{window_start}"
        
        current_count = await self.redis.incr(key)
        if current_count == 1:
            await self.redis.expire(key, self.window_seconds)
        
        return current_count <= limit

# Middleware implementation
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if not await rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    response = await call_next(request)
    return response
```

---

## Error Handling & Validation

### Comprehensive Error Responses

**Error Response Models**:
```python
class ErrorDetail(BaseModel):
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused error")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error summary")
    details: List[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
```

**Global Exception Handler**:
```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        details.append(ErrorDetail(
            type="validation_error",
            message=error['msg'],
            field='.'.join(str(loc) for loc in error['loc'])
        ))
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation failed",
            details=details,
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

@app.exception_handler(GlobalMemoryError)
async def global_memory_exception_handler(request: Request, exc: GlobalMemoryError):
    """Handle Global Memory specific errors."""
    status_code = 500
    
    if isinstance(exc, MemoryNotFoundError):
        status_code = 404
    elif isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, DatabaseConnectionError):
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            details=[ErrorDetail(
                type=exc.__class__.__name__.lower(),
                message=str(exc)
            )],
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )
```

### Input Validation

**Advanced Validation Rules**:
```python
class MemoryContentValidator:
    @staticmethod
    def validate_episodic_content(content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate episodic memory content structure."""
        required_fields = ['type']
        
        if content.get('type') == 'conversation_turn':
            required_fields.extend(['user_message', 'assistant_response'])
        
        for field in required_fields:
            if field not in content:
                raise ValidationError(f"Required field '{field}' missing from episodic content")
        
        return content
    
    @staticmethod
    def validate_semantic_content(content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate semantic memory content structure."""
        if 'fact' not in content and 'concept' not in content:
            raise ValidationError("Semantic memory must contain 'fact' or 'concept'")
        
        # Validate confidence score if present
        if 'confidence' in content:
            confidence = content['confidence']
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                raise ValidationError("Confidence must be a number between 0 and 1")
        
        return content
    
    @staticmethod
    def validate_procedural_content(content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate procedural memory content structure."""
        required_fields = ['skill_name', 'procedure']
        
        for field in required_fields:
            if field not in content:
                raise ValidationError(f"Required field '{field}' missing from procedural content")
        
        return content

# Usage in endpoint
@app.post("/memories/{memory_type}")
async def store_memory(
    memory_type: str,
    request: MemoryRequest,
    manager: GlobalMemoryManager = Depends(get_memory_manager)
):
    # Validate content based on memory type
    validator_map = {
        'episodic': MemoryContentValidator.validate_episodic_content,
        'semantic': MemoryContentValidator.validate_semantic_content,
        'procedural': MemoryContentValidator.validate_procedural_content
    }
    
    if memory_type in validator_map:
        request.content = validator_map[memory_type](request.content)
    
    # Store memory...
```

---

## Integration Examples

### 1. Simple Memory Storage

**Python Integration Example**:
```python
import asyncio
from api.client import GMCPClient

async def basic_memory_example():
    """Basic memory storage and retrieval example."""
    async with GMCPClient("http://localhost:8000") as client:
        # Store a conversation
        memory_id = await client.store_conversation_turn(
            agent_id="demo-agent",
            user_message="What's the weather like?",
            assistant_response="I don't have access to current weather data.",
            conversation_id="demo-conv-001",
            turn_number=1
        )
        
        print(f"Stored memory: {memory_id}")
        
        # Search for similar conversations
        similar = await client.search_memories(
            query="weather information",
            memory_type="episodic",
            agent_id="demo-agent"
        )
        
        print(f"Found {len(similar)} similar memories")

# Run example
asyncio.run(basic_memory_example())
```

### 2. AgentROS Integration

**Enhanced Agent Example**:
```python
from api.agentros_integration import AgentROSMemoryIntegration
from api.client import GMCPClient

async def agentros_integration_example():
    """AgentROS memory integration example."""
    async with GMCPClient("http://localhost:8000") as client:
        integration = AgentROSMemoryIntegration(client)
        
        # Enhance existing agent with memory
        base_agent_config = {
            'agent_id': 'planning-agent-001',
            'type': 'planning_agent',
            'system_prompt': 'You are a helpful planning assistant.'
        }
        
        enhanced_config = await integration.enhance_agent_with_memory(base_agent_config)
        
        # Store agent interaction
        await integration.store_agent_interaction(
            agent_id='planning-agent-001',
            interaction={
                'type': 'skill_execution',
                'skill_name': 'create_project_plan',
                'procedure': 'Analyze requirements, break into tasks, estimate timeline',
                'success': True,
                'execution_time': 45.2
            }
        )
        
        # Get context for new task
        context = await integration.get_agent_context(
            agent_id='planning-agent-001',
            query='create software project plan'
        )
        
        print(f"Retrieved {len(context)} relevant memories for planning context")

asyncio.run(agentros_integration_example())
```

### 3. Knowledge Sharing

**Multi-Agent Knowledge Sharing**:
```python
async def knowledge_sharing_example():
    """Demonstrate knowledge sharing between agents."""
    async with GMCPClient("http://localhost:8000") as client:
        integration = AgentROSMemoryIntegration(client)
        
        # Agent A learns something new
        await client.store_memory(
            memory_type='semantic',
            content={
                'fact': 'FastAPI supports automatic OpenAPI documentation generation',
                'concept_type': 'web_development',
                'confidence': 0.95
            },
            agent_id='expert-agent-001',
            metadata={'source': 'official_documentation'}
        )
        
        # Share knowledge from expert to novice
        shared = await integration.share_knowledge_between_agents(
            source_agent='expert-agent-001',
            target_agent='novice-agent-002',
            topic='FastAPI web development'
        )
        
        if shared:
            print("Knowledge successfully shared between agents")
            
            # Verify novice agent now has the knowledge
            novice_knowledge = await client.search_memories(
                query='FastAPI OpenAPI documentation',
                agent_id='novice-agent-002',
                memory_type='semantic'
            )
            
            print(f"Novice agent now has {len(novice_knowledge)} relevant memories")

asyncio.run(knowledge_sharing_example())
```

---

## Summary

The API and Integration Layer of the Global Memory MCP Server provides:

**Comprehensive API Coverage**:
- 15 RESTful endpoints for complete memory operations
- Type-safe request/response models with Pydantic validation
- Comprehensive error handling and meaningful error responses
- Health monitoring and system statistics endpoints

**Universal Client Library**:
- Easy-to-use async client for any Python-based AI system
- Automatic retry logic and connection management
- Built-in error handling with custom exception hierarchy
- Support for batch operations and efficient memory management

**AgentROS Specialized Integration**:
- Zero-code memory enhancement for existing agents
- Automatic context injection and memory-guided planning
- Cross-agent knowledge sharing capabilities
- Memory-enhanced agent factory for creating new agents

**Production-Ready Features**:
- API key authentication and permission-based access control
- Rate limiting with Redis-based implementation
- Comprehensive logging and monitoring
- CORS support for web integration

**Integration Benefits**:
- **Seamless Integration**: Works with existing AI systems without modification
- **Performance**: Async operations with connection pooling for high throughput
- **Reliability**: Comprehensive error handling and automatic retry mechanisms
- **Scalability**: Designed for high-concurrency multi-agent environments

The API layer successfully bridges the gap between the sophisticated memory storage system and real-world AI applications, enabling any AI system to gain human-like long-lasting memory capabilities with minimal integration effort.

---

**Next**: [Part VI - Performance & Scalability Analysis](./part-vi-performance-analysis.md)
