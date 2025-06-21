#!/usr/bin/env python3
"""
LANS Simple Launcher - Streamlined System Initialization

A simplified launcher that focuses on core functionality:
- Ollama service verification
- Model discovery and selection  
- Basic LLM interaction
- Minimal dependencies
"""

import asyncio
import json
import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Install httpx if needed
try:
    import httpx
except ImportError:
    print("Installing httpx...")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Basic configuration
class SimpleConfig:
    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        self.default_model = "deepseek-coder:6.7b"
        self.temperature = 0.7
        self.max_tokens = 2048

# Simple Ollama client
class SimpleOllamaClient:
    def __init__(self, config: SimpleConfig):
        self.config = config
        self.base_url = config.ollama_base_url
        
    async def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate a response from Ollama."""
        model = model or self.config.default_model
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"Ollama API error: {response.status_code}")

# Simple agent
class SimpleAgent:
    def __init__(self, name: str, model: str, personality: str):
        self.name = name
        self.model = model
        self.personality = personality
        self.config = SimpleConfig()
        self.ollama = SimpleOllamaClient(self.config)
        self.conversation_history = []
    
    async def respond(self, user_input: str) -> str:
        """Generate a response to user input."""
        # Build context-aware prompt
        context = ""
        if self.conversation_history:
            context = "\nRecent conversation:\n" + "\n".join(self.conversation_history[-4:]) + "\n"
        
        prompt = f"""You are {self.name}, an AI assistant with a {self.personality} personality.{context}
User: {user_input}

{self.name}:"""
        
        response = await self.ollama.generate_response(prompt, self.model)
        
        # Update conversation history
        self.conversation_history.append(f"User: {user_input}")
        self.conversation_history.append(f"{self.name}: {response}")
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response

class LANSSimpleLauncher:
    def __init__(self):
        self.config = SimpleConfig()
        self.available_models = []
        self.selected_model = None
        self.agents = {}
        self.current_agent = None
    
    def print_header(self):
        """Print system header."""
        print("\n" + "="*70)
        print("🚀 LANS SIMPLE LAUNCHER")
        print("="*70)
        print("Streamlined Large Agent Network System")
        print("🤖 Multi-Model | 💬 Interactive Chat | ⚡ Fast Setup")
        print("="*70 + "\n")
    
    async def check_ollama(self) -> bool:
        """Check if Ollama is running."""
        print("🔍 Checking Ollama service...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    print("✅ Ollama service is running")
                    return True
                else:
                    print(f"❌ Ollama returned status {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Ollama not accessible: {str(e)}")
            print("💡 Please start Ollama: ollama serve")
            return False
    
    async def discover_models(self) -> bool:
        """Discover available models."""
        print("🔍 Discovering models...")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    if models:
                        self.available_models = models
                        print(f"✅ Found {len(models)} models:")
                        for i, model in enumerate(models, 1):
                            print(f"   {i}. {model}")
                        return True
                    else:
                        print("❌ No models found")
                        return False
        except Exception as e:
            print(f"❌ Error discovering models: {str(e)}")
            return False
    
    def select_model(self) -> bool:
        """Allow user to select a model."""
        if not self.available_models:
            return False
        
        print(f"\n📋 Select a model (1-{len(self.available_models)}):")
        for i, model in enumerate(self.available_models, 1):
            default_marker = " (default)" if model == self.config.default_model else ""
            print(f"   {i}. {model}{default_marker}")
        
        while True:
            try:
                choice = input(f"\nChoice (1-{len(self.available_models)}, Enter for default): ").strip()
                
                if not choice:
                    if self.config.default_model in self.available_models:
                        self.selected_model = self.config.default_model
                    else:
                        self.selected_model = self.available_models[0]
                    print(f"✅ Using: {self.selected_model}")
                    return True
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.available_models):
                    self.selected_model = self.available_models[choice_num - 1]
                    print(f"✅ Selected: {self.selected_model}")
                    return True
                else:
                    print(f"❌ Please enter 1-{len(self.available_models)}")
            
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Cancelled")
                return False
    
    async def test_model(self) -> bool:
        """Test the selected model."""
        print(f"🧪 Testing model '{self.selected_model}'...")
        try:
            client = SimpleOllamaClient(self.config)
            response = await client.generate_response(
                "Say 'Hello! I am ready to help.' to confirm you're working.",
                self.selected_model
            )
            
            if response and len(response.strip()) > 0:
                print(f"✅ Model working correctly")
                print(f"📝 Test response: {response[:80]}...")
                return True
            else:
                print("❌ Model returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Model test failed: {str(e)}")
            return False
    
    def create_agents(self):
        """Create cognitive agents."""
        print("🤖 Creating agents...")
        
        agent_configs = [
            ("Strategic", "strategic and analytical, focused on planning and reasoning"),
            ("Creative", "creative and innovative, focused on ideas and solutions"),
            ("Technical", "technical and precise, focused on implementation details"),
            ("General", "balanced and helpful, good for general conversation")
        ]
        
        for name, personality in agent_configs:
            agent = SimpleAgent(name.lower(), self.selected_model, personality)
            self.agents[name.lower()] = agent
            print(f"   ✅ {name} agent ready")
        
        # Set default agent
        self.current_agent = self.agents['general']
        print(f"🎯 Current agent: {self.current_agent.name}")
    
    async def interactive_mode(self):
        """Run interactive chat mode."""
        print("\n🎮 Interactive Mode")
        print("-" * 50)
        print("Commands:")
        print("  /switch - Switch agent")
        print("  /agents - List agents") 
        print("  /quit   - Exit")
        print("-" * 50)
        print(f"Current: {self.current_agent.name} ({self.current_agent.personality})")
        print("Type your message and press Enter.\n")
        
        while True:
            try:
                user_input = input(f"[{self.current_agent.name}]> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    if user_input == '/quit':
                        break
                    elif user_input == '/switch':
                        await self.switch_agent()
                    elif user_input == '/agents':
                        self.list_agents()
                    else:
                        print("❌ Unknown command. Use /quit, /switch, or /agents")
                    continue
                
                # Generate response
                print(f"\n💭 {self.current_agent.name} thinking...")
                start_time = time.time()
                
                try:
                    response = await self.current_agent.respond(user_input)
                    elapsed = time.time() - start_time
                    
                    print(f"🤖 {self.current_agent.name}: {response}")
                    print(f"⏱️  {elapsed:.1f}s\n")
                    
                except Exception as e:
                    print(f"❌ Error: {str(e)}\n")
            
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
    
    async def switch_agent(self):
        """Switch to different agent."""
        print("\n🔄 Available agents:")
        agents_list = list(self.agents.items())
        for i, (name, agent) in enumerate(agents_list, 1):
            current = " (current)" if agent == self.current_agent else ""
            print(f"  {i}. {name.title()} - {agent.personality}{current}")
        
        try:
            choice = input(f"\nSelect agent (1-{len(agents_list)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(agents_list):
                name, agent = agents_list[choice_num - 1]
                self.current_agent = agent
                print(f"✅ Switched to {name.title()}")
            else:
                print(f"❌ Please enter 1-{len(agents_list)}")
        except (ValueError, KeyboardInterrupt):
            print("❌ Switch cancelled")
        print()
    
    def list_agents(self):
        """List all available agents."""
        print(f"\n🤖 Available Agents ({len(self.agents)}):")
        for name, agent in self.agents.items():
            current = " (current)" if agent == self.current_agent else ""
            print(f"  • {name.title()} - {agent.personality}{current}")
        print()
    
    async def run(self):
        """Main execution."""
        try:
            self.print_header()
            
            # Basic checks
            if not await self.check_ollama():
                return
            
            if not await self.discover_models():
                return
            
            if not self.select_model():
                return
            
            if not await self.test_model():
                return
            
            # Create agents
            self.create_agents()
            
            print("\n🎉 LANS Simple Launcher ready!")
            print("🚀 Starting interactive mode...\n")
            
            # Interactive mode
            await self.interactive_mode()
        
        except KeyboardInterrupt:
            print("\n👋 Launcher interrupted")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

def main():
    """Main entry point."""
    launcher = LANSSimpleLauncher()
    
    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
