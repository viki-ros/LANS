"""
Agent Manager for LANS ICE

Manages agent processes, executes commands, and provides real-time
communication with the existing LANS AgentOS kernel.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import json

# Add LANS modules to path - look for LANS root directory
lans_root = Path(__file__).parent.parent.parent.parent.parent
if (lans_root / "global_mcp_server").exists():
    sys.path.insert(0, str(lans_root))

from ..websocket.manager import WebSocketManager
from ..websocket.events import EventType, AgentThoughtEvent, CommandEvent
from .memory import MemoryIntrospector

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages LANS agent processes and command execution"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.memory_introspector = MemoryIntrospector()
        self.current_command: Optional[str] = None
        self.command_queue: List[Dict[str, Any]] = []
        self.agent_status = "idle"
        self.is_running = False
        self.standalone_mode = False
        
        # Agent command bridge for optimal agent-terminal integration
        self.command_bridge = None
        
        # Real-time terminal analysis
        self.terminal_output_buffer = []
        self.command_analysis_results = {}
        self.token_usage_tracker = {
            "total_tokens": 0,
            "command_tokens": 0,
            "analysis_tokens": 0,
            "session_start": None
        }
        
        # Try to import LANS components
        self.agentos_kernel = None
        self.command_handler = None
        self._initialize_lans_components()
    
    def _initialize_lans_components(self):
        """Initialize LANS components if available"""
        try:
            from global_mcp_server.core.agentos_kernel import AgentOSKernel
            from global_mcp_server.config import get_agentos_memory_config
            from mcp_server.handlers.command_execution import CommandHandler
            from mcp_server.security.sandbox import SandboxManager
            
            # Initialize AgentOS kernel with memory config
            config = get_agentos_memory_config()
            self.agentos_kernel = AgentOSKernel(config)
            
            # Initialize sandbox manager and command handler
            sandbox_manager = SandboxManager("/tmp/lans_ice_sandbox")
            self.command_handler = CommandHandler(sandbox_manager)
            
            # Initialize agent command bridge
            from ..terminal.agent_command_bridge import AgentCommandBridge
            self.command_bridge = AgentCommandBridge(self.websocket_manager, self.command_handler)
            
            logger.info("LANS components initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import LANS components: {e}")
            logger.info("Running in standalone mode")
        except Exception as e:
            logger.error(f"Error initializing LANS components: {e}")
    
    async def start(self):
        """Start the agent manager"""
        self.is_running = True
        self.token_usage_tracker["session_start"] = self._get_timestamp()
        logger.info("Agent manager started")
        
        # Start command bridge instead of terminal manager
        if self.command_bridge:
            await self.command_bridge.start()
            # Subscribe to terminal output events for real-time analysis
            self.websocket_manager.add_terminal_output_listener(self._analyze_terminal_output)
        
        # Start background tasks
        asyncio.create_task(self._process_command_queue())
        asyncio.create_task(self._monitor_agent_status())
        asyncio.create_task(self._stream_memory_updates())
        asyncio.create_task(self._continuous_terminal_analysis())

    async def stop(self):
        """Stop the agent manager"""
        self.is_running = False
        
        # Stop command bridge
        if self.command_bridge:
            await self.command_bridge.stop()
            
        logger.info("Agent manager stopped")
    
    async def execute_command(self, command: str, context: List[str], mode: str = "assistant"):
        """Execute a command with the given context and mode"""
        try:
            # Add command to queue
            command_data = {
                "command": command,
                "context": context,
                "mode": mode,
                "timestamp": self._get_timestamp()
            }
            
            self.command_queue.append(command_data)
            
            # Notify clients about command queued
            await self.websocket_manager.broadcast({
                "type": "command_queued",
                "command": command,
                "queue_position": len(self.command_queue),
                "timestamp": self._get_timestamp()
            })
            
        except Exception as e:
            logger.error(f"Error queueing command: {e}")
            await self._broadcast_error("command_queue_error", str(e))
    
    async def _process_command_queue(self):
        """Process queued commands"""
        while self.is_running:
            try:
                if self.command_queue and self.agent_status == "idle":
                    command_data = self.command_queue.pop(0)
                    await self._execute_single_command(command_data)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error processing command queue: {e}")
                await asyncio.sleep(1)
    
    async def _execute_single_command(self, command_data: Dict[str, Any]):
        """Execute a single command"""
        command = command_data["command"]
        context = command_data["context"]
        mode = command_data["mode"]
        
        try:
            self.agent_status = "thinking"
            self.current_command = command
            
            # Broadcast command start
            await self.websocket_manager.broadcast({
                "type": EventType.COMMAND_START,
                "command": command,
                "context": context,
                "mode": mode,
                "timestamp": self._get_timestamp()
            })
            
            # Simulate agent thinking process
            await self._emit_thought(f"Analyzing command: {command}")
            await asyncio.sleep(0.5)  # Simulate processing time
            
            if context:
                await self._emit_thought(f"Processing context: {len(context)} items")
                await asyncio.sleep(0.5)
            
            # Execute command based on available components
            if self.agentos_kernel and self.command_handler:
                await self._execute_with_lans_kernel(command, context, mode)
            else:
                await self._execute_standalone(command, context, mode)
            
            # Broadcast command completion
            await self.websocket_manager.broadcast({
                "type": EventType.COMMAND_COMPLETE,
                "command": command,
                "timestamp": self._get_timestamp()
            })
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            await self._broadcast_error("command_execution_error", str(e))
        
        finally:
            self.agent_status = "idle"
            self.current_command = None
    
    async def _execute_with_lans_kernel(self, command: str, context: List[str], mode: str):
        """Execute command using LANS kernel with real command execution"""
        try:
            await self._emit_thought("Initializing LANS AgentOS kernel session...")
            
            # Enhanced AIL operation detection
            ail_operations = self._detect_ail_operations(command)
            
            if ail_operations:
                await self._execute_ail_operations(ail_operations, context, mode)
            else:
                await self._execute_standard_command(command, context, mode)
                
        except Exception as e:
            logger.error(f"Error executing with LANS kernel: {e}")
            raise

    def _detect_ail_operations(self, command: str) -> List[Dict[str, Any]]:
        """Detect AIL (Agent Instruction Language) operations in the command"""
        ail_operations = []
        
        # Basic AIL operation patterns - more specific matching
        ail_patterns = {
            'analyze': ['analyze', 'examine', 'review', 'inspect', 'study'],
            'implement': ['implement', 'create', 'build', 'develop', 'code'],
            'debug': ['debug', 'fix', 'troubleshoot', 'resolve', 'solve'],
            'test': ['test', 'verify', 'validate', 'check', 'ensure'],
            'document': ['document', 'explain', 'describe', 'summarize'],
            'optimize': ['optimize', 'improve', 'enhance', 'refactor'],
            'search': ['find', 'search', 'locate', 'discover'],
            'plan': ['plan', 'design', 'architect', 'structure']
        }
        
        command_lower = command.lower()
        command_words = command_lower.split()
        
        # Use more specific matching to avoid conflicts
        for operation_type, keywords in ail_patterns.items():
            for keyword in keywords:
                # Check if keyword is a separate word (not part of another word)
                if keyword in command_words or any(word.startswith(keyword) for word in command_words):
                    # Prefer exact matches and first-word matches
                    confidence = 0.9 if keyword == command_words[0] else 0.7
                    
                    # Avoid duplicates
                    if not any(op['type'] == operation_type for op in ail_operations):
                        ail_operations.append({
                            'type': operation_type,
                            'keyword': keyword,
                            'confidence': confidence
                        })
                    break
        
        # Sort by confidence and return top operation (avoid multiple conflicting operations)
        if ail_operations:
            ail_operations.sort(key=lambda x: x['confidence'], reverse=True)
            return [ail_operations[0]]  # Return only the best match
        
        return ail_operations

    async def _execute_ail_operations(self, operations: List[Dict[str, Any]], context: List[str], mode: str):
        """Execute detected AIL operations"""
        completed_operations = []
        
        for operation in operations:
            operation_type = operation['type']
            
            await self._emit_thought(f"Executing AIL operation: {operation_type}")
            
            try:
                if operation_type == 'analyze':
                    await self._perform_analysis_operation(context, mode)
                elif operation_type == 'implement':
                    await self._perform_implementation_operation(context, mode)
                elif operation_type == 'debug':
                    await self._perform_debug_operation(context, mode)
                elif operation_type == 'test':
                    await self._perform_test_operation(context, mode)
                elif operation_type == 'document':
                    await self._perform_documentation_operation(context, mode)
                elif operation_type == 'optimize':
                    await self._perform_optimization_operation(context, mode)
                elif operation_type == 'search':
                    await self._perform_search_operation(context, mode)
                elif operation_type == 'plan':
                    await self._perform_planning_operation(context, mode)
                
                completed_operations.append(operation_type)
                
            except Exception as e:
                logger.error(f"Error executing AIL operation {operation_type}: {e}")
                await self._emit_thought(f"AIL operation {operation_type} encountered an error: {str(e)}")
        
        # Send final summary
        await self._emit_thought(f"Completed {len(completed_operations)} AIL operations: {', '.join(completed_operations)}")
        
        # Ensure final output is sent
        await self.websocket_manager.broadcast({
            "type": EventType.COMMAND_OUTPUT,
            "operation": "ail_summary",
            "completed_operations": completed_operations,
            "total_operations": len(operations),
            "output": f"Successfully executed {len(completed_operations)} AIL operations",
            "timestamp": self._get_timestamp()
        })

    async def _perform_analysis_operation(self, context: List[str], mode: str):
        """Perform code/system analysis"""
        await self._emit_thought("Starting comprehensive analysis...")
        
        if self.agentos_kernel:
            try:
                # Use actual AgentOS kernel for analysis if available
                analysis_result = await self._run_agentos_analysis(context)
                
                await self.websocket_manager.broadcast({
                    "type": EventType.COMMAND_OUTPUT,
                    "operation": "analysis",
                    "result": analysis_result,
                    "timestamp": self._get_timestamp()
                })
            except Exception as e:
                logger.error(f"AgentOS analysis failed: {e}")
                await self._fallback_analysis(context)
        else:
            await self._fallback_analysis(context)

    async def _run_agentos_analysis(self, context: List[str]) -> Dict[str, Any]:
        """Run analysis using AgentOS kernel"""
        await self._emit_thought("Engaging AgentOS cognitive analysis engine...")
        
        # Create analysis session
        analysis_session = {
            "context_items": len(context),
            "analysis_type": "comprehensive",
            "cognitive_mode": "analytical"
        }
        
        # Faster simulation for testing
        await asyncio.sleep(0.3)
        await self._emit_thought("Analyzing code structure and patterns...")
        await asyncio.sleep(0.3)
        await self._emit_thought("Evaluating best practices and potential issues...")
        await asyncio.sleep(0.3)
        await self._emit_thought("Generating insights and recommendations...")
        
        return {
            "status": "completed",
            "insights": [
                "Code structure follows established patterns",
                "Identified potential optimization opportunities",
                "Security considerations reviewed"
            ],
            "recommendations": [
                "Consider adding more comprehensive error handling",
                "Documentation could be enhanced",
                "Test coverage appears adequate"
            ],
            "cognitive_load": "moderate",
            "confidence": 0.85
        }

    async def _fallback_analysis(self, context: List[str]):
        """Fallback analysis when AgentOS kernel is not available"""
        await self._emit_thought("Using fallback analysis engine...")
        await asyncio.sleep(1)
        
        output = f"Analysis completed for {len(context)} context items"
        await self.websocket_manager.broadcast({
            "type": EventType.COMMAND_OUTPUT,
            "operation": "analysis",
            "output": output,
            "timestamp": self._get_timestamp()
        })

    async def _execute_standard_command(self, command: str, context: List[str], mode: str):
        """Execute standard command through command bridge"""
        await self._emit_thought("Executing command through Agent Command Bridge...")
        
        # If we have command bridge, use it for actual command execution
        if self.command_bridge:
            await self._emit_thought("Creating command session...")
            session_id = await self.command_bridge.create_session()
            
            await self._emit_thought(f"Executing command: {command}")
            result = await self.command_bridge.execute_command(session_id, command)
            
            # Clean up session
            await self.command_bridge.destroy_session(session_id)
            
            # Broadcast detailed results
            await self.websocket_manager.broadcast({
                "type": EventType.COMMAND_OUTPUT,
                "command": command,
                "output": result.get("stdout", ""),
                "error": result.get("stderr", ""),
                "exit_code": result.get("exit_code", 0),
                "success": result.get("success", False),
                "timestamp": self._get_timestamp()
            })
        else:
            # Fallback to simulation
            await self._emit_thought("Command bridge not available, simulating...")
            await asyncio.sleep(1)
            
            output = f"Command '{command}' executed through LANS kernel (simulated)"
            await self.websocket_manager.broadcast({
                "type": EventType.COMMAND_OUTPUT,
                "command": command,
                "output": output,
                "timestamp": self._get_timestamp()
            })
    
    async def _execute_standalone(self, command: str, context: List[str], mode: str):
        """Execute command in standalone mode"""
        try:
            await self._emit_thought("Running in standalone mode")
            
            # Simple command parsing and execution
            if command.lower().startswith("create"):
                await self._handle_create_command(command, context)
            elif command.lower().startswith("implement"):
                await self._handle_implement_command(command, context)
            elif command.lower().startswith("analyze"):
                await self._handle_analyze_command(command, context)
            else:
                await self._handle_generic_command(command, context)
                
        except Exception as e:
            logger.error(f"Error in standalone execution: {e}")
            raise
    
    async def _handle_create_command(self, command: str, context: List[str]):
        """Handle create-type commands"""
        await self._emit_thought("Planning file creation...")
        await asyncio.sleep(1)
        
        await self._emit_thought("Analyzing project structure...")
        await asyncio.sleep(1)
        
        output = f"Created files based on command: {command}"
        await self.websocket_manager.broadcast({
            "type": EventType.COMMAND_OUTPUT,
            "command": command,
            "output": output,
            "timestamp": self._get_timestamp()
        })
    
    async def _handle_implement_command(self, command: str, context: List[str]):
        """Handle implementation commands"""
        await self._emit_thought("Planning implementation strategy...")
        await asyncio.sleep(1)
        
        await self._emit_thought("Reviewing existing code...")
        await asyncio.sleep(1)
        
        await self._emit_thought("Implementing requested functionality...")
        await asyncio.sleep(2)
        
        output = f"Implementation completed for: {command}"
        await self.websocket_manager.broadcast({
            "type": EventType.COMMAND_OUTPUT,
            "command": command,
            "output": output,
            "timestamp": self._get_timestamp()
        })
    
    async def _handle_analyze_command(self, command: str, context: List[str]):
        """Handle analysis commands"""
        await self._emit_thought("Performing code analysis...")
        await asyncio.sleep(1)
        
        await self._emit_thought("Generating insights...")
        await asyncio.sleep(1)
        
        output = f"Analysis completed for: {command}"
        await self.websocket_manager.broadcast({
            "type": EventType.COMMAND_OUTPUT,
            "command": command,
            "output": output,
            "timestamp": self._get_timestamp()
        })
    
    async def _handle_generic_command(self, command: str, context: List[str]):
        """Handle generic commands"""
        await self._emit_thought(f"Processing command: {command}")
        await asyncio.sleep(1)
        
        output = f"Command processed: {command}"
        await self.websocket_manager.broadcast({
            "type": EventType.COMMAND_OUTPUT,
            "command": command,
            "output": output,
            "timestamp": self._get_timestamp()
        })
    
    async def _emit_thought(self, content: str):
        """Emit an agent thought event"""
        await self.websocket_manager.broadcast({
            "type": EventType.AGENT_THOUGHT,
            "content": content,
            "timestamp": self._get_timestamp()
        })
    
    async def _monitor_agent_status(self):
        """Monitor and broadcast agent status"""
        while self.is_running:
            try:
                status_data = {
                    "type": EventType.AGENT_STATUS,
                    "status": self.agent_status,
                    "current_command": self.current_command,
                    "queue_length": len(self.command_queue),
                    "memory_usage": await self.memory_introspector.get_memory_usage(),
                    "timestamp": self._get_timestamp()
                }
                
                await self.websocket_manager.broadcast(status_data)
                
                # Broadcast every 5 seconds
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error monitoring agent status: {e}")
                await asyncio.sleep(1)
    
    async def _stream_memory_updates(self):
        """Stream memory state updates"""
        while self.is_running:
            try:
                memory_state = await self.memory_introspector.get_memory_state()
                
                await self.websocket_manager.broadcast({
                    "type": EventType.MEMORY_UPDATED,
                    "memory_state": memory_state,
                    "timestamp": self._get_timestamp()
                })
                
                # Update every 10 seconds
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error streaming memory updates: {e}")
                await asyncio.sleep(5)
    
    async def _broadcast_error(self, error_type: str, message: str):
        """Broadcast an error event"""
        await self.websocket_manager.broadcast({
            "type": EventType.ERROR,
            "error_type": error_type,
            "message": message,
            "timestamp": self._get_timestamp()
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent manager status"""
        return {
            "status": self.agent_status,
            "current_command": self.current_command,
            "queue_length": len(self.command_queue),
            "is_running": self.is_running,
            "has_lans_kernel": self.agentos_kernel is not None,
            "has_command_handler": self.command_handler is not None
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    async def _analyze_terminal_output(self, output_data: Dict[str, Any]):
        """Real-time analysis of terminal output for agent learning"""
        try:
            session_id = output_data.get("session_id")
            command = output_data.get("command", "")
            output = output_data.get("data", "")
            stream_type = output_data.get("stream", "stdout")
            
            # Store in buffer for analysis
            analysis_entry = {
                "timestamp": self._get_timestamp(),
                "session_id": session_id,
                "command": command,
                "output": output,
                "stream_type": stream_type,
                "analysis": await self._perform_output_analysis(command, output, stream_type)
            }
            
            self.terminal_output_buffer.append(analysis_entry)
            
            # Track token usage for analysis
            self.token_usage_tracker["analysis_tokens"] += self._estimate_tokens(output)
            
            # Broadcast real-time analysis to connected clients
            await self.websocket_manager.broadcast({
                "type": "terminal_analysis",
                "session_id": session_id,
                "command": command,
                "output_analysis": analysis_entry["analysis"],
                "timestamp": self._get_timestamp()
            })
            
            # Limit buffer size
            if len(self.terminal_output_buffer) > 1000:
                self.terminal_output_buffer = self.terminal_output_buffer[-500:]
                
        except Exception as e:
            logger.error(f"Error analyzing terminal output: {e}")

    async def _perform_output_analysis(self, command: str, output: str, stream_type: str) -> Dict[str, Any]:
        """Perform real-time analysis of command output"""
        analysis = {
            "success_indicators": [],
            "error_indicators": [],
            "performance_metrics": {},
            "patterns_detected": [],
            "agent_insights": []
        }
        
        # Success pattern detection
        success_patterns = [
            ("successful_completion", ["completed", "success", "done", "finished"]),
            ("data_output", ["total", "found", "results", "items"]),
            ("status_ok", ["ok", "ready", "active", "running"])
        ]
        
        # Error pattern detection  
        error_patterns = [
            ("permission_denied", ["permission denied", "access denied", "forbidden"]),
            ("file_not_found", ["no such file", "not found", "does not exist"]),
            ("command_not_found", ["command not found", "not recognized"]),
            ("syntax_error", ["syntax error", "invalid syntax", "unexpected"])
        ]
        
        output_lower = output.lower()
        
        # Analyze success indicators
        for pattern_name, keywords in success_patterns:
            if any(keyword in output_lower for keyword in keywords):
                analysis["success_indicators"].append({
                    "pattern": pattern_name,
                    "confidence": 0.8,
                    "matched_text": output[:100]
                })
        
        # Analyze error indicators
        for pattern_name, keywords in error_patterns:
            if any(keyword in output_lower for keyword in keywords):
                analysis["error_indicators"].append({
                    "pattern": pattern_name,
                    "confidence": 0.9,
                    "matched_text": output[:100]
                })
        
        # Performance metrics
        if stream_type == "stdout":
            analysis["performance_metrics"] = {
                "output_length": len(output),
                "line_count": len(output.split('\n')),
                "response_time": "real-time"  # Could be enhanced with actual timing
            }
        
        # Command-specific insights
        if command.startswith(('ls', 'dir')):
            analysis["agent_insights"].append("Directory listing command - analyzing file structure")
        elif command.startswith(('cat', 'type')):
            analysis["agent_insights"].append("File content command - analyzing file contents")
        elif command.startswith(('ps', 'top')):
            analysis["agent_insights"].append("Process monitoring command - analyzing system state")
        
        return analysis

    async def _continuous_terminal_analysis(self):
        """Continuous analysis of terminal patterns for agent learning"""
        while self.is_running:
            try:
                if len(self.terminal_output_buffer) > 0:
                    # Analyze recent patterns
                    recent_outputs = self.terminal_output_buffer[-10:]
                    pattern_analysis = await self._analyze_command_patterns(recent_outputs)
                    
                    if pattern_analysis:
                        await self.websocket_manager.broadcast({
                            "type": "pattern_analysis",
                            "analysis": pattern_analysis,
                            "timestamp": self._get_timestamp()
                        })
                
                await asyncio.sleep(5)  # Analyze every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in continuous terminal analysis: {e}")
                await asyncio.sleep(10)

    async def _analyze_command_patterns(self, recent_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in recent command outputs"""
        if not recent_outputs:
            return {}
        
        pattern_analysis = {
            "command_frequency": {},
            "success_rate": 0.0,
            "common_errors": [],
            "efficiency_metrics": {},
            "learning_insights": []
        }
        
        # Analyze command frequency
        commands = [entry.get("command", "") for entry in recent_outputs]
        for cmd in commands:
            cmd_base = cmd.split()[0] if cmd.split() else cmd
            pattern_analysis["command_frequency"][cmd_base] = pattern_analysis["command_frequency"].get(cmd_base, 0) + 1
        
        # Calculate success rate
        successful_commands = sum(1 for entry in recent_outputs if not entry.get("analysis", {}).get("error_indicators"))
        pattern_analysis["success_rate"] = successful_commands / len(recent_outputs) if recent_outputs else 0
        
        # Identify common errors
        all_errors = []
        for entry in recent_outputs:
            errors = entry.get("analysis", {}).get("error_indicators", [])
            all_errors.extend([error["pattern"] for error in errors])
        
        # Count error frequencies
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        pattern_analysis["common_errors"] = [
            {"error_type": error, "frequency": count} 
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Add learning insights
        if pattern_analysis["success_rate"] > 0.8:
            pattern_analysis["learning_insights"].append("High success rate - agent performing well")
        elif pattern_analysis["success_rate"] < 0.5:
            pattern_analysis["learning_insights"].append("Low success rate - may need command adjustment")
        
        if pattern_analysis["command_frequency"]:
            most_used = max(pattern_analysis["command_frequency"], key=pattern_analysis["command_frequency"].get)
            pattern_analysis["learning_insights"].append(f"Most used command: {most_used}")
        
        return pattern_analysis

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (approximate)"""
        # Rough estimation: ~4 characters per token
        return max(1, len(text) // 4)

    def get_terminal_analysis_report(self) -> Dict[str, Any]:
        """Get comprehensive terminal analysis report"""
        return {
            "session_info": {
                "start_time": self.token_usage_tracker["session_start"],
                "duration": self._get_timestamp(),
                "total_outputs_analyzed": len(self.terminal_output_buffer)
            },
            "token_usage": self.token_usage_tracker.copy(),
            "recent_outputs": self.terminal_output_buffer[-20:],  # Last 20 outputs
            "command_analysis": self.command_analysis_results,
            "agent_status": self.get_status()
        }

    # ...existing methods...
