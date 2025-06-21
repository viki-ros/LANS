#!/usr/bin/env python3
"""
LANS Launcher Demo - Shows the functionality of the fresh launcher
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def demo_launcher():
    """Demonstrate the LANS launcher functionality."""
    
    print("\n" + "="*80)
    print("🎯 LANS FRESH LAUNCHER DEMONSTRATION")
    print("="*80)
    print("This demo shows the functionality of the new LANS fresh launcher")
    print("="*80)
    
    # Import and test the simple launcher components
    try:
        from lans_simple_launcher import LANSSimpleLauncher, SimpleConfig, SimpleOllamaClient
        print("✅ Simple launcher components imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # Initialize launcher
    launcher = LANSSimpleLauncher()
    
    print("\n🔍 SYSTEM CHECKS")
    print("-" * 40)
    
    # Test Ollama connection
    ollama_status = await launcher.check_ollama()
    
    if ollama_status:
        # Test model discovery
        models_found = await launcher.discover_models()
        
        if models_found:
            print(f"\n📊 SYSTEM STATUS:")
            print(f"   🌐 Ollama Service: {'✅ Running' if ollama_status else '❌ Not Running'}")
            print(f"   🤖 Available Models: {len(launcher.available_models)}")
            print(f"   🔧 Models Found:")
            for i, model in enumerate(launcher.available_models[:3], 1):  # Show first 3
                print(f"      {i}. {model}")
            if len(launcher.available_models) > 3:
                print(f"      ... and {len(launcher.available_models) - 3} more")
            
            # Test a model (use the first available)
            launcher.selected_model = launcher.available_models[0]
            print(f"\n🧪 Testing model: {launcher.selected_model}")
            model_works = await launcher.test_model()
            
            if model_works:
                print(f"   ✅ Model '{launcher.selected_model}' is working correctly")
                
                # Create agents
                launcher.create_agents()
                print(f"\n🤖 AGENT SYSTEM:")
                print(f"   📊 Agents Created: {len(launcher.agents)}")
                for name, agent in launcher.agents.items():
                    print(f"      • {name.title()}: {agent.personality[:50]}...")
                
                # Test a simple interaction
                print(f"\n💬 TESTING INTERACTION:")
                try:
                    test_agent = launcher.agents['general']
                    print(f"   🤔 Asking {test_agent.name}: 'Hello, introduce yourself briefly'")
                    
                    response = await test_agent.respond("Hello, introduce yourself briefly in one sentence.")
                    print(f"   🤖 Response: {response[:100]}...")
                    
                    print(f"\n✅ LANS SYSTEM FULLY FUNCTIONAL!")
                    print(f"   🚀 Ready for interactive use")
                    print(f"   💡 Run: python lans_simple_launcher.py")
                    
                except Exception as e:
                    print(f"   ❌ Interaction test failed: {e}")
            else:
                print(f"   ❌ Model test failed")
        else:
            print("   ❌ No models found")
    else:
        print("   ❌ Ollama service not available")
    
    print(f"\n📋 LAUNCHER FEATURES:")
    print(f"   🔍 Automatic Ollama service detection")
    print(f"   🤖 Model discovery and selection")
    print(f"   🧪 Model functionality testing")
    print(f"   👥 Multi-agent system creation")
    print(f"   💬 Interactive chat interface")
    print(f"   🔄 Agent switching capabilities")
    print(f"   ⚡ Minimal dependencies")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Run: python lans_simple_launcher.py")
    print(f"   2. Select your preferred model")
    print(f"   3. Start chatting with AI agents")
    print(f"   4. Use /switch to change agents")
    print(f"   5. Use /quit to exit")

if __name__ == "__main__":
    try:
        asyncio.run(demo_launcher())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
