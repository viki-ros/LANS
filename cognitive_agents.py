#!/usr/bin/env python3
"""
Enhanced Cognitive Agents with Deep AIL Integration
True cognitive capabilities: memory, reasoning, self-reflection, goal-oriented behavior
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add LANS to path
sys.path.append('.')

from agent_core.core.config import LANSConfig
from agent_core.llm.ollama_client import OllamaClient

class CognitiveAgent:
    """Enhanced cognitive agent with memory, reasoning, and self-reflection"""
    
    def __init__(self, model_name: str, agent_id: str):
        self.model_name = model_name
        self.agent_id = agent_id
        self.client = None
        
        # Cognitive state
        self.memory_context = []
        self.conversation_history = []
        self.current_goals = []
        self.learned_patterns = {}
        self.performance_metrics = {
            'successful_responses': 0,
            'failed_responses': 0,
            'memory_recalls': 0,
            'reasoning_chains': 0
        }
        
        # Cognitive capabilities
        self.gmcp_url = "http://localhost:8080"
        
    async def initialize(self):
        """Initialize the cognitive agent"""
        config = LANSConfig()
        config.model = self.model_name
        self.client = OllamaClient(config)
        
        # Test connection and establish cognitive baseline
        test_response = await self.client.generate_response("Say 'COGNITIVE AGENT READY' if you understand.")
        
        if "COGNITIVE AGENT READY" in test_response or "ready" in test_response.lower():
            await self.establish_cognitive_baseline()
            return True
        return False
    
    async def establish_cognitive_baseline(self):
        """Establish the agent's cognitive capabilities and self-awareness"""
        baseline_prompt = f"""
        You are {self.agent_id}, an advanced cognitive AI agent with these capabilities:
        
        1. MEMORY: You can store and recall information using AIL expressions
        2. REASONING: You can perform multi-step logical reasoning
        3. SELF-REFLECTION: You can analyze your own performance and decisions
        4. GOAL-ORIENTED: You can pursue objectives across multiple interactions
        5. LEARNING: You can adapt based on experience and feedback
        
        Your current status:
        - Model: {self.model_name}
        - Agent ID: {self.agent_id}
        - Initialization: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Respond with:
        1. An acknowledgment of your cognitive capabilities
        2. A brief self-assessment of your current state
        3. One goal you'd like to pursue in conversations
        
        Keep response concise but thoughtful.
        """
        
        response = await self.client.generate_response(baseline_prompt)
        print(f"🧠 {self.agent_id} Cognitive Baseline:")
        print(f"   {response[:100]}...")
        
        # Store this as initial memory
        await self.store_memory("cognitive_baseline", response)
    
    async def send_ail_to_gmcp(self, ail_code: str) -> Dict[str, Any]:
        """Send AIL to GMCP with cognitive context"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                request = {
                    "ail_code": ail_code,
                    "agent_id": self.agent_id,
                    "context": {
                        "timestamp": time.time(),
                        "cognitive_state": {
                            "memory_items": len(self.memory_context),
                            "active_goals": len(self.current_goals),
                            "conversation_depth": len(self.conversation_history)
                        }
                    },
                    "execution_mode": "safe"
                }
                
                response = await client.post(f"{self.gmcp_url}/cognition", json=request)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.performance_metrics['successful_responses'] += 1
                        return result
                    else:
                        self.performance_metrics['failed_responses'] += 1
                        return result
                else:
                    self.performance_metrics['failed_responses'] += 1
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            self.performance_metrics['failed_responses'] += 1
            return {"success": False, "error": str(e)}
    
    async def store_memory(self, key: str, content: str):
        """Store information in both local and GMCP memory"""
        # Local memory
        memory_item = {
            'key': key,
            'content': content,
            'timestamp': time.time(),
            'context': 'cognitive_agent'
        }
        self.memory_context.append(memory_item)
        
        # GMCP memory via AIL
        ail_memory = f'(REMEMBER {{"event": "{key}", "content": "{content[:100]}...", "agent": "{self.agent_id}"}})'
        await self.send_ail_to_gmcp(ail_memory)
        
        # Keep memory manageable
        if len(self.memory_context) > 20:
            self.memory_context = self.memory_context[-15:]  # Keep last 15
    
    async def recall_relevant_memories(self, topic: str) -> List[Dict]:
        """Recall memories relevant to current topic"""
        self.performance_metrics['memory_recalls'] += 1
        
        # Simple relevance matching (could be enhanced with embeddings)
        relevant_memories = []
        topic_lower = topic.lower()
        
        for memory in self.memory_context[-10:]:  # Check recent memories
            if any(word in memory['content'].lower() for word in topic_lower.split()):
                relevant_memories.append(memory)
        
        # Also query GMCP for memories
        ail_recall = f'(RECALL {{"query": "{topic}", "agent": "{self.agent_id}"}})'
        gmcp_result = await self.send_ail_to_gmcp(ail_recall)
        
        return relevant_memories
    
    async def perform_reasoning_chain(self, problem: str) -> Dict[str, Any]:
        """Perform multi-step reasoning on a problem"""
        self.performance_metrics['reasoning_chains'] += 1
        
        reasoning_prompt = f"""
        Perform step-by-step reasoning on this problem: "{problem}"
        
        Use this cognitive process:
        1. ANALYZE: Break down the problem
        2. RECALL: What relevant information do you remember?
        3. REASON: Apply logical steps
        4. SYNTHESIZE: Combine insights for solution
        5. VERIFY: Check your reasoning
        
        For each step, also create an AIL expression that represents your thinking.
        
        Format your response as:
        Step 1 - ANALYZE: [your analysis]
        AIL: (ANALYZE "problem breakdown")
        
        Step 2 - RECALL: [relevant information]
        AIL: (RECALL {{"query": "relevant info"}})
        
        Continue for all 5 steps...
        """
        
        response = await self.client.generate_response(reasoning_prompt)
        
        # Extract AIL expressions and process them
        ail_expressions = []
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith('AIL:'):
                ail = line.replace('AIL:', '').strip()
                ail_expressions.append(ail)
        
        # Process AIL expressions through GMCP
        gmcp_results = []
        for ail in ail_expressions:
            if ail and '(' in ail:
                result = await self.send_ail_to_gmcp(ail)
                gmcp_results.append(result)
        
        return {
            'reasoning_response': response,
            'ail_expressions': ail_expressions,
            'gmcp_results': gmcp_results,
            'successful_ail_ops': sum(1 for r in gmcp_results if r.get('success'))
        }
    
    async def self_reflect(self) -> str:
        """Perform self-reflection on performance and state"""
        reflection_prompt = f"""
        Perform self-reflection as cognitive agent {self.agent_id}:
        
        Current state:
        - Model: {self.model_name}
        - Memories stored: {len(self.memory_context)}
        - Conversations: {len(self.conversation_history)}
        - Goals: {len(self.current_goals)}
        - Success rate: {self.performance_metrics['successful_responses']}/{self.performance_metrics['successful_responses'] + self.performance_metrics['failed_responses']}
        
        Reflect on:
        1. What have you learned recently?
        2. How well are you achieving your goals?
        3. What cognitive capabilities need improvement?
        4. What should you focus on next?
        
        Provide a thoughtful self-assessment and set one new goal.
        """
        
        reflection = await self.client.generate_response(reflection_prompt)
        
        # Store reflection as memory
        await self.store_memory("self_reflection", reflection)
        
        # Send reflection to GMCP
        ail_reflect = f'(REFLECT "cognitive performance and goal assessment")'
        await self.send_ail_to_gmcp(ail_reflect)
        
        return reflection
    
    async def cognitive_respond(self, user_input: str) -> Dict[str, Any]:
        """Generate a cognitive response using full capabilities"""
        print(f"\n🧠 {self.agent_id} Cognitive Processing...")
        start_time = time.time()
        
        # Step 1: Recall relevant memories
        print("   1️⃣ Recalling relevant memories...")
        relevant_memories = await self.recall_relevant_memories(user_input)
        
        # Step 2: Determine response strategy
        print("   2️⃣ Planning response strategy...")
        strategy_prompt = f"""
        User input: "{user_input}"
        
        Relevant memories: {len(relevant_memories)} items
        Recent context: {self.conversation_history[-3:] if self.conversation_history else "None"}
        
        Choose response strategy:
        1. SIMPLE: Direct answer
        2. REASONING: Multi-step problem solving
        3. CREATIVE: Innovative thinking
        4. MEMORY: Draw from past experience
        
        Respond with just the strategy name and brief reason.
        """
        
        strategy_response = await self.client.generate_response(strategy_prompt)
        strategy = "SIMPLE"  # Default
        if "REASONING" in strategy_response:
            strategy = "REASONING"
        elif "CREATIVE" in strategy_response:
            strategy = "CREATIVE"
        elif "MEMORY" in strategy_response:
            strategy = "MEMORY"
        
        print(f"   📋 Strategy: {strategy}")
        
        # Step 3: Generate response based on strategy
        print("   3️⃣ Generating cognitive response...")
        
        if strategy == "REASONING":
            reasoning_result = await self.perform_reasoning_chain(user_input)
            response_content = reasoning_result['reasoning_response']
            cognitive_data = reasoning_result
        else:
            # Enhanced prompt with cognitive context
            memory_context = "\n".join([f"- {m['content'][:100]}..." for m in relevant_memories[-3:]])
            
            cognitive_prompt = f"""
            You are {self.agent_id}, a cognitive AI agent with memory and reasoning capabilities.
            
            User input: "{user_input}"
            
            Relevant memories:
            {memory_context if memory_context else "No specific memories found"}
            
            Recent conversation: {self.conversation_history[-2:] if len(self.conversation_history) >= 2 else "Fresh conversation"}
            
            Generate a thoughtful response that:
            1. Addresses the user's input directly
            2. Incorporates relevant memories if applicable
            3. Shows cognitive depth and understanding
            4. Includes an appropriate AIL expression for this interaction
            
            Format:
            [Your thoughtful response]
            
            AIL: [appropriate AIL expression]
            """
            
            response_content = await self.client.generate_response(cognitive_prompt)
            cognitive_data = {'response': response_content}
        
        # Step 4: Process AIL expressions
        print("   4️⃣ Processing AIL expressions...")
        ail_expressions = []
        if "AIL:" in response_content:
            ail_lines = [line.strip() for line in response_content.split('\n') if line.strip().startswith('AIL:')]
            for ail_line in ail_lines:
                ail = ail_line.replace('AIL:', '').strip()
                if ail:
                    ail_expressions.append(ail)
                    gmcp_result = await self.send_ail_to_gmcp(ail)
                    print(f"      📡 GMCP: {'✅' if gmcp_result.get('success') else '❌'}")
        
        # Step 5: Update cognitive state
        print("   5️⃣ Updating cognitive state...")
        conversation_item = {
            'user_input': user_input,
            'response': response_content,
            'strategy': strategy,
            'timestamp': time.time(),
            'ail_expressions': ail_expressions
        }
        self.conversation_history.append(conversation_item)
        
        # Store important parts in memory
        await self.store_memory(f"interaction_{len(self.conversation_history)}", 
                               f"User: {user_input[:50]}... Response: {response_content[:50]}...")
        
        processing_time = time.time() - start_time
        
        result = {
            'response': response_content,
            'strategy': strategy,
            'relevant_memories': len(relevant_memories),
            'ail_expressions': ail_expressions,
            'processing_time': processing_time,
            'cognitive_data': cognitive_data
        }
        
        print(f"   ✅ Cognitive processing complete ({processing_time:.2f}s)")
        return result
    
    async def close(self):
        """Close agent connections"""
        if self.client:
            await self.client.close()

class CognitiveAgentSystem:
    """System for managing multiple cognitive agents"""
    
    def __init__(self):
        self.agents = {}
        
    async def create_agent(self, model_name: str, agent_id: str) -> bool:
        """Create and initialize a new cognitive agent"""
        print(f"🧠 Creating cognitive agent: {agent_id} ({model_name})")
        
        agent = CognitiveAgent(model_name, agent_id)
        
        if await agent.initialize():
            self.agents[agent_id] = agent
            print(f"   ✅ {agent_id} cognitive agent ready")
            return True
        else:
            print(f"   ❌ {agent_id} initialization failed")
            return False
    
    async def interactive_cognitive_session(self):
        """Interactive session with cognitive agents"""
        print("\n🧠 COGNITIVE AGENT INTERACTIVE SESSION")
        print("=" * 50)
        print("Enhanced agents with memory, reasoning, and self-reflection")
        print("Type 'quit' to exit, 'reflect' for self-reflection, 'status' for agent status")
        print("=" * 50)
        
        # Create cognitive agents
        models = ["phi4-mini:latest", "qwen2.5:latest"]
        agent_ids = ["CognitiveAgent_A", "CognitiveAgent_B"]
        
        for model, agent_id in zip(models, agent_ids):
            await self.create_agent(model, agent_id)
        
        if not self.agents:
            print("❌ No cognitive agents available")
            return
        
        print(f"\n👥 {len(self.agents)} cognitive agents ready for interaction")
        for agent_id in self.agents:
            print(f"   🧠 {agent_id}")
        
        # Interactive loop
        while True:
            try:
                print("\n" + "-" * 50)
                user_input = input("🧑‍💻 You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'reflect':
                    # Trigger self-reflection in all agents
                    for agent_id, agent in self.agents.items():
                        print(f"\n🪞 {agent_id} Self-Reflection:")
                        reflection = await agent.self_reflect()
                        print(f"   {reflection[:200]}...")
                    continue
                elif user_input.lower() == 'status':
                    # Show agent status
                    for agent_id, agent in self.agents.items():
                        print(f"\n📊 {agent_id} Status:")
                        print(f"   Memories: {len(agent.memory_context)}")
                        print(f"   Conversations: {len(agent.conversation_history)}")
                        print(f"   Success Rate: {agent.performance_metrics['successful_responses']}/{agent.performance_metrics['successful_responses'] + agent.performance_metrics['failed_responses']}")
                    continue
                elif not user_input:
                    continue
                
                # Get responses from all cognitive agents
                for agent_id, agent in self.agents.items():
                    print(f"\n🧠 {agent_id}:")
                    
                    try:
                        cognitive_response = await agent.cognitive_respond(user_input)
                        
                        # Display response
                        response = cognitive_response['response']
                        # Remove AIL line for cleaner display
                        clean_response = '\n'.join([line for line in response.split('\n') if not line.strip().startswith('AIL:')])
                        
                        print(f"   {clean_response}")
                        print(f"   📋 Strategy: {cognitive_response['strategy']}")
                        print(f"   🧠 Memories used: {cognitive_response['relevant_memories']}")
                        print(f"   ⚡ Processing: {cognitive_response['processing_time']:.2f}s")
                        
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Session error: {e}")
        
        # Cleanup
        print("\n🔄 Closing cognitive agents...")
        for agent in self.agents.values():
            await agent.close()
        
        print("👋 Cognitive session ended")

async def main():
    """Run the cognitive agent system"""
    system = CognitiveAgentSystem()
    await system.interactive_cognitive_session()

if __name__ == "__main__":
    print("🧠 ENHANCED COGNITIVE AGENT SYSTEM")
    print("🚀 Initializing advanced AI agents with memory, reasoning, and self-reflection...")
    asyncio.run(main())
