"""
Global MCP Server - FastAPI server providing global memory access.
Transforming into AIL-3.0 AgentOS Kernel (Project Phoenix Phase 1)
"""

import asyncio
import json
import logging
import warnings
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import asdict
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .memory_manager import GlobalMemoryManager, MemoryQuery, MemoryItem
from .agentos_kernel import AgentOSKernel


# AIL-3.0 Cognition Models
class CognitionRequest(BaseModel):
    """Request model for AIL-3.0 cognition processing."""
    ail_code: str
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Dict[str, Any] = {}
    execution_mode: str = "safe"  # safe, permissive, sandbox


class CognitionResponse(BaseModel):
    """Response model for AIL-3.0 cognition execution."""
    success: bool
    result: Any
    execution_time_ms: float
    cognition_id: str
    execution_plan: List[Dict[str, Any]]
    causality_chain: List[str]
    warnings: List[str] = []
    error: Optional[str] = None


# Legacy Request/Response Models (deprecated in Phase 1)
class StoreMemoryRequest(BaseModel):
    memory_type: str
    content: str
    metadata: Dict[str, Any] = {}
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    importance_score: float = 0.5


class RetrieveMemoryRequest(BaseModel):
    query_text: str
    memory_types: Optional[List[str]] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    time_range_hours: Optional[int] = None
    max_results: int = 10
    similarity_threshold: float = 0.7


class ShareKnowledgeRequest(BaseModel):
    source_agent_id: str
    target_agent_id: str
    knowledge_domain: str
    max_items: int = 50


class MemoryResponse(BaseModel):
    id: str
    memory_type: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    importance_score: float
    similarity_score: Optional[float] = None


class StoreMemoryResponse(BaseModel):
    memory_id: str
    success: bool
    message: str


class InsightResponse(BaseModel):
    agent_id: Optional[str]
    time_period: str
    total_memories: int
    memory_breakdown: Dict[str, int]
    top_concepts: List[str]
    success_patterns: List[str]
    recommendations: List[str]


class GlobalMCPServer:
    """
    Global Memory MCP Server providing HTTP API access to persistent
    memory for AI agents across different systems and sessions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = FastAPI(
            title="AIL-3.0 AgentOS Kernel (Project Phoenix)",
            description="Intelligent cognition processor with AIL-3.0 support and legacy memory compatibility",
            version="1.0.0-phoenix",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Setup CORS for cross-origin requests
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize memory manager (legacy compatibility)
        self.memory_manager = GlobalMemoryManager(config)
        
        # Initialize AgentOS Kernel (Project Phoenix Phase 1)
        self.agentos_kernel = AgentOSKernel(config)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            await self.memory_manager.initialize()
            await self.agentos_kernel.initialize()
            self.logger.info("AIL-3.0 AgentOS Kernel started successfully (Project Phoenix Phase 1)")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            self.logger.info("AgentOS Kernel shutting down")
            await self.agentos_kernel.close()
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            return {
                "service": "AIL-3.0 AgentOS Kernel",
                "version": "1.0.0-phoenix", 
                "status": "operational",
                "project": "Phoenix Phase 1 - AIL-3.0 Transformation",
                "capabilities": [
                    "ail_cognition_processing",
                    "intelligent_query_planning",
                    "tool_execution_registry",
                    "causality_chain_tracking",
                    # Legacy capabilities (deprecated)
                    "episodic_memory",
                    "semantic_memory", 
                    "procedural_memory",
                    "cross_agent_knowledge_sharing",
                    "memory_consolidation",
                    "intelligent_retrieval"
                ],
                "deprecated_endpoints": [
                    "/api/memory/store",
                    "/api/memory/retrieve", 
                    "/api/knowledge/share",
                    "/api/memory/insights",
                    "/api/memory/consolidate"
                ],
                "new_endpoints": [
                    "/cognition - AIL-3.0 cognition processing"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                stats = await self.memory_manager.get_statistics()
                kernel_stats = await self.agentos_kernel.get_statistics()
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow(),
                    "statistics": stats,
                    "kernel_statistics": kernel_stats
                }
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
        
        @self.app.post("/cognition", response_model=CognitionResponse)
        async def process_cognition(request: CognitionRequest):
            """
            AIL-3.0 Cognition Processing Endpoint (Project Phoenix Phase 1)
            
            Processes Agent Instruction Language (AIL-3.0) code and returns 
            intelligent execution results with query planning and causality tracking.
            
            This is the primary endpoint replacing granular REST API operations.
            """
            try:
                import time
                start_time = time.time()
                
                self.logger.info(f"Processing AIL cognition: {request.ail_code[:100]}...")
                
                # Execute cognition through AgentOS Kernel
                result = await self.agentos_kernel.execute_cognition(
                    ail_code=request.ail_code,
                    agent_id=request.agent_id,
                    user_id=request.user_id,
                    context=request.context,
                    execution_mode=request.execution_mode
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                return CognitionResponse(
                    success=result.success,
                    result=result.result,
                    execution_time_ms=result.execution_time_ms,
                    cognition_id=result.cognition_id,
                    execution_plan=result.metadata.get("execution_plan", []),
                    causality_chain=result.causality_chain,
                    warnings=result.metadata.get("warnings", [])
                )
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                self.logger.error(f"Cognition processing failed: {e}")
                
                return CognitionResponse(
                    success=False,
                    result=None,
                    execution_time_ms=execution_time,
                    cognition_id="error",
                    execution_plan=[],
                    causality_chain=[],
                    error=str(e)
                )
        
        @self.app.post("/api/memory/store", response_model=StoreMemoryResponse)
        async def store_memory(request: StoreMemoryRequest):
            """Store a new memory item. [DEPRECATED: Use /cognition with AIL-3.0 STORE operation]"""
            # Issue deprecation warning
            warnings.warn(
                "The /api/memory/store endpoint is deprecated. Use /cognition with AIL-3.0 STORE operation instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self.logger.warning("DEPRECATED ENDPOINT USED: /api/memory/store - Migrate to /cognition with AIL-3.0")
            
            try:
                memory_id = await self.memory_manager.store_memory(
                    memory_type=request.memory_type,
                    content=request.content,
                    metadata=request.metadata,
                    agent_id=request.agent_id,
                    user_id=request.user_id,
                    importance_score=request.importance_score
                )
                
                return StoreMemoryResponse(
                    memory_id=memory_id,
                    success=True,
                    message="Memory stored successfully [DEPRECATED - Use /cognition]"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to store memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/memory/retrieve")
        async def retrieve_memories(request: RetrieveMemoryRequest):
            """Retrieve memories based on query. [DEPRECATED: Use /cognition with AIL-3.0 QUERY operation]"""
            # Issue deprecation warning
            warnings.warn(
                "The /api/memory/retrieve endpoint is deprecated. Use /cognition with AIL-3.0 QUERY operation instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self.logger.warning("DEPRECATED ENDPOINT USED: /api/memory/retrieve - Migrate to /cognition with AIL-3.0")
            
            try:
                # Build time range if specified
                time_range = None
                if request.time_range_hours:
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(hours=request.time_range_hours)
                    time_range = (start_time, end_time)
                
                # Create memory query
                query = MemoryQuery(
                    query_text=request.query_text,
                    memory_types=request.memory_types,
                    agent_id=request.agent_id,
                    user_id=request.user_id,
                    time_range=time_range,
                    max_results=request.max_results,
                    similarity_threshold=request.similarity_threshold
                )
                
                # Retrieve memories
                memories = await self.memory_manager.retrieve_memories(query)
                
                # Convert to response format
                response_memories = []
                for memory in memories:
                    response_memories.append(MemoryResponse(
                        id=memory.id,
                        memory_type=memory.memory_type,
                        content=memory.content,
                        metadata=memory.metadata,
                        timestamp=memory.timestamp,
                        importance_score=memory.importance_score
                    ))
                
                return {
                    "memories": response_memories,
                    "total_found": len(response_memories),
                    "query_processed": True
                }
                
            except Exception as e:
                self.logger.error(f"Failed to retrieve memories: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/knowledge/share")
        async def share_knowledge(request: ShareKnowledgeRequest):
            """Share knowledge between agents."""
            try:
                shared_memories = await self.memory_manager.share_knowledge(
                    source_agent_id=request.source_agent_id,
                    target_agent_id=request.target_agent_id,
                    knowledge_domain=request.knowledge_domain,
                    max_items=request.max_items
                )
                
                return {
                    "success": True,
                    "shared_items": len(shared_memories),
                    "message": f"Successfully shared {len(shared_memories)} memories"
                }
                
            except Exception as e:
                self.logger.error(f"Failed to share knowledge: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/memory/insights")
        async def get_memory_insights(
            agent_id: Optional[str] = None,
            hours_back: int = 24 * 7  # Default: 1 week
        ):
            """Get insights from stored memories."""
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=hours_back)
                time_range = (start_time, end_time)
                
                insights = await self.memory_manager.get_memory_insights(
                    agent_id=agent_id,
                    time_range=time_range
                )
                
                return insights
                
            except Exception as e:
                self.logger.error(f"Failed to get insights: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/memory/consolidate")
        async def consolidate_memories(
            background_tasks: BackgroundTasks,
            agent_id: Optional[str] = None
        ):
            """Trigger memory consolidation (background task)."""
            try:
                background_tasks.add_task(
                    self.memory_manager.consolidate_memories,
                    agent_id
                )
                
                return {
                    "success": True,
                    "message": "Memory consolidation started",
                    "agent_id": agent_id
                }
                
            except Exception as e:
                self.logger.error(f"Failed to start consolidation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/statistics")
        async def get_statistics():
            """Get global memory system statistics."""
            try:
                stats = await self.memory_manager.get_statistics()
                return stats
            except Exception as e:
                self.logger.error(f"Failed to get statistics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/register")
        async def register_agent(
            agent_id: str,
            agent_type: str = "generic",
            capabilities: List[str] = []
        ):
            """Register a new agent with the global memory system."""
            try:
                await self.memory_manager.db_manager.insert("agent_registry", {
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "capabilities": json.dumps(capabilities),
                    "last_active": datetime.utcnow()
                })
                
                return {
                    "success": True,
                    "message": f"Agent {agent_id} registered successfully",
                    "agent_id": agent_id
                }
                
            except Exception as e:
                self.logger.error(f"Failed to register agent: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Legacy MCP endpoint support
        @self.app.post("/mcp/tools/call")
        async def mcp_tool_call(request: Dict[str, Any]):
            """Legacy MCP protocol endpoint for backward compatibility."""
            try:
                tool_name = request.get("name")
                arguments = request.get("arguments", {})
                
                if tool_name == "store_memory":
                    memory_id = await self.memory_manager.store_memory(**arguments)
                    return {"result": {"memory_id": memory_id}}
                
                elif tool_name == "retrieve_memories":
                    query = MemoryQuery(**arguments)
                    memories = await self.memory_manager.retrieve_memories(query)
                    return {"result": {"memories": [asdict(m) for m in memories]}}
                
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
                    
            except Exception as e:
                self.logger.error(f"MCP tool call failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/cognition/execute")
        async def execute_cognition(request: CognitionRequest):
            """Execute AIL-3.0 cognition code."""
            try:
                # Start time for execution duration
                start_time = datetime.utcnow()
                
                # Execute the AIL code using AgentOS Kernel
                result = await self.agentos_kernel.execute_cognition(
                    request.ail_code,
                    agent_id=request.agent_id,
                    user_id=request.user_id,
                    context=request.context,
                    execution_mode=request.execution_mode
                )
                
                # Calculate execution time
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to ms
                
                # Build response
                response = CognitionResponse(
                    success=result.success,
                    result=result.result,
                    execution_time_ms=result.execution_time_ms,
                    cognition_id=result.cognition_id,
                    execution_plan=getattr(result, 'execution_plan', []),
                    causality_chain=result.causality_chain,
                    warnings=getattr(result, 'warnings', []),
                    error=None if result.success else getattr(result, 'error', 'Unknown error')
                )
                
                return response
                
            except Exception as e:
                self.logger.error(f"Failed to execute cognition: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
        # New AIL Memory Management Endpoints
        @self.app.post("/api/ail/memory/store")
        async def store_ail_memory(request: StoreMemoryRequest):
            """Store a memory in AIL format."""
            try:
                memory_id = await self.memory_manager.store_memory(
                    memory_type=request.memory_type,
                    content=request.content,
                    metadata=request.metadata,
                    agent_id=request.agent_id,
                    user_id=request.user_id,
                    importance_score=request.importance_score,
                    store_as_ail=True  # Force AIL formatting
                )
                
                return StoreMemoryResponse(
                    memory_id=memory_id,
                    success=True,
                    message="Memory stored in AIL format successfully"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to store AIL memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/ail/memory/store-natural")
        async def store_natural_memory(request: StoreMemoryRequest):
            """Store a memory in natural language format (no AIL conversion)."""
            try:
                memory_id = await self.memory_manager.store_memory(
                    memory_type=request.memory_type,
                    content=request.content,
                    metadata=request.metadata,
                    agent_id=request.agent_id,
                    user_id=request.user_id,
                    importance_score=request.importance_score,
                    store_as_ail=False  # Keep as natural language
                )
                
                return StoreMemoryResponse(
                    memory_id=memory_id,
                    success=True,
                    message="Memory stored in natural language format successfully"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to store natural language memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/ail/memory/format-stats")
        async def get_memory_format_statistics():
            """Get statistics about memory storage formats (AIL vs natural language)."""
            try:
                stats = await self.memory_manager.get_memory_format_statistics()
                return {
                    "status": "success",
                    "timestamp": datetime.utcnow(),
                    "format_statistics": stats
                }
            except Exception as e:
                self.logger.error(f"Failed to get memory format statistics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/ail/memory/{memory_id}/convert")
        async def convert_memory_to_natural_language(memory_id: str, memory_type: str):
            """Convert an AIL memory to natural language for display."""
            try:
                # Get the AIL content
                ail_content = await self.memory_manager.get_ail_memory_content(memory_id, memory_type)
                if not ail_content:
                    raise HTTPException(status_code=404, detail="Memory not found")
                
                # Convert to natural language
                natural_content = await self.memory_manager.convert_memory_to_natural_language(ail_content)
                
                return {
                    "memory_id": memory_id,
                    "memory_type": memory_type,
                    "ail_content": ail_content,
                    "natural_language_content": natural_content,
                    "converted_at": datetime.utcnow()
                }
                
            except Exception as e:
                self.logger.error(f"Failed to convert memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the AIL-3.0 AgentOS Kernel Server."""
        try:
            # Initialize the memory manager (legacy)
            await self.memory_manager.initialize()
            
            # Initialize the AgentOS Kernel (Project Phoenix)
            await self.agentos_kernel.initialize()
            
            # Configure CORS
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Configure appropriately for production
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Run the server
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            self.logger.info(f"Starting AIL-3.0 AgentOS Kernel Server on {host}:{port}")
            await server.serve()
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
        finally:
            # Clean shutdown
            await self.memory_manager.close()
            await self.agentos_kernel.close()


def create_default_config() -> Dict[str, Any]:
    """Create default configuration for the Global Memory MCP Server."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "global_memory",
            "username": "postgres",
            "password": "postgres",
            "max_connections": 10
        },
        "embeddings": {
            "model": "all-MiniLM-L6-v2",
            "device": "cpu",
            "batch_size": 32,
            "max_seq_length": 512
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8001,
            "log_level": "info"
        }
    }


async def main():
    """Main entry point for the Global Memory MCP Server."""
    import argparse
    import os
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Global Memory MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Load configuration
    config = create_default_config()
    if args.config and os.path.exists(args.config):
        import yaml
        with open(args.config, 'r') as f:
            user_config = yaml.safe_load(f)
            config.update(user_config)
    
    # Override with command line arguments
    config["server"]["host"] = args.host
    config["server"]["port"] = args.port
    
    # Create and run server
    server = GlobalMCPServer(config)
    await server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
