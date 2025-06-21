"""
Simple AgentOS Implementation using SQLite
-----------------------------------------
A lightweight AIL processing system that doesn't require Docker
"""

import asyncio
import json
import os
import sqlite3
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

class AILOperation(Enum):
    """AIL Operations supported by the simple AgentOS"""
    QUERY = "QUERY"
    EXECUTE = "EXECUTE"
    PLAN = "PLAN"
    COMMUNICATE = "COMMUNICATE"
    RETRIEVE = "RETRIEVE"
    STORE = "STORE"

class SimpleAgentOS:
    """
    Lightweight AgentOS implementation using SQLite for persistence
    Supports core AIL operations without external dependencies
    """
    
    def __init__(self, db_path: str = None):
        """Initialize the simple AgentOS with SQLite backend"""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "simple_agentos.db")
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cognitions (
            id TEXT PRIMARY KEY,
            operation TEXT,
            arguments TEXT,
            timestamp REAL,
            result TEXT,
            success INTEGER
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id TEXT PRIMARY KEY,
            agent_id TEXT,
            content TEXT,
            context TEXT,
            importance REAL,
            timestamp REAL,
            memory_type TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
    async def process_cognition(self, ail_instruction: str) -> Dict[str, Any]:
        """Process an AIL instruction"""
        start_time = time.time()
        cognition_id = f"cog_{int(time.time()*1000)}"
        
        try:
            # Parse the AIL instruction
            operation, arguments = self._parse_ail(ail_instruction)
            
            # Execute based on operation
            if operation == AILOperation.QUERY:
                result = await self._handle_query(arguments)
            elif operation == AILOperation.EXECUTE:
                result = await self._handle_execute(arguments)
            elif operation == AILOperation.PLAN:
                result = await self._handle_plan(arguments)
            elif operation == AILOperation.COMMUNICATE:
                result = await self._handle_communicate(arguments)
            elif operation == AILOperation.RETRIEVE:
                result = await self._handle_retrieve(arguments)
            elif operation == AILOperation.STORE:
                result = await self._handle_store(arguments)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            success = True
            
        except Exception as e:
            result = {"error": str(e)}
            success = False
            
        # Store the cognition in the database
        self._store_cognition(cognition_id, operation, arguments, result, success)
        
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "success": success,
            "result": result,
            "execution_time_ms": execution_time,
            "operation_type": str(operation.value) if isinstance(operation, AILOperation) else str(operation),
            "cognition_id": cognition_id
        }
    
    def _parse_ail(self, ail_instruction: str):
        """Parse an AIL instruction into operation and arguments"""
        # Basic parsing for common AIL format (OPERATION [arg1, arg2, ...])
        ail_instruction = ail_instruction.strip()
        
        if not (ail_instruction.startswith('(') and ail_instruction.endswith(')')):
            raise ValueError("AIL must be enclosed in parentheses")
            
        # Extract content inside parentheses
        content = ail_instruction[1:-1].strip()
        
        # Split into operation and arguments
        parts = content.split(' ', 1)
        if len(parts) < 1:
            raise ValueError("Invalid AIL instruction format")
            
        operation_str = parts[0]
        arguments_str = parts[1] if len(parts) > 1 else ""
        
        # Convert operation to enum
        try:
            operation = AILOperation(operation_str)
        except ValueError:
            raise ValueError(f"Unsupported AIL operation: {operation_str}")
        
        # Parse arguments (simplified)
        try:
            # Handle basic JSON-like arguments
            arguments_str = arguments_str.strip()
            if arguments_str.startswith('[') and arguments_str.endswith(']'):
                arguments = json.loads(arguments_str)
            else:
                arguments = [arguments_str]
        except json.JSONDecodeError:
            # Fallback to string argument
            arguments = [arguments_str]
            
        return operation, arguments
        
    def _store_cognition(self, cognition_id, operation, arguments, result, success):
        """Store a processed cognition in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO cognitions VALUES (?, ?, ?, ?, ?, ?)",
            (
                cognition_id,
                str(operation.value) if isinstance(operation, AILOperation) else str(operation),
                json.dumps(arguments),
                time.time(),
                json.dumps(result),
                1 if success else 0
            )
        )
        
        conn.commit()
        conn.close()
    
    async def store_memory(self, agent_id: str, content: str, context: Dict[str, Any], 
                           importance: float = 0.5, memory_type: str = "episodic"):
        """Store a memory in the database"""
        memory_id = f"mem_{int(time.time()*1000)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO memory VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                memory_id,
                agent_id,
                content,
                json.dumps(context),
                importance,
                time.time(),
                memory_type
            )
        )
        
        conn.commit()
        conn.close()
        
        return {"id": memory_id, "success": True}
        
    async def retrieve_memory(self, query: str, memory_type: str = None, limit: int = 5):
        """Retrieve memories matching the query"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute(
                "SELECT * FROM memory WHERE memory_type = ? ORDER BY importance DESC, timestamp DESC LIMIT ?",
                (memory_type, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM memory ORDER BY importance DESC, timestamp DESC LIMIT ?",
                (limit,)
            )
            
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memories.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "content": row["content"],
                "context": json.loads(row["context"]),
                "importance": row["importance"],
                "timestamp": row["timestamp"],
                "memory_type": row["memory_type"]
            })
            
        return memories
    
    # AIL Operation Handlers
    
    async def _handle_query(self, arguments: List):
        """Handle QUERY operation"""
        if not arguments:
            raise ValueError("QUERY requires at least one argument")
            
        query = arguments[0] if isinstance(arguments[0], str) else json.dumps(arguments[0])
        
        # Simple mock query response
        return {
            "query": query,
            "result": f"Processed query: {query}",
            "timestamp": time.time()
        }
    
    async def _handle_execute(self, arguments: List):
        """Handle EXECUTE operation"""
        if len(arguments) < 2:
            raise ValueError("EXECUTE requires tool and parameters")
            
        tool = arguments[0]
        params = arguments[1]
        
        if tool == "shell":
            # Execute shell command (with safety checks)
            if isinstance(params, list) and len(params) > 0:
                command = params[0]
                if self._is_safe_command(command):
                    # Execute the command
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    return {
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                        "exit_code": process.returncode
                    }
                else:
                    raise ValueError(f"Unsafe command: {command}")
            else:
                raise ValueError("Invalid shell parameters")
        else:
            # Mock response for other tools
            return {
                "tool": tool,
                "params": params,
                "message": f"Executed {tool} with parameters {params}"
            }
    
    async def _handle_plan(self, arguments: List):
        """Handle PLAN operation"""
        if not arguments:
            raise ValueError("PLAN requires arguments")
            
        # Mock response for plan
        return {
            "plan": arguments,
            "status": "created"
        }
    
    async def _handle_communicate(self, arguments: List):
        """Handle COMMUNICATE operation"""
        if len(arguments) < 2:
            raise ValueError("COMMUNICATE requires recipient and message")
            
        recipient = arguments[0]
        message = arguments[1]
        
        # Mock communication
        return {
            "recipient": recipient,
            "message": message,
            "status": "delivered"
        }
    
    async def _handle_retrieve(self, arguments: List):
        """Handle RETRIEVE operation"""
        if not arguments:
            raise ValueError("RETRIEVE requires arguments")
            
        # Get memory type and query
        memory_type = arguments[0] if len(arguments) > 0 else None
        query = arguments[1] if len(arguments) > 1 else ""
        
        # Actually retrieve from the database
        memories = await self.retrieve_memory(query, memory_type)
        
        return {
            "memories": memories,
            "count": len(memories)
        }
    
    async def _handle_store(self, arguments: List):
        """Handle STORE operation"""
        if len(arguments) < 3:
            raise ValueError("STORE requires agent_id, content, and context")
            
        agent_id = arguments[0]
        content = arguments[1]
        context = arguments[2]
        importance = arguments[3] if len(arguments) > 3 else 0.5
        memory_type = arguments[4] if len(arguments) > 4 else "episodic"
        
        # Actually store in the database
        result = await self.store_memory(agent_id, content, context, importance, memory_type)
        
        return result
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute"""
        # Very basic security - only allow certain commands
        # In production, use a more sophisticated sandbox
        allowed_commands = [
            "echo", "mkdir", "ls", "pwd", "cat", "touch", "find"
        ]
        
        command_parts = command.split()
        if not command_parts:
            return False
            
        base_command = command_parts[0]
        return base_command in allowed_commands

class SimpleGMCPClient:
    """
    Simple GMCP client implementation using SQLite
    Provides memory storage/retrieval compatible with the full GMCP system
    """
    
    def __init__(self, agent_os: SimpleAgentOS, agent_id: str = None):
        """Initialize the GMCP client"""
        self.agent_os = agent_os
        self.agent_id = agent_id or f"agent_{int(time.time())}"
        
    async def store_episodic_memory(self, content: str, context: Dict[str, Any], 
                                   importance_score: float = 0.5, memory_type: str = "episodic"):
        """Store an episodic memory"""
        return await self.agent_os.store_memory(
            self.agent_id, content, context, importance_score, memory_type
        )
        
    async def store_semantic_memory(self, content: str, context: Dict[str, Any],
                                   importance_score: float = 0.5):
        """Store a semantic memory"""
        return await self.agent_os.store_memory(
            self.agent_id, content, context, importance_score, "semantic"
        )
        
    async def retrieve_memories(self, query: str, memory_type: str = None, limit: int = 5):
        """Retrieve memories matching the query"""
        return await self.agent_os.retrieve_memory(query, memory_type, limit)
        
    async def execute_ail(self, ail_instruction: str) -> Dict[str, Any]:
        """Execute an AIL instruction directly"""
        return await self.agent_os.process_cognition(ail_instruction)
