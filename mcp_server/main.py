"""
MCP Server main entry point.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

from .handlers.file_operations import FileHandler
from .handlers.command_execution import CommandHandler
from .security.sandbox import SandboxManager


class MCPRequest(BaseModel):
    """Standard MCP request format."""
    method: str
    params: Dict[str, Any] = {}
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """Standard MCP response format."""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class MCPServer:
    """Model Context Protocol Server for secure agent operations."""
    
    def __init__(self, sandbox_root: str = "/tmp/agentros_sandbox"):
        self.app = FastAPI(
            title="LANS MCP Server",
            description="Secure operations server for AI agents",
            version="0.1.0"
        )
        
        # Initialize handlers
        self.sandbox_manager = SandboxManager(sandbox_root)
        self.file_handler = FileHandler(self.sandbox_manager)
        self.command_handler = CommandHandler(self.sandbox_manager)
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _register_routes(self):
        """Register MCP API routes."""
        
        @self.app.post("/mcp", response_model=MCPResponse)
        async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
            """Main MCP request handler."""
            try:
                if request.method == "read_file":
                    result = await self.file_handler.read_file(
                        request.params.get("path", "")
                    )
                elif request.method == "write_file":
                    result = await self.file_handler.write_file(
                        request.params.get("path", ""),
                        request.params.get("content", "")
                    )
                elif request.method == "run_cmd":
                    result = await self.command_handler.run_command(
                        request.params.get("command", ""),
                        request.params.get("cwd"),
                        request.params.get("timeout", 30)
                    )
                elif request.method == "list_files":
                    result = await self.file_handler.list_files(
                        request.params.get("path", ".")
                    )
                elif request.method == "create_directory":
                    result = await self.file_handler.create_directory(
                        request.params.get("path", "")
                    )
                else:
                    raise ValueError(f"Unknown method: {request.method}")
                
                return MCPResponse(result=result, id=request.id)
                
            except Exception as e:
                self.logger.error(f"Error handling {request.method}: {str(e)}")
                return MCPResponse(
                    error={"code": -1, "message": str(e)},
                    id=request.id
                )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "sandbox_root": str(self.sandbox_manager.root)}
        
        @self.app.get("/methods")
        async def list_methods():
            """List available MCP methods."""
            return {
                "methods": [
                    "read_file",
                    "write_file", 
                    "run_cmd",
                    "list_files",
                    "create_directory"
                ]
            }
    
    async def startup(self):
        """Initialize server components."""
        await self.sandbox_manager.initialize()
        self.logger.info(f"MCP Server started with sandbox: {self.sandbox_manager.root}")
    
    async def shutdown(self):
        """Cleanup server components."""
        await self.sandbox_manager.cleanup()
        self.logger.info("MCP Server shutdown")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    server = MCPServer()
    
    @server.app.on_event("startup")
    async def startup_event():
        await server.startup()
    
    @server.app.on_event("shutdown") 
    async def shutdown_event():
        await server.shutdown()
    
    return server.app


def main():
    """Main entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LANS MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--sandbox-root", default="/tmp/agentros_sandbox", 
                       help="Sandbox root directory")
    
    args = parser.parse_args()
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
