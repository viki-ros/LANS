#!/usr/bin/env python3
"""
LANS Fresh Launcher - Comprehensive System Initialization and Interactive Interface

This launcher performs all necessary system checks, initializations, and provides
a user-friendly interface for interacting with the LANS cognitive architecture.

Features:
- Comprehensive system health checks
- Automatic model and service initialization
- Real-time LLM interaction with agent switching
- Memory system validation
- GMCP server startup and verification
- Robust error handling and user guidance
"""

import asyncio
import json
import sys
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
import signal

# Ensure required dependencies are available
required_packages = ['httpx', 'aiofiles']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing required dependency: {package}")
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

# Import httpx after ensuring it's available
import httpx

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core components with better error handling
try:
    from agent_core.core.config import LANSConfig
    from agent_core.llm.ollama_client import OllamaClient
except ImportError as e:
    print(f"❌ Core LANS components not available: {e}")
    print("💡 Please ensure all dependencies are installed:")
    print("   - pip install aiofiles")
    sys.exit(1)

# Try to import enhanced agents, with fallback to simple implementation
try:
    from enhanced_cognitive_agents import EnhancedCognitiveAgent
except ImportError as e:
    print(f"⚠️  Enhanced agents not available: {e}")
    EnhancedCognitiveAgent = None


class SimpleCognitiveAgent:
    """Simple cognitive agent fallback for when enhanced agents are not available."""
    
    def __init__(self, name: str, model: str, personality: str = "helpful"):
        self.name = name
        self.model = model
        self.personality = personality
        
        # Initialize basic Ollama client
        config = LANSConfig()
        config.model = model
        self.ollama = OllamaClient(config)
        
        # Simple conversation context
        self.conversation_context = []
    
    async def think_and_respond(self, input_text: str, context: List[str] = None) -> Dict[str, Any]:
        """Simple response generation."""
        start_time = time.time()
        
        # Build basic prompt
        prompt = f"""You are {self.name}, an AI assistant with a {self.personality} personality.
        
User: {input_text}

Please respond helpfully and in character:"""
        
        # Generate response
        response = await self.ollama.generate_response(prompt)
        
        # Update context
        self.conversation_context.append(f"User: {input_text}")
        self.conversation_context.append(f"{self.name}: {response}")
        
        # Keep context manageable
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        processing_time = time.time() - start_time
        
        return {
            "agent": self.name,
            "response": response,
            "strategy": "direct",
            "memories_used": 0,
            "memory_id": None,
            "processing_time": processing_time,
            "cognitive_metadata": {
                "personality": self.personality,
                "model": self.model,
                "simple_mode": True
            }
        }


class LANSFreshLauncher:
    """Comprehensive LANS system launcher with full initialization and interactive mode."""
    
    def __init__(self):
        self.config = LANSConfig()
        self.available_models = []
        self.selected_model = None
        self.ollama_client = None
        self.cognitive_agents = {}
        self.current_agent = None
        self.gmcp_server_process = None
        self.startup_complete = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('lans_launcher.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def print_header(self):
        """Print the LANS system header."""
        print("\n" + "="*80)
        print("🚀 LANS FRESH LAUNCHER - Cognitive Architecture System")
        print("="*80)
        print("Initializing Large Agent Network System with multi-LLM collaboration")
        print("🧠 Cognitive Amplification | 🤖 Multi-Agent | 🧘‍♂️ Memory Recall")
        print("="*80 + "\n")
    
    async def check_ollama_service(self) -> bool:
        """Check if Ollama service is running and accessible."""
        print("🔍 Checking Ollama service...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    print("✅ Ollama service is running")
                    return True
                else:
                    print(f"❌ Ollama service returned status {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Ollama service not accessible: {str(e)}")
            print("💡 Please ensure Ollama is installed and running:")
            print("   - Install: curl -fsSL https://ollama.ai/install.sh | sh")
            print("   - Start: ollama serve")
            return False
    
    async def discover_models(self) -> List[str]:
        """Discover available LLM models from Ollama."""
        print("🔍 Discovering available models...")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    if models:
                        print(f"✅ Found {len(models)} available models:")
                        for i, model in enumerate(models, 1):
                            print(f"   {i}. {model}")
                        self.available_models = models
                        return models
                    else:
                        print("⚠️  No models found in Ollama")
                        return []
                else:
                    print(f"❌ Failed to retrieve models (status {response.status_code})")
                    return []
        except Exception as e:
            print(f"❌ Error discovering models: {str(e)}")
            return []
    
    def select_model(self) -> Optional[str]:
        """Allow user to select a model for interaction."""
        if not self.available_models:
            print("❌ No models available for selection")
            return None
        
        print("\n📋 Model Selection:")
        for i, model in enumerate(self.available_models, 1):
            marker = " (default)" if model == self.config.default_model else ""
            print(f"   {i}. {model}{marker}")
        
        while True:
            try:
                choice = input(f"\nSelect model (1-{len(self.available_models)}, or Enter for default): ").strip()
                
                if not choice:
                    # Use default model if available
                    if self.config.default_model in self.available_models:
                        selected = self.config.default_model
                        print(f"✅ Using default model: {selected}")
                        return selected
                    else:
                        selected = self.available_models[0]
                        print(f"✅ Default not available, using: {selected}")
                        return selected
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.available_models):
                    selected = self.available_models[choice_num - 1]
                    print(f"✅ Selected model: {selected}")
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(self.available_models)}")
            
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                return None
    
    async def test_model_response(self, model: str) -> bool:
        """Test if the selected model can generate responses."""
        print(f"🧪 Testing model '{model}' response...")
        try:
            # Create temporary config for this model
            test_config = LANSConfig()
            test_config.model = model
            test_client = OllamaClient(test_config)
            
            test_prompt = "Hello! Please respond with 'LANS system ready' to confirm you're working."
            response = await test_client.generate_response(test_prompt)
            
            if response and len(response.strip()) > 0:
                print(f"✅ Model '{model}' responding correctly")
                print(f"📝 Test response: {response[:100]}...")
                return True
            else:
                print(f"❌ Model '{model}' returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Model '{model}' test failed: {str(e)}")
            return False
    
    async def check_memory_system(self) -> bool:
        """Check if the memory system is accessible."""
        print("🧠 Checking memory system...")
        try:
            # Try to import and test memory components
            from global_mcp_server.core.memory_manager import GlobalMemoryManager
            from global_mcp_server.storage.database import DatabaseManager
            
            # Create a basic config for testing
            test_config = {
                "database_type": "sqlite",
                "database_url": "sqlite:///test_memory.db",
                "embeddings": {
                    "model": "all-MiniLM-L6-v2",
                    "device": "cpu"
                }
            }
            
            # Test memory manager initialization
            memory_manager = GlobalMemoryManager(test_config)
            print("✅ Memory system components loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Memory system check failed: {str(e)}")
            print("💡 Memory system may need initialization")
            return False
    
    async def start_gmcp_server(self) -> bool:
        """Start the GMCP server if not already running."""
        print("🌐 Starting GMCP server...")
        try:
            # First check if server is already running
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    response = await client.get("http://localhost:8001/health")
                    if response.status_code == 200:
                        print("✅ GMCP server already running")
                        return True
                except:
                    pass  # Server not running, will start it
            
            # Start the server in background
            python_cmd = sys.executable
            server_script = project_root / "global_mcp_server" / "core" / "server.py"
            
            if server_script.exists():
                print("🔧 Starting GMCP server process...")
                self.gmcp_server_process = subprocess.Popen(
                    [python_cmd, str(server_script), "--port", "8001"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(project_root)
                )
                
                # Wait for server to start and check multiple times
                for attempt in range(6):  # Try for 30 seconds (6 * 5s)
                    await asyncio.sleep(5)
                    print(f"🔍 Testing server connectivity (attempt {attempt + 1}/6)...")
                    
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        try:
                            response = await client.get("http://localhost:8001/health")
                            if response.status_code == 200:
                                print("✅ GMCP server started successfully")
                                return True
                        except Exception as e:
                            if attempt == 5:  # Last attempt
                                print(f"❌ Server connectivity test failed: {str(e)}")
                
                # If we get here, server didn't start properly
                if self.gmcp_server_process:
                    stdout, stderr = self.gmcp_server_process.communicate(timeout=1)
                    if stderr:
                        print(f"🔍 Server error output: {stderr.decode()[:200]}...")
                    
            print("❌ Failed to start GMCP server")
            print("💡 You can continue without GMCP for basic LLM interaction")
            return False
            
        except Exception as e:
            print(f"❌ GMCP server startup error: {str(e)}")
            print("💡 You can continue without GMCP for basic LLM interaction")
            return False
    
    async def initialize_agents(self) -> bool:
        """Initialize cognitive agents for interaction."""
        print("🤖 Initializing cognitive agents...")
        try:
            # Create different types of agents
            agent_configs = [
                ("Strategic", "strategic and analytical"),
                ("Creative", "creative and innovative"),
                ("Technical", "technical and precise"),
                ("General", "balanced and helpful")
            ]
            
            for name, personality in agent_configs:
                agent = None
                
                # Try enhanced agent first
                if EnhancedCognitiveAgent:
                    try:
                        agent = EnhancedCognitiveAgent(
                            name=name.lower(),
                            model=self.selected_model,
                            personality=personality
                        )
                        self.cognitive_agents[name.lower()] = agent
                        print(f"   ✅ {name} enhanced agent initialized")
                        continue
                    except Exception as e:
                        print(f"   ⚠️  {name} enhanced agent failed: {str(e)}")
                
                # Fall back to simple agent
                try:
                    agent = SimpleCognitiveAgent(
                        name=name.lower(),
                        model=self.selected_model,
                        personality=personality
                    )
                    self.cognitive_agents[name.lower()] = agent
                    print(f"   ✅ {name} simple agent initialized")
                except Exception as e:
                    print(f"   ❌ {name} simple agent also failed: {str(e)}")
            
            if self.cognitive_agents:
                # Set default current agent
                self.current_agent = list(self.cognitive_agents.values())[0]
                print(f"✅ {len(self.cognitive_agents)} cognitive agents ready")
                print(f"🎯 Current agent: {self.current_agent.name}")
                return True
            else:
                print("❌ No cognitive agents could be initialized")
                return False
                
        except Exception as e:
            print(f"❌ Agent initialization error: {str(e)}")
            return False
    
    async def run_system_checks(self) -> bool:
        """Run comprehensive system checks."""
        print("🔍 Running comprehensive system checks...\n")
        
        checks = [
            ("Ollama Service", self.check_ollama_service()),
            ("Model Discovery", self.discover_models()),
            ("Memory System", self.check_memory_system()),
            ("GMCP Server", self.start_gmcp_server()),
        ]
        
        failed_checks = []
        
        for check_name, check_coro in checks:
            try:
                if check_name == "Model Discovery":
                    result = await check_coro
                    success = len(result) > 0 if isinstance(result, list) else bool(result)
                else:
                    success = await check_coro
                
                if not success:
                    failed_checks.append(check_name)
                    
            except Exception as e:
                print(f"❌ {check_name} check failed with error: {str(e)}")
                failed_checks.append(check_name)
        
        if failed_checks:
            print(f"\n⚠️  Some checks failed: {', '.join(failed_checks)}")
            print("💡 You can continue with limited functionality")
            print("   - Ollama LLM interaction will work")
            print("   - Memory and GMCP features may be limited")
            
            continue_anyway = input("\nContinue anyway? (Y/n): ").strip().lower()
            return continue_anyway != 'n'
        else:
            print("\n✅ All system checks passed!")
            return True
    
    async def interactive_mode(self):
        """Run interactive mode for real-time LLM interaction."""
        print("\n🎮 Entering Interactive Mode")
        print("="*50)
        print("Commands:")
        print("  /help     - Show this help")
        print("  /switch   - Switch to different agent")
        print("  /agents   - List available agents")
        print("  /status   - Show system status")
        print("  /quit     - Exit LANS")
        print("="*50)
        print(f"Current agent: {self.current_agent.name} ({self.current_agent.personality})")
        print("Type your message and press Enter to chat with the AI agent.\n")
        
        while True:
            try:
                user_input = input(f"[{self.current_agent.name}]> ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue
                
                # Generate response from current agent
                print(f"\n🤔 {self.current_agent.name} is thinking...")
                start_time = time.time()
                
                try:
                    result = await self.current_agent.think_and_respond(user_input)
                    response_time = time.time() - start_time
                    
                    # Extract response from the result dictionary
                    response = result.get('response', 'No response generated')
                    strategy = result.get('strategy', 'unknown')
                    memories_used = result.get('memories_used', 0)
                    
                    print(f"\n🤖 {self.current_agent.name} ({strategy}): {response}")
                    print(f"💾 Used {memories_used} memories | ⏱️ {response_time:.2f}s\n")
                    
                except Exception as e:
                    print(f"\n❌ Error generating response: {str(e)}")
                    print("💡 Try switching to a different agent or check system status\n")
            
            except KeyboardInterrupt:
                print("\n\n👋 Exiting LANS interactive mode...")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
    
    async def handle_command(self, command: str):
        """Handle interactive mode commands."""
        cmd = command.lower().strip()
        
        if cmd == '/help':
            print("\n🆘 Available Commands:")
            print("  /help     - Show this help")
            print("  /switch   - Switch to different agent")
            print("  /agents   - List available agents")
            print("  /status   - Show system status")
            print("  /quit     - Exit LANS")
            print()
        
        elif cmd == '/agents':
            print(f"\n🤖 Available Agents ({len(self.cognitive_agents)}):")
            for i, (name, agent) in enumerate(self.cognitive_agents.items(), 1):
                current_marker = " (current)" if agent == self.current_agent else ""
                print(f"  {i}. {name.title()} - {agent.personality}{current_marker}")
            print()
        
        elif cmd == '/switch':
            await self.switch_agent()
        
        elif cmd == '/status':
            await self.show_status()
        
        elif cmd in ['/quit', '/exit']:
            print("\n👋 Exiting LANS...")
            raise KeyboardInterrupt
        
        else:
            print(f"\n❌ Unknown command: {command}")
            print("💡 Type /help for available commands\n")
    
    async def switch_agent(self):
        """Switch to a different cognitive agent."""
        if len(self.cognitive_agents) <= 1:
            print("\n⚠️  Only one agent available")
            return
        
        print(f"\n🔄 Current agent: {self.current_agent.name}")
        print("Available agents:")
        
        agents_list = list(self.cognitive_agents.items())
        for i, (name, agent) in enumerate(agents_list, 1):
            print(f"  {i}. {name.title()} - {agent.personality}")
        
        try:
            choice = input(f"\nSelect agent (1-{len(agents_list)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(agents_list):
                selected_name, selected_agent = agents_list[choice_num - 1]
                self.current_agent = selected_agent
                print(f"✅ Switched to {selected_name.title()} agent")
            else:
                print(f"❌ Please enter a number between 1 and {len(agents_list)}")
        
        except (ValueError, KeyboardInterrupt):
            print("❌ Agent switch cancelled")
        
        print()
    
    async def show_status(self):
        """Show current system status."""
        print(f"\n📊 LANS System Status:")
        print(f"  🤖 Current Agent: {self.current_agent.name} ({self.current_agent.personality})")
        print(f"  🧠 Selected Model: {self.selected_model}")
        print(f"  🔧 Available Agents: {len(self.cognitive_agents)}")
        print(f"  🌐 GMCP Server: {'Running' if self.gmcp_server_process else 'Unknown'}")
        print(f"  ⚙️  Configuration: Ollama @ {self.config.ollama_base_url}")
        print()
    
    def cleanup(self):
        """Clean up resources before exit."""
        if self.gmcp_server_process:
            try:
                self.gmcp_server_process.terminate()
                self.gmcp_server_process.wait(timeout=5)
                print("🧹 GMCP server stopped")
            except:
                try:
                    self.gmcp_server_process.kill()
                except:
                    pass
    
    async def run(self):
        """Main launcher execution."""
        try:
            self.print_header()
            
            # Run system checks
            if not await self.run_system_checks():
                print("\n❌ System checks failed. Exiting...")
                return
            
            # Model selection and testing
            self.selected_model = self.select_model()
            if not self.selected_model:
                print("\n❌ No model selected. Exiting...")
                return
            
            if not await self.test_model_response(self.selected_model):
                print(f"\n❌ Model '{self.selected_model}' is not responding correctly")
                return
            
            # Initialize agents
            if not await self.initialize_agents():
                print("\n❌ Agent initialization failed. Exiting...")
                return
            
            self.startup_complete = True
            print("\n🎉 LANS system fully initialized and ready!")
            print("🚀 Starting interactive mode...\n")
            
            # Start interactive mode
            await self.interactive_mode()
        
        except KeyboardInterrupt:
            print("\n\n👋 LANS launcher interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in launcher: {str(e)}", exc_info=True)
            print(f"\n❌ Unexpected error: {str(e)}")
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    launcher = LANSFreshLauncher()
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n\n🛑 Received signal {signum}, shutting down...")
        launcher.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the launcher
    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print("\n👋 LANS launcher stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
