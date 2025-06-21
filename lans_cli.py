#!/usr/bin/env python3
"""
LANS CLI - Command Line Interface for LANS System
Allows users to assign LLMs to agent roles and command them.
"""

import asyncio
import argparse
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_core.core.config import LANSConfig
from agent_core.core.lans_engine import LANSEngine
from agent_core.agents.coordinator_simple import Coordinator
from agent_core.llm.ollama_client import OllamaClient
from global_mcp_server.core.agentos_kernel import AgentOSKernel
from global_mcp_server.core.memory_manager import GlobalMemoryManager


class LANSCommandLineInterface:
    """Main CLI class for LANS system."""
    
    def __init__(self):
        self.config = None
        self.engine = None
        self.coordinator = None
        self.kernel = None
        self.memory_manager = None
        self.available_models = []
        
    async def initialize(self, config_path: Optional[str] = None):
        """Initialize LANS system."""
        try:
            # Load configuration
            if config_path and Path(config_path).exists():
                # Load from config file
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                # Convert workspace string to Path object
                if 'workspace' in config_data:
                    config_data['workspace'] = Path(config_data['workspace'])
                self.config = LANSConfig(**config_data)
            else:
                self.config = LANSConfig()
            
            # Initialize components
            self.engine = LANSEngine(self.config)
            await self.engine.initialize()
            
            self.coordinator = Coordinator(self.config)
            await self.coordinator.initialize()
            
            # Initialize kernel and memory if available
            try:
                # Shared database configuration
                database_config = {
                    "database_url": "sqlite:///lans_memory.db",
                    "database_type": "sqlite"
                }
                
                kernel_config = {
                    "workspace_path": str(self.config.workspace),
                    "memory_enabled": self.config.memory_enabled,
                    "database": database_config
                }
                self.kernel = AgentOSKernel(kernel_config)
                await self.kernel.initialize()
                
                if self.config.memory_enabled:
                    self.memory_manager = GlobalMemoryManager(database_config)
                    await self.memory_manager.initialize()
                    
            except Exception as e:
                print(f"⚠️ Advanced features unavailable: {e}")
            
            # Get available models
            try:
                ollama_client = OllamaClient(self.config)
                if await ollama_client.health_check():
                    # Mock model list for demo
                    self.available_models = [
                        "phi4-mini:latest",
                        "deepseek-coder:6.7b", 
                        "llama3.2:3b",
                        "codellama:7b"
                    ]
                else:
                    self.available_models = ["offline-mode"]
            except Exception:
                self.available_models = ["offline-mode"]
            
            print("✅ LANS system initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize LANS: {e}")
            return False
    
    def show_status(self):
        """Show current system status."""
        print("\n🔍 LANS System Status")
        print("=" * 40)
        print(f"Workspace: {self.config.workspace}")
        print(f"Model: {self.config.model or self.config.default_model}")
        print(f"Available Models: {len(self.available_models)}")
        for model in self.available_models:
            print(f"  - {model}")
        print(f"Memory Enabled: {self.config.memory_enabled}")
        print(f"Ollama URL: {self.config.ollama_base_url}")
        
        if self.kernel:
            print("✅ AgentOS Kernel: Active")
        else:
            print("❌ AgentOS Kernel: Inactive")
            
        if self.memory_manager:
            print("✅ Memory Manager: Active")
        else:
            print("❌ Memory Manager: Inactive")
    
    async def assign_agent_role(self, agent_type: str, model: str, role_config: Dict):
        """Assign an LLM to a specific agent role."""
        print(f"\n🤖 Assigning {model} to {agent_type} role...")
        
        try:
            if model not in self.available_models and model != "auto":
                print(f"❌ Model '{model}' not available. Available: {self.available_models}")
                return False
            
            # Update configuration
            if model != "auto":
                self.config.model = model
            
            # Configure agent role
            role_settings = {
                "model": model,
                "agent_type": agent_type,
                "configuration": role_config
            }
            
            print(f"✅ Assigned {model} to {agent_type}")
            print(f"   Configuration: {role_config}")
            
            # Store in memory if available
            if self.memory_manager:
                await self.memory_manager.store_memory(
                    memory_type="procedural",
                    content=f"Agent role assignment: {agent_type} -> {model}",
                    metadata={
                        "skill_name": f"{agent_type}_role_assignment",
                        "domain": "agent_management",
                        "procedure": f"Assign {model} to {agent_type} role",
                        "steps": [f"Configure {agent_type}", f"Set model to {model}"],
                        "contributors": ["cli_system"],
                        **role_settings
                    }
                )
                print("✅ Role assignment stored in memory")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to assign agent role: {e}")
            return False
    
    async def execute_command(self, command: str, agent_type: Optional[str] = None):
        """Execute a command using the specified agent or auto-select."""
        print(f"\n⚡ Executing: {command}")
        
        try:
            if agent_type:
                print(f"   Using agent: {agent_type}")
            else:
                print("   Auto-selecting agent...")
            
            # Process request through engine
            result = await self.engine.process_request(command)
            
            if result.success:
                print("✅ Command executed successfully")
                if result.message:
                    print(f"   Result: {result.message}")
                
                # Show files created/modified
                if result.files_created:
                    print(f"   Files created: {result.files_created}")
                if result.files_modified:
                    print(f"   Files modified: {result.files_modified}")
                    
            else:
                print("❌ Command execution failed")
                if result.error:
                    print(f"   Error: {result.error}")
            
            return result.success
            
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return False
    
    async def interactive_mode(self):
        """Start interactive command mode."""
        print("\n🚀 LANS Interactive Mode")
        print("Type 'help' for commands, 'exit' to quit")
        print("=" * 40)
        
        while True:
            try:
                user_input = input("\nlans> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break
                    
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                    
                if user_input.lower() == 'status':
                    self.show_status()
                    continue
                    
                if user_input.startswith('assign '):
                    # Parse assignment command: assign <agent_type> <model> [config]
                    parts = user_input[7:].split()
                    if len(parts) >= 2:
                        agent_type = parts[0]
                        model = parts[1]
                        config = {"priority": "normal"}
                        if len(parts) > 2:
                            try:
                                config = json.loads(' '.join(parts[2:]))
                            except:
                                pass
                        await self.assign_agent_role(agent_type, model, config)
                    else:
                        print("Usage: assign <agent_type> <model> [config_json]")
                    continue
                
                # Execute as general command
                await self.execute_command(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show help information."""
        print("""
🆘 LANS CLI Help
================

Commands:
  status                     - Show system status
  assign <agent> <model>     - Assign LLM to agent role
  help                      - Show this help
  exit/quit                 - Exit LANS
  
  <any text>                - Execute as natural language command

Examples:
  assign coder phi4-mini:latest
  assign planner deepseek-coder:6.7b  
  create a Python script for data analysis
  setup a new FastAPI project
  
Available Agent Types:
  - coder      (code generation and modification)
  - planner    (project planning and architecture) 
  - analyzer   (code analysis and review)
  - tester     (test generation and execution)
  - coordinator (orchestration and management)

Available Models: """ + ", ".join(self.available_models) + """

Configuration:
  Config file: ~/.lans/config.json
  Workspace: """ + str(self.config.workspace if self.config else "not set") + """
""")


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="LANS - Local Agent Network System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lans                                    # Interactive mode
  lans status                            # Show system status  
  lans assign coder phi4-mini:latest     # Assign model to agent
  lans "create a Python web server"     # Execute natural language command
  lans --config ./my-config.json        # Use custom config
        """
    )
    
    parser.add_argument(
        'command', 
        nargs='*', 
        help='Command to execute (if not provided, starts interactive mode)'
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--agent', '-a',
        help='Specify agent type for command execution'
    )
    parser.add_argument(
        '--model', '-m', 
        help='Specify model to use'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Initialize LANS CLI
    cli = LANSCommandLineInterface()
    
    print("🚀 Initializing LANS...")
    if not await cli.initialize(args.config):
        return 1
    
    # Handle specific commands
    if args.command:
        command = ' '.join(args.command)
        
        if command == 'status':
            cli.show_status()
            return 0
            
        elif command.startswith('assign '):
            # Parse assignment: assign <agent_type> <model>
            parts = command[7:].split()
            if len(parts) >= 2:
                agent_type = parts[0]
                model = parts[1]
                success = await cli.assign_agent_role(agent_type, model, {})
                return 0 if success else 1
            else:
                print("Usage: lans assign <agent_type> <model>")
                return 1
        else:
            # Execute as natural language command
            success = await cli.execute_command(command, args.agent)
            return 0 if success else 1
    else:
        # Interactive mode
        await cli.interactive_mode()
        return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
