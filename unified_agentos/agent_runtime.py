"""
Unified Agent Runtime - Phase 1 Foundation
==========================================

A unified agent runtime environment that addresses the critical architectural
issues identified in the AgentOS analysis. This replaces the fragmented
agent lifecycle management with a clean, unified approach.

Key improvements:
- Simplified agent creation and initialization
- Unified agent identity and lifecycle management
- Proper resource cleanup and state tracking
- Integration with unified memory and communication systems
"""

import asyncio
import uuid
import logging
import weakref
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states"""
    CREATING = "creating"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    ERROR = "error"


class AgentCapability(Enum):
    """Standard agent capabilities"""
    MEMORY_ACCESS = "memory_access"
    COMMUNICATION = "communication"
    TOOL_EXECUTION = "tool_execution"
    PLANNING = "planning"
    LEARNING = "learning"
    COLLABORATION = "collaboration"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CREATIVE_WRITING = "creative_writing"


@dataclass
class AgentProfile:
    """Agent profile with identity and capabilities"""
    agent_id: str
    name: str
    agent_type: str
    capabilities: Set[AgentCapability]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentContext:
    """Agent execution context"""
    agent_id: str
    session_id: str
    working_memory: Dict[str, Any] = field(default_factory=dict)
    attention_focus: List[str] = field(default_factory=list)
    recent_activities: List[Dict[str, Any]] = field(default_factory=list)
    collaboration_partners: Set[str] = field(default_factory=set)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class AgentRegistry:
    """
    Centralized agent registry for identity and discovery.
    Addresses the agent identity management issues identified in the analysis.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentProfile] = {}
        self._agents_by_type: Dict[str, Set[str]] = {}
        self._agents_by_capability: Dict[AgentCapability, Set[str]] = {}
        self._lock = asyncio.Lock()
        logger.info("AgentRegistry initialized")
    
    async def register_agent(self, profile: AgentProfile) -> bool:
        """Register a new agent with the registry"""
        async with self._lock:
            if profile.agent_id in self._agents:
                logger.warning(f"Agent {profile.agent_id} already registered")
                return False
            
            # Store agent profile
            self._agents[profile.agent_id] = profile
            
            # Index by type
            if profile.agent_type not in self._agents_by_type:
                self._agents_by_type[profile.agent_type] = set()
            self._agents_by_type[profile.agent_type].add(profile.agent_id)
            
            # Index by capabilities
            for capability in profile.capabilities:
                if capability not in self._agents_by_capability:
                    self._agents_by_capability[capability] = set()
                self._agents_by_capability[capability].add(profile.agent_id)
            
            logger.info(f"Registered agent {profile.agent_id} ({profile.agent_type})")
            return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the registry"""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            profile = self._agents[agent_id]
            
            # Remove from indexes
            self._agents_by_type[profile.agent_type].discard(agent_id)
            for capability in profile.capabilities:
                self._agents_by_capability[capability].discard(agent_id)
            
            # Remove agent
            del self._agents[agent_id]
            
            logger.info(f"Unregistered agent {agent_id}")
            return True
    
    async def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Get agent profile by ID"""
        return self._agents.get(agent_id)
    
    async def find_agents_by_type(self, agent_type: str) -> List[AgentProfile]:
        """Find agents by type"""
        agent_ids = self._agents_by_type.get(agent_type, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    async def find_agents_by_capability(self, capability: AgentCapability) -> List[AgentProfile]:
        """Find agents by capability"""
        agent_ids = self._agents_by_capability.get(capability, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    async def get_all_agents(self) -> List[AgentProfile]:
        """Get all registered agents"""
        return list(self._agents.values())


class AgentRuntime:
    """
    Unified agent runtime environment.
    Addresses agent lifecycle and initialization complexity issues.
    """
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._agents: Dict[str, 'Agent'] = {}
        self._contexts: Dict[str, AgentContext] = {}
        self._states: Dict[str, AgentState] = {}
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}
        self._lock = None  # Will be created when needed
        self._shutdown = False
        self._maintenance_task = None
        self._initialized = False
        
        logger.info("AgentRuntime initialized")
    
    async def _ensure_initialized(self):
        """Ensure runtime is properly initialized"""
        if not self._initialized:
            self._lock = asyncio.Lock()
            # Start background maintenance
            self._maintenance_task = asyncio.create_task(self._background_maintenance())
            self._initialized = True
    
    async def create_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: Set[AgentCapability],
        agent_class: type,
        **kwargs
    ) -> str:
        """
        Create and register a new agent.
        Simplified agent creation addressing initialization complexity.
        """
        await self._ensure_initialized()
        
        agent_id = f"{agent_type}_{name}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Set state to creating
            self._states[agent_id] = AgentState.CREATING
            
            # Create agent profile
            profile = AgentProfile(
                agent_id=agent_id,
                name=name,
                agent_type=agent_type,
                capabilities=capabilities,
                metadata=kwargs.get('metadata', {})
            )
            
            # Register with registry
            if not await self.registry.register_agent(profile):
                raise RuntimeError(f"Failed to register agent {agent_id}")
            
            # Create agent context
            context = AgentContext(
                agent_id=agent_id,
                session_id=f"session_{uuid.uuid4().hex[:8]}"
            )
            self._contexts[agent_id] = context
            
            # Create agent instance
            agent = agent_class(agent_id=agent_id, context=context, **kwargs)
            self._agents[agent_id] = agent
            
            # Initialize agent
            await agent.initialize()
            
            # Set state to active
            self._states[agent_id] = AgentState.ACTIVE
            
            logger.info(f"Created agent {agent_id} ({agent_type})")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            await self._cleanup_failed_agent(agent_id)
            raise
    
    async def get_agent(self, agent_id: str) -> Optional['Agent']:
        """Get agent instance by ID"""
        await self._ensure_initialized()
        return self._agents.get(agent_id)
    
    async def get_agent_context(self, agent_id: str) -> Optional[AgentContext]:
        """Get agent context by ID"""
        return self._contexts.get(agent_id)
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state by ID"""
        return self._states.get(agent_id)
    
    async def suspend_agent(self, agent_id: str) -> bool:
        """Suspend an agent"""
        await self._ensure_initialized()
        if agent_id not in self._agents:
            return False
        
        try:
            self._states[agent_id] = AgentState.SUSPENDED
            await self._agents[agent_id].suspend()
            logger.info(f"Suspended agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to suspend agent {agent_id}: {e}")
            return False
    
    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a suspended agent"""
        if agent_id not in self._agents or self._states.get(agent_id) != AgentState.SUSPENDED:
            return False
        
        try:
            await self._agents[agent_id].resume()
            self._states[agent_id] = AgentState.ACTIVE
            logger.info(f"Resumed agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume agent {agent_id}: {e}")
            return False
    
    async def terminate_agent(self, agent_id: str, cleanup: bool = True) -> bool:
        """Terminate an agent with proper cleanup"""
        await self._ensure_initialized()
        if agent_id not in self._agents:
            return False
        
        try:
            self._states[agent_id] = AgentState.TERMINATING
            
            # Terminate agent
            await self._agents[agent_id].terminate()
            
            if cleanup:
                await self._cleanup_agent(agent_id)
            
            self._states[agent_id] = AgentState.TERMINATED
            logger.info(f"Terminated agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate agent {agent_id}: {e}")
            self._states[agent_id] = AgentState.ERROR
            return False
    
    async def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs"""
        return [
            aid for aid, state in self._states.items()
            if state == AgentState.ACTIVE
        ]
    
    async def shutdown(self):
        """Shutdown the runtime and cleanup all agents"""
        self._shutdown = True
        
        # Cancel maintenance task
        if self._maintenance_task:
            self._maintenance_task.cancel()
        
        # Terminate all agents
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            await self.terminate_agent(agent_id, cleanup=True)
        
        logger.info("AgentRuntime shutdown complete")
    
    async def _cleanup_agent(self, agent_id: str):
        """Cleanup agent resources"""
        try:
            # Unregister from registry
            await self.registry.unregister_agent(agent_id)
            
            # Remove from runtime
            self._agents.pop(agent_id, None)
            self._contexts.pop(agent_id, None)
            self._states.pop(agent_id, None)
            
            # Cancel any cleanup tasks
            if agent_id in self._cleanup_tasks:
                self._cleanup_tasks[agent_id].cancel()
                del self._cleanup_tasks[agent_id]
            
            logger.debug(f"Cleaned up agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up agent {agent_id}: {e}")
    
    async def _cleanup_failed_agent(self, agent_id: str):
        """Cleanup after failed agent creation"""
        try:
            await self.registry.unregister_agent(agent_id)
            self._agents.pop(agent_id, None)
            self._contexts.pop(agent_id, None)
            self._states.pop(agent_id, None)
        except Exception as e:
            logger.error(f"Error cleaning up failed agent {agent_id}: {e}")
    
    async def _background_maintenance(self):
        """Background maintenance for agent health monitoring"""
        while not self._shutdown:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                
                # Check agent health
                for agent_id, agent in list(self._agents.items()):
                    if hasattr(agent, 'health_check'):
                        try:
                            if not await agent.health_check():
                                logger.warning(f"Agent {agent_id} failed health check")
                        except Exception as e:
                            logger.error(f"Health check failed for agent {agent_id}: {e}")
                
                # Clean up terminated agents
                terminated_agents = [
                    aid for aid, state in self._states.items()
                    if state == AgentState.TERMINATED
                ]
                for agent_id in terminated_agents:
                    await self._cleanup_agent(agent_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background maintenance error: {e}")
        
        logger.info("Background maintenance stopped")


class Agent:
    """
    Base agent class for the unified runtime.
    Provides standard lifecycle methods and integration points.
    """
    
    def __init__(self, agent_id: str, context: AgentContext, **kwargs):
        self.agent_id = agent_id
        self.context = context
        self.config = kwargs
        self._initialized = False
        self._suspended = False
        logger.debug(f"Agent {agent_id} created")
    
    async def initialize(self):
        """Initialize the agent - called during creation"""
        self._initialized = True
        logger.debug(f"Agent {self.agent_id} initialized")
    
    async def suspend(self):
        """Suspend the agent - pause operations"""
        self._suspended = True
        logger.debug(f"Agent {self.agent_id} suspended")
    
    async def resume(self):
        """Resume the agent - restart operations"""
        self._suspended = False
        logger.debug(f"Agent {self.agent_id} resumed")
    
    async def terminate(self):
        """Terminate the agent - cleanup and shutdown"""
        logger.debug(f"Agent {self.agent_id} terminating")
    
    async def health_check(self) -> bool:
        """Health check - return True if agent is healthy"""
        return self._initialized and not self._suspended
    
    @property
    def is_active(self) -> bool:
        """Check if agent is active"""
        return self._initialized and not self._suspended


# Global registry and runtime instances
_global_registry = None
_global_runtime = None


async def get_global_registry() -> AgentRegistry:
    """Get the global agent registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


async def get_global_runtime() -> AgentRuntime:
    """Get the global agent runtime"""
    global _global_runtime, _global_registry
    if _global_runtime is None:
        if _global_registry is None:
            _global_registry = AgentRegistry()
        _global_runtime = AgentRuntime(_global_registry)
    return _global_runtime


async def create_agent(
    name: str,
    agent_type: str,
    capabilities: Set[AgentCapability],
    agent_class: type = Agent,
    **kwargs
) -> str:
    """Convenience function to create an agent using global runtime"""
    runtime = await get_global_runtime()
    return await runtime.create_agent(
        name=name,
        agent_type=agent_type,
        capabilities=capabilities,
        agent_class=agent_class,
        **kwargs
    )
