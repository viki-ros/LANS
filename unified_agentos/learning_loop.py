"""
Learning Loop - Phase 2 Component
=================================

The LearningLoop provides adaptive learning capabilities for agents,
enabling continuous learning from experiences, feedback integration,
knowledge consolidation, and behavioral adaptation based on outcomes.

Key Features:
- Experience-based learning from interactions
- Feedback integration and error correction
- Knowledge consolidation and pattern extraction
- Behavioral adaptation and strategy optimization
- Multi-modal learning (observation, instruction, experimentation)
- Transfer learning between contexts and agents
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from collections import defaultdict, deque
import numpy as np

from .memory_interface import UnifiedMemoryInterface, MemoryType, MemoryItem, MemoryQuery
from .message_bus import UnifiedMessageBus, Message, MessageType, MessagePriority
from .cognitive_engine import CognitiveEngine, CognitiveProcessType, CognitiveResult


class LearningType(Enum):
    """Types of learning"""
    EXPERIENTIAL = "experiential"      # Learning from direct experience
    OBSERVATIONAL = "observational"    # Learning from observing others
    INSTRUCTIONAL = "instructional"    # Learning from explicit instruction
    REFLECTIVE = "reflective"          # Learning from self-reflection
    COLLABORATIVE = "collaborative"    # Learning from collaboration
    EXPERIMENTAL = "experimental"      # Learning from experimentation


class LearningMode(Enum):
    """Learning modes"""
    PASSIVE = "passive"                # Background learning
    ACTIVE = "active"                  # Intentional learning
    ADAPTIVE = "adaptive"              # Context-adaptive learning
    EXPLORATIVE = "explorative"        # Exploration-based learning


class KnowledgeType(Enum):
    """Types of knowledge"""
    FACTUAL = "factual"                # Facts and information
    PROCEDURAL = "procedural"          # How-to knowledge
    CONCEPTUAL = "conceptual"          # Concepts and relationships
    METACOGNITIVE = "metacognitive"    # Knowledge about knowledge
    STRATEGIC = "strategic"            # Strategic knowledge
    CONTEXTUAL = "contextual"          # Context-specific knowledge


@dataclass
class LearningExperience:
    """An experience that can be learned from"""
    experience_id: str
    agent_id: str
    learning_type: LearningType
    context: Dict[str, Any] = field(default_factory=dict)
    action_taken: str = ""
    outcome: Dict[str, Any] = field(default_factory=dict)
    feedback: Dict[str, Any] = field(default_factory=dict)
    success_score: float = 0.5
    confidence: float = 0.5
    extractable_knowledge: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningPattern:
    """A learned pattern or rule"""
    pattern_id: str
    agent_id: str
    pattern_type: str  # 'causal', 'temporal', 'conditional', etc.
    condition: str
    action: str
    outcome: str
    confidence: float = 0.5
    support_count: int = 1
    contradiction_count: int = 0
    contexts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeItem:
    """A piece of learned knowledge"""
    knowledge_id: str
    agent_id: str
    knowledge_type: KnowledgeType
    content: str
    confidence: float = 0.5
    source: str = "learning"
    evidence_count: int = 1
    contradiction_count: int = 0
    applicability_contexts: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningGoal:
    """A learning objective"""
    goal_id: str
    agent_id: str
    objective: str
    target_knowledge: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    priority: float = 0.5
    deadline: Optional[datetime] = None
    strategies: List[str] = field(default_factory=list)
    status: str = "active"  # 'active', 'completed', 'paused', 'abandoned'
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningState:
    """Current learning state of an agent"""
    agent_id: str
    learning_mode: LearningMode = LearningMode.ADAPTIVE
    active_goals: List[LearningGoal] = field(default_factory=list)
    recent_experiences: deque = field(default_factory=lambda: deque(maxlen=50))
    learned_patterns: Dict[str, LearningPattern] = field(default_factory=dict)
    knowledge_base: Dict[str, KnowledgeItem] = field(default_factory=dict)
    learning_efficiency: float = 0.5
    exploration_rate: float = 0.3
    consolidation_threshold: float = 0.7
    last_learning_event: Optional[datetime] = None
    total_learning_events: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LearningLoop:
    """
    Adaptive learning system for agents.
    
    Provides continuous learning capabilities through experience processing,
    pattern extraction, knowledge consolidation, and behavioral adaptation.
    """
    
    def __init__(self, memory_interface: UnifiedMemoryInterface, 
                 message_bus: UnifiedMessageBus, 
                 cognitive_engine: Optional[CognitiveEngine] = None):
        self.memory_interface = memory_interface
        self.message_bus = message_bus
        self.cognitive_engine = cognitive_engine
        self.logger = logging.getLogger(f"{__name__}.LearningLoop")
        
        # Learning state tracking
        self.agent_states: Dict[str, LearningState] = {}
        self.pending_experiences: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.learning_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        
        # Learning parameters
        self.min_pattern_support = 3
        self.max_pattern_contradictions = 1
        self.knowledge_confidence_threshold = 0.6
        self.experience_batch_size = 5
        self.learning_update_interval = 10.0  # seconds
        self.consolidation_interval = 60.0    # seconds
        
        # Learning strategies
        self.learning_strategies: Dict[LearningType, Callable] = {}
        self._register_learning_strategies()
        
        # Background processing
        self._learning_loop_task = None
        self._consolidation_task = None
        self._running = False
    
    def _register_learning_strategies(self):
        """Register learning strategy handlers"""
        self.learning_strategies = {
            LearningType.EXPERIENTIAL: self._process_experiential_learning,
            LearningType.OBSERVATIONAL: self._process_observational_learning,
            LearningType.INSTRUCTIONAL: self._process_instructional_learning,
            LearningType.REFLECTIVE: self._process_reflective_learning,
            LearningType.COLLABORATIVE: self._process_collaborative_learning,
            LearningType.EXPERIMENTAL: self._process_experimental_learning,
        }
    
    async def start(self):
        """Start the learning loop"""
        if self._running:
            return
        
        self._running = True
        self._learning_loop_task = asyncio.create_task(self._learning_loop())
        self._consolidation_task = asyncio.create_task(self._consolidation_loop())
        self.logger.info("Learning loop started")
    
    async def stop(self):
        """Stop the learning loop"""
        self._running = False
        
        if self._learning_loop_task:
            self._learning_loop_task.cancel()
            try:
                await self._learning_loop_task
            except asyncio.CancelledError:
                pass
        
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Learning loop stopped")
    
    async def _learning_loop(self):
        """Main learning processing loop"""
        while self._running:
            try:
                # Process pending experiences for all agents
                for agent_id in list(self.pending_experiences.keys()):
                    await self._process_pending_experiences(agent_id)
                
                await asyncio.sleep(self.learning_update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _consolidation_loop(self):
        """Knowledge consolidation loop"""
        while self._running:
            try:
                # Consolidate knowledge for all agents
                for agent_id in list(self.agent_states.keys()):
                    await self._consolidate_knowledge(agent_id)
                
                await asyncio.sleep(self.consolidation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in consolidation loop: {e}")
                await asyncio.sleep(5.0)
    
    async def register_agent(self, agent_id: str) -> LearningState:
        """Register an agent with the learning loop"""
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = LearningState(agent_id=agent_id)
            self.logger.info(f"Registered agent {agent_id} with learning loop")
        
        return self.agent_states[agent_id]
    
    async def add_learning_experience(self, experience: LearningExperience) -> bool:
        """Add a learning experience for processing"""
        try:
            await self.register_agent(experience.agent_id)
            
            # Add to pending experiences
            self.pending_experiences[experience.agent_id].append(experience)
            
            # Update learning state
            state = self.agent_states[experience.agent_id]
            state.recent_experiences.append(experience)
            state.last_learning_event = datetime.now(timezone.utc)
            state.total_learning_events += 1
            
            self.logger.debug(f"Added learning experience for {experience.agent_id}: {experience.experience_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding learning experience: {e}")
            return False
    
    async def _process_pending_experiences(self, agent_id: str):
        """Process pending learning experiences for an agent"""
        try:
            pending = self.pending_experiences[agent_id]
            if not pending:
                return
            
            # Process experiences in batches
            batch = []
            while pending and len(batch) < self.experience_batch_size:
                batch.append(pending.popleft())
            
            if not batch:
                return
            
            # Process each experience
            for experience in batch:
                await self._process_learning_experience(experience)
            
            self.logger.debug(f"Processed {len(batch)} learning experiences for {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing pending experiences for {agent_id}: {e}")
    
    async def _process_learning_experience(self, experience: LearningExperience):
        """Process a single learning experience"""
        try:
            # Get appropriate learning strategy
            strategy = self.learning_strategies.get(experience.learning_type)
            if not strategy:
                self.logger.warning(f"No strategy for learning type: {experience.learning_type}")
                return
            
            # Process the experience
            learning_result = await strategy(experience)
            
            # Extract patterns and knowledge
            await self._extract_patterns(experience, learning_result)
            await self._extract_knowledge(experience, learning_result)
            
            # Update learning efficiency
            await self._update_learning_efficiency(experience.agent_id, learning_result)
            
            # Mark as processed
            experience.processed = True
            
            # Store learning event in history
            self.learning_histories[experience.agent_id].append({
                'experience_id': experience.experience_id,
                'learning_type': experience.learning_type.value,
                'success_score': experience.success_score,
                'knowledge_extracted': len(learning_result.get('knowledge_items', [])),
                'patterns_extracted': len(learning_result.get('patterns', [])),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error processing learning experience {experience.experience_id}: {e}")
    
    async def _process_experiential_learning(self, experience: LearningExperience) -> Dict[str, Any]:
        """Process experiential learning"""
        try:
            result = {
                'knowledge_items': [],
                'patterns': [],
                'insights': []
            }
            
            # Extract action-outcome relationships
            if experience.action_taken and experience.outcome:
                # Create causal pattern
                pattern = LearningPattern(
                    pattern_id=f"pattern_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    pattern_type="causal",
                    condition=json.dumps(experience.context),
                    action=experience.action_taken,
                    outcome=json.dumps(experience.outcome),
                    confidence=experience.success_score,
                    contexts=[json.dumps(experience.context)]
                )
                result['patterns'].append(pattern)
            
            # Extract procedural knowledge
            if experience.success_score > 0.7:
                knowledge = KnowledgeItem(
                    knowledge_id=f"knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    knowledge_type=KnowledgeType.PROCEDURAL,
                    content=f"In context {experience.context}, action '{experience.action_taken}' leads to {experience.outcome}",
                    confidence=experience.success_score,
                    source="experiential_learning",
                    applicability_contexts=[json.dumps(experience.context)]
                )
                result['knowledge_items'].append(knowledge)
            
            # Extract insights from feedback
            if experience.feedback:
                insight = f"Feedback on '{experience.action_taken}': {experience.feedback}"
                result['insights'].append(insight)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in experiential learning: {e}")
            return {'knowledge_items': [], 'patterns': [], 'insights': []}
    
    async def _process_observational_learning(self, experience: LearningExperience) -> Dict[str, Any]:
        """Process observational learning"""
        try:
            result = {
                'knowledge_items': [],
                'patterns': [],
                'insights': []
            }
            
            # Extract patterns from observed behavior
            observed_agent = experience.context.get('observed_agent')
            observed_action = experience.context.get('observed_action')
            observed_outcome = experience.context.get('observed_outcome')
            
            if observed_action and observed_outcome:
                # Create observational pattern
                pattern = LearningPattern(
                    pattern_id=f"obs_pattern_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    pattern_type="observational",
                    condition=json.dumps(experience.context),
                    action=observed_action,
                    outcome=json.dumps(observed_outcome),
                    confidence=experience.confidence * 0.8,  # Slightly lower confidence for observed learning
                    contexts=[json.dumps(experience.context)]
                )
                result['patterns'].append(pattern)
                
                # Create strategic knowledge
                knowledge = KnowledgeItem(
                    knowledge_id=f"obs_knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    knowledge_type=KnowledgeType.STRATEGIC,
                    content=f"Observed: {observed_agent} used '{observed_action}' resulting in {observed_outcome}",
                    confidence=experience.confidence * 0.8,
                    source="observational_learning"
                )
                result['knowledge_items'].append(knowledge)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in observational learning: {e}")
            return {'knowledge_items': [], 'patterns': [], 'insights': []}
    
    async def _process_instructional_learning(self, experience: LearningExperience) -> Dict[str, Any]:
        """Process instructional learning"""
        try:
            result = {
                'knowledge_items': [],
                'patterns': [],
                'insights': []
            }
            
            instruction = experience.context.get('instruction', '')
            instructor = experience.context.get('instructor', 'unknown')
            
            if instruction:
                # Create factual knowledge
                knowledge = KnowledgeItem(
                    knowledge_id=f"inst_knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    knowledge_type=KnowledgeType.FACTUAL,
                    content=instruction,
                    confidence=experience.confidence,
                    source=f"instruction_from_{instructor}"
                )
                result['knowledge_items'].append(knowledge)
                
                # Extract any procedural steps
                if any(word in instruction.lower() for word in ['how to', 'step', 'procedure', 'process']):
                    proc_knowledge = KnowledgeItem(
                        knowledge_id=f"proc_knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                        agent_id=experience.agent_id,
                        knowledge_type=KnowledgeType.PROCEDURAL,
                        content=instruction,
                        confidence=experience.confidence,
                        source=f"instruction_from_{instructor}"
                    )
                    result['knowledge_items'].append(proc_knowledge)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in instructional learning: {e}")
            return {'knowledge_items': [], 'patterns': [], 'insights': []}
    
    async def _process_reflective_learning(self, experience: LearningExperience) -> Dict[str, Any]:
        """Process reflective learning"""
        try:
            result = {
                'knowledge_items': [],
                'patterns': [],
                'insights': []
            }
            
            # Use cognitive engine for reflection if available
            if self.cognitive_engine:
                reflection_result = await self.cognitive_engine.process_cognitive_request(
                    agent_id=experience.agent_id,
                    process_type=CognitiveProcessType.REFLECTION,
                    input_data={
                        'experience': experience.context,
                        'action': experience.action_taken,
                        'outcome': experience.outcome,
                        'success_score': experience.success_score
                    }
                )
                
                # Extract insights from reflection
                for insight in reflection_result.reasoning_trace:
                    result['insights'].append(insight)
                
                # Create metacognitive knowledge
                if reflection_result.result_data.get('insights'):
                    for insight in reflection_result.result_data['insights']:
                        knowledge = KnowledgeItem(
                            knowledge_id=f"meta_knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                            agent_id=experience.agent_id,
                            knowledge_type=KnowledgeType.METACOGNITIVE,
                            content=insight,
                            confidence=reflection_result.confidence,
                            source="reflective_learning"
                        )
                        result['knowledge_items'].append(knowledge)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in reflective learning: {e}")
            return {'knowledge_items': [], 'patterns': [], 'insights': []}
    
    async def _process_collaborative_learning(self, experience: LearningExperience) -> Dict[str, Any]:
        """Process collaborative learning"""
        try:
            result = {
                'knowledge_items': [],
                'patterns': [],
                'insights': []
            }
            
            collaborators = experience.context.get('collaborators', [])
            shared_knowledge = experience.context.get('shared_knowledge', [])
            collaboration_outcome = experience.outcome
            
            # Extract collaborative patterns
            if collaborators and collaboration_outcome:
                pattern = LearningPattern(
                    pattern_id=f"collab_pattern_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    pattern_type="collaborative",
                    condition=f"collaborating_with_{len(collaborators)}_agents",
                    action=experience.action_taken,
                    outcome=json.dumps(collaboration_outcome),
                    confidence=experience.success_score,
                    contexts=[json.dumps(experience.context)]
                )
                result['patterns'].append(pattern)
            
            # Extract shared knowledge
            for knowledge_item in shared_knowledge:
                knowledge = KnowledgeItem(
                    knowledge_id=f"shared_knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    knowledge_type=KnowledgeType.CONCEPTUAL,
                    content=str(knowledge_item),
                    confidence=experience.confidence * 0.9,  # High confidence in shared knowledge
                    source="collaborative_learning"
                )
                result['knowledge_items'].append(knowledge)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in collaborative learning: {e}")
            return {'knowledge_items': [], 'patterns': [], 'insights': []}
    
    async def _process_experimental_learning(self, experience: LearningExperience) -> Dict[str, Any]:
        """Process experimental learning"""
        try:
            result = {
                'knowledge_items': [],
                'patterns': [],
                'insights': []
            }
            
            hypothesis = experience.context.get('hypothesis', '')
            experiment_result = experience.outcome
            variables = experience.context.get('variables', {})
            
            # Extract experimental patterns
            if hypothesis and experiment_result:
                pattern = LearningPattern(
                    pattern_id=f"exp_pattern_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    pattern_type="experimental",
                    condition=f"hypothesis: {hypothesis}",
                    action=f"experiment with variables: {variables}",
                    outcome=json.dumps(experiment_result),
                    confidence=experience.success_score,
                    contexts=[json.dumps(experience.context)]
                )
                result['patterns'].append(pattern)
                
                # Create factual knowledge about the experiment
                knowledge = KnowledgeItem(
                    knowledge_id=f"exp_knowledge_{experience.agent_id}_{int(time.time() * 1000)}",
                    agent_id=experience.agent_id,
                    knowledge_type=KnowledgeType.FACTUAL,
                    content=f"Experimental finding: {hypothesis} -> {experiment_result}",
                    confidence=experience.success_score,
                    source="experimental_learning"
                )
                result['knowledge_items'].append(knowledge)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in experimental learning: {e}")
            return {'knowledge_items': [], 'patterns': [], 'insights': []}
    
    async def _extract_patterns(self, experience: LearningExperience, learning_result: Dict[str, Any]):
        """Extract and store learning patterns"""
        try:
            state = self.agent_states[experience.agent_id]
            
            for pattern in learning_result.get('patterns', []):
                # Check if similar pattern already exists
                existing_pattern = await self._find_similar_pattern(experience.agent_id, pattern)
                
                if existing_pattern:
                    # Update existing pattern
                    existing_pattern.support_count += 1
                    existing_pattern.confidence = (existing_pattern.confidence + pattern.confidence) / 2
                    existing_pattern.last_updated = datetime.now(timezone.utc)
                    if pattern.contexts[0] not in existing_pattern.contexts:
                        existing_pattern.contexts.extend(pattern.contexts)
                else:
                    # Store new pattern
                    state.learned_patterns[pattern.pattern_id] = pattern
                
                self.logger.debug(f"Extracted pattern for {experience.agent_id}: {pattern.pattern_id}")
                
        except Exception as e:
            self.logger.error(f"Error extracting patterns: {e}")
    
    async def _extract_knowledge(self, experience: LearningExperience, learning_result: Dict[str, Any]):
        """Extract and store knowledge items"""
        try:
            state = self.agent_states[experience.agent_id]
            
            for knowledge in learning_result.get('knowledge_items', []):
                # Check if similar knowledge already exists
                existing_knowledge = await self._find_similar_knowledge(experience.agent_id, knowledge)
                
                if existing_knowledge:
                    # Update existing knowledge
                    existing_knowledge.evidence_count += 1
                    existing_knowledge.confidence = (existing_knowledge.confidence + knowledge.confidence) / 2
                    existing_knowledge.last_updated = datetime.now(timezone.utc)
                else:
                    # Store new knowledge
                    state.knowledge_base[knowledge.knowledge_id] = knowledge
                    
                    # Also store in memory interface
                    memory_item = MemoryItem(
                        memory_id=f"knowledge_{experience.agent_id}_{knowledge.knowledge_id}",
                        agent_id=experience.agent_id,
                        memory_type=MemoryType.SEMANTIC,
                        content=knowledge.content,
                        metadata={
                            'knowledge_type': knowledge.knowledge_type.value,
                            'confidence': knowledge.confidence,
                            'source': knowledge.source,
                            'learning_timestamp': datetime.now(timezone.utc).isoformat()
                        }
                    )
                    await self.memory_interface.store_memory_item(memory_item)
                
                self.logger.debug(f"Extracted knowledge for {experience.agent_id}: {knowledge.knowledge_id}")
                
        except Exception as e:
            self.logger.error(f"Error extracting knowledge: {e}")
    
    async def _find_similar_pattern(self, agent_id: str, pattern: LearningPattern) -> Optional[LearningPattern]:
        """Find similar existing pattern"""
        try:
            state = self.agent_states[agent_id]
            
            for existing_pattern in state.learned_patterns.values():
                if (existing_pattern.pattern_type == pattern.pattern_type and
                    existing_pattern.condition == pattern.condition and
                    existing_pattern.action == pattern.action):
                    return existing_pattern
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding similar pattern: {e}")
            return None
    
    async def _find_similar_knowledge(self, agent_id: str, knowledge: KnowledgeItem) -> Optional[KnowledgeItem]:
        """Find similar existing knowledge"""
        try:
            state = self.agent_states[agent_id]
            
            for existing_knowledge in state.knowledge_base.values():
                if (existing_knowledge.knowledge_type == knowledge.knowledge_type and
                    existing_knowledge.content.lower() == knowledge.content.lower()):
                    return existing_knowledge
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding similar knowledge: {e}")
            return None
    
    async def _update_learning_efficiency(self, agent_id: str, learning_result: Dict[str, Any]):
        """Update learning efficiency metrics"""
        try:
            state = self.agent_states[agent_id]
            
            # Calculate learning efficiency based on knowledge and patterns extracted
            knowledge_count = len(learning_result.get('knowledge_items', []))
            pattern_count = len(learning_result.get('patterns', []))
            
            efficiency_score = min(1.0, (knowledge_count + pattern_count) / 3.0)
            
            # Update running average
            state.learning_efficiency = (state.learning_efficiency * 0.9) + (efficiency_score * 0.1)
            
        except Exception as e:
            self.logger.error(f"Error updating learning efficiency: {e}")
    
    async def _consolidate_knowledge(self, agent_id: str):
        """Consolidate and optimize agent's knowledge base"""
        try:
            state = self.agent_states[agent_id]
            
            # Strengthen high-confidence patterns
            for pattern in state.learned_patterns.values():
                if pattern.support_count >= self.min_pattern_support:
                    pattern.confidence = min(1.0, pattern.confidence * 1.05)
            
            # Remove contradicted patterns
            patterns_to_remove = []
            for pattern_id, pattern in state.learned_patterns.items():
                if pattern.contradiction_count > self.max_pattern_contradictions:
                    patterns_to_remove.append(pattern_id)
            
            for pattern_id in patterns_to_remove:
                del state.learned_patterns[pattern_id]
                self.logger.debug(f"Removed contradicted pattern: {pattern_id}")
            
            # Consolidate related knowledge
            await self._consolidate_related_knowledge(agent_id)
            
            self.logger.debug(f"Consolidated knowledge for {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error consolidating knowledge for {agent_id}: {e}")
    
    async def _consolidate_related_knowledge(self, agent_id: str):
        """Consolidate related knowledge items"""
        try:
            state = self.agent_states[agent_id]
            
            # Group knowledge by type and similarity
            knowledge_groups = defaultdict(list)
            for knowledge in state.knowledge_base.values():
                key = f"{knowledge.knowledge_type.value}_{knowledge.content[:50]}"
                knowledge_groups[key].append(knowledge)
            
            # Merge similar knowledge items
            for group in knowledge_groups.values():
                if len(group) > 1:
                    # Keep the highest confidence item and merge evidence
                    primary = max(group, key=lambda k: k.confidence)
                    for other in group:
                        if other != primary:
                            primary.evidence_count += other.evidence_count
                            primary.contradiction_count += other.contradiction_count
                            # Remove the merged item
                            if other.knowledge_id in state.knowledge_base:
                                del state.knowledge_base[other.knowledge_id]
            
        except Exception as e:
            self.logger.error(f"Error consolidating related knowledge: {e}")
    
    async def set_learning_goal(self, agent_id: str, goal: LearningGoal) -> bool:
        """Set a learning goal for an agent"""
        try:
            await self.register_agent(agent_id)
            state = self.agent_states[agent_id]
            
            state.active_goals.append(goal)
            self.logger.info(f"Set learning goal for {agent_id}: {goal.objective}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting learning goal: {e}")
            return False
    
    async def get_learning_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get learning recommendations for an agent"""
        try:
            if agent_id not in self.agent_states:
                return []
            
            state = self.agent_states[agent_id]
            recommendations = []
            
            # Recommend exploring areas with low knowledge
            knowledge_types = [k.knowledge_type for k in state.knowledge_base.values()]
            missing_types = []
            for kt in KnowledgeType:
                if kt not in knowledge_types:
                    missing_types.append(kt)
            
            for missing_type in missing_types[:3]:  # Top 3 missing types
                recommendations.append({
                    'type': 'knowledge_gap',
                    'recommendation': f"Learn more {missing_type.value} knowledge",
                    'priority': 0.7,
                    'learning_type': LearningType.INSTRUCTIONAL.value
                })
            
            # Recommend strengthening weak patterns
            weak_patterns = [p for p in state.learned_patterns.values() if p.confidence < 0.6]
            if weak_patterns:
                recommendations.append({
                    'type': 'pattern_strengthening',
                    'recommendation': f"Practice scenarios to strengthen {len(weak_patterns)} weak patterns",
                    'priority': 0.8,
                    'learning_type': LearningType.EXPERIENTIAL.value
                })
            
            # Recommend collaborative learning if low social knowledge
            social_knowledge = [k for k in state.knowledge_base.values() 
                             if 'collaborative' in k.content.lower() or 'social' in k.content.lower()]
            if len(social_knowledge) < 3:
                recommendations.append({
                    'type': 'collaboration',
                    'recommendation': "Engage in collaborative learning to build social knowledge",
                    'priority': 0.6,
                    'learning_type': LearningType.COLLABORATIVE.value
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting learning recommendations: {e}")
            return []
    
    def get_learning_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get learning summary for an agent"""
        try:
            if agent_id not in self.agent_states:
                return {'error': 'Agent not registered'}
            
            state = self.agent_states[agent_id]
            
            # Calculate knowledge distribution
            knowledge_distribution = defaultdict(int)
            for knowledge in state.knowledge_base.values():
                knowledge_distribution[knowledge.knowledge_type.value] += 1
            
            # Calculate pattern distribution
            pattern_distribution = defaultdict(int)
            for pattern in state.learned_patterns.values():
                pattern_distribution[pattern.pattern_type] += 1
            
            return {
                'agent_id': agent_id,
                'learning_mode': state.learning_mode.value,
                'learning_efficiency': state.learning_efficiency,
                'total_learning_events': state.total_learning_events,
                'active_goals': len(state.active_goals),
                'knowledge_base_size': len(state.knowledge_base),
                'learned_patterns_count': len(state.learned_patterns),
                'knowledge_distribution': dict(knowledge_distribution),
                'pattern_distribution': dict(pattern_distribution),
                'recent_experiences': len(state.recent_experiences),
                'last_learning_event': state.last_learning_event.isoformat() if state.last_learning_event else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting learning summary: {e}")
            return {'error': str(e)}
    
    def get_learning_history(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get learning history for an agent"""
        history = list(self.learning_histories.get(agent_id, deque()))
        return history[-limit:] if history else []


# Global learning loop instance
_global_learning_loop: Optional[LearningLoop] = None


def get_learning_loop(memory_interface: Optional[UnifiedMemoryInterface] = None,
                     message_bus: Optional[UnifiedMessageBus] = None,
                     cognitive_engine: Optional[CognitiveEngine] = None) -> LearningLoop:
    """Get the global learning loop instance"""
    global _global_learning_loop
    
    if _global_learning_loop is None:
        if memory_interface is None:
            from .memory_interface import get_memory_interface
            memory_interface = get_memory_interface()
        
        if message_bus is None:
            from .message_bus import get_message_bus
            message_bus = get_message_bus()
        
        if cognitive_engine is None:
            from .cognitive_engine import get_cognitive_engine
            cognitive_engine = get_cognitive_engine()
        
        _global_learning_loop = LearningLoop(memory_interface, message_bus, cognitive_engine)
    
    return _global_learning_loop


async def add_agent_experience(agent_id: str, learning_type: LearningType, 
                              context: Dict[str, Any], action: str, outcome: Dict[str, Any],
                              success_score: float = 0.5, feedback: Optional[Dict[str, Any]] = None) -> bool:
    """Helper function to add a learning experience"""
    loop = get_learning_loop()
    experience = LearningExperience(
        experience_id=f"exp_{agent_id}_{int(time.time() * 1000)}",
        agent_id=agent_id,
        learning_type=learning_type,
        context=context,
        action_taken=action,
        outcome=outcome,
        success_score=success_score,
        feedback=feedback or {}
    )
    return await loop.add_learning_experience(experience)
