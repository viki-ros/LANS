"""
Enhanced AIL Processor - Phase 2 Component
==========================================

Enhanced Agent Interaction Language (AIL) processor that integrates with
cognitive components for more sophisticated inter-agent communication,
cognitive context sharing, and collaborative reasoning.

Key Features:
- Cognitive context-aware message processing
- Attention-filtered communication
- Learning-integrated message handling
- Collaborative cognitive processing
- Enhanced semantic understanding
- Multi-modal communication support
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from .memory_interface import UnifiedMemoryInterface, MemoryType, MemoryItem, MemoryQuery
from .message_bus import UnifiedMessageBus, Message, MessageType, MessagePriority
from .cognitive_engine import CognitiveEngine, CognitiveProcessType, CognitiveResult, CognitiveContext
from .attention_manager import AttentionManager, AttentionTarget, AttentionType
from .learning_loop import LearningLoop, LearningExperience, LearningType


class AILMessageType(Enum):
    """Enhanced AIL message types"""
    COGNITIVE_REQUEST = "cognitive_request"
    COGNITIVE_RESPONSE = "cognitive_response"
    KNOWLEDGE_SHARE = "knowledge_share"
    COLLABORATION_INVITE = "collaboration_invite"
    ATTENTION_ALERT = "attention_alert"
    LEARNING_FEEDBACK = "learning_feedback"
    CONTEXT_SYNC = "context_sync"
    REASONING_TRACE = "reasoning_trace"
    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    COMMAND = "command"


class CognitiveIntentType(Enum):
    """Types of cognitive intent in messages"""
    INFORM = "inform"
    REQUEST = "request"
    COLLABORATE = "collaborate"
    TEACH = "teach"
    LEARN = "learn"
    REASON = "reason"
    DECIDE = "decide"
    REFLECT = "reflect"
    PLAN = "plan"
    EVALUATE = "evaluate"


@dataclass
class AILCognitiveContext:
    """Cognitive context for AIL messages"""
    sender_attention_state: Optional[Dict[str, Any]] = None
    sender_cognitive_load: float = 0.0
    sender_learning_goals: List[str] = field(default_factory=list)
    required_cognitive_processes: List[CognitiveProcessType] = field(default_factory=list)
    attention_targets: List[str] = field(default_factory=list)
    knowledge_dependencies: List[str] = field(default_factory=list)
    reasoning_depth: int = 1
    collaboration_context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EnhancedAILMessage:
    """Enhanced AIL message with cognitive components"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: AILMessageType
    cognitive_intent: CognitiveIntentType
    content: str
    cognitive_context: AILCognitiveContext = field(default_factory=AILCognitiveContext)
    attention_priority: float = 0.5
    learning_value: float = 0.5
    collaboration_potential: float = 0.5
    semantic_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None


@dataclass
class AILProcessingResult:
    """Result of AIL message processing"""
    message_id: str
    processed: bool = False
    cognitive_response: Optional[CognitiveResult] = None
    attention_updates: List[AttentionTarget] = field(default_factory=list)
    learning_experiences: List[LearningExperience] = field(default_factory=list)
    memory_updates: List[MemoryItem] = field(default_factory=list)
    response_messages: List[EnhancedAILMessage] = field(default_factory=list)
    collaboration_opportunities: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


class EnhancedAILProcessor:
    """
    Enhanced AIL processor with cognitive integration.
    
    Processes inter-agent communication with sophisticated cognitive
    understanding, attention management, and learning integration.
    """
    
    def __init__(self, memory_interface: UnifiedMemoryInterface,
                 message_bus: UnifiedMessageBus,
                 cognitive_engine: CognitiveEngine,
                 attention_manager: AttentionManager,
                 learning_loop: LearningLoop):
        self.memory_interface = memory_interface
        self.message_bus = message_bus
        self.cognitive_engine = cognitive_engine
        self.attention_manager = attention_manager
        self.learning_loop = learning_loop
        self.logger = logging.getLogger(f"{__name__}.EnhancedAILProcessor")
        
        # Processing state
        self.processing_queue: Dict[str, List[EnhancedAILMessage]] = {}
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.message_history: Dict[str, List[EnhancedAILMessage]] = {}
        
        # Processing handlers
        self.message_handlers: Dict[AILMessageType, callable] = {}
        self._register_message_handlers()
        
        # Cognitive processing parameters
        self.max_reasoning_depth = 3
        self.collaboration_threshold = 0.7
        self.attention_update_threshold = 0.6
        self.learning_value_threshold = 0.5
        
        # Background processing
        self._processing_task = None
        self._running = False
    
    def _register_message_handlers(self):
        """Register message type handlers"""
        self.message_handlers = {
            AILMessageType.COGNITIVE_REQUEST: self._handle_cognitive_request,
            AILMessageType.COGNITIVE_RESPONSE: self._handle_cognitive_response,
            AILMessageType.KNOWLEDGE_SHARE: self._handle_knowledge_share,
            AILMessageType.COLLABORATION_INVITE: self._handle_collaboration_invite,
            AILMessageType.ATTENTION_ALERT: self._handle_attention_alert,
            AILMessageType.LEARNING_FEEDBACK: self._handle_learning_feedback,
            AILMessageType.CONTEXT_SYNC: self._handle_context_sync,
            AILMessageType.REASONING_TRACE: self._handle_reasoning_trace,
            AILMessageType.QUERY: self._handle_query,
            AILMessageType.RESPONSE: self._handle_response,
            AILMessageType.NOTIFICATION: self._handle_notification,
            AILMessageType.COMMAND: self._handle_command,
        }
    
    async def start(self):
        """Start the enhanced AIL processor"""
        if self._running:
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Enhanced AIL processor started")
    
    async def stop(self):
        """Stop the enhanced AIL processor"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Enhanced AIL processor stopped")
    
    async def _processing_loop(self):
        """Main processing loop"""
        while self._running:
            try:
                # Process queued messages for all agents
                for agent_id in list(self.processing_queue.keys()):
                    await self._process_agent_queue(agent_id)
                
                await asyncio.sleep(0.5)  # High frequency processing
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_agent_queue(self, agent_id: str):
        """Process message queue for a specific agent"""
        try:
            queue = self.processing_queue.get(agent_id, [])
            if not queue:
                return
            
            # Process messages with attention filtering
            filtered_messages = await self._filter_messages_by_attention(agent_id, queue)
            
            # Process each filtered message
            for message in filtered_messages:
                try:
                    result = await self._process_enhanced_message(message)
                    await self._handle_processing_result(result)
                    
                    # Remove from queue
                    if message in self.processing_queue[agent_id]:
                        self.processing_queue[agent_id].remove(message)
                        
                except Exception as e:
                    self.logger.error(f"Error processing message {message.message_id}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing queue for {agent_id}: {e}")
    
    async def send_enhanced_ail_message(self, message: EnhancedAILMessage) -> bool:
        """Send an enhanced AIL message"""
        try:
            # Enrich message with sender's cognitive context
            await self._enrich_message_context(message)
            
            # Add to receiver's processing queue
            receiver_id = message.receiver_id
            if receiver_id not in self.processing_queue:
                self.processing_queue[receiver_id] = []
            
            self.processing_queue[receiver_id].append(message)
            
            # Store in message history
            if message.sender_id not in self.message_history:
                self.message_history[message.sender_id] = []
            self.message_history[message.sender_id].append(message)
            
            # Send via message bus for external systems
            bus_message = Message(
                message_id=message.message_id,
                sender_id=message.sender_id,
                recipient_id=message.receiver_id,
                content=message.content,
                message_type=MessageType.AIL_COGNITION,
                priority=MessagePriority.NORMAL if message.attention_priority < 0.8 else MessagePriority.HIGH,
                metadata={
                    'ail_message_type': message.message_type.value,
                    'cognitive_intent': message.cognitive_intent.value,
                    'attention_priority': message.attention_priority,
                    'learning_value': message.learning_value,
                    'collaboration_potential': message.collaboration_potential
                }
            )
            
            await self.message_bus.send_message(bus_message)
            
            self.logger.debug(f"Sent enhanced AIL message: {message.message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending enhanced AIL message: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def _enrich_message_context(self, message: EnhancedAILMessage):
        """Enrich message with sender's cognitive context"""
        try:
            sender_id = message.sender_id
            
            # Get sender's attention state
            attention_summary = await self.attention_manager.get_attention_summary(sender_id)
            if 'error' not in attention_summary:
                message.cognitive_context.sender_attention_state = attention_summary
                message.cognitive_context.sender_cognitive_load = attention_summary.get('cognitive_load', 0.0)
            
            # Get sender's learning goals
            learning_summary = self.learning_loop.get_learning_summary(sender_id)
            if 'error' not in learning_summary:
                # Extract learning objectives from active goals
                learning_goals = []
                active_goals_count = learning_summary.get('active_goals', 0)
                # Since we only get the count, we'll set a simple indication
                if active_goals_count > 0:
                    learning_goals.append(f"Active learning goals: {active_goals_count}")
                message.cognitive_context.sender_learning_goals = learning_goals
            
            # Analyze message for cognitive requirements
            await self._analyze_cognitive_requirements(message)
            
        except Exception as e:
            self.logger.error(f"Error enriching message context: {e}")
    
    async def _analyze_cognitive_requirements(self, message: EnhancedAILMessage):
        """Analyze message for cognitive processing requirements"""
        try:
            content = message.content.lower()
            
            # Detect required cognitive processes
            if any(word in content for word in ['why', 'because', 'reason', 'cause']):
                message.cognitive_context.required_cognitive_processes.append(CognitiveProcessType.REASONING)
            
            if any(word in content for word in ['decide', 'choose', 'option', 'alternative']):
                message.cognitive_context.required_cognitive_processes.append(CognitiveProcessType.DECISION_MAKING)
            
            if any(word in content for word in ['plan', 'strategy', 'approach', 'steps']):
                message.cognitive_context.required_cognitive_processes.append(CognitiveProcessType.PLANNING)
            
            if any(word in content for word in ['learn', 'teach', 'knowledge', 'understand']):
                message.cognitive_context.required_cognitive_processes.append(CognitiveProcessType.LEARNING)
            
            if any(word in content for word in ['reflect', 'think about', 'consider', 'ponder']):
                message.cognitive_context.required_cognitive_processes.append(CognitiveProcessType.REFLECTION)
            
            if any(word in content for word in ['evaluate', 'assess', 'judge', 'rate']):
                message.cognitive_context.required_cognitive_processes.append(CognitiveProcessType.EVALUATION)
            
            # Set reasoning depth based on complexity
            complex_indicators = ['complex', 'complicated', 'detailed', 'thorough', 'comprehensive']
            if any(indicator in content for indicator in complex_indicators):
                message.cognitive_context.reasoning_depth = min(3, message.cognitive_context.reasoning_depth + 1)
            
        except Exception as e:
            self.logger.error(f"Error analyzing cognitive requirements: {e}")
    
    async def _filter_messages_by_attention(self, agent_id: str, messages: List[EnhancedAILMessage]) -> List[EnhancedAILMessage]:
        """Filter messages based on agent's attention state"""
        try:
            if not messages:
                return []
            
            # Convert messages to information format for attention filtering
            info_items = []
            for msg in messages:
                info_items.append({
                    'content': msg.content,
                    'priority': msg.attention_priority,
                    'timestamp': msg.created_at.isoformat(),
                    'agent_id': msg.sender_id,
                    'message_obj': msg
                })
            
            # Apply attention filtering
            filtered_info = await self.attention_manager.filter_information(agent_id, info_items)
            
            # Extract original message objects
            filtered_messages = [item['message_obj'] for item in filtered_info]
            
            self.logger.debug(f"Filtered {len(messages)} messages to {len(filtered_messages)} for {agent_id}")
            return filtered_messages
            
        except Exception as e:
            self.logger.error(f"Error filtering messages by attention: {e}")
            return messages  # Return unfiltered on error
    
    async def _process_enhanced_message(self, message: EnhancedAILMessage) -> AILProcessingResult:
        """Process an enhanced AIL message"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = AILProcessingResult(message_id=message.message_id)
            
            # Get appropriate handler
            handler = self.message_handlers.get(message.message_type)
            if not handler:
                result.errors.append(f"No handler for message type: {message.message_type}")
                return result
            
            # Process the message
            handler_result = await handler(message)
            
            # Merge handler result
            if isinstance(handler_result, dict):
                for key, value in handler_result.items():
                    if hasattr(result, key) and value:
                        if isinstance(getattr(result, key), list):
                            getattr(result, key).extend(value if isinstance(value, list) else [value])
                        else:
                            setattr(result, key, value)
            
            # Update attention if message has high attention priority
            if message.attention_priority >= self.attention_update_threshold:
                attention_target = AttentionTarget(
                    target_id=message.message_id,
                    target_type='message',
                    content=message.content,
                    priority=message.attention_priority,
                    relevance=message.attention_priority
                )
                result.attention_updates.append(attention_target)
            
            # Create learning experience if message has learning value
            if message.learning_value >= self.learning_value_threshold:
                learning_exp = LearningExperience(
                    experience_id=f"msg_learning_{message.message_id}",
                    agent_id=message.receiver_id,
                    learning_type=LearningType.COLLABORATIVE if message.collaboration_potential > 0.5 else LearningType.OBSERVATIONAL,
                    context={
                        'sender': message.sender_id,
                        'message_type': message.message_type.value,
                        'cognitive_intent': message.cognitive_intent.value
                    },
                    action_taken='process_message',
                    outcome={'processed': True},
                    success_score=0.8,  # Assume successful processing
                    confidence=message.learning_value
                )
                result.learning_experiences.append(learning_exp)
            
            result.processed = True
            message.processed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            result.errors.append(str(e))
            self.logger.error(f"Error processing enhanced message {message.message_id}: {e}")
        
        finally:
            result.processing_time = asyncio.get_event_loop().time() - start_time
        
        return result
    
    async def _handle_cognitive_request(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle cognitive request message"""
        try:
            # Parse the cognitive request
            request_data = json.loads(message.content) if message.content.startswith('{') else {'query': message.content}
            
            # Determine cognitive process type
            if message.cognitive_context.required_cognitive_processes:
                process_type = message.cognitive_context.required_cognitive_processes[0]
            else:
                process_type = CognitiveProcessType.REASONING  # Default
            
            # Process cognitive request
            cognitive_result = await self.cognitive_engine.process_cognitive_request(
                agent_id=message.receiver_id,
                process_type=process_type,
                input_data=request_data
            )
            
            # Create response message
            response = EnhancedAILMessage(
                message_id=f"response_{message.message_id}",
                sender_id=message.receiver_id,
                receiver_id=message.sender_id,
                message_type=AILMessageType.COGNITIVE_RESPONSE,
                cognitive_intent=CognitiveIntentType.INFORM,
                content=json.dumps(cognitive_result.result_data),
                attention_priority=message.attention_priority,
                learning_value=0.6  # Responses have learning value
            )
            
            return {
                'cognitive_response': cognitive_result,
                'response_messages': [response]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling cognitive request: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_cognitive_response(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle cognitive response message"""
        try:
            # Store cognitive response in memory
            memory_item = MemoryItem(
                memory_id=f"cog_response_{message.receiver_id}_{int(time.time() * 1000)}",
                agent_id=message.receiver_id,
                memory_type=MemoryType.EPISODIC,
                content=f"Cognitive response from {message.sender_id}: {message.content}",
                metadata={
                    'response_to': message.metadata.get('original_request_id'),
                    'cognitive_response': True,
                    'sender': message.sender_id
                }
            )
            
            return {
                'memory_updates': [memory_item]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling cognitive response: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_knowledge_share(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle knowledge sharing message"""
        try:
            # Store shared knowledge
            memory_item = MemoryItem(
                memory_id=f"knowledge_share_{message.receiver_id}_{int(time.time() * 1000)}",
                agent_id=message.receiver_id,
                memory_type=MemoryType.SEMANTIC,
                content=f"Shared knowledge from {message.sender_id}: {message.content}",
                metadata={
                    'knowledge_source': message.sender_id,
                    'shared_knowledge': True,
                    'learning_value': message.learning_value
                }
            )
            
            # Create learning experience
            learning_exp = LearningExperience(
                experience_id=f"knowledge_share_{message.message_id}",
                agent_id=message.receiver_id,
                learning_type=LearningType.COLLABORATIVE,
                context={'knowledge_sharer': message.sender_id},
                action_taken='receive_shared_knowledge',
                outcome={'knowledge_acquired': True},
                success_score=message.learning_value,
                confidence=0.8
            )
            
            return {
                'memory_updates': [memory_item],
                'learning_experiences': [learning_exp]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling knowledge share: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_collaboration_invite(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle collaboration invitation"""
        try:
            # Check if receiver can collaborate
            receiver_attention = await self.attention_manager.get_attention_summary(message.receiver_id)
            cognitive_load = receiver_attention.get('cognitive_load', 0.0)
            
            if cognitive_load < 0.8:  # Can collaborate if not overloaded
                # Accept collaboration
                collaboration_id = f"collab_{message.sender_id}_{message.receiver_id}_{int(asyncio.get_event_loop().time())}"
                
                self.active_collaborations[collaboration_id] = {
                    'participants': [message.sender_id, message.receiver_id],
                    'started_at': datetime.now(timezone.utc),
                    'context': json.loads(message.content) if message.content.startswith('{') else {'topic': message.content}
                }
                
                # Send acceptance response
                response = EnhancedAILMessage(
                    message_id=f"collab_accept_{message.message_id}",
                    sender_id=message.receiver_id,
                    receiver_id=message.sender_id,
                    message_type=AILMessageType.COLLABORATION_INVITE,
                    cognitive_intent=CognitiveIntentType.COLLABORATE,
                    content=json.dumps({'status': 'accepted', 'collaboration_id': collaboration_id}),
                    collaboration_potential=1.0
                )
                
                return {
                    'response_messages': [response],
                    'collaboration_opportunities': [collaboration_id]
                }
            else:
                # Decline due to high cognitive load
                response = EnhancedAILMessage(
                    message_id=f"collab_decline_{message.message_id}",
                    sender_id=message.receiver_id,
                    receiver_id=message.sender_id,
                    message_type=AILMessageType.COLLABORATION_INVITE,
                    cognitive_intent=CognitiveIntentType.INFORM,
                    content=json.dumps({'status': 'declined', 'reason': 'high_cognitive_load'}),
                    collaboration_potential=0.0
                )
                
                return {
                    'response_messages': [response]
                }
            
        except Exception as e:
            self.logger.error(f"Error handling collaboration invite: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_attention_alert(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle attention alert message"""
        try:
            # Create high-priority attention target
            attention_target = AttentionTarget(
                target_id=f"alert_{message.message_id}",
                target_type='alert',
                content=message.content,
                priority=1.0,  # Maximum priority
                urgency=1.0,
                relevance=message.attention_priority
            )
            
            return {
                'attention_updates': [attention_target]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling attention alert: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_learning_feedback(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle learning feedback message"""
        try:
            feedback_data = json.loads(message.content) if message.content.startswith('{') else {'feedback': message.content}
            
            # Create learning experience from feedback
            learning_exp = LearningExperience(
                experience_id=f"feedback_{message.message_id}",
                agent_id=message.receiver_id,
                learning_type=LearningType.INSTRUCTIONAL,
                context={'feedback_provider': message.sender_id},
                action_taken='receive_feedback',
                outcome={'feedback_received': True},
                feedback=feedback_data,
                success_score=0.7,
                confidence=message.learning_value
            )
            
            return {
                'learning_experiences': [learning_exp]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling learning feedback: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_context_sync(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle context synchronization message"""
        try:
            context_data = json.loads(message.content) if message.content.startswith('{') else {'context': message.content}
            
            # Store context information
            memory_item = MemoryItem(
                memory_id=f"context_sync_{message.receiver_id}_{int(time.time() * 1000)}",
                agent_id=message.receiver_id,
                memory_type=MemoryType.EPISODIC,
                content=f"Context sync from {message.sender_id}: {json.dumps(context_data)}",
                metadata={
                    'context_sync': True,
                    'source_agent': message.sender_id,
                    'sync_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return {
                'memory_updates': [memory_item]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling context sync: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_reasoning_trace(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle reasoning trace sharing"""
        try:
            trace_data = json.loads(message.content) if message.content.startswith('{') else {'trace': message.content}
            
            # Store reasoning trace for learning
            memory_item = MemoryItem(
                memory_id=f"reasoning_trace_{message.receiver_id}_{int(time.time() * 1000)}",
                agent_id=message.receiver_id,
                memory_type=MemoryType.PROCEDURAL,
                content=f"Reasoning trace from {message.sender_id}: {json.dumps(trace_data)}",
                metadata={
                    'reasoning_trace': True,
                    'source_agent': message.sender_id,
                    'learning_opportunity': True
                }
            )
            
            # Create learning experience
            learning_exp = LearningExperience(
                experience_id=f"reasoning_trace_{message.message_id}",
                agent_id=message.receiver_id,
                learning_type=LearningType.OBSERVATIONAL,
                context={'reasoning_source': message.sender_id, 'trace': trace_data},
                action_taken='observe_reasoning',
                outcome={'reasoning_observed': True},
                success_score=0.8,
                confidence=message.learning_value
            )
            
            return {
                'memory_updates': [memory_item],
                'learning_experiences': [learning_exp]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling reasoning trace: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_query(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle query message (legacy support)"""
        return await self._handle_cognitive_request(message)
    
    async def _handle_response(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle response message (legacy support)"""
        return await self._handle_cognitive_response(message)
    
    async def _handle_notification(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle notification message"""
        try:
            # Store notification
            memory_item = MemoryItem(
                memory_id=f"notification_{message.receiver_id}_{int(time.time() * 1000)}",
                agent_id=message.receiver_id,
                memory_type=MemoryType.EPISODIC,
                content=f"Notification from {message.sender_id}: {message.content}",
                metadata={
                    'notification': True,
                    'source_agent': message.sender_id,
                    'priority': message.attention_priority
                }
            )
            
            return {
                'memory_updates': [memory_item]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling notification: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_command(self, message: EnhancedAILMessage) -> Dict[str, Any]:
        """Handle command message"""
        try:
            # Process command with cognitive engine
            command_result = await self.cognitive_engine.process_cognitive_request(
                agent_id=message.receiver_id,
                process_type=CognitiveProcessType.DECISION_MAKING,
                input_data={'command': message.content, 'commander': message.sender_id}
            )
            
            # Store command execution
            memory_item = MemoryItem(
                memory_id=f"command_{message.receiver_id}_{int(time.time() * 1000)}",
                agent_id=message.receiver_id,
                memory_type=MemoryType.PROCEDURAL,
                content=f"Command from {message.sender_id}: {message.content}",
                metadata={
                    'command': True,
                    'commander': message.sender_id,
                    'execution_result': command_result.result_data
                }
            )
            
            return {
                'cognitive_response': command_result,
                'memory_updates': [memory_item]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            return {'errors': [str(e)]}
    
    async def _handle_processing_result(self, result: AILProcessingResult):
        """Handle the result of message processing"""
        try:
            # Apply attention updates
            for attention_target in result.attention_updates:
                await self.attention_manager.set_primary_focus(
                    agent_id=attention_target.target_id.split('_')[0],  # Extract agent ID
                    target=attention_target
                )
            
            # Add learning experiences
            for learning_exp in result.learning_experiences:
                await self.learning_loop.add_learning_experience(learning_exp)
            
            # Store memory updates
            for memory_item in result.memory_updates:
                await self.memory_interface.store_memory_item(memory_item)
            
            # Send response messages
            for response_msg in result.response_messages:
                await self.send_enhanced_ail_message(response_msg)
            
            # Log processing result
            if result.errors:
                self.logger.warning(f"Processing errors for {result.message_id}: {result.errors}")
            else:
                self.logger.debug(f"Successfully processed message {result.message_id} in {result.processing_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"Error handling processing result: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            total_messages = sum(len(history) for history in self.message_history.values())
            active_queues = sum(len(queue) for queue in self.processing_queue.values())
            active_collaborations = len(self.active_collaborations)
            
            return {
                'total_messages_processed': total_messages,
                'active_message_queues': active_queues,
                'active_collaborations': active_collaborations,
                'registered_agents': len(self.processing_queue),
                'message_types_supported': len(self.message_handlers),
                'running': self._running
            }
            
        except Exception as e:
            self.logger.error(f"Error getting processing stats: {e}")
            return {'error': str(e)}


# Global enhanced AIL processor instance
_global_enhanced_ail_processor: Optional[EnhancedAILProcessor] = None


def get_enhanced_ail_processor(memory_interface: Optional[UnifiedMemoryInterface] = None,
                              message_bus: Optional[UnifiedMessageBus] = None,
                              cognitive_engine: Optional[CognitiveEngine] = None,
                              attention_manager: Optional[AttentionManager] = None,
                              learning_loop: Optional[LearningLoop] = None) -> EnhancedAILProcessor:
    """Get the global enhanced AIL processor instance"""
    global _global_enhanced_ail_processor
    
    if _global_enhanced_ail_processor is None:
        if memory_interface is None:
            from .memory_interface import get_memory_interface
            memory_interface = get_memory_interface()
        
        if message_bus is None:
            from .message_bus import get_message_bus
            message_bus = get_message_bus()
        
        if cognitive_engine is None:
            from .cognitive_engine import get_cognitive_engine
            cognitive_engine = get_cognitive_engine()
        
        if attention_manager is None:
            from .attention_manager import get_attention_manager
            attention_manager = get_attention_manager()
        
        if learning_loop is None:
            from .learning_loop import get_learning_loop
            learning_loop = get_learning_loop()
        
        _global_enhanced_ail_processor = EnhancedAILProcessor(
            memory_interface, message_bus, cognitive_engine, attention_manager, learning_loop
        )
    
    return _global_enhanced_ail_processor


async def send_cognitive_request(sender_id: str, receiver_id: str, query: str, 
                               process_type: CognitiveProcessType = CognitiveProcessType.REASONING) -> bool:
    """Helper function to send a cognitive request"""
    processor = get_enhanced_ail_processor()
    message = EnhancedAILMessage(
        message_id=f"cog_req_{sender_id}_{int(asyncio.get_event_loop().time() * 1000)}",
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=AILMessageType.COGNITIVE_REQUEST,
        cognitive_intent=CognitiveIntentType.REQUEST,
        content=json.dumps({'query': query, 'process_type': process_type.value}),
        attention_priority=0.8,
        learning_value=0.7
    )
    message.cognitive_context.required_cognitive_processes = [process_type]
    
    return await processor.send_enhanced_ail_message(message)


async def share_knowledge(sender_id: str, receiver_id: str, knowledge: str, 
                         knowledge_type: str = 'general') -> bool:
    """Helper function to share knowledge"""
    processor = get_enhanced_ail_processor()
    message = EnhancedAILMessage(
        message_id=f"knowledge_{sender_id}_{int(asyncio.get_event_loop().time() * 1000)}",
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=AILMessageType.KNOWLEDGE_SHARE,
        cognitive_intent=CognitiveIntentType.TEACH,
        content=knowledge,
        attention_priority=0.7,
        learning_value=0.9,
        collaboration_potential=0.6,
        semantic_tags=[knowledge_type, 'knowledge_sharing']
    )
    
    return await processor.send_enhanced_ail_message(message)
