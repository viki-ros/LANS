"""
Simple AIL Coordinator
----------------------
Uses the SimpleAgentOS for AIL processing without requiring Docker or PostgreSQL
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from .simple_agentos import SimpleAgentOS, SimpleGMCPClient
from .llm.ollama_client import OllamaClient
from .core.config import LANSConfig

class SimpleAILCoordinator:
    """
    Simplified coordinator that uses the SimpleAgentOS for AIL processing
    Compatible with the IntelligentCoordinator interface but with no external dependencies
    """
    
    def __init__(self, llm_client: OllamaClient, config: Optional[LANSConfig] = None):
        """Initialize the coordinator with SimpleAgentOS"""
        self.llm_client = llm_client
        self.config = config
        
        # Initialize SimpleAgentOS
        self.agentos_kernel = SimpleAgentOS()
        self.gmcp_client = SimpleGMCPClient(self.agentos_kernel, "simple_coordinator")
        
        # Available agents
        self.available_agents = {
            "creative_writer": {"capabilities": ["writing", "creative"]},
            "code_generator": {"capabilities": ["code", "programming"]},
            "file_manager": {"capabilities": ["files", "filesystem"]},
            "data_analyst": {"capabilities": ["data", "analysis"]},
            "research_agent": {"capabilities": ["research", "search"]}
        }
        
        print(f"✅ SimpleAILCoordinator initialized")
        print(f"   AgentOS Kernel: SimpleAgentOS")
        print(f"   GMCP Client: SimpleGMCPClient")
        
    async def process_query(self, user_query: str, workspace: str = "./workspace") -> Dict[str, Any]:
        """Process a natural language user query"""
        try:
            # Step 1: Analyze the query
            analysis = await self._analyze_query(user_query)
            
            # Step 2: Determine the best agent for this task
            agent_name = self._select_agent_for_task(analysis)
            
            # Step 3: Translate to AIL instruction
            ail_instruction = self._translate_to_ail_instruction(agent_name, user_query)
            
            # Step 4: Execute AIL instruction
            ail_result = await self._execute_ail_instruction(ail_instruction)
            
            # Step 5: Process the result for user consumption
            return {
                "success": ail_result.get("success", False),
                "response": ail_result.get("result", {}),
                "ail_execution": True,
                "agent": agent_name,
                "workspace": workspace,
                "files_created": []  # Would be populated with actual file paths
            }
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to process request: {str(e)}"
            }
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze the user query to determine intent and required capabilities"""
        # Simple analysis for demonstration
        analysis = {
            "intent": "unknown",
            "required_capabilities": []
        }
        
        if "file" in query.lower() or "folder" in query.lower() or "directory" in query.lower():
            analysis["intent"] = "file_operation"
            analysis["required_capabilities"] = ["files", "filesystem"]
        elif "code" in query.lower() or "program" in query.lower() or "script" in query.lower():
            analysis["intent"] = "code_generation"
            analysis["required_capabilities"] = ["code", "programming"]
        elif "write" in query.lower() or "story" in query.lower() or "poem" in query.lower():
            analysis["intent"] = "creative_writing"
            analysis["required_capabilities"] = ["writing", "creative"]
        elif "data" in query.lower() or "analyze" in query.lower() or "statistics" in query.lower():
            analysis["intent"] = "data_analysis"
            analysis["required_capabilities"] = ["data", "analysis"]
        elif "search" in query.lower() or "find" in query.lower() or "research" in query.lower():
            analysis["intent"] = "research"
            analysis["required_capabilities"] = ["research", "search"]
        
        return analysis
    
    def _select_agent_for_task(self, analysis: Dict[str, Any]) -> str:
        """Select the best agent based on the analysis"""
        # Simple capability matching
        for agent_name, agent_info in self.available_agents.items():
            for capability in analysis.get("required_capabilities", []):
                if capability in agent_info.get("capabilities", []):
                    return agent_name
        
        # Default to code_generator if no match
        return "code_generator"
    
    def _translate_to_ail_instruction(self, agent_name: str, task_description: str, metadata: Dict[str, Any] = None) -> str:
        """Translate a natural language task to AIL instruction"""
        metadata = metadata or {}
        
        # Simplified AIL instruction generation
        if agent_name == "file_manager":
            if "create folder" in task_description.lower() or "create directory" in task_description.lower():
                folder_name = task_description.lower().replace("create folder", "").replace("create directory", "").strip()
                return f'(EXECUTE [shell] ["mkdir -p \\"{folder_name}\\""])'
                
            elif "create file" in task_description.lower():
                file_parts = task_description.lower().replace("create file", "").strip().split("with")
                file_name = file_parts[0].strip()
                content = file_parts[1].strip() if len(file_parts) > 1 else ""
                return f'(EXECUTE [shell] ["touch \\"{file_name}\\""])'
                
            else:
                return f'(EXECUTE [shell] ["echo \\"Processing file task: {task_description}\\""])'
                
        elif agent_name == "code_generator":
            return f'(QUERY [{json.dumps({"code_request": task_description})}])'
            
        elif agent_name == "creative_writer":
            return f'(QUERY [{json.dumps({"writing_request": task_description})}])'
            
        elif agent_name == "data_analyst":
            return f'(QUERY [{json.dumps({"analysis_request": task_description})}])'
            
        elif agent_name == "research_agent":
            return f'(QUERY [{json.dumps({"research_request": task_description})}])'
            
        else:
            # Generic query for unknown agent types
            return f'(QUERY [{json.dumps({"request": task_description})}])'
    
    async def _execute_ail_instruction(self, ail_instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an AIL instruction"""
        context = context or {}
        
        try:
            # Execute the instruction using SimpleAgentOS
            result = await self.agentos_kernel.process_cognition(ail_instruction)
            
            # Store the interaction for future context
            await self._store_ail_interaction(ail_instruction, result)
            
            return result
            
        except Exception as e:
            print(f"❌ AIL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ail_instruction": ail_instruction
            }
    
    async def _store_ail_interaction(self, ail_instruction: str, result: Any):
        """Store AIL interaction for learning and context"""
        try:
            await self.gmcp_client.store_episodic_memory(
                content=f"AIL Execution: {ail_instruction}",
                context={
                    "type": "ail_execution",
                    "instruction": ail_instruction,
                    "success": result.get('success', False),
                    "operation_type": result.get('operation_type', 'unknown'),
                    "execution_time_ms": result.get('execution_time_ms', 0)
                },
                importance_score=0.7,
                memory_type="ail_coordination"
            )
        except Exception as e:
            print(f"⚠️  Failed to store AIL interaction: {e}")

async def test_simple_ail_coordinator():
    """Test the SimpleAILCoordinator with basic tasks"""
    # Create a mock LLM client
    class MockLLMClient:
        async def generate_response(self, prompt):
            return f"Response to: {prompt}"
    
    config = LANSConfig(workspace=Path.cwd(), model=None, verbose=True)
    coordinator = SimpleAILCoordinator(MockLLMClient(), config)
    
    # Test file operation
    print("\n🔍 Testing file operation...")
    result = await coordinator.process_query("create folder test_folder")
    print(f"Success: {result['success']}")
    print(f"AIL execution: {result['ail_execution']}")
    print(f"Response: {result['response']}")
    
    # Test code generation
    print("\n🔍 Testing code generation...")
    result = await coordinator.process_query("write a Python function to calculate factorial")
    print(f"Success: {result['success']}")
    print(f"AIL execution: {result['ail_execution']}")
    print(f"Response: {result['response']}")
    
    # Test memory retrieval
    print("\n🔍 Testing memory retrieval...")
    memories = await coordinator.gmcp_client.retrieve_memories("", limit=2)
    print(f"Retrieved {len(memories)} memories")
    for memory in memories:
        print(f"Memory: {memory['content'][:50]}...")

if __name__ == "__main__":
    asyncio.run(test_simple_ail_coordinator())
