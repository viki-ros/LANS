"""
Attention Manager - Phase 2 Component
=====================================

The AttentionManager provides sophisticated attention control and focus
management for agents, enabling them to prioritize processing, filter
information, and maintain cognitive focus on relevant tasks and contexts.

Key Features:
- Dynamic attention allocation and priority management
- Context-aware focus shifting
- Information filtering and relevance scoring
- Attention persistence and restoration
- Multi-modal attention handling
- Cognitive load balancing
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timezone
from collections import defaultdict, deque

from .memory_interface import UnifiedMemoryInterface, MemoryType, MemoryItem, MemoryQuery
from .message_bus import UnifiedMessageBus, Message, MessageType, MessagePriority


class AttentionType(Enum):
    """Types of attention"""
    FOCUSED = "focused"          # Intense focus on specific task
    SELECTIVE = "selective"      # Filtering specific information
    DIVIDED = "divided"          # Multi-tasking attention
    SUSTAINED = "sustained"      # Long-term sustained attention
    EXECUTIVE = "executive"      # Meta-attention control


class AttentionScope(Enum):
    """Scope of attention"""
    IMMEDIATE = "immediate"      # Current task/context
    SHORT_TERM = "short_term"    # Recent context
    LONG_TERM = "long_term"      # Extended context
    GLOBAL = "global"            # All available context


class FocusState(Enum):
    """Current focus state"""
    SHARP = "sharp"              # Highly focused
    BROAD = "broad"              # Broad attention
    SCATTERED = "scattered"      # Unfocused
    TRANSITIONING = "transitioning"  # Changing focus


@dataclass
class AttentionTarget:
    """Target of attention"""
    target_id: str
    target_type: str  # 'task', 'memory', 'agent', 'context', etc.
    content: str
    priority: float = 0.5
    relevance: float = 0.5
    urgency: float = 0.5
    emotional_weight: float = 0.0
    temporal_weight: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttentionFilter:
    """Filter for attention processing"""
    filter_id: str
    filter_type: str  # 'relevance', 'priority', 'temporal', 'semantic', etc.
    criteria: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.5
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AttentionContext:
    """Context for attention processing"""
    agent_id: str
    session_id: str
    current_task: Optional[str] = None
    focus_targets: List[AttentionTarget] = field(default_factory=list)
    active_filters: List[AttentionFilter] = field(default_factory=list)
    attention_history: List[str] = field(default_factory=list)
    cognitive_load: float = 0.0
    interruption_tolerance: float = 0.5
    context_switch_cost: float = 0.3
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AttentionState:
    """Current attention state of an agent"""
    agent_id: str
    attention_type: AttentionType = AttentionType.SELECTIVE
    focus_state: FocusState = FocusState.BROAD
    attention_scope: AttentionScope = AttentionScope.IMMEDIATE
    primary_focus: Optional[AttentionTarget] = None
    secondary_focuses: List[AttentionTarget] = field(default_factory=list)
    attention_strength: float = 0.7
    focus_duration: float = 0.0
    last_shift: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    shift_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AttentionManager:
    """
    Sophisticated attention management system for agents.
    
    Manages attention allocation, focus control, information filtering,
    and cognitive load balancing to optimize agent performance.
    """
    
    def __init__(self, memory_interface: UnifiedMemoryInterface, message_bus: UnifiedMessageBus):
        self.memory_interface = memory_interface
        self.message_bus = message_bus
        self.logger = logging.getLogger(f"{__name__}.AttentionManager")
        
        # Attention state tracking
        self.agent_states: Dict[str, AttentionState] = {}
        self.attention_contexts: Dict[str, AttentionContext] = {}
        self.attention_targets: Dict[str, List[AttentionTarget]] = defaultdict(list)
        self.attention_filters: Dict[str, List[AttentionFilter]] = defaultdict(list)
        
        # Attention history
        self.attention_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Attention parameters
        self.max_primary_focus_targets = 1
        self.max_secondary_focus_targets = 3
        self.attention_decay_rate = 0.95
        self.focus_shift_threshold = 0.7
        self.cognitive_load_threshold = 0.8
        self.attention_update_interval = 2.0  # seconds
        
        # Background processing
        self._attention_loop_task = None
        self._running = False
    
    async def start(self):
        """Start the attention manager"""
        if self._running:
            return
        
        self._running = True
        self._attention_loop_task = asyncio.create_task(self._attention_loop())
        self.logger.info("Attention manager started")
    
    async def stop(self):
        """Stop the attention manager"""
        self._running = False
        if self._attention_loop_task:
            self._attention_loop_task.cancel()
            try:
                await self._attention_loop_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Attention manager stopped")
    
    async def _attention_loop(self):
        """Continuous attention processing loop"""
        while self._running:
            try:
                # Update attention for all active agents
                for agent_id in list(self.agent_states.keys()):
                    await self._update_attention(agent_id)
                
                await asyncio.sleep(self.attention_update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in attention loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_attention(self, agent_id: str):
        """Update attention state for an agent"""
        try:
            # Decay attention strengths
            await self._decay_attention(agent_id)
            
            # Check for focus shifts
            await self._check_focus_shifts(agent_id)
            
            # Update cognitive load
            await self._update_cognitive_load(agent_id)
            
            # Prune inactive targets
            await self._prune_inactive_targets(agent_id)
            
        except Exception as e:
            self.logger.error(f"Error updating attention for {agent_id}: {e}")
    
    async def register_agent(self, agent_id: str) -> AttentionState:
        """Register an agent with the attention manager"""
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = AttentionState(agent_id=agent_id)
            self.attention_contexts[agent_id] = AttentionContext(
                agent_id=agent_id,
                session_id=f"session_{int(time.time())}"
            )
            self.logger.info(f"Registered agent {agent_id} with attention manager")
        
        return self.agent_states[agent_id]
    
    async def set_primary_focus(self, agent_id: str, target: AttentionTarget) -> bool:
        """Set primary focus for an agent"""
        try:
            await self.register_agent(agent_id)
            
            state = self.agent_states[agent_id]
            context = self.attention_contexts[agent_id]
            
            # Store previous focus in history
            if state.primary_focus:
                self.attention_histories[agent_id].append({
                    'action': 'focus_shift',
                    'from': state.primary_focus.target_id,
                    'to': target.target_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            # Set new primary focus
            state.primary_focus = target
            state.last_shift = datetime.now(timezone.utc)
            state.shift_count += 1
            state.focus_state = FocusState.SHARP
            state.attention_type = AttentionType.FOCUSED
            
            # Add to targets list
            self.attention_targets[agent_id].append(target)
            
            # Update context
            context.current_task = target.target_id
            context.focus_targets = [target]
            
            self.logger.info(f"Set primary focus for {agent_id}: {target.target_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting primary focus for {agent_id}: {e}")
            return False
    
    async def add_secondary_focus(self, agent_id: str, target: AttentionTarget) -> bool:
        """Add secondary focus for an agent"""
        try:
            await self.register_agent(agent_id)
            
            state = self.agent_states[agent_id]
            
            # Check if we can add more secondary focuses
            if len(state.secondary_focuses) >= self.max_secondary_focus_targets:
                # Remove least relevant secondary focus
                state.secondary_focuses.sort(key=lambda t: t.relevance)
                removed = state.secondary_focuses.pop(0)
                self.logger.debug(f"Removed secondary focus: {removed.target_id}")
            
            # Add new secondary focus
            state.secondary_focuses.append(target)
            state.attention_type = AttentionType.DIVIDED
            
            # Add to targets list
            self.attention_targets[agent_id].append(target)
            
            self.logger.info(f"Added secondary focus for {agent_id}: {target.target_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding secondary focus for {agent_id}: {e}")
            return False
    
    async def shift_attention(self, agent_id: str, new_target: AttentionTarget, 
                            force: bool = False) -> bool:
        """Shift attention to a new target"""
        try:
            await self.register_agent(agent_id)
            
            state = self.agent_states[agent_id]
            context = self.attention_contexts[agent_id]
            
            # Check if shift is warranted
            if not force and state.primary_focus:
                # Calculate shift cost
                shift_cost = self._calculate_shift_cost(agent_id, new_target)
                if shift_cost > context.context_switch_cost:
                    self.logger.debug(f"Attention shift rejected due to high cost: {shift_cost}")
                    return False
            
            # Perform the shift
            if state.primary_focus:
                # Move current primary to secondary if space
                if len(state.secondary_focuses) < self.max_secondary_focus_targets:
                    state.secondary_focuses.append(state.primary_focus)
            
            # Set new primary focus
            await self.set_primary_focus(agent_id, new_target)
            
            # Update state
            state.focus_state = FocusState.TRANSITIONING
            state.attention_strength = max(0.5, state.attention_strength - context.context_switch_cost)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error shifting attention for {agent_id}: {e}")
            return False
    
    async def filter_information(self, agent_id: str, information: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter information based on current attention state"""
        try:
            if agent_id not in self.agent_states:
                return information  # No filtering if agent not registered
            
            state = self.agent_states[agent_id]
            context = self.attention_contexts[agent_id]
            
            filtered_info = []
            
            for item in information:
                relevance_score = await self._calculate_relevance(agent_id, item)
                
                # Apply attention filters
                if await self._passes_attention_filters(agent_id, item, relevance_score):
                    item['attention_score'] = relevance_score
                    filtered_info.append(item)
            
            # Sort by relevance
            filtered_info.sort(key=lambda x: x.get('attention_score', 0), reverse=True)
            
            # Limit based on attention scope
            max_items = self._get_attention_capacity(state.attention_scope)
            filtered_info = filtered_info[:max_items]
            
            self.logger.debug(f"Filtered {len(information)} items to {len(filtered_info)} for {agent_id}")
            return filtered_info
            
        except Exception as e:
            self.logger.error(f"Error filtering information for {agent_id}: {e}")
            return information
    
    async def _calculate_relevance(self, agent_id: str, item: Dict[str, Any]) -> float:
        """Calculate relevance score for an information item"""
        try:
            state = self.agent_states[agent_id]
            relevance = 0.0
            
            # Base relevance from content similarity
            content = str(item.get('content', ''))
            
            # Check relevance to primary focus
            if state.primary_focus:
                primary_content = state.primary_focus.content.lower()
                if primary_content in content.lower():
                    relevance += 0.8
                else:
                    # Simple word overlap
                    primary_words = set(primary_content.split())
                    content_words = set(content.lower().split())
                    overlap = len(primary_words.intersection(content_words))
                    if primary_words:
                        relevance += 0.5 * (overlap / len(primary_words))
            
            # Check relevance to secondary focuses
            for secondary in state.secondary_focuses:
                secondary_content = secondary.content.lower()
                if secondary_content in content.lower():
                    relevance += 0.3
            
            # Temporal relevance
            timestamp = item.get('timestamp')
            if timestamp:
                try:
                    item_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_diff = (datetime.now(timezone.utc) - item_time).total_seconds()
                    # More recent items are more relevant
                    temporal_factor = max(0, 1.0 - (time_diff / 86400))  # Decay over 24 hours
                    relevance += 0.2 * temporal_factor
                except:
                    pass
            
            # Priority boosting
            priority = item.get('priority', 0.5)
            relevance += 0.3 * priority
            
            return min(1.0, relevance)
            
        except Exception as e:
            self.logger.error(f"Error calculating relevance: {e}")
            return 0.5
    
    async def _passes_attention_filters(self, agent_id: str, item: Dict[str, Any], 
                                      relevance_score: float) -> bool:
        """Check if item passes attention filters"""
        try:
            filters = self.attention_filters.get(agent_id, [])
            
            for filter_obj in filters:
                if not filter_obj.active:
                    continue
                
                if filter_obj.filter_type == 'relevance':
                    if relevance_score < filter_obj.threshold:
                        return False
                
                elif filter_obj.filter_type == 'priority':
                    priority = item.get('priority', 0.5)
                    if priority < filter_obj.threshold:
                        return False
                
                elif filter_obj.filter_type == 'content':
                    required_terms = filter_obj.criteria.get('required_terms', [])
                    content = str(item.get('content', '')).lower()
                    if required_terms:
                        if not any(term.lower() in content for term in required_terms):
                            return False
                
                elif filter_obj.filter_type == 'agent':
                    allowed_agents = filter_obj.criteria.get('allowed_agents', [])
                    item_agent = item.get('agent_id', '')
                    if allowed_agents and item_agent not in allowed_agents:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking attention filters: {e}")
            return True
    
    def _get_attention_capacity(self, scope: AttentionScope) -> int:
        """Get attention capacity based on scope"""
        capacity_map = {
            AttentionScope.IMMEDIATE: 3,
            AttentionScope.SHORT_TERM: 7,
            AttentionScope.LONG_TERM: 15,
            AttentionScope.GLOBAL: 25
        }
        return capacity_map.get(scope, 7)
    
    def _calculate_shift_cost(self, agent_id: str, new_target: AttentionTarget) -> float:
        """Calculate cost of shifting attention to new target"""
        try:
            state = self.agent_states[agent_id]
            context = self.attention_contexts[agent_id]
            
            base_cost = context.context_switch_cost
            
            # Increase cost if current focus is highly relevant
            if state.primary_focus and state.primary_focus.relevance > 0.8:
                base_cost += 0.2
            
            # Decrease cost if new target is highly urgent
            if new_target.urgency > 0.8:
                base_cost -= 0.1
            
            # Increase cost based on recent shift frequency
            recent_shifts = sum(1 for entry in list(self.attention_histories[agent_id])[-10:] 
                              if entry.get('action') == 'focus_shift')
            base_cost += recent_shifts * 0.05
            
            return max(0.0, min(1.0, base_cost))
            
        except Exception as e:
            self.logger.error(f"Error calculating shift cost: {e}")
            return context.context_switch_cost if context else 0.3
    
    async def _decay_attention(self, agent_id: str):
        """Decay attention strengths over time"""
        try:
            state = self.agent_states[agent_id]
            
            # Decay primary focus
            if state.primary_focus:
                state.primary_focus.relevance *= self.attention_decay_rate
                state.primary_focus.priority *= self.attention_decay_rate
            
            # Decay secondary focuses
            for target in state.secondary_focuses:
                target.relevance *= self.attention_decay_rate
                target.priority *= self.attention_decay_rate
            
            # Decay overall attention strength
            state.attention_strength *= self.attention_decay_rate
            
        except Exception as e:
            self.logger.error(f"Error decaying attention for {agent_id}: {e}")
    
    async def _check_focus_shifts(self, agent_id: str):
        """Check if focus should shift based on attention dynamics"""
        try:
            state = self.agent_states[agent_id]
            
            # Check if primary focus is still strong enough
            if state.primary_focus and state.primary_focus.relevance < self.focus_shift_threshold:
                # Look for stronger secondary focus
                if state.secondary_focuses:
                    strongest_secondary = max(state.secondary_focuses, key=lambda t: t.relevance)
                    if strongest_secondary.relevance > state.primary_focus.relevance + 0.1:
                        # Shift to strongest secondary
                        state.secondary_focuses.remove(strongest_secondary)
                        old_primary = state.primary_focus
                        state.primary_focus = strongest_secondary
                        state.secondary_focuses.append(old_primary)
                        
                        self.logger.info(f"Auto-shifted primary focus for {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error checking focus shifts for {agent_id}: {e}")
    
    async def _update_cognitive_load(self, agent_id: str):
        """Update cognitive load based on attention state"""
        try:
            state = self.agent_states[agent_id]
            context = self.attention_contexts[agent_id]
            
            load = 0.0
            
            # Base load from primary focus
            if state.primary_focus:
                load += 0.3
            
            # Additional load from secondary focuses
            load += len(state.secondary_focuses) * 0.2
            
            # Load from attention type
            type_load_map = {
                AttentionType.FOCUSED: 0.1,
                AttentionType.SELECTIVE: 0.2,
                AttentionType.DIVIDED: 0.5,
                AttentionType.SUSTAINED: 0.3,
                AttentionType.EXECUTIVE: 0.4
            }
            load += type_load_map.get(state.attention_type, 0.2)
            
            # Load from recent attention shifts
            recent_shifts = sum(1 for entry in list(self.attention_histories[agent_id])[-5:] 
                              if entry.get('action') == 'focus_shift')
            load += recent_shifts * 0.1
            
            context.cognitive_load = min(1.0, load)
            
            # Adjust attention capacity based on load
            if context.cognitive_load > self.cognitive_load_threshold:
                # Reduce secondary focuses if overloaded
                if len(state.secondary_focuses) > 1:
                    # Remove least relevant secondary focus
                    state.secondary_focuses.sort(key=lambda t: t.relevance)
                    removed = state.secondary_focuses.pop(0)
                    self.logger.debug(f"Removed secondary focus due to cognitive load: {removed.target_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating cognitive load for {agent_id}: {e}")
    
    async def _prune_inactive_targets(self, agent_id: str):
        """Remove inactive or irrelevant attention targets"""
        try:
            targets = self.attention_targets[agent_id]
            current_time = datetime.now(timezone.utc)
            
            # Remove targets that haven't been accessed recently and have low relevance
            active_targets = []
            for target in targets:
                time_since_access = (current_time - target.last_accessed).total_seconds()
                if time_since_access < 3600 or target.relevance > 0.3:  # Keep if accessed within hour or still relevant
                    active_targets.append(target)
                else:
                    self.logger.debug(f"Pruned inactive target: {target.target_id}")
            
            self.attention_targets[agent_id] = active_targets
            
        except Exception as e:
            self.logger.error(f"Error pruning inactive targets for {agent_id}: {e}")
    
    async def add_attention_filter(self, agent_id: str, filter_obj: AttentionFilter) -> bool:
        """Add an attention filter for an agent"""
        try:
            await self.register_agent(agent_id)
            self.attention_filters[agent_id].append(filter_obj)
            self.logger.info(f"Added attention filter for {agent_id}: {filter_obj.filter_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding attention filter for {agent_id}: {e}")
            return False
    
    async def remove_attention_filter(self, agent_id: str, filter_id: str) -> bool:
        """Remove an attention filter for an agent"""
        try:
            filters = self.attention_filters.get(agent_id, [])
            original_count = len(filters)
            self.attention_filters[agent_id] = [f for f in filters if f.filter_id != filter_id]
            
            removed = original_count - len(self.attention_filters[agent_id])
            if removed > 0:
                self.logger.info(f"Removed attention filter for {agent_id}: {filter_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing attention filter for {agent_id}: {e}")
            return False
    
    async def get_attention_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get attention summary for an agent"""
        try:
            if agent_id not in self.agent_states:
                return {'error': 'Agent not registered'}
            
            state = self.agent_states[agent_id]
            context = self.attention_contexts[agent_id]
            
            return {
                'agent_id': agent_id,
                'attention_type': state.attention_type.value,
                'focus_state': state.focus_state.value,
                'attention_scope': state.attention_scope.value,
                'attention_strength': state.attention_strength,
                'cognitive_load': context.cognitive_load,
                'primary_focus': {
                    'target_id': state.primary_focus.target_id,
                    'relevance': state.primary_focus.relevance,
                    'priority': state.primary_focus.priority
                } if state.primary_focus else None,
                'secondary_focuses': [
                    {
                        'target_id': target.target_id,
                        'relevance': target.relevance,
                        'priority': target.priority
                    } for target in state.secondary_focuses
                ],
                'active_filters': len(self.attention_filters.get(agent_id, [])),
                'focus_shift_count': state.shift_count,
                'last_shift': state.last_shift.isoformat() if state.last_shift else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting attention summary for {agent_id}: {e}")
            return {'error': str(e)}
    
    def get_attention_history(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get attention history for an agent"""
        history = list(self.attention_histories.get(agent_id, deque()))
        return history[-limit:] if history else []


# Global attention manager instance
_global_attention_manager: Optional[AttentionManager] = None


def get_attention_manager(memory_interface: Optional[UnifiedMemoryInterface] = None,
                         message_bus: Optional[UnifiedMessageBus] = None) -> AttentionManager:
    """Get the global attention manager instance"""
    global _global_attention_manager
    
    if _global_attention_manager is None:
        if memory_interface is None:
            from .memory_interface import get_memory_interface
            memory_interface = get_memory_interface()
        
        if message_bus is None:
            from .message_bus import get_message_bus
            message_bus = get_message_bus()
        
        _global_attention_manager = AttentionManager(memory_interface, message_bus)
    
    return _global_attention_manager


async def set_agent_focus(agent_id: str, target_id: str, content: str, 
                         priority: float = 0.7, relevance: float = 0.7) -> bool:
    """Helper function to set agent focus"""
    manager = get_attention_manager()
    target = AttentionTarget(
        target_id=target_id,
        target_type='task',
        content=content,
        priority=priority,
        relevance=relevance
    )
    return await manager.set_primary_focus(agent_id, target)


async def filter_agent_information(agent_id: str, information: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper function to filter information for an agent"""
    manager = get_attention_manager()
    return await manager.filter_information(agent_id, information)
