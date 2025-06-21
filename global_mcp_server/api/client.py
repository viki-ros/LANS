"""
Global Memory MCP Client - Integration client for LANS and other AI systems.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
import logging


class GMCPClient:
    """
    Client for connecting to Global Memory MCP Server.
    Provides easy integration for AI agents to access persistent memory.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.logger = logging.getLogger(__name__)
        
        # Agent identification
        self.agent_id = None
        self.user_id = None
        self.session_id = None
    
    def configure_agent(self, agent_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Configure agent identification for memory operations."""
        self.agent_id = agent_id
        self.user_id = user_id
        self.session_id = session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    async def connect(self):
        """Connect and verify connection to GMCP server."""
        try:
            # Test connection with health check
            response = await self.health_check()
            self.logger.info(f"GMCP client connected successfully to {self.base_url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to GMCP server: {e}")
            return False
    
    async def register_agent(self, agent_type: str, capabilities: List[str] = None):
        """Register agent with the global memory system."""
        if not self.agent_id:
            raise ValueError("Agent ID must be configured before registration")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/agents/register",
                params={
                    "agent_id": self.agent_id,
                    "agent_type": agent_type,
                    "capabilities": ",".join(capabilities or [])
                }
            )
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(f"Agent {self.agent_id} registered successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            raise
    
    async def store_memory(
        self,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
        importance_score: float = 0.5
    ) -> str:
        """Store a memory in the global system."""
        try:
            payload = {
                "memory_type": memory_type,
                "content": content,
                "metadata": {
                    **(metadata or {}),
                    "session_id": self.session_id
                },
                "agent_id": self.agent_id,
                "user_id": self.user_id,
                "importance_score": importance_score
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/memory/store",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(f"Stored {memory_type} memory: {result['memory_id']}")
            return result["memory_id"]
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_memories(
        self,
        query: str,
        memory_types: List[str] = None,
        max_results: int = 10,
        time_range_hours: int = None,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Retrieve memories based on query."""
        try:
            payload = {
                "query_text": query,
                "memory_types": memory_types,
                "agent_id": self.agent_id,
                "user_id": self.user_id,
                "max_results": max_results,
                "similarity_threshold": similarity_threshold
            }
            
            if time_range_hours:
                payload["time_range_hours"] = time_range_hours
            
            response = await self.client.post(
                f"{self.base_url}/api/memory/retrieve",
                json=payload
            )
            response.raise_for_status()
            memories = response.json()
            
            self.logger.info(f"Retrieved {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memories: {e}")
            raise
    
    async def remember_conversation(self, content: str, context: Dict[str, Any] = None):
        """Store a conversation memory."""
        return await self.store_memory(
            memory_type="episodic",
            content=content,
            metadata={
                "type": "conversation",
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat()
            },
            importance_score=0.6
        )
    
    async def remember_fact(self, concept: str, definition: str, relations: List[str] = None):
        """Store a semantic fact/knowledge."""
        return await self.store_memory(
            memory_type="semantic",
            content=f"{concept}: {definition}",
            metadata={
                "concept": concept,
                "definition": definition,
                "relations": relations or [],
                "type": "fact"
            },
            importance_score=0.7
        )
    
    async def remember_skill(self, skill_name: str, procedure: str, success_rate: float = None):
        """Store a procedural skill/method."""
        return await self.store_memory(
            memory_type="procedural",
            content=procedure,
            metadata={
                "skill_name": skill_name,
                "success_rate": success_rate,
                "type": "skill",
                "domain": "general"
            },
            importance_score=0.8
        )
    
    async def recall_similar_experiences(self, current_situation: str, max_results: int = 5):
        """Recall similar past experiences."""
        return await self.retrieve_memories(
            query=current_situation,
            memory_types=["episodic"],
            max_results=max_results,
            similarity_threshold=0.6
        )
    
    async def recall_relevant_knowledge(self, topic: str, max_results: int = 10):
        """Recall relevant semantic knowledge."""
        return await self.retrieve_memories(
            query=topic,
            memory_types=["semantic"],
            max_results=max_results,
            similarity_threshold=0.7
        )
    
    async def recall_applicable_skills(self, task_description: str, max_results: int = 5):
        """Recall applicable procedural skills."""
        return await self.retrieve_memories(
            query=task_description,
            memory_types=["procedural"],
            max_results=max_results,
            similarity_threshold=0.6
        )
    
    async def share_knowledge_with(self, target_agent_id: str, knowledge_domain: str):
        """Share knowledge with another agent."""
        try:
            payload = {
                "source_agent_id": self.agent_id,
                "target_agent_id": target_agent_id,
                "knowledge_domain": knowledge_domain
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/knowledge/share",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(f"Shared knowledge with {target_agent_id}: {result['shared_items']} items")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to share knowledge: {e}")
            raise
    
    async def get_conversation_history(self, days_back: int = 7):
        """Get recent conversation history."""
        return await self.retrieve_memories(
            query="",  # Empty query to get all memories
            memory_types=["episodic"],
            time_range_hours=days_back * 24,
            max_results=100,
            similarity_threshold=0.0  # Include all memories
        )
    
    async def get_insights(self, hours_back: int = 24 * 7):
        """Get insights from stored memories."""
        try:
            params = {"hours_back": hours_back}
            if self.agent_id:
                params["agent_id"] = self.agent_id
            
            response = await self.client.get(
                f"{self.base_url}/api/memory/insights",
                params=params
            )
            response.raise_for_status()
            insights = response.json()
            
            self.logger.info("Retrieved memory insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get insights: {e}")
            raise
    
    async def consolidate_memories(self):
        """Trigger memory consolidation."""
        try:
            params = {}
            if self.agent_id:
                params["agent_id"] = self.agent_id
            
            response = await self.client.post(
                f"{self.base_url}/api/memory/consolidate",
                params=params
            )
            response.raise_for_status()
            result = response.json()
            
            self.logger.info("Memory consolidation triggered")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to consolidate memories: {e}")
            raise
    
    async def health_check(self):
        """Check if the global memory server is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise
    
    async def get_statistics(self):
        """Get memory system statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/api/statistics")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def process_cognition(self, ail_code: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Process AIL cognition through the /cognition endpoint."""
        try:
            payload = {
                "ail_code": ail_code,
                "agent_id": agent_id or self.agent_id,
                "user_id": self.user_id,
                "context": {
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/cognition",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Convert to the expected format
            return type('CognitionResponse', (), {
                'success': result.get('success', False),
                'execution_time_ms': result.get('execution_time_ms', 0),
                'result': result.get('result'),
                'error': result.get('error')
            })()
            
        except Exception as e:
            self.logger.error(f"Failed to process cognition: {e}")
            return type('CognitionResponse', (), {
                'success': False,
                'execution_time_ms': 0,
                'result': None,
                'error': str(e)
            })()
    
    # Context manager support
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Integration helper for LANS
class LANSMemoryIntegration:
    """Helper class for integrating Global Memory with LANS agents."""
    
    def __init__(self, gmcp_client: GMCPClient):
        self.gmcp = gmcp_client
    
    async def setup_agent_memory(self, agent_type: str, agent_id: str, user_id: str = None):
        """Setup memory for an LANS agent."""
        self.gmcp.configure_agent(agent_id, user_id)
        await self.gmcp.register_agent(agent_type, ["software_development", "project_generation", "code_analysis"])
    
    async def remember_task_execution(
        self, 
        task_description: str, 
        approach: str, 
        outcome: str, 
        metrics: Dict[str, Any]
    ):
        """Remember how a task was executed."""
        await self.gmcp.store_memory(
            memory_type="episodic",
            content=f"Task: {task_description}\nApproach: {approach}\nOutcome: {outcome}",
            metadata={
                "task_type": "project_generation",
                "approach": approach,
                "outcome": outcome,
                "metrics": metrics,
                "domain": "software_development"
            },
            importance_score=0.8 if outcome == "success" else 0.6
        )
    
    async def remember_code_pattern(self, pattern_name: str, code: str, use_case: str):
        """Remember a successful code pattern."""
        await self.gmcp.store_memory(
            memory_type="procedural",
            content=code,
            metadata={
                "pattern_name": pattern_name,
                "use_case": use_case,
                "language": "python",
                "framework": "general",
                "type": "code_pattern"
            },
            importance_score=0.7
        )
    
    async def remember_development_knowledge(self, concept: str, explanation: str, examples: List[str] = None):
        """Remember software development specific knowledge."""
        await self.gmcp.store_memory(
            memory_type="semantic",
            content=f"{concept}: {explanation}",
            metadata={
                "concept": concept,
                "domain": "software_development",
                "examples": examples or [],
                "type": "technical_knowledge"
            },
            importance_score=0.75
        )
    
    async def recall_for_planning(self, user_request: str):
        """Recall relevant memories for planning phase."""
        # Get similar past experiences
        experiences = await self.gmcp.recall_similar_experiences(user_request, max_results=5)
        
        # Get relevant ROS 2 knowledge
        knowledge = await self.gmcp.recall_relevant_knowledge(user_request, max_results=10)
        
        # Get applicable patterns and skills
        skills = await self.gmcp.recall_applicable_skills(user_request, max_results=5)
        
        return {
            "experiences": experiences,
            "knowledge": knowledge,
            "skills": skills
        }
    
    async def share_successful_approach(self, target_agent: str, domain: str = "software_development"):
        """Share successful approaches with other agents."""
        return await self.gmcp.share_knowledge_with(target_agent, domain)
