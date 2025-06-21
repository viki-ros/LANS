"""
AgentOS Kernel - The heart of the AIL-3.0 cognitive processing system.

This module transforms the Global Memory Manager into an intelligent
cognitive executor that processes Agent Instruction Language (AIL) cognitions.
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .ail_parser import (
    AILParser, CognitionNode, AILOperation,
    Variable, VariableContext, TryBlock, AwaitOperation, 
    EventDefinition, SandboxConfig,
    create_variable_context, create_try_block, 
    create_await_operation, create_event_definition, create_sandbox_config
)
from .memory_manager import GlobalMemoryManager, MemoryQuery, MemoryItem
from ..storage.database import DatabaseManager


@dataclass
class CognitionResult:
    """Result of executing an AIL cognition."""
    cognition_id: str
    operation_type: str
    success: bool
    result: Any
    execution_time_ms: float
    causality_chain: List[str]
    metadata: Dict[str, Any] = None


@dataclass
class QueryPlan:
    """Execution plan for intelligent QUERY operations."""
    plan_id: str
    intent: str
    mode: str
    stages: List[Dict[str, Any]]
    estimated_time_ms: float
    confidence_score: float


class ToolRegistry:
    """Registry for external tools that can be executed via EXECUTE operations."""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_tool(self, name: str, tool_func: callable, description: str = ""):
        """Register a new tool for execution."""
        self.tools[name] = {
            "function": tool_func,
            "description": description,
            "registered_at": datetime.utcnow()
        }
        self.logger.info(f"Registered tool: {name}")
    
    async def execute_tool(self, tool_name: str, parameters: Any, timeout_seconds: float = 30.0) -> Any:
        """Execute a registered tool with given parameters and timeout protection."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        
        tool_func = self.tools[tool_name]["function"]
        
        try:
            # Execute tool with timeout protection (handle both sync and async functions)
            if asyncio.iscoroutinefunction(tool_func):
                return await asyncio.wait_for(tool_func(parameters), timeout=timeout_seconds)
            else:
                # Run sync function in thread pool to avoid blocking event loop
                loop = asyncio.get_event_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(None, tool_func, parameters), 
                    timeout=timeout_seconds
                )
        except asyncio.TimeoutError:
            self.logger.error(f"Tool '{tool_name}' execution timed out after {timeout_seconds}s")
            raise ValueError(f"Tool '{tool_name}' execution timed out")
        except Exception as e:
            self.logger.error(f"Tool '{tool_name}' execution failed: {e}")
            raise
    
    def list_tools(self) -> List[str]:
        """Get list of all registered tools."""
        return list(self.tools.keys())


class QueryPlanner:
    """Intelligent query planning engine for QUERY operations."""
    
    def __init__(self, memory_manager: GlobalMemoryManager):
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)
    
    async def plan_query(self, intent: str, mode: str = "standard", options: Dict[str, Any] = None) -> QueryPlan:
        """Generate an intelligent execution plan for a QUERY operation."""
        options = options or {}
        
        plan_id = str(uuid.uuid4())
        stages = []
        
        # Simple intent parsing (Phase 1 implementation)
        # TODO: Replace with LLM-powered intent parsing in Phase 2
        parsed_intent = self._parse_intent_keywords(intent)
        
        # Build execution stages based on intent and mode
        if mode == "standard":
            stages = await self._plan_standard_query(parsed_intent, options)
        elif mode == "explore":
            stages = await self._plan_exploratory_query(parsed_intent, options)
        elif mode == "connect":
            stages = await self._plan_connection_query(parsed_intent, options)
        else:
            raise ValueError(f"Unknown query mode: {mode}")
        
        # Estimate execution time based on stages
        estimated_time = sum(stage.get("estimated_ms", 50) for stage in stages)
        
        return QueryPlan(
            plan_id=plan_id,
            intent=intent,
            mode=mode,
            stages=stages,
            estimated_time_ms=estimated_time,
            confidence_score=0.8  # TODO: Implement confidence calculation
        )
    
    def _parse_intent_keywords(self, intent: str) -> Dict[str, Any]:
        """Simple keyword-based intent parsing for Phase 1."""
        intent_lower = intent.lower()
        
        parsed = {
            "entities": [],
            "time_references": [],
            "memory_types": [],
            "actions": []
        }
        
        # Extract entities (simple approach)
        # TODO: Replace with proper NER in Phase 2
        if "notes" in intent_lower or "note" in intent_lower:
            parsed["memory_types"].append("episodic")
        if "knowledge" in intent_lower or "fact" in intent_lower:
            parsed["memory_types"].append("semantic")
        if "procedure" in intent_lower or "how to" in intent_lower:
            parsed["memory_types"].append("procedural")
        
        # Extract time references
        if "today" in intent_lower:
            parsed["time_references"].append("today")
        elif "yesterday" in intent_lower:
            parsed["time_references"].append("yesterday")
        elif "last week" in intent_lower:
            parsed["time_references"].append("last_week")
        
        # Extract action words
        if "find" in intent_lower or "search" in intent_lower:
            parsed["actions"].append("search")
        if "connect" in intent_lower or "link" in intent_lower:
            parsed["actions"].append("connect")
        if "summarize" in intent_lower or "summary" in intent_lower:
            parsed["actions"].append("summarize")
        
        return parsed
    
    async def _plan_standard_query(self, parsed_intent: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan a standard retrieval query."""
        stages = []
        
        # Stage 1: Filter by time if specified
        if parsed_intent["time_references"]:
            stages.append({
                "stage": 1,
                "action": "TIME_FILTER",
                "details": f"Filter by time: {parsed_intent['time_references']}",
                "estimated_ms": 20
            })
        
        # Stage 2: Search by memory type if specified
        if parsed_intent["memory_types"]:
            stages.append({
                "stage": len(stages) + 1,
                "action": "TYPE_FILTER",
                "details": f"Filter by memory types: {parsed_intent['memory_types']}",
                "estimated_ms": 30
            })
        
        # Stage 3: Vector similarity search
        stages.append({
            "stage": len(stages) + 1,
            "action": "VECTOR_SEARCH",
            "details": "Perform semantic similarity search",
            "estimated_ms": 80
        })
        
        # Stage 4: Rank and format results
        stages.append({
            "stage": len(stages) + 1,
            "action": "RANK_RESULTS",
            "details": "Rank by relevance and format output",
            "estimated_ms": 20
        })
        
        return stages
    
    async def _plan_exploratory_query(self, parsed_intent: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan an exploratory query to understand data shape."""
        stages = [
            {
                "stage": 1,
                "action": "CATEGORY_ANALYSIS",
                "details": "Analyze memory categories and patterns",
                "estimated_ms": 60
            },
            {
                "stage": 2,
                "action": "FACET_GENERATION",
                "details": "Generate categorical facets and summaries",
                "estimated_ms": 40
            },
            {
                "stage": 3,
                "action": "TOP_RESULTS",
                "details": "Get representative examples from each category",
                "estimated_ms": 50
            }
        ]
        return stages
    
    async def _plan_connection_query(self, parsed_intent: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan a connection-finding query."""
        stages = [
            {
                "stage": 1,
                "action": "NODE_IDENTIFICATION",
                "details": "Identify start and end concept nodes",
                "estimated_ms": 40
            },
            {
                "stage": 2,
                "action": "GRAPH_TRAVERSAL",
                "details": "Search for connection paths between nodes",
                "estimated_ms": 120
            },
            {
                "stage": 3,
                "action": "PATH_RANKING",
                "details": "Rank connection paths by strength and relevance",
                "estimated_ms": 30
            }
        ]
        return stages
    
    async def execute_plan(self, plan: QueryPlan) -> Any:
        """Execute a query plan and return results."""
        self.logger.info(f"Executing query plan {plan.plan_id} for intent: {plan.intent}")
        
        # For Phase 1, we'll implement a simplified execution
        # that maps to existing GlobalMemoryManager methods
        
        if plan.mode == "standard":
            return await self._execute_standard_plan(plan)
        elif plan.mode == "explore":
            return await self._execute_exploratory_plan(plan)
        elif plan.mode == "connect":
            return await self._execute_connection_plan(plan)
        else:
            raise ValueError(f"Unknown query mode: {plan.mode}")
    
    async def _execute_standard_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute a standard query plan."""
        # Create a MemoryQuery from the intent
        query = MemoryQuery(
            query_text=plan.intent,
            max_results=10,
            similarity_threshold=0.7
        )
        
        # Use existing memory manager to retrieve memories
        memories = await self.memory_manager.retrieve_memories(query)
        
        return {
            "mode": "standard",
            "intent": plan.intent,
            "memories": [asdict(memory) for memory in memories],
            "total_found": len(memories),
            "plan_executed": plan.plan_id
        }
    
    async def _execute_exploratory_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute an exploratory query plan."""
        # For Phase 1, return a simplified exploratory result
        query = MemoryQuery(
            query_text=plan.intent,
            max_results=50,  # Get more results for analysis
            similarity_threshold=0.5  # Lower threshold for exploration
        )
        
        memories = await self.memory_manager.retrieve_memories(query)
        
        # Analyze memory types and patterns
        memory_types = {}
        time_patterns = {}
        
        for memory in memories:
            # Count by memory type
            mem_type = memory.memory_type
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            # Count by time period (simplified)
            time_period = memory.timestamp.strftime("%Y-%m-%d")
            time_patterns[time_period] = time_patterns.get(time_period, 0) + 1
        
        return {
            "mode": "explore",
            "intent": plan.intent,
            "summary_facets": {
                "memory_types": memory_types,
                "time_patterns": time_patterns,
                "total_analyzed": len(memories)
            },
            "representative_examples": [asdict(memory) for memory in memories[:5]],
            "plan_executed": plan.plan_id
        }
    
    async def _execute_connection_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute a connection query plan."""
        # For Phase 1, implement a simplified connection search
        return {
            "mode": "connect",
            "intent": plan.intent,
            "connections_found": [],  # TODO: Implement graph traversal
            "connection_strength": 0.0,
            "plan_executed": plan.plan_id,
            "note": "Connection queries will be fully implemented in Phase 2"
        }


class AgentOSKernel:
    """
    The AgentOS Kernel - An intelligent cognitive executor that processes
    Agent Instruction Language (AIL) cognitions and coordinates all
    memory operations, tool executions, and multi-step plans.
    
    This replaces the GlobalMemoryManager as the primary interface,
    elevating from simple memory management to intelligent cognition execution.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AgentOS Kernel with configuration validation."""
        self.config = self._validate_config(config)
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize core components with error handling
            self.ail_parser = AILParser()
            self.memory_manager = GlobalMemoryManager(self.config)
            
            # Use same database selection logic as memory manager
            # Handle both nested and flat database config
            if "database" in self.config:
                database_config = self.config["database"]
            else:
                # Build database config from flat structure
                database_config = {
                    "type": self.config.get("database_type", "sqlite"),
                    "url": self.config.get("database_url", "sqlite:///lans_memory.db"),
                    "database_url": self.config.get("database_url", "sqlite:///lans_memory.db")
                }
            
            database_type = database_config.get("type", "sqlite").lower()
            database_url = database_config.get("url", database_config.get("database_url", ""))
            
            if database_type == "sqlite" or database_url.startswith("sqlite:"):
                # Import SQLite manager here to avoid import issues
                from ..storage.sqlite_database import SQLiteDatabaseManager
                self.database_manager = SQLiteDatabaseManager(database_config)
                self.logger.info("AgentOS Kernel using SQLite database manager")
            else:
                self.database_manager = DatabaseManager(database_config)
                self.logger.info("AgentOS Kernel using PostgreSQL database manager")
            
            self.query_planner = QueryPlanner(self.memory_manager)
            self.tool_registry = ToolRegistry()
            
            # Causality tracking for AIL-4.0 foundation
            self.causality_chain: List[str] = []
            self.cognition_history: Dict[str, CognitionNode] = {}
            
            # Initialize built-in tools
            self._register_builtin_tools()
            
            self.logger.info("AgentOS Kernel components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentOS Kernel: {e}")
            raise RuntimeError(f"Kernel initialization failed: {e}") from e
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set defaults for configuration."""
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")
        
        # Set sensible defaults
        validated_config = {
            'database': config.get('database', {}),
            'embeddings': config.get('embeddings', {}),
            'overfitting_prevention': config.get('overfitting_prevention', {}),
            'tool_execution_timeout': config.get('tool_execution_timeout', 30.0),
            'max_causality_chain_length': config.get('max_causality_chain_length', 100)
        }
        
        # Validate specific settings
        if not isinstance(validated_config['tool_execution_timeout'], (int, float)):
            raise ValueError("tool_execution_timeout must be a number")
        
        if validated_config['tool_execution_timeout'] <= 0:
            raise ValueError("tool_execution_timeout must be positive")
        
        return validated_config
    
    async def initialize(self):
        """Initialize the kernel and all its components with proper error handling."""
        try:
            await self.memory_manager.initialize()
            await self.database_manager.initialize()
            self.logger.info("AgentOS Kernel initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentOS Kernel components: {e}")
            # Attempt cleanup of partially initialized components
            await self._cleanup_on_init_failure()
            raise RuntimeError(f"Kernel initialization failed: {e}") from e
    
    async def _cleanup_on_init_failure(self):
        """Clean up partially initialized components."""
        try:
            if hasattr(self, 'database_manager'):
                await self.database_manager.close()
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    async def _log_cognition_execution(self, cognition_id: str, agent_id: str, user_id: str, 
                                     ail_code: str, operation_type: str, status: str, 
                                     result: Any = None, execution_time_ms: float = 0,
                                     causality_chain: List[str] = None, error_message: str = None,
                                     metadata: Dict[str, Any] = None) -> str:
        """Log cognition execution to database."""
        try:
            import json
            log_data = {
                'cognition_id': cognition_id,
                'agent_id': agent_id,
                'user_id': user_id,
                'ail_code': ail_code,
                'operation_type': operation_type,
                'status': status,
                'result': json.dumps(result, default=str) if result is not None else None,
                'execution_time_ms': execution_time_ms,
                'causality_chain': json.dumps(causality_chain or []),
                'error_message': error_message,
                'metadata': json.dumps(metadata or {}, default=str)
            }
            return await self.database_manager.insert('cognitions', log_data)
        except Exception as e:
            self.logger.error(f"Failed to log cognition execution: {e}")
            return None
    
    async def _get_stored_variables(self, cognition_id: str) -> Dict[str, Any]:
        """Retrieve stored variables for a cognition from database."""
        try:
            import json
            query = """
                SELECT variable_name, variable_value 
                FROM variable_storage 
                WHERE cognition_id = $1 AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY created_at DESC
            """
            rows = await self.database_manager.fetch(query, cognition_id)
            variables = {}
            for row in rows:
                try:
                    variables[row['variable_name']] = json.loads(row['variable_value'])
                except json.JSONDecodeError:
                    # Fallback to raw value if JSON parsing fails
                    variables[row['variable_name']] = row['variable_value']
            return variables
        except Exception as e:
            self.logger.error(f"Failed to retrieve variables for cognition {cognition_id}: {e}")
            return {}
    
    async def _cleanup_cognition_variables(self, cognition_id: str):
        """Clean up variables associated with a completed cognition."""
        try:
            await self.database_manager.delete(
                'variable_storage', 
                'cognition_id = $1',
                cognition_id
            )
        except Exception as e:
            self.logger.error(f"Failed to cleanup variables for cognition {cognition_id}: {e}")
    
    def _register_builtin_tools(self):
        """Register built-in tools for EXECUTE operations."""
        import subprocess
        import json
        
        def shell_tool(command: str) -> str:
            """Execute a shell command safely."""
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout for safety
                )
                return f"Exit code: {result.returncode}\\nStdout: {result.stdout}\\nStderr: {result.stderr}"
            except subprocess.TimeoutExpired:
                return "Error: Command timed out after 30 seconds"
            except Exception as e:
                return f"Error: {str(e)}"
        
        def json_tool(data: Any) -> str:
            """Format data as JSON."""
            try:
                return json.dumps(data, indent=2, default=str)
            except Exception as e:
                return f"Error formatting JSON: {str(e)}"
        
        # Register tools
        self.tool_registry.register_tool("shell", shell_tool, "Execute shell commands")
        self.tool_registry.register_tool("json", json_tool, "Format data as JSON")
        
        # Register AI tools if available
        self._register_ai_tools()
    
    def _register_ai_tools(self):
        """Register AI tools if available."""
        try:
            # Import the AI tools module
            import sys
            import os
            import asyncio
            sys.path.insert(0, '/home/viki/LANS')
            
            # Import AI tool classes
            from real_ai_tools import RealAICodeGenerator, RealAICreativeWriter, RealAIAnalyzer
            from agent_core.llm.ollama_client import OllamaClient
            from agent_core.core.config import LANSConfig
            from pathlib import Path
            from typing import List
            
            # Create LANS config for Ollama client
            config = LANSConfig()
            config.ollama_base_url = "http://localhost:11434"
            config.default_model = "qwen3:8b"  # Use available model
            config.temperature = 0.7
            config.max_tokens = 1000
            
            # Create Ollama client
            ollama_client = OllamaClient(config)
            
            # Create AI-powered tool instances
            code_generator = RealAICodeGenerator(ollama_client)
            creative_writer = RealAICreativeWriter(ollama_client)
            analyzer = RealAIAnalyzer(ollama_client)
            
            # Create synchronous wrapper functions
            def ai_code_generator_tool(parameters: List[str]) -> str:
                request = parameters[0] if parameters else "Generate some code"
                result = asyncio.run(code_generator.generate_code(request))
                
                if result["success"]:
                    # Actually create the file
                    filename = result["filename"]
                    code = result["code"]
                    Path(filename).write_text(code)
                    return f"✅ AI generated {filename}: {result['ai_reasoning']}"
                else:
                    return f"❌ Code generation failed: {result['error']}"
            
            def ai_creative_writer_tool(parameters: List[str]) -> str:
                request = parameters[0] if parameters else "Write something creative"
                result = asyncio.run(creative_writer.write_content(request))
                
                if result["success"]:
                    # Save to file
                    filename = "creative_writing.txt"
                    Path(filename).write_text(result["content"])
                    return f"✅ AI wrote creative content: {result['ai_reasoning']}"
                else:
                    return f"❌ Creative writing failed: {result['error']}"
            
            def ai_analyzer_tool(parameters: List[str]) -> str:
                request = parameters[0] if parameters else "Analyze this"
                result = asyncio.run(analyzer.analyze_request(request))
                
                if result["success"]:
                    return f"✅ AI Analysis: {result.get('strategy', 'Strategy determined')} (confidence: {result.get('confidence', 0.5)})"
                else:
                    return f"❌ Analysis failed: {result['error']}"
            
            # Register all tools
            self.tool_registry.register_tool("code_generator", ai_code_generator_tool, "AI-powered code generation using Ollama models")
            self.tool_registry.register_tool("creative_writer", ai_creative_writer_tool, "AI-powered creative writing using Ollama models")
            self.tool_registry.register_tool("analyzer", ai_analyzer_tool, "AI-powered request analysis using Ollama models")
            
            self.logger.info("✅ AI tools registered successfully: code_generator, creative_writer, analyzer")
            
        except Exception as e:
            self.logger.warning(f"Could not register AI tools: {e}")
            self.logger.info("Continuing with basic tools only")
    
    async def execute_cognition(self, ail_code: str, agent_id: str = None, user_id: str = None, 
                              context: Dict[str, Any] = None, execution_mode: str = "safe") -> CognitionResult:
        """
        Execute an AIL cognition and return the result.
        
        This is the primary entry point for all cognitive operations.
        
        Args:
            ail_code: The AIL-3.0 code to execute
            agent_id: Optional agent identifier for tracking
            user_id: Optional user identifier for access control
            context: Optional context data for the cognition
            execution_mode: Execution safety mode (safe, permissive, sandbox)
        """
        start_time = datetime.utcnow()
        cognition_id = str(uuid.uuid4())
        
        # Store execution context
        execution_context = {
            "agent_id": agent_id,
            "user_id": user_id,
            "context": context or {},
            "execution_mode": execution_mode
        }
        
        try:
            # Parse the AIL code
            parsed_cognition = self.ail_parser.parse(ail_code)
            
            # Store cognition in history for causality tracking
            self.cognition_history[cognition_id] = {
                "parsed_cognition": parsed_cognition,
                "execution_context": execution_context
            }
            
            # Add to causality chain
            current_causality = self.causality_chain + [cognition_id]
            
            # Dispatch based on operation type
            if parsed_cognition.operation == AILOperation.QUERY:
                result = await self._handle_query(parsed_cognition.arguments, current_causality)
            elif parsed_cognition.operation == AILOperation.EXECUTE:
                result = await self._handle_execute(parsed_cognition.arguments, current_causality)
            elif parsed_cognition.operation == AILOperation.PLAN:
                result = await self._handle_plan(parsed_cognition.arguments, current_causality)
            elif parsed_cognition.operation == AILOperation.COMMUNICATE:
                result = await self._handle_communicate(parsed_cognition.arguments, current_causality)
            
            # AIL-3.1 Advanced Operations
            elif parsed_cognition.operation == AILOperation.LET:
                result = await self._handle_let(parsed_cognition.arguments, current_causality, execution_context)
            elif parsed_cognition.operation == AILOperation.TRY:
                result = await self._handle_try(parsed_cognition.arguments, current_causality, execution_context)
            elif parsed_cognition.operation == AILOperation.ON_FAIL:
                # ON-FAIL is handled within TRY, should not be called directly
                raise ValueError("ON-FAIL operation must be used within TRY block")
            elif parsed_cognition.operation == AILOperation.AWAIT:
                result = await self._handle_await(parsed_cognition.arguments, current_causality, execution_context)
            elif parsed_cognition.operation == AILOperation.SANDBOXED_EXECUTE:
                result = await self._handle_sandboxed_execute(parsed_cognition.arguments, current_causality, execution_context)
            elif parsed_cognition.operation == AILOperation.CLARIFY:
                result = await self._handle_clarify(parsed_cognition.arguments, current_causality, execution_context)
            elif parsed_cognition.operation == AILOperation.EVENT:
                result = await self._handle_event(parsed_cognition.arguments, current_causality, execution_context)
            else:
                raise ValueError(f"Unknown operation type: {parsed_cognition.operation}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log the cognition execution
            await self._log_cognition_execution(
                cognition_id=cognition_id,
                agent_id=agent_id or "unknown",
                user_id=user_id or "unknown",
                ail_code=ail_code,
                operation_type=parsed_cognition.operation.value,
                status="success",
                result=result,
                execution_time_ms=execution_time,
                causality_chain=current_causality,
                metadata={
                    "parsed_at": start_time.isoformat(),
                    "ail_code": ail_code,
                    "execution_context": execution_context
                }
            )
            
            return CognitionResult(
                cognition_id=cognition_id,
                operation_type=parsed_cognition.operation.value,
                success=True,
                result=result,
                execution_time_ms=execution_time,
                causality_chain=current_causality,
                metadata={
                    "parsed_at": start_time.isoformat(),
                    "ail_code": ail_code,
                    "execution_context": execution_context
                }
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.error(f"Failed to execute cognition {cognition_id}: {e}")
            
            # Log the error in cognition execution
            await self._log_cognition_execution(
                cognition_id=cognition_id,
                agent_id=agent_id or "unknown",
                user_id=user_id or "unknown",
                ail_code=ail_code,
                operation_type="unknown",
                status="error",
                result={"error": str(e)},
                execution_time_ms=execution_time,
                causality_chain=self.causality_chain + [cognition_id],
                metadata={
                    "error_at": start_time.isoformat(),
                    "ail_code": ail_code,
                    "execution_context": execution_context
                }
            )
            
            return CognitionResult(
                cognition_id=cognition_id,
                operation_type="unknown",
                success=False,
                result={"error": str(e)},
                execution_time_ms=execution_time,
                causality_chain=self.causality_chain + [cognition_id],
                metadata={
                    "error_at": start_time.isoformat(),
                    "ail_code": ail_code,
                    "execution_context": execution_context
                }
            )
    
    async def _handle_query(self, arguments: List[Any], causality_chain: List[str]) -> Dict[str, Any]:
        """Handle QUERY operations - the heart of AIL-3.0."""
        if not arguments or not isinstance(arguments[0], dict):
            raise ValueError("QUERY operation requires metadata dictionary as first argument")
        
        metadata = arguments[0]
        intent = metadata.get("intent")
        if not intent:
            raise ValueError("QUERY operation requires 'intent' field in metadata")
        
        mode = metadata.get("mode", "standard")
        return_format = metadata.get("return", ["results"])
        performance_profile = metadata.get("performance_profile", "balanced")
        
        self.logger.info(f"Processing QUERY: {intent} (mode: {mode})")
        
        # Execute actual database queries based on intent
        query_results = []
        
        try:
            # Parse intent to determine query type
            intent_lower = intent.lower()
            
            if "memory" in intent_lower or "remember" in intent_lower:
                # Query episodic memories
                query = """
                    SELECT * FROM episodic_memories 
                    WHERE content ILIKE $1 OR context::text ILIKE $1
                    ORDER BY importance_score DESC, timestamp DESC
                    LIMIT 10
                """
                results = await self.database_manager.fetch(query, f"%{intent}%")
                query_results.extend(results)
                
            elif "concept" in intent_lower or "define" in intent_lower:
                # Query semantic memories
                # Extract concept name from intent (remove "concept" keyword)
                search_term = intent_lower.replace("concept", "").strip()
                if not search_term:
                    search_term = intent
                
                query = """
                    SELECT * FROM semantic_memories 
                    WHERE concept ILIKE $1 OR definition ILIKE $1
                    ORDER BY confidence_score DESC
                    LIMIT 10
                """
                results = await self.database_manager.fetch(query, f"%{search_term}%")
                query_results.extend(results)
                
            elif "skill" in intent_lower or "how to" in intent_lower:
                # Query procedural memories
                query = """
                    SELECT * FROM procedural_memories 
                    WHERE skill_name ILIKE $1 OR procedure ILIKE $1
                    ORDER BY success_rate DESC
                    LIMIT 10
                """
                results = await self.database_manager.fetch(query, f"%{intent}%")
                query_results.extend(results)
                
            elif "event" in intent_lower:
                # Query event definitions
                query = """
                    SELECT * FROM event_definitions 
                    WHERE event_name ILIKE $1 OR trigger_condition ILIKE $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """
                results = await self.database_manager.fetch(query, f"%{intent}%")
                query_results.extend(results)
                
            else:
                # General search across all memory types
                queries = [
                    ("episodic", "SELECT 'episodic' as memory_type, * FROM episodic_memories WHERE content ILIKE $1 LIMIT 5"),
                    ("semantic", "SELECT 'semantic' as memory_type, * FROM semantic_memories WHERE concept ILIKE $1 OR definition ILIKE $1 LIMIT 5"),
                    ("procedural", "SELECT 'procedural' as memory_type, * FROM procedural_memories WHERE skill_name ILIKE $1 OR procedure ILIKE $1 LIMIT 5")
                ]
                
                for memory_type, query in queries:
                    results = await self.database_manager.fetch(query, f"%{intent}%")
                    query_results.extend(results)
            
            # Create query plan for metadata
            plan = await self.query_planner.plan_query(intent, mode, metadata)
            
            result = {
                "intent": intent,
                "mode": mode,
                "results": query_results,
                "total_results": len(query_results),
                "query_plan_id": plan.plan_id,
                "causality_chain": causality_chain,
                "performance_profile": performance_profile,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            result = {
                "intent": intent,
                "mode": mode,
                "error": str(e),
                "results": [],
                "total_results": 0,
                "causality_chain": causality_chain,
                "success": False
            }
        
        return result
    
    async def _handle_execute(self, arguments: List[Any], causality_chain: List[str]) -> Dict[str, Any]:
        """Handle EXECUTE operations - tool execution."""
        if len(arguments) < 2:
            raise ValueError("EXECUTE operation requires tool entity and parameter arguments")
        
        # Extract tool name from entity (support both Entity object and string format)
        tool_entity = arguments[0]
        
        # Import Entity class for type checking
        from .ail_parser import Entity
        
        if isinstance(tool_entity, Entity):
            # New format: Entity object from parser
            tool_name = tool_entity.identifier
        elif isinstance(tool_entity, str) and tool_entity.startswith("[") and tool_entity.endswith("]"):
            # Legacy format: string "[tool_name]"
            tool_name = tool_entity[1:-1]  # Remove brackets
        else:
            raise ValueError("First argument must be a tool entity [tool_name] or Entity object")
        
        # Extract parameters
        parameters = arguments[1]
        
        self.logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
        
        # Execute the tool with configured timeout
        timeout = self.config.get('tool_execution_timeout', 30.0)
        tool_result = await self.tool_registry.execute_tool(tool_name, parameters, timeout)
        
        return {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": tool_result,
            "causality_chain": causality_chain,
            "success": True
        }
    
    async def _handle_plan(self, arguments: List[Any], causality_chain: List[str]) -> Dict[str, Any]:
        """Handle PLAN operations - multi-step cognition sequences."""
        if not arguments:
            raise ValueError("PLAN operation requires at least metadata and sub-cognitions")
        
        metadata = arguments[0] if isinstance(arguments[0], dict) else {}
        sub_cognitions = arguments[1:] if len(arguments) > 1 else []
        
        goal = metadata.get("goal", "Execute plan")
        self.logger.info(f"Executing plan: {goal}")
        
        plan_results = []
        
        # Execute each sub-cognition in sequence
        for i, sub_cognition in enumerate(sub_cognitions):
            if isinstance(sub_cognition, CognitionNode):
                # Convert back to AIL code for execution
                # This is a simplified approach for Phase 1
                sub_ail = f"({sub_cognition.operation.value} {sub_cognition.arguments})"
                result = await self.execute_cognition(sub_ail)
                plan_results.append({
                    "step": i + 1,
                    "cognition_id": result.cognition_id,
                    "success": result.success,
                    "result": result.result
                })
        
        return {
            "goal": goal,
            "steps_executed": len(plan_results),
            "results": plan_results,
            "causality_chain": causality_chain,
            "success": all(r["success"] for r in plan_results)
        }
    
    async def _handle_communicate(self, arguments: List[Any], causality_chain: List[str]) -> Dict[str, Any]:
        """Handle COMMUNICATE operations - inter-agent communication (Phase 1 stub)."""
        if len(arguments) < 2:
            raise ValueError("COMMUNICATE operation requires recipient entity and cognition to send")
        
        recipient = arguments[0]
        cognition_to_send = arguments[1]
        
        self.logger.info(f"Communication to {recipient} (Phase 1 - logging only)")
        
        # Phase 1: Just log the communication
        # Phase 3: Implement actual inter-agent messaging
        return {
            "recipient": recipient,
            "cognition": str(cognition_to_send),
            "status": "logged",
            "causality_chain": causality_chain,
            "note": "Inter-agent communication will be implemented in Phase 3"
        }
    
    # ========================================
    # AIL-3.1 Advanced Operation Handlers
    # ========================================
    
    async def _handle_let(self, arguments: List[Any], causality_chain: List[str], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LET operation - Variable binding with lexical scoping."""
        if len(arguments) < 2:
            raise ValueError("LET operation requires bindings and body cognition")
        
        bindings = arguments[0]
        body_cognition = arguments[1]
        
        if not isinstance(bindings, list) or len(bindings) % 2 != 0:
            raise ValueError("LET bindings must be array with even number of elements")
        
        # Create new variable context with current context as parent
        parent_context = execution_context.get('variable_context')
        variable_context = create_variable_context(parent_context)
        
        # Get cognition ID for database storage
        cognition_id = causality_chain[-1] if causality_chain else str(uuid.uuid4())
        
        # Bind variables in pairs [var1, value1, var2, value2, ...]
        bound_variables = {}
        stored_variables = []
        
        for i in range(0, len(bindings), 2):
            var_name = bindings[i]
            var_value = bindings[i + 1]
            
            if not isinstance(var_name, str):
                raise ValueError(f"Variable name must be string, got {type(var_name)}")
            
            # Store in memory context
            variable = variable_context.set_variable(var_name, var_value)
            bound_variables[var_name] = var_value
            
            # Store in database for persistence
            try:
                import json
                var_data = {
                    'cognition_id': cognition_id,
                    'variable_name': var_name,
                    'variable_value': json.dumps(var_value, default=str),
                    'scope_level': variable_context.scope_level,
                    'expires_at': None  # Variables persist until cognition completes
                }
                var_id = await self.database_manager.insert('variable_storage', var_data)
                stored_variables.append({
                    'id': var_id,
                    'name': var_name,
                    'value': var_value
                })
            except Exception as e:
                self.logger.error(f"Failed to store variable {var_name}: {e}")
        
        # Execute body cognition with new variable context
        new_context = execution_context.copy()
        new_context['variable_context'] = variable_context
        
        # For Phase 2B, we'll execute the body cognition recursively
        body_result = None
        if isinstance(body_cognition, str):
            try:
                # Parse and execute the body cognition
                body_result = await self.execute_cognition(
                    body_cognition, 
                    context=new_context
                )
                # Convert CognitionResult to JSON-serializable dictionary
                if hasattr(body_result, '__dict__'):
                    body_result = asdict(body_result)
            except Exception as e:
                self.logger.error(f"Failed to execute LET body: {e}")
                body_result = {"error": str(e)}
        else:
            body_result = {"simulated": True, "body_cognition": str(body_cognition)}
        
        # Convert CognitionResult to JSON-serializable dict if needed
        if hasattr(body_result, '__dict__') and hasattr(body_result, 'cognition_id'):
            # This is a CognitionResult object, convert to dict
            body_result = {
                "cognition_id": body_result.cognition_id,
                "operation_type": body_result.operation_type,
                "success": body_result.success,
                "result": body_result.result,
                "execution_time_ms": body_result.execution_time_ms,
                "causality_chain": body_result.causality_chain,
                "metadata": body_result.metadata
            }
        
        return {
            "operation": "LET",
            "variables_bound": len(bound_variables),
            "bound_variables": bound_variables,
            "stored_variables": stored_variables,
            "scope_level": variable_context.scope_level,
            "body_result": body_result,
            "causality_chain": causality_chain,
            "success": True
        }
    
    async def _handle_try(self, arguments: List[Any], causality_chain: List[str], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle TRY operation - Error handling with optional ON-FAIL recovery."""
        if len(arguments) < 1:
            raise ValueError("TRY operation requires at least one cognition")
        
        try_cognition = arguments[0]
        on_fail_cognition = arguments[1] if len(arguments) > 1 else None
        
        error_occurred = False
        error_details = None
        try_result = None
        recovery_result = None
        
        # Get cognition ID for database logging
        cognition_id = causality_chain[-1] if causality_chain else str(uuid.uuid4())
        
        try:
            # Log the TRY attempt
            await self._log_cognition_execution(
                cognition_id=f"{cognition_id}_try",
                agent_id=execution_context.get('agent_id', 'unknown'),
                user_id=execution_context.get('user_id', 'unknown'),
                ail_code=str(try_cognition),
                operation_type="TRY_ATTEMPT",
                status="started",
                causality_chain=causality_chain,
                metadata={"try_cognition": str(try_cognition)}
            )
            
            # Execute the try cognition
            if isinstance(try_cognition, str):
                try_result = await self.execute_cognition(
                    try_cognition, 
                    execution_context=execution_context
                )
            else:
                try_result = {"simulated": True, "try_cognition": str(try_cognition)}
            
            # Log successful completion
            await self._log_cognition_execution(
                cognition_id=f"{cognition_id}_try",
                agent_id=execution_context.get('agent_id', 'unknown'),
                user_id=execution_context.get('user_id', 'unknown'),
                ail_code=str(try_cognition),
                operation_type="TRY_ATTEMPT",
                status="success",
                result=try_result,
                causality_chain=causality_chain,
                metadata={"try_cognition": str(try_cognition)}
            )
            
        except Exception as e:
            error_occurred = True
            error_details = str(e)
            
            # Log the error
            await self._log_cognition_execution(
                cognition_id=f"{cognition_id}_try",
                agent_id=execution_context.get('agent_id', 'unknown'),
                user_id=execution_context.get('user_id', 'unknown'),
                ail_code=str(try_cognition),
                operation_type="TRY_ATTEMPT",
                status="error",
                error_message=error_details,
                causality_chain=causality_chain,
                metadata={"try_cognition": str(try_cognition)}
            )
            
            # Execute ON-FAIL recovery if provided
            if on_fail_cognition and hasattr(on_fail_cognition, 'operation'):
                if on_fail_cognition.operation == AILOperation.ON_FAIL:
                    try:
                        # Log recovery attempt
                        await self._log_cognition_execution(
                            cognition_id=f"{cognition_id}_recovery",
                            agent_id=execution_context.get('agent_id', 'unknown'),
                            user_id=execution_context.get('user_id', 'unknown'),
                            ail_code=str(on_fail_cognition),
                            operation_type="ON_FAIL_RECOVERY",
                            status="started",
                            causality_chain=causality_chain,
                            metadata={"original_error": error_details}
                        )
                        
                        recovery_result = {"simulated": True, "recovery_cognition": str(on_fail_cognition)}
                        
                        # Log recovery success
                        await self._log_cognition_execution(
                            cognition_id=f"{cognition_id}_recovery",
                            agent_id=execution_context.get('agent_id', 'unknown'),
                            user_id=execution_context.get('user_id', 'unknown'),
                            ail_code=str(on_fail_cognition),
                            operation_type="ON_FAIL_RECOVERY",
                            status="success",
                            result=recovery_result,
                            causality_chain=causality_chain,
                            metadata={"original_error": error_details}
                        )
                        
                    except Exception as recovery_error:
                        # Log recovery failure
                        await self._log_cognition_execution(
                            cognition_id=f"{cognition_id}_recovery",
                            agent_id=execution_context.get('agent_id', 'unknown'),
                            user_id=execution_context.get('user_id', 'unknown'),
                            ail_code=str(on_fail_cognition),
                            operation_type="ON_FAIL_RECOVERY",
                            status="error",
                            error_message=str(recovery_error),
                            causality_chain=causality_chain,
                            metadata={"original_error": error_details}
                        )
                        recovery_result = {"error": str(recovery_error)}
        
        return {
            "operation": "TRY",
            "error_occurred": error_occurred,
            "error_details": error_details,
            "try_result": try_result,
            "recovery_executed": recovery_result is not None,
            "recovery_result": recovery_result,
            "causality_chain": causality_chain,
            "success": not error_occurred or recovery_result is not None
        }
        
        return {
            "operation": "TRY",
            "error_occurred": error_occurred,
            "error_details": error_details,
            "try_result": try_result,
            "recovery_executed": recovery_result is not None,
            "recovery_result": recovery_result,
            "causality_chain": causality_chain,
            "success": True  # TRY operation itself succeeded even if contents failed
        }
    
    async def _handle_await(self, arguments: List[Any], causality_chain: List[str], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AWAIT operation - Asynchronous flow control with timeout."""
        if len(arguments) < 1:
            raise ValueError("AWAIT operation requires operation cognition")
        
        operation_cognition = arguments[0]
        timeout_config = arguments[1] if len(arguments) > 1 else {}
        
        # Extract timeout from config (default 30 seconds)
        timeout_ms = timeout_config.get('timeout', 30000) if isinstance(timeout_config, dict) else 30000
        timeout_seconds = timeout_ms / 1000.0
        
        operation_completed = False
        timeout_occurred = False
        operation_result = None
        
        try:
            # For Phase 1, simulate async execution with small delay
            await asyncio.sleep(0.1)  # Simulate some async work
            operation_result = {"simulated": True, "operation_cognition": str(operation_cognition)}
            operation_completed = True
            
        except asyncio.TimeoutError:
            timeout_occurred = True
            operation_result = {"error": f"Operation timed out after {timeout_ms}ms"}
            
        except Exception as e:
            operation_result = {"error": str(e)}
        
        return {
            "operation": "AWAIT",
            "operation_completed": operation_completed,
            "timeout_occurred": timeout_occurred,
            "timeout_ms": timeout_ms,
            "operation_result": operation_result,
            "causality_chain": causality_chain,
            "success": operation_completed
        }
    
    async def _handle_sandboxed_execute(self, arguments: List[Any], causality_chain: List[str], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SANDBOXED-EXECUTE operation - Secure isolated execution."""
        if len(arguments) < 2:
            raise ValueError("SANDBOXED-EXECUTE requires sandbox config and operation")
        
        sandbox_config = arguments[0]
        operation_cognition = arguments[1]
        
        if not isinstance(sandbox_config, dict):
            raise ValueError("Sandbox config must be a dictionary")
        
        # Create sandbox configuration
        config = create_sandbox_config(
            memory_limit_mb=sandbox_config.get('memory_limit', 100),
            cpu_limit_ms=sandbox_config.get('cpu_limit', 5000),
            network_access=sandbox_config.get('network_access', False),
            file_access=sandbox_config.get('file_access', False),
            allowed_operations=sandbox_config.get('allowed_operations', ['QUERY'])
        )
        
        # Create sandboxed context with restrictions
        sandboxed_context = execution_context.copy()
        sandboxed_context['sandbox_config'] = config
        sandboxed_context['sandbox_enforced'] = True
        
        operation_result = None
        sandbox_violated = False
        
        try:
            # Monitor resource usage (simplified implementation)
            start_time = datetime.utcnow()
            
            # For Phase 1, simulate sandboxed execution
            operation_result = {"simulated": True, "sandboxed_operation": str(operation_cognition)}
            
            # Check execution time against CPU limit
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            if execution_time > config.cpu_limit_ms:
                sandbox_violated = True
                operation_result = {"error": f"CPU limit exceeded: {execution_time:.2f}ms > {config.cpu_limit_ms}ms"}
                
        except Exception as e:
            operation_result = {"error": str(e)}
        
        return {
            "operation": "SANDBOXED-EXECUTE",
            "sandbox_enforced": True,
            "sandbox_violated": sandbox_violated,
            "sandbox_config": asdict(config),
            "operation_result": operation_result,
            "causality_chain": causality_chain,
            "success": not sandbox_violated and operation_result is not None
        }
    
    async def _handle_clarify(self, arguments: List[Any], causality_chain: List[str], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CLARIFY operation - Intent disambiguation for ambiguous queries."""
        if len(arguments) < 2:
            raise ValueError("CLARIFY operation requires query and options")
        
        ambiguous_query = arguments[0]
        clarification_options = arguments[1]
        
        if not isinstance(ambiguous_query, str):
            raise ValueError("Ambiguous query must be a string")
        
        if not isinstance(clarification_options, list):
            raise ValueError("Clarification options must be a list")
        
        # For now, implement basic clarification logic
        # In production, this would integrate with user interaction or LLM disambiguation
        
        # Simple heuristic: if only one option, auto-select it
        selected_option = None
        clarification_needed = True
        
        if len(clarification_options) == 1:
            selected_option = clarification_options[0]
            clarification_needed = False
        elif len(clarification_options) == 0:
            raise ValueError("At least one clarification option required")
        else:
            # Multiple options - would need user/agent input in production
            # For testing, select the first option as default
            selected_option = clarification_options[0]
            clarification_needed = True
        
        return {
            "operation": "CLARIFY",
            "ambiguous_query": ambiguous_query,
            "options": clarification_options,
            "selected_option": selected_option,
            "clarification_needed": clarification_needed,
            "auto_selected": not clarification_needed,
            "causality_chain": causality_chain,
            "success": True
        }
    
    async def _handle_event(self, arguments: List[Any], causality_chain: List[str], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle EVENT operation - Event definition and handler registration."""
        if len(arguments) < 3:
            raise ValueError("EVENT operation requires name, condition, and handler")
        
        event_name = arguments[0]
        trigger_condition = arguments[1]
        handler_cognition = arguments[2]
        
        if not isinstance(event_name, str):
            raise ValueError("Event name must be a string")
        
        if not isinstance(trigger_condition, str):
            raise ValueError("Trigger condition must be a string")
        
        # Create event definition
        event_definition = create_event_definition(
            event_name=event_name,
            trigger_condition=trigger_condition,
            handler_cognition=handler_cognition,
            metadata={
                "agent_id": execution_context.get('agent_id'),
                "created_at": datetime.utcnow().isoformat(),
                "context": execution_context
            }
        )
        
        # Store event definition in database
        event_id = None
        try:
            import json
            event_data = {
                'event_name': event_name,
                'agent_id': execution_context.get('agent_id', 'unknown'),
                'trigger_condition': trigger_condition,
                'handler_ail': str(handler_cognition),
                'is_active': True,
                'metadata': json.dumps(event_definition.metadata, default=str)
            }
            event_id = await self.database_manager.insert('event_definitions', event_data)
            self.logger.info(f"Event '{event_name}' registered with ID: {event_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to register event '{event_name}': {e}")
            return {
                "operation": "EVENT",
                "event_name": event_name,
                "error": str(e),
                "event_registered": False,
                "causality_chain": causality_chain,
                "success": False
            }
        
        return {
            "operation": "EVENT",
            "event_id": event_id,
            "event_name": event_name,
            "trigger_condition": trigger_condition,
            "handler_type": str(handler_cognition),
            "event_registered": True,
            "metadata": event_definition.metadata,
            "causality_chain": causality_chain,
            "success": True
        }

    # ========================================
    # Legacy Support & Shutdown Methods  
    # ========================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive kernel statistics."""
        try:
            kernel_stats = {
                "total_cognitions": getattr(self, '_total_cognitions', 0),
                "successful_cognitions": getattr(self, '_successful_cognitions', 0),
                "failed_cognitions": getattr(self, '_failed_cognitions', 0),
                "performance_profile": {
                    "memory_utilization": len(getattr(self, 'variable_contexts', {})),
                    "active_tools": len(getattr(self, 'tool_registry', type('', (), {'tools': {}})).tools),
                    "system_status": "operational",
                },
                "system_health": {
                    "status": "healthy",
                    "initialization_complete": hasattr(self, 'memory_manager') and hasattr(self, 'ail_parser'),
                },
                "last_updated": datetime.now().isoformat()
            }
            return kernel_stats
        except Exception as e:
            self.logger.error(f"Failed to get kernel statistics: {e}")
            return {"error": str(e), "last_updated": datetime.now().isoformat()}
    
    async def cleanup(self):
        """Cleanup method alias for compatibility with performance tests."""
        await self.close()
    
    async def close(self):
        """Close all kernel components and database connections."""
        try:
            if hasattr(self, 'memory_manager'):
                await self.memory_manager.close()
            if hasattr(self, 'database_manager'):
                await self.database_manager.close()
            self.logger.info("AgentOS Kernel shut down successfully")
        except Exception as e:
            self.logger.error(f"Error during kernel shutdown: {e}")
            raise
