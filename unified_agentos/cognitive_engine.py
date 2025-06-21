"""
Cognitive Engine - Phase 2 Component
====================================

The CognitiveEngine provides the core cognitive processing capabilities
for agents, including reasoning, decision-making, context integration,
and cognitive loops for continuous learning and adaptation.

Key Features:
- Cognitive reasoning with memory integration
- Context-aware decision making
- Reflection and metacognition
- Adaptive learning loops
- Integration with attention and learning systems
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timezone

from .memory_interface import UnifiedMemoryInterface, MemoryType, MemoryItem, MemoryQuery
from .message_bus import UnifiedMessageBus, Message, MessageType, MessagePriority


class CognitiveProcessType(Enum):
    """Types of cognitive processes"""
    REASONING = "reasoning"
    DECISION_MAKING = "decision_making"
    REFLECTION = "reflection"
    LEARNING = "learning"
    PROBLEM_SOLVING = "problem_solving"
    METACOGNITION = "metacognition"
    PLANNING = "planning"
    EVALUATION = "evaluation"


class CognitiveState(Enum):
    """Current cognitive state of the agent"""
    IDLE = "idle"
    PROCESSING = "processing"
    REASONING = "reasoning"
    LEARNING = "learning"
    REFLECTING = "reflecting"
    PLANNING = "planning"
    EXECUTING = "executing"


@dataclass
class CognitiveContext:
    """Context for cognitive processing"""
    agent_id: str
    session_id: str
    task_context: Dict[str, Any] = field(default_factory=dict)
    relevant_memories: List[MemoryItem] = field(default_factory=list)
    current_focus: Optional[str] = None
    attention_weights: Dict[str, float] = field(default_factory=dict)
    cognitive_load: float = 0.0
    processing_depth: int = 1
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CognitiveProcess:
    """Represents a cognitive process"""
    process_id: str
    process_type: CognitiveProcessType
    agent_id: str
    context: CognitiveContext
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveResult:
    """Result of cognitive processing"""
    process_id: str
    agent_id: str
    result_type: CognitiveProcessType
    result_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning_trace: List[str] = field(default_factory=list)
    memory_updates: List[MemoryItem] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    learned_concepts: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CognitiveEngine:
    """
    Core cognitive processing engine for agents.
    
    Provides sophisticated cognitive capabilities including reasoning,
    learning, reflection, and adaptive behavior through cognitive loops.
    """
    
    def __init__(self, memory_interface: UnifiedMemoryInterface, message_bus: UnifiedMessageBus):
        self.memory_interface = memory_interface
        self.message_bus = message_bus
        self.logger = logging.getLogger(f"{__name__}.CognitiveEngine")
        
        # Cognitive state tracking
        self.agent_states: Dict[str, CognitiveState] = {}
        self.active_processes: Dict[str, CognitiveProcess] = {}
        self.cognitive_histories: Dict[str, List[CognitiveResult]] = {}
        
        # Processing handlers
        self.process_handlers: Dict[CognitiveProcessType, Callable] = {}
        self._register_default_handlers()
        
        # Cognitive parameters
        self.max_concurrent_processes = 10
        self.cognitive_loop_interval = 5.0  # seconds
        self.reflection_threshold = 0.7
        self.learning_threshold = 0.6
        
        # Background cognitive loop
        self._cognitive_loop_task = None
        self._running = False
    
    def _register_default_handlers(self):
        """Register default cognitive process handlers"""
        self.process_handlers = {
            CognitiveProcessType.REASONING: self._process_reasoning,
            CognitiveProcessType.DECISION_MAKING: self._process_decision_making,
            CognitiveProcessType.REFLECTION: self._process_reflection,
            CognitiveProcessType.LEARNING: self._process_learning,
            CognitiveProcessType.PROBLEM_SOLVING: self._process_problem_solving,
            CognitiveProcessType.METACOGNITION: self._process_metacognition,
            CognitiveProcessType.PLANNING: self._process_planning,
            CognitiveProcessType.EVALUATION: self._process_evaluation,
        }
    
    async def start(self):
        """Start the cognitive engine"""
        if self._running:
            return
        
        self._running = True
        self._cognitive_loop_task = asyncio.create_task(self._cognitive_loop())
        self.logger.info("Cognitive engine started")
    
    async def stop(self):
        """Stop the cognitive engine"""
        self._running = False
        if self._cognitive_loop_task:
            self._cognitive_loop_task.cancel()
            try:
                await self._cognitive_loop_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Cognitive engine stopped")
    
    async def _cognitive_loop(self):
        """Continuous cognitive processing loop"""
        while self._running:
            try:
                # Process cognitive maintenance for all active agents
                for agent_id in list(self.agent_states.keys()):
                    await self._process_cognitive_maintenance(agent_id)
                
                await asyncio.sleep(self.cognitive_loop_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cognitive loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_cognitive_maintenance(self, agent_id: str):
        """Process cognitive maintenance for an agent"""
        try:
            # Check if agent needs reflection
            await self._check_reflection_trigger(agent_id)
            
            # Check if agent needs learning
            await self._check_learning_trigger(agent_id)
            
            # Process metacognition
            await self._check_metacognition_trigger(agent_id)
            
        except Exception as e:
            self.logger.error(f"Error in cognitive maintenance for {agent_id}: {e}")
    
    async def process_cognitive_request(self, agent_id: str, process_type: CognitiveProcessType, 
                                       input_data: Dict[str, Any], context: Optional[CognitiveContext] = None) -> CognitiveResult:
        """Process a cognitive request"""
        try:
            # Create cognitive context if not provided
            if context is None:
                context = await self._create_cognitive_context(agent_id, input_data)
            
            # Create cognitive process
            process = CognitiveProcess(
                process_id=f"{agent_id}_{process_type.value}_{int(time.time() * 1000)}",
                process_type=process_type,
                agent_id=agent_id,
                context=context,
                input_data=input_data,
                started_at=datetime.now(timezone.utc)
            )
            
            # Update agent state
            self.agent_states[agent_id] = CognitiveState.PROCESSING
            self.active_processes[process.process_id] = process
            
            # Process the request
            handler = self.process_handlers.get(process_type)
            if not handler:
                raise ValueError(f"No handler for process type: {process_type}")
            
            result = await handler(process)
            
            # Update process status
            process.completed_at = datetime.now(timezone.utc)
            process.status = "completed"
            
            # Store cognitive history
            if agent_id not in self.cognitive_histories:
                self.cognitive_histories[agent_id] = []
            self.cognitive_histories[agent_id].append(result)
            
            # Update memory with cognitive results
            await self._store_cognitive_memory(result)
            
            # Clean up
            del self.active_processes[process.process_id]
            self.agent_states[agent_id] = CognitiveState.IDLE
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing cognitive request for {agent_id}: {e}")
            # Clean up on error
            if process.process_id in self.active_processes:
                del self.active_processes[process.process_id]
            self.agent_states[agent_id] = CognitiveState.IDLE
            raise
    
    async def _create_cognitive_context(self, agent_id: str, input_data: Dict[str, Any]) -> CognitiveContext:
        """Create cognitive context for processing"""
        # Retrieve relevant memories
        relevant_memories = await self._get_relevant_memories(agent_id, input_data)
        
        # Calculate attention weights
        attention_weights = await self._calculate_attention_weights(agent_id, input_data, relevant_memories)
        
        # Determine cognitive load
        cognitive_load = len(self.active_processes) / self.max_concurrent_processes
        
        return CognitiveContext(
            agent_id=agent_id,
            session_id=input_data.get('session_id', 'default'),
            task_context=input_data,
            relevant_memories=relevant_memories,
            attention_weights=attention_weights,
            cognitive_load=cognitive_load
        )
    
    async def _get_relevant_memories(self, agent_id: str, input_data: Dict[str, Any]) -> List[MemoryItem]:
        """Retrieve relevant memories for cognitive processing"""
        try:
            # Extract key concepts for memory search
            query_text = input_data.get('query', input_data.get('content', ''))
            if not query_text:
                return []
            
            # Search for relevant memories
            query = MemoryQuery(
                query_text=str(query_text)[:100],  # Limit query length
                agent_id=agent_id,
                max_results=10
            )
            
            memories = await self.memory_interface.retrieve_memories(query)
            return memories
            
        except Exception as e:
            self.logger.error(f"Error retrieving relevant memories: {e}")
            return []
    
    async def _calculate_attention_weights(self, agent_id: str, input_data: Dict[str, Any], 
                                         memories: List[MemoryItem]) -> Dict[str, float]:
        """Calculate attention weights for different aspects"""
        weights = {
            'current_task': 1.0,
            'recent_memory': 0.8,
            'long_term_memory': 0.6,
            'social_context': 0.7,
            'emotional_context': 0.5
        }
        
        # Adjust weights based on context
        if memories:
            weights['recent_memory'] = min(1.0, weights['recent_memory'] + len(memories) * 0.1)
        
        return weights
    
    async def _process_reasoning(self, process: CognitiveProcess) -> CognitiveResult:
        """Process reasoning request"""
        try:
            input_data = process.input_data
            context = process.context
            
            reasoning_trace = []
            result_data = {}
            
            # Step 1: Analyze the problem/question
            problem = input_data.get('problem', input_data.get('query', ''))
            reasoning_trace.append(f"Analyzing problem: {problem}")
            
            # Step 2: Integrate relevant memories
            if context.relevant_memories:
                reasoning_trace.append(f"Integrating {len(context.relevant_memories)} relevant memories")
                memory_insights = []
                for memory in context.relevant_memories:
                    if hasattr(memory, 'content') and memory.content:
                        memory_insights.append(memory.content[:200])
                result_data['memory_insights'] = memory_insights
            
            # Step 3: Apply reasoning patterns
            reasoning_patterns = [
                "analytical_reasoning",
                "analogical_reasoning", 
                "causal_reasoning",
                "deductive_reasoning",
                "inductive_reasoning"
            ]
            
            reasoning_trace.append("Applying reasoning patterns:")
            for pattern in reasoning_patterns:
                reasoning_trace.append(f"  - {pattern}")
            
            # Step 4: Generate conclusions
            conclusions = []
            if problem:
                # Simple reasoning simulation - in real implementation, this would use LLM
                if "why" in problem.lower():
                    conclusions.append("Causal analysis suggests multiple factors")
                elif "how" in problem.lower():
                    conclusions.append("Process analysis indicates step-by-step approach")
                elif "what" in problem.lower():
                    conclusions.append("Definitional analysis provides clarity")
                else:
                    conclusions.append("General analysis yields insights")
            
            result_data['conclusions'] = conclusions
            reasoning_trace.append(f"Generated {len(conclusions)} conclusions")
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=process.agent_id,
                result_type=CognitiveProcessType.REASONING,
                result_data=result_data,
                confidence=0.8,
                reasoning_trace=reasoning_trace,
                memory_updates=[],
                next_actions=["store_reasoning_result", "evaluate_conclusions"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in reasoning process: {e}")
            raise
    
    async def _process_decision_making(self, process: CognitiveProcess) -> CognitiveResult:
        """Process decision making request"""
        try:
            input_data = process.input_data
            context = process.context
            
            reasoning_trace = []
            result_data = {}
            
            # Extract decision parameters
            options = input_data.get('options', [])
            criteria = input_data.get('criteria', [])
            
            reasoning_trace.append(f"Evaluating {len(options)} options against {len(criteria)} criteria")
            
            # Simple decision matrix - in real implementation, this would be more sophisticated
            decision_scores = {}
            for option in options:
                score = 0.5  # Base score
                # Adjust based on memory relevance
                if context.relevant_memories:
                    score += 0.2
                decision_scores[option] = score
            
            # Select best option
            if decision_scores:
                best_option = max(decision_scores.keys(), key=lambda x: decision_scores[x])
                result_data['selected_option'] = best_option
                result_data['decision_scores'] = decision_scores
                reasoning_trace.append(f"Selected option: {best_option}")
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=process.agent_id,
                result_type=CognitiveProcessType.DECISION_MAKING,
                result_data=result_data,
                confidence=0.7,
                reasoning_trace=reasoning_trace,
                next_actions=["implement_decision", "monitor_outcomes"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in decision making process: {e}")
            raise
    
    async def _process_reflection(self, process: CognitiveProcess) -> CognitiveResult:
        """Process reflection request"""
        try:
            agent_id = process.agent_id
            reasoning_trace = []
            result_data = {}
            
            # Get recent cognitive history
            recent_history = self.cognitive_histories.get(agent_id, [])[-10:]  # Last 10 results
            reasoning_trace.append(f"Reflecting on {len(recent_history)} recent cognitive activities")
            
            # Analyze patterns
            process_types = [r.result_type.value for r in recent_history]
            most_common = max(set(process_types), key=process_types.count) if process_types else "none"
            
            # Generate insights
            insights = []
            if recent_history:
                avg_confidence = sum(r.confidence for r in recent_history) / len(recent_history)
                insights.append(f"Average confidence level: {avg_confidence:.2f}")
                insights.append(f"Most frequent cognitive process: {most_common}")
                
                if avg_confidence < self.reflection_threshold:
                    insights.append("Low confidence detected - may need more learning")
            
            result_data['insights'] = insights
            result_data['patterns'] = {
                'most_common_process': most_common,
                'average_confidence': avg_confidence if recent_history else 0.0
            }
            
            reasoning_trace.extend(insights)
            
            # Generate memory updates for reflective insights
            memory_updates = []
            if insights:
                reflection_memory = MemoryItem(
                    memory_id=f"reflection_{agent_id}_{int(time.time() * 1000)}",
                    agent_id=agent_id,
                    memory_type=MemoryType.EPISODIC,
                    content=f"Reflection insights: {'; '.join(insights)}",
                    metadata={'reflection_timestamp': datetime.now(timezone.utc).isoformat()}
                )
                memory_updates.append(reflection_memory)
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=agent_id,
                result_type=CognitiveProcessType.REFLECTION,
                result_data=result_data,
                confidence=0.9,
                reasoning_trace=reasoning_trace,
                memory_updates=memory_updates,
                next_actions=["apply_insights", "adjust_behavior"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in reflection process: {e}")
            raise
    
    async def _process_learning(self, process: CognitiveProcess) -> CognitiveResult:
        """Process learning request"""
        try:
            input_data = process.input_data
            agent_id = process.agent_id
            reasoning_trace = []
            result_data = {}
            
            # Extract learning content
            content = input_data.get('content', input_data.get('experience', ''))
            learning_type = input_data.get('learning_type', 'experiential')
            
            reasoning_trace.append(f"Processing {learning_type} learning from content")
            
            # Extract concepts and patterns
            learned_concepts = []
            if content:
                # Simple concept extraction - in real implementation, this would use NLP
                words = content.lower().split()
                important_words = [w for w in words if len(w) > 4][:5]
                learned_concepts = important_words
            
            reasoning_trace.append(f"Extracted {len(learned_concepts)} concepts")
            
            # Create learning memory
            memory_updates = []
            if content:
                learning_memory = MemoryItem(
                    memory_id=f"learning_{agent_id}_{int(time.time() * 1000)}",
                    agent_id=agent_id,
                    memory_type=MemoryType.SEMANTIC,
                    content=f"Learning: {content}",
                    metadata={
                        'learning_type': learning_type,
                        'concepts': learned_concepts,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                memory_updates.append(learning_memory)
            
            result_data['learned_concepts'] = learned_concepts
            result_data['learning_type'] = learning_type
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=agent_id,
                result_type=CognitiveProcessType.LEARNING,
                result_data=result_data,
                confidence=0.8,
                reasoning_trace=reasoning_trace,
                memory_updates=memory_updates,
                learned_concepts=learned_concepts,
                next_actions=["integrate_knowledge", "update_models"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in learning process: {e}")
            raise
    
    async def _process_problem_solving(self, process: CognitiveProcess) -> CognitiveResult:
        """Process problem solving request"""
        try:
            input_data = process.input_data
            reasoning_trace = []
            result_data = {}
            
            problem = input_data.get('problem', '')
            constraints = input_data.get('constraints', [])
            
            reasoning_trace.append(f"Solving problem with {len(constraints)} constraints")
            
            # Problem decomposition
            sub_problems = []
            if problem:
                # Simple decomposition - split by logical connectors
                parts = problem.replace(' and ', ' | ').replace(' or ', ' | ').split(' | ')
                sub_problems = [p.strip() for p in parts if p.strip()]
            
            reasoning_trace.append(f"Decomposed into {len(sub_problems)} sub-problems")
            
            # Generate solution approaches
            approaches = [
                "analytical_approach",
                "creative_approach", 
                "systematic_approach",
                "collaborative_approach"
            ]
            
            result_data['sub_problems'] = sub_problems
            result_data['solution_approaches'] = approaches
            result_data['constraints'] = constraints
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=process.agent_id,
                result_type=CognitiveProcessType.PROBLEM_SOLVING,
                result_data=result_data,
                confidence=0.7,
                reasoning_trace=reasoning_trace,
                next_actions=["implement_solutions", "test_approaches", "evaluate_results"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in problem solving process: {e}")
            raise
    
    async def _process_metacognition(self, process: CognitiveProcess) -> CognitiveResult:
        """Process metacognition request"""
        try:
            agent_id = process.agent_id
            reasoning_trace = []
            result_data = {}
            
            reasoning_trace.append("Analyzing cognitive processes and strategies")
            
            # Analyze cognitive performance
            recent_results = self.cognitive_histories.get(agent_id, [])[-20:]  # Last 20 results
            
            performance_metrics = {}
            if recent_results:
                # Calculate performance metrics
                avg_confidence = sum(r.confidence for r in recent_results) / len(recent_results)
                process_diversity = len(set(r.result_type.value for r in recent_results))
                
                performance_metrics = {
                    'average_confidence': avg_confidence,
                    'process_diversity': process_diversity,
                    'total_processes': len(recent_results)
                }
            
            # Generate metacognitive insights
            insights = []
            if performance_metrics:
                if performance_metrics['average_confidence'] > 0.8:
                    insights.append("High confidence levels indicate good cognitive calibration")
                elif performance_metrics['average_confidence'] < 0.5:
                    insights.append("Low confidence suggests need for more diverse learning")
                
                if performance_metrics['process_diversity'] < 3:
                    insights.append("Limited cognitive diversity - should explore more process types")
            
            result_data['performance_metrics'] = performance_metrics
            result_data['metacognitive_insights'] = insights
            
            reasoning_trace.extend(insights)
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=agent_id,
                result_type=CognitiveProcessType.METACOGNITION,
                result_data=result_data,
                confidence=0.85,
                reasoning_trace=reasoning_trace,
                next_actions=["optimize_strategies", "adjust_parameters"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in metacognition process: {e}")
            raise
    
    async def _process_planning(self, process: CognitiveProcess) -> CognitiveResult:
        """Process planning request"""
        try:
            input_data = process.input_data
            reasoning_trace = []
            result_data = {}
            
            goal = input_data.get('goal', '')
            resources = input_data.get('resources', [])
            timeline = input_data.get('timeline', 'flexible')
            
            reasoning_trace.append(f"Planning for goal: {goal}")
            reasoning_trace.append(f"Available resources: {len(resources)}")
            
            # Generate plan steps
            plan_steps = []
            if goal:
                # Simple planning - break goal into phases
                phases = ["analysis", "preparation", "execution", "evaluation"]
                for i, phase in enumerate(phases, 1):
                    plan_steps.append({
                        'step': i,
                        'phase': phase,
                        'description': f"{phase.capitalize()} phase for: {goal}",
                        'estimated_effort': 'medium'
                    })
            
            result_data['plan_steps'] = plan_steps
            result_data['goal'] = goal
            result_data['timeline'] = timeline
            
            reasoning_trace.append(f"Generated plan with {len(plan_steps)} steps")
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=process.agent_id,
                result_type=CognitiveProcessType.PLANNING,
                result_data=result_data,
                confidence=0.75,
                reasoning_trace=reasoning_trace,
                next_actions=["begin_execution", "monitor_progress", "adapt_plan"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in planning process: {e}")
            raise
    
    async def _process_evaluation(self, process: CognitiveProcess) -> CognitiveResult:
        """Process evaluation request"""
        try:
            input_data = process.input_data
            reasoning_trace = []
            result_data = {}
            
            subject = input_data.get('subject', '')
            criteria = input_data.get('criteria', [])
            evidence = input_data.get('evidence', [])
            
            reasoning_trace.append(f"Evaluating: {subject}")
            reasoning_trace.append(f"Using {len(criteria)} criteria")
            
            # Perform evaluation
            evaluation_scores = {}
            for criterion in criteria:
                # Simple scoring - in real implementation, this would be more sophisticated
                score = 0.7  # Base score
                if evidence:
                    score += 0.2  # Bonus for having evidence
                evaluation_scores[criterion] = score
            
            # Calculate overall score
            overall_score = sum(evaluation_scores.values()) / len(evaluation_scores) if evaluation_scores else 0.0
            
            result_data['evaluation_scores'] = evaluation_scores
            result_data['overall_score'] = overall_score
            result_data['evidence_considered'] = evidence
            
            reasoning_trace.append(f"Overall evaluation score: {overall_score:.2f}")
            
            return CognitiveResult(
                process_id=process.process_id,
                agent_id=process.agent_id,
                result_type=CognitiveProcessType.EVALUATION,
                result_data=result_data,
                confidence=0.8,
                reasoning_trace=reasoning_trace,
                next_actions=["document_evaluation", "communicate_results"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in evaluation process: {e}")
            raise
    
    async def _check_reflection_trigger(self, agent_id: str):
        """Check if agent should trigger reflection"""
        try:
            recent_results = self.cognitive_histories.get(agent_id, [])[-5:]  # Last 5 results
            
            if len(recent_results) >= 5:
                avg_confidence = sum(r.confidence for r in recent_results) / len(recent_results)
                
                if avg_confidence < self.reflection_threshold:
                    # Trigger reflection
                    await self.process_cognitive_request(
                        agent_id=agent_id,
                        process_type=CognitiveProcessType.REFLECTION,
                        input_data={'trigger': 'low_confidence', 'threshold': self.reflection_threshold}
                    )
        except Exception as e:
            self.logger.error(f"Error checking reflection trigger for {agent_id}: {e}")
    
    async def _check_learning_trigger(self, agent_id: str):
        """Check if agent should trigger learning"""
        try:
            recent_results = self.cognitive_histories.get(agent_id, [])
            
            # Check if agent has had varied experiences that could be learned from
            if len(recent_results) >= 3:
                process_types = [r.result_type for r in recent_results[-3:]]
                if len(set(process_types)) >= 2:  # Diverse experiences
                    # Trigger learning consolidation
                    await self.process_cognitive_request(
                        agent_id=agent_id,
                        process_type=CognitiveProcessType.LEARNING,
                        input_data={
                            'content': 'Recent diverse cognitive experiences',
                            'learning_type': 'experiential',
                            'trigger': 'experience_diversity'
                        }
                    )
        except Exception as e:
            self.logger.error(f"Error checking learning trigger for {agent_id}: {e}")
    
    async def _check_metacognition_trigger(self, agent_id: str):
        """Check if agent should trigger metacognition"""
        try:
            recent_results = self.cognitive_histories.get(agent_id, [])
            
            # Trigger metacognition periodically
            if len(recent_results) % 10 == 0 and len(recent_results) > 0:
                await self.process_cognitive_request(
                    agent_id=agent_id,
                    process_type=CognitiveProcessType.METACOGNITION,
                    input_data={'trigger': 'periodic_review', 'interval': 10}
                )
        except Exception as e:
            self.logger.error(f"Error checking metacognition trigger for {agent_id}: {e}")
    
    async def _store_cognitive_memory(self, result: CognitiveResult):
        """Store cognitive processing results in memory"""
        try:
            # Create memory item for the cognitive result
            memory_item = MemoryItem(
                memory_id=f"cognitive_{result.agent_id}_{result.process_id}",
                agent_id=result.agent_id,
                memory_type=MemoryType.EPISODIC,
                content=f"Cognitive process: {result.result_type.value} - {json.dumps(result.result_data)}",
                metadata={
                    'process_type': result.result_type.value,
                    'confidence': result.confidence,
                    'reasoning_trace': result.reasoning_trace,
                    'next_actions': result.next_actions,
                    'learned_concepts': result.learned_concepts,
                    'cognitive_timestamp': result.timestamp.isoformat()
                }
            )
            
            await self.memory_interface.store_memory_item(memory_item)
            
            # Store any additional memory updates
            for memory_update in result.memory_updates:
                await self.memory_interface.store_memory_item(memory_update)
                
        except Exception as e:
            self.logger.error(f"Error storing cognitive memory: {e}")
    
    def get_agent_cognitive_state(self, agent_id: str) -> Optional[CognitiveState]:
        """Get current cognitive state of an agent"""
        return self.agent_states.get(agent_id)
    
    def get_cognitive_history(self, agent_id: str, limit: int = 10) -> List[CognitiveResult]:
        """Get cognitive history for an agent"""
        history = self.cognitive_histories.get(agent_id, [])
        return history[-limit:] if history else []
    
    def get_cognitive_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get cognitive statistics for an agent"""
        history = self.cognitive_histories.get(agent_id, [])
        
        if not history:
            return {'total_processes': 0}
        
        process_counts = {}
        confidences = []
        
        for result in history:
            process_type = result.result_type.value
            process_counts[process_type] = process_counts.get(process_type, 0) + 1
            confidences.append(result.confidence)
        
        return {
            'total_processes': len(history),
            'process_distribution': process_counts,
            'average_confidence': sum(confidences) / len(confidences),
            'current_state': self.agent_states.get(agent_id, CognitiveState.IDLE).value,
            'active_processes': len([p for p in self.active_processes.values() if p.agent_id == agent_id])
        }


# Global cognitive engine instance
_global_cognitive_engine: Optional[CognitiveEngine] = None


def get_cognitive_engine(memory_interface: Optional[UnifiedMemoryInterface] = None,
                        message_bus: Optional[UnifiedMessageBus] = None) -> CognitiveEngine:
    """Get the global cognitive engine instance"""
    global _global_cognitive_engine
    
    if _global_cognitive_engine is None:
        if memory_interface is None:
            from .memory_interface import get_memory_interface
            memory_interface = get_memory_interface()
        
        if message_bus is None:
            from .message_bus import get_message_bus
            message_bus = get_message_bus()
        
        _global_cognitive_engine = CognitiveEngine(memory_interface, message_bus)
    
    return _global_cognitive_engine


async def process_cognitive_request(agent_id: str, process_type: CognitiveProcessType,
                                   input_data: Dict[str, Any]) -> CognitiveResult:
    """Helper function to process a cognitive request"""
    engine = get_cognitive_engine()
    return await engine.process_cognitive_request(agent_id, process_type, input_data)
