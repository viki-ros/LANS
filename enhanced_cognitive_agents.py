#!/usr/bin/env python3
"""
Enhanced Cognitive Agents with Real AIL/GMCP Integration
Real-time multi-agent cognitive system with proper GMCP connectivity.
"""

import asyncio
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.llm.ollama_client import OllamaClient
from agent_core.core.config import LANSConfig
from global_mcp_server.api.client import GMCPClient


class EnhancedCognitiveAgent:
    """Enhanced AI agent with real cognitive capabilities and GMCP integration."""
    
    def __init__(self, name: str, model: str, personality: str = "analytical"):
        self.name = name
        self.model = model
        self.personality = personality
        
        # Initialize OllamaClient with proper config
        config = LANSConfig()
        config.model = model
        self.ollama = OllamaClient(config)
        
        # Initialize proper GMCP client
        self.gmcp_client = GMCPClient(base_url="http://localhost:8001")
        self.gmcp_client.configure_agent(
            agent_id=name,
            user_id="user_demo",
            session_id=f"session_{name}"
        )
        
        self.memory_buffer = []
        self.conversation_context = []
        self.cognitive_strategies = ["MEMORY", "REASONING", "CREATIVE", "ANALYTICAL", "COLLABORATIVE"]
        self.last_memory_id = None
        
    async def store_memory(self, content: str, memory_type: str = "episodic", metadata: Dict = None) -> Optional[str]:
        """Store memory in GMCP with enhanced context."""
        try:
            if metadata is None:
                metadata = {}
            
            # Enhanced metadata with cognitive context
            enhanced_metadata = {
                **metadata,
                "agent_name": self.name,
                "model": self.model,
                "personality": self.personality,
                "timestamp": datetime.now().isoformat(),
                "conversation_turn": len(self.conversation_context),
                "cognitive_state": random.choice(self.cognitive_strategies)
            }
            
            # Use direct GMCP client method instead of AIL
            memory_id = await self.gmcp_client.store_memory(
                memory_type=memory_type,
                content=content,
                metadata=enhanced_metadata,
                importance_score=0.7
            )
            
            if memory_id:
                self.last_memory_id = memory_id
                self.memory_buffer.append({
                    "id": memory_id,
                    "content": content,
                    "type": memory_type,
                    "metadata": enhanced_metadata
                })
                print(f"💾 {self.name} stored memory: {memory_id}")
            
            return memory_id
            
        except Exception as e:
            print(f"❌ Memory storage failed for {self.name}: {e}")
            return None
    
    async def retrieve_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant memories from GMCP."""
        try:
            # Use direct GMCP client method for better results
            memories = await self.gmcp_client.retrieve_memories(
                query=query,
                memory_types=["episodic", "semantic", "procedural"],
                max_results=limit,
                similarity_threshold=0.6
            )
            print(f"🧠 {self.name} retrieved {len(memories)} memories")
            return memories
            
        except Exception as e:
            print(f"❌ Memory retrieval failed for {self.name}: {e}")
            return []
    
    async def think_and_respond(self, input_text: str, context: List[str] = None) -> Dict[str, Any]:
        """Enhanced cognitive processing with multi-stage thinking."""
        start_time = time.time()
        
        # Stage 1: Memory retrieval
        print(f"🧠 {self.name} retrieving relevant memories...")
        memories = await self.retrieve_memories(input_text)
        memory_context = ""
        if memories:
            memory_context = f"\nRelevant memories: {len(memories)} items found"
            for i, mem in enumerate(memories[:3]):  # Use top 3 memories
                memory_context += f"\n- Memory {i+1}: {mem.get('content', 'N/A')[:100]}..."
        
        # Stage 2: Cognitive strategy selection
        strategy = random.choice(self.cognitive_strategies)
        print(f"🎯 {self.name} using {strategy} strategy...")
        
        # Stage 3: Context assembly
        conversation_context = ""
        if context:
            conversation_context = f"\nConversation context:\n" + "\n".join(context[-3:])  # Last 3 exchanges
        
        # Stage 4: Enhanced prompt construction
        cognitive_prompt = f"""You are {self.name}, an advanced AI agent with {self.personality} personality.
Current cognitive strategy: {strategy}

Input: {input_text}
{memory_context}
{conversation_context}

Instructions:
- Use your {strategy} cognitive approach
- Be aware of your persistent memories and context
- Respond as {self.name} with {self.personality} personality
- Keep responses concise but insightful
- Show awareness of being an AI agent in the LANS ecosystem

Respond naturally and cognitively:"""
        
        # Stage 5: LLM processing
        print(f"🤖 {self.name} generating cognitive response...")
        response = await self.ollama.generate_response(
            prompt=cognitive_prompt
        )
        
        # Stage 6: Memory storage
        memory_content = f"Conversation: User said '{input_text}', I responded using {strategy} strategy: '{response[:100]}...'"
        memory_id = await self.store_memory(memory_content, "episodic", {
            "strategy": strategy,
            "user_input": input_text,
            "response_preview": response[:50]
        })
        
        # Stage 7: Context update
        self.conversation_context.append(f"User: {input_text}")
        self.conversation_context.append(f"{self.name}: {response}")
        
        total_time = time.time() - start_time
        
        return {
            "agent": self.name,
            "response": response,
            "strategy": strategy,
            "memories_used": len(memories),
            "memory_id": memory_id,
            "processing_time": total_time,
            "cognitive_metadata": {
                "personality": self.personality,
                "model": self.model,
                "memory_buffer_size": len(self.memory_buffer),
                "conversation_turns": len(self.conversation_context)
            }
        }


async def multi_agent_cognitive_conversation():
    """Enhanced multi-agent cognitive conversation with real GMCP integration."""
    
    print("🧠 ENHANCED COGNITIVE AGENT SYSTEM")
    print("="*60)
    print("🎯 Initializing real cognitive agents...")
    
    # Initialize enhanced cognitive agents
    agents = [
        EnhancedCognitiveAgent("CognitiveAlpha", "phi4-mini:latest", "analytical"),
        EnhancedCognitiveAgent("CognitiveBeta", "qwen2.5:latest", "creative")
    ]
    
    # Verify GMCP connectivity
    print("📡 Testing GMCP connectivity...")
    for agent in agents:
        try:
            # Test with a simple QUERY through the cognition endpoint
            response = await agent.gmcp_client.process_cognition(
                '(QUERY {"intent": "system_test", "query": "connectivity_check"})',
                agent.name
            )
            if response.success:
                print(f"   ✅ {agent.name} connected to GMCP (response time: {response.execution_time_ms:.1f}ms)")
            else:
                print(f"   ❌ {agent.name} GMCP connection failed: {response.error}")
                return
        except Exception as e:
            print(f"   ❌ {agent.name} GMCP connection failed: {e}")
            return
    
    conversation_topics = [
        "What makes human consciousness different from AI cognition?",
        "How can multiple AI agents collaborate effectively?",
        "What are the ethical implications of persistent AI memory?",
        "How should AI agents balance individual goals with collective objectives?",
        "What role does uncertainty play in intelligent decision-making?"
    ]
    
    print(f"\n🎉 Starting enhanced cognitive conversation with {len(agents)} agents...")
    print("🔄 Each agent will use different cognitive strategies and maintain memory")
    
    conversation_history = []
    
    for round_num, topic in enumerate(conversation_topics, 1):
        print(f"\n{'='*60}")
        print(f"🗣️  ROUND {round_num}: {topic}")
        print("="*60)
        
        for agent in agents:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
            print(f"🤖 {agent.name} ({agent.model}) is thinking...")
            
            # Agent processes the topic with full cognitive capabilities
            result = await agent.think_and_respond(topic, conversation_history)
            
            print(f"💭 Strategy: {result['strategy']}")
            print(f"🧠 Memories used: {result['memories_used']}")
            print(f"💾 Memory stored: {result['memory_id'][:8] if result['memory_id'] else 'None'}")
            print(f"⚡ Processing time: {result['processing_time']:.2f}s")
            print(f"💬 {result['agent']}: {result['response']}")
            
            # Add to conversation history
            conversation_history.append(f"{result['agent']}: {result['response']}")
            
            # Pause for realistic conversation flow
            await asyncio.sleep(1)
    
    print(f"\n🎯 COGNITIVE CONVERSATION COMPLETE")
    print("="*60)
    
    # Display agent statistics
    for agent in agents:
        print(f"\n📊 {agent.name} Statistics:")
        print(f"   🧠 Memory buffer: {len(agent.memory_buffer)} items")
        print(f"   💬 Conversation turns: {len(agent.conversation_context)}")
        print(f"   🎭 Personality: {agent.personality}")
        print(f"   🤖 Model: {agent.model}")


async def interactive_cognitive_chat():
    """Interactive chat with enhanced cognitive agents."""
    
    print("🧠 INTERACTIVE COGNITIVE AGENT CHAT")
    print("="*60)
    
    # Initialize agent
    agent = EnhancedCognitiveAgent("CognitiveAssistant", "phi4-mini:latest", "helpful")
    
    # Test GMCP connectivity
    print("📡 Testing GMCP connectivity...")
    try:
        response = await agent.gmcp_client.process_cognition(
            '(QUERY {"intent": "system_test", "query": "ready_check"})',
            agent.name
        )
        if not response.success:
            print(f"❌ GMCP connection failed: {response.error}")
            return
        print(f"✅ Agent ready! (GMCP response time: {response.execution_time_ms:.1f}ms)")
    except Exception as e:
        print(f"❌ GMCP connection failed: {e}")
        return
    print("\n💬 Start chatting! Type 'quit' to exit.")
    print("🎯 The agent will remember our conversation and use cognitive strategies.")
    
    while True:
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        user_input = input("👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        print(f"🧠 {agent.name} is thinking cognitively...")
        result = await agent.think_and_respond(user_input)
        
        print(f"💭 Strategy: {result['strategy']}")
        print(f"🧠 Memories: {result['memories_used']} used")
        print(f"⚡ Time: {result['processing_time']:.2f}s")
        print(f"🤖 {result['agent']}: {result['response']}")


if __name__ == "__main__":
    print("🧠 ENHANCED COGNITIVE AGENT SYSTEM")
    print("Choose your demonstration:")
    print("1. Multi-agent cognitive conversation")
    print("2. Interactive cognitive chat")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(multi_agent_cognitive_conversation())
    elif choice == "2":
        asyncio.run(interactive_cognitive_chat())
    else:
        print("Invalid choice. Running multi-agent conversation...")
        asyncio.run(multi_agent_cognitive_conversation())
