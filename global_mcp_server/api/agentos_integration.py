"""
AgentOS Integration helper for the Global Memory MCP Server.
Provides seamless integration between AgentOS agents and global memory.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .client import GMCPClient


class AgentOSIntegration:
    """
    Helper class that integrates AgentOS agents with the Global Memory system.
    Provides agent-specific memory operations and learning capabilities.
    """
    
    def __init__(self, gmcp_client: GMCPClient, agent_name: str, agent_type: str):
        self.client = gmcp_client
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        
        # Configure the client for this agent
        self.client.configure_agent(
            agent_id=f"agentros_{agent_name}",
            user_id="agentros_system"
        )
    
    async def initialize(self):
        """Initialize the memory integration for this agent."""
        try:
            # Register agent with global memory system
            capabilities = self._get_agent_capabilities()
            await self.client.register_agent(
                agent_type=self.agent_type,
                capabilities=capabilities
            )
            
            self.logger.info(f"Agent {self.agent_name} registered with global memory system")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory integration: {e}")
            raise
    
    def _get_agent_capabilities(self) -> List[str]:
        """Get capabilities based on agent type."""
        capabilities_map = {
            "planning": [
                "task_decomposition",
                "requirement_analysis", 
                "code_planning",
                "software_architecture",
                "dependency_management"
            ],
            "coding": [
                "code_generation",
                "software_components",
                "cpp_programming",
                "python_programming",
                "cmake_configuration"
            ],
            "coordinator": [
                "multi_agent_coordination",
                "task_orchestration",
                "progress_monitoring",
                "quality_assurance"
            ]
        }
        
        return capabilities_map.get(self.agent_type, ["general_ai_agent"])
    
    async def remember_successful_solution(
        self, 
        problem: str, 
        solution: str, 
        context: Dict[str, Any] = None
    ) -> str:
        """Remember a successful problem-solution pair."""
        try:
            # Store as episodic memory (experience)
            episodic_id = await self.client.store_memory(
                memory_type="episodic",
                content=f"Problem: {problem}\nSolution: {solution}",
                metadata={
                    "type": "successful_solution",
                    "problem": problem,
                    "solution": solution,
                    "context": context or {},
                    "agent_type": self.agent_type,
                    "timestamp": datetime.utcnow().isoformat()
                },
                importance_score=0.8  # High importance for successful solutions
            )
            
            # Also store as procedural memory if it's a reusable skill
            if self.agent_type in ["planning", "coding"]:
                await self._store_as_skill(problem, solution, context)
            
            self.logger.info(f"Remembered successful solution: {episodic_id}")
            return episodic_id
            
        except Exception as e:
            self.logger.error(f"Failed to remember successful solution: {e}")
            raise
    
    async def _store_as_skill(self, problem: str, solution: str, context: Dict[str, Any]):
        """Store solution as a reusable skill in procedural memory."""
        skill_name = f"{self.agent_type}_solution_{hash(problem) % 10000}"
        domain = context.get("domain", "software_development")
        
        steps = []
        if "steps" in context:
            steps = context["steps"]
        elif self.agent_type == "planning":
            steps = [
                "Analyze requirements",
                "Decompose into tasks", 
                "Plan architecture",
                "Identify dependencies"
            ]
        elif self.agent_type == "coding":
            steps = [
                "Design interfaces",
                "Implement core logic",
                "Add error handling",
                "Write tests"
            ]
        
        await self.client.store_memory(
            memory_type="procedural",
            content=solution,
            metadata={
                "skill_name": skill_name,
                "domain": domain,
                "procedure": solution,
                "steps": steps,
                "prerequisites": context.get("prerequisites", []),
                "problem_type": context.get("problem_type", "general")
            },
            importance_score=0.7
        )
    
    async def learn_from_error(self, error: str, attempted_solution: str, context: Dict[str, Any] = None):
        """Learn from errors and failed attempts."""
        try:
            await self.client.store_memory(
                memory_type="episodic",
                content=f"Error: {error}\nAttempted Solution: {attempted_solution}",
                metadata={
                    "type": "error_learning",
                    "error": error,
                    "attempted_solution": attempted_solution,
                    "context": context or {},
                    "agent_type": self.agent_type,
                    "timestamp": datetime.utcnow().isoformat()
                },
                importance_score=0.6  # Medium importance for learning from errors
            )
            
            self.logger.info("Learned from error for future reference")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from error: {e}")
    
    async def recall_similar_problems(self, problem: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Recall similar problems and their solutions."""
        try:
            # Search for episodic memories of successful solutions
            memories = await self.client.retrieve_memories(
                query=problem,
                memory_types=["episodic"],
                max_results=max_results,
                similarity_threshold=0.6
            )
            
            # Filter for successful solutions from this agent type
            relevant_memories = []
            for memory in memories:
                metadata = memory.get("metadata", {})
                if (metadata.get("type") == "successful_solution" and 
                    metadata.get("agent_type") == self.agent_type):
                    relevant_memories.append(memory)
            
            self.logger.info(f"Recalled {len(relevant_memories)} similar problems")
            return relevant_memories
            
        except Exception as e:
            self.logger.error(f"Failed to recall similar problems: {e}")
            return []
    
    async def get_relevant_skills(self, task_domain: str, max_skills: int = 10) -> List[Dict[str, Any]]:
        """Get relevant skills for a task domain."""
        try:
            skills = await self.client.retrieve_memories(
                query=f"{task_domain} {self.agent_type}",
                memory_types=["procedural"],
                max_results=max_skills,
                similarity_threshold=0.5
            )
            
            self.logger.info(f"Retrieved {len(skills)} relevant skills for {task_domain}")
            return skills
            
        except Exception as e:
            self.logger.error(f"Failed to get relevant skills: {e}")
            return []
    
    async def share_expertise(self, target_agent: str, domain: str):
        """Share expertise with another agent."""
        try:
            result = await self.client.share_knowledge(
                target_agent_id=f"agentros_{target_agent}",
                knowledge_domain=domain
            )
            
            self.logger.info(f"Shared expertise with {target_agent} in domain {domain}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to share expertise: {e}")
            raise
    
    async def remember_user_preference(self, preference_type: str, preference_value: Any, context: Dict[str, Any] = None):
        """Remember user preferences for personalization."""
        try:
            await self.client.store_memory(
                memory_type="semantic",
                content=f"User preference: {preference_type} = {preference_value}",
                metadata={
                    "concept": f"user_preference_{preference_type}",
                    "definition": str(preference_value),
                    "domain": "user_preferences",
                    "context": context or {},
                    "agent_observed": self.agent_name
                },
                importance_score=0.7
            )
            
            self.logger.info(f"Remembered user preference: {preference_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to remember user preference: {e}")
    
    async def get_memory_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get a summary of this agent's memory activity."""
        try:
            insights = await self.client.get_insights(hours_back=days_back * 24)
            
            # Filter insights for this agent
            agent_insights = {
                "agent_name": self.agent_name,
                "agent_type": self.agent_type,
                "period_days": days_back,
                "total_memories": insights.get("memory_distribution", {}).get("total", 0),
                "successful_solutions": 0,  # Would need to query specifically
                "errors_learned": 0,  # Would need to query specifically
                "skills_acquired": 0,  # Would need to query specifically
                "knowledge_shared": 0  # Would need to query specifically
            }
            
            return agent_insights
            
        except Exception as e:
            self.logger.error(f"Failed to get memory summary: {e}")
            return {}
    
    async def close(self):
        """Close the memory integration."""
        await self.client.close()
