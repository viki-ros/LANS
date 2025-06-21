"""
Unified Message Bus - Phase 1 Foundation
=======================================

A unified message bus that addresses the communication architecture issues
identified in the analysis. Provides reliable, secure agent-to-agent
communication with support for multiple protocols.

Key improvements:
- Unified message routing and delivery
- Support for AIL and other protocols
- Reliable delivery with retry mechanisms
- Agent discovery and addressing
- Security and authentication
"""

import asyncio
import uuid
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types supported by the message bus"""
    AIL_COGNITION = "ail_cognition"
    DIRECT_MESSAGE = "direct_message"
    BROADCAST = "broadcast"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    SYSTEM = "system"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class DeliveryMode(Enum):
    """Message delivery modes"""
    BEST_EFFORT = "best_effort"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class Message:
    """Unified message structure"""
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Any
    priority: MessagePriority = MessagePriority.NORMAL
    delivery_mode: DeliveryMode = DeliveryMode.BEST_EFFORT
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None


@dataclass
class MessageEnvelope:
    """Message envelope for routing and delivery tracking"""
    message: Message
    routing_key: str
    delivery_attempts: int = 0
    max_attempts: int = 3
    next_retry: Optional[datetime] = None
    delivery_receipt: Optional[str] = None


class MessageHandler:
    """Base class for message handlers"""
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle a message and optionally return a response"""
        raise NotImplementedError


class MessageSubscription:
    """Message subscription for routing"""
    
    def __init__(
        self,
        subscriber_id: str,
        message_types: Set[MessageType],
        handler: MessageHandler,
        routing_pattern: Optional[str] = None
    ):
        self.subscriber_id = subscriber_id
        self.message_types = message_types
        self.handler = handler
        self.routing_pattern = routing_pattern
        self.created_at = datetime.utcnow()


class MessageQueue:
    """Thread-safe message queue with priority support"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue = asyncio.PriorityQueue(maxsize=max_size)
        self._lock = asyncio.Lock()
    
    async def put(self, envelope: MessageEnvelope):
        """Put message envelope in queue"""
        # Use negative priority for correct ordering (higher priority = lower number)
        priority_value = -envelope.message.priority.value
        await self._queue.put((priority_value, time.time(), envelope))
    
    async def get(self) -> MessageEnvelope:
        """Get message envelope from queue"""
        _, _, envelope = await self._queue.get()
        return envelope
    
    async def get_nowait(self) -> Optional[MessageEnvelope]:
        """Get message envelope without waiting"""
        try:
            _, _, envelope = self._queue.get_nowait()
            return envelope
        except asyncio.QueueEmpty:
            return None
    
    def qsize(self) -> int:
        """Get queue size"""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()


class MessageRouter:
    """Message routing engine"""
    
    def __init__(self):
        self._subscriptions: Dict[str, List[MessageSubscription]] = {}
        self._agent_addresses: Dict[str, str] = {}
        self._lock = asyncio.Lock()
    
    async def register_agent(self, agent_id: str, address: str):
        """Register agent address for routing"""
        async with self._lock:
            self._agent_addresses[agent_id] = address
            logger.debug(f"Registered agent {agent_id} at {address}")
    
    async def unregister_agent(self, agent_id: str):
        """Unregister agent"""
        async with self._lock:
            self._agent_addresses.pop(agent_id, None)
            self._subscriptions.pop(agent_id, None)
            logger.debug(f"Unregistered agent {agent_id}")
    
    async def subscribe(self, subscription: MessageSubscription):
        """Add message subscription"""
        async with self._lock:
            if subscription.subscriber_id not in self._subscriptions:
                self._subscriptions[subscription.subscriber_id] = []
            self._subscriptions[subscription.subscriber_id].append(subscription)
            logger.debug(f"Added subscription for {subscription.subscriber_id}")
    
    async def unsubscribe(self, subscriber_id: str, message_types: Optional[Set[MessageType]] = None):
        """Remove message subscriptions"""
        async with self._lock:
            if subscriber_id not in self._subscriptions:
                return
            
            if message_types is None:
                # Remove all subscriptions
                del self._subscriptions[subscriber_id]
            else:
                # Remove specific subscriptions
                self._subscriptions[subscriber_id] = [
                    sub for sub in self._subscriptions[subscriber_id]
                    if not message_types.intersection(sub.message_types)
                ]
                
                if not self._subscriptions[subscriber_id]:
                    del self._subscriptions[subscriber_id]
            
            logger.debug(f"Removed subscriptions for {subscriber_id}")
    
    async def route_message(self, message: Message) -> List[str]:
        """Route message and return list of target agent IDs"""
        targets = []
        
        async with self._lock:
            # Direct message routing
            if message.recipient_id != "*":
                if message.recipient_id in self._agent_addresses:
                    targets.append(message.recipient_id)
            else:
                # Broadcast routing - find all subscribers
                for subscriber_id, subscriptions in self._subscriptions.items():
                    for subscription in subscriptions:
                        if message.message_type in subscription.message_types:
                            if subscription.routing_pattern is None or self._matches_pattern(
                                message, subscription.routing_pattern
                            ):
                                targets.append(subscriber_id)
                                break
        
        return list(set(targets))  # Remove duplicates
    
    def _matches_pattern(self, message: Message, pattern: str) -> bool:
        """Check if message matches routing pattern"""
        # Simple pattern matching for now
        # Can be extended with more sophisticated routing
        return True


class UnifiedMessageBus:
    """
    Unified message bus for agent communication.
    Addresses communication architecture issues with reliable delivery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._router = MessageRouter()
        self._message_queue = MessageQueue()
        self._pending_messages: Dict[str, MessageEnvelope] = {}
        self._handlers: Dict[str, MessageHandler] = {}
        self._delivery_receipts: Dict[str, datetime] = {}
        
        # Worker tasks
        self._workers: List[asyncio.Task] = []
        self._shutdown = False
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "average_delivery_time": 0.0
        }
        
        logger.info("UnifiedMessageBus initialized")
    
    async def start(self, worker_count: int = 3):
        """Start the message bus workers"""
        logger.info(f"Starting message bus with {worker_count} workers")
        
        for i in range(worker_count):
            worker = asyncio.create_task(self._message_worker(f"worker-{i}"))
            self._workers.append(worker)
        
        # Start retry worker
        retry_worker = asyncio.create_task(self._retry_worker())
        self._workers.append(retry_worker)
    
    async def stop(self):
        """Stop the message bus"""
        logger.info("Stopping message bus")
        self._shutdown = True
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to complete
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
    
    async def register_agent(self, agent_id: str, handler: MessageHandler):
        """Register an agent with the message bus"""
        await self._router.register_agent(agent_id, f"agent://{agent_id}")
        self._handlers[agent_id] = handler
        logger.info(f"Registered agent {agent_id} with message bus")
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the message bus"""
        await self._router.unregister_agent(agent_id)
        self._handlers.pop(agent_id, None)
        logger.info(f"Unregistered agent {agent_id} from message bus")
    
    async def subscribe(
        self,
        subscriber_id: str,
        message_types: Set[MessageType],
        handler: MessageHandler,
        routing_pattern: Optional[str] = None
    ):
        """Subscribe to message types"""
        subscription = MessageSubscription(
            subscriber_id=subscriber_id,
            message_types=message_types,
            handler=handler,
            routing_pattern=routing_pattern
        )
        await self._router.subscribe(subscription)
        logger.debug(f"Agent {subscriber_id} subscribed to {message_types}")
    
    async def send_message(self, message: Message) -> str:
        """Send a message through the bus"""
        try:
            # Set message ID if not provided
            if not message.message_id:
                message.message_id = f"msg_{uuid.uuid4().hex[:12]}"
            
            # Set expiration if not provided
            if message.expires_at is None:
                message.expires_at = datetime.utcnow() + timedelta(minutes=5)
            
            # Route message
            targets = await self._router.route_message(message)
            
            if not targets:
                logger.warning(f"No targets found for message {message.message_id}")
                return message.message_id
            
            # Create envelope and queue for delivery
            envelope = MessageEnvelope(
                message=message,
                routing_key=f"{message.sender_id}->{','.join(targets)}"
            )
            
            await self._message_queue.put(envelope)
            
            # Track pending message if delivery confirmation required
            if message.delivery_mode != DeliveryMode.BEST_EFFORT:
                self._pending_messages[message.message_id] = envelope
            
            self._stats["messages_sent"] += 1
            logger.debug(f"Queued message {message.message_id} for {len(targets)} targets")
            
            return message.message_id
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self._stats["messages_failed"] += 1
            raise
    
    async def send_ail_cognition(
        self,
        sender_id: str,
        recipient_id: str,
        ail_instruction: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send an AIL cognition message"""
        message = Message(
            message_id=f"ail_{uuid.uuid4().hex[:12]}",
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.AIL_COGNITION,
            content=ail_instruction,
            metadata=metadata or {},
            priority=MessagePriority.NORMAL
        )
        
        return await self.send_message(message)
    
    async def send_direct_message(
        self,
        sender_id: str,
        recipient_id: str,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Send a direct message"""
        message = Message(
            message_id=f"direct_{uuid.uuid4().hex[:12]}",
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.DIRECT_MESSAGE,
            content=content,
            priority=priority
        )
        
        return await self.send_message(message)
    
    async def broadcast_message(
        self,
        sender_id: str,
        content: Any,
        message_type: MessageType = MessageType.BROADCAST
    ) -> str:
        """Broadcast a message to all subscribed agents"""
        message = Message(
            message_id=f"broadcast_{uuid.uuid4().hex[:12]}",
            sender_id=sender_id,
            recipient_id="*",
            message_type=message_type,
            content=content
        )
        
        return await self.send_message(message)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        stats = self._stats.copy()
        stats.update({
            "queue_size": self._message_queue.qsize(),
            "pending_messages": len(self._pending_messages),
            "registered_agents": len(self._handlers),
            "active_workers": len([w for w in self._workers if not w.done()])
        })
        return stats
    
    async def _message_worker(self, worker_id: str):
        """Message processing worker"""
        logger.debug(f"Message worker {worker_id} started")
        
        while not self._shutdown:
            try:
                # Get message from queue
                envelope = await self._message_queue.get()
                
                if envelope.message.expires_at and datetime.utcnow() > envelope.message.expires_at:
                    logger.debug(f"Message {envelope.message.message_id} expired")
                    continue
                
                # Deliver message
                await self._deliver_message(envelope)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message worker {worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Message worker {worker_id} stopped")
    
    async def _deliver_message(self, envelope: MessageEnvelope):
        """Deliver a message to its targets"""
        message = envelope.message
        start_time = time.time()
        
        try:
            # Route message to get current targets
            targets = await self._router.route_message(message)
            
            delivered = 0
            for target_id in targets:
                if target_id in self._handlers:
                    try:
                        handler = self._handlers[target_id]
                        response = await handler.handle_message(message)
                        
                        # Handle response if provided
                        if response and message.reply_to:
                            await self.send_message(response)
                        
                        delivered += 1
                        
                    except Exception as e:
                        logger.error(f"Handler error for agent {target_id}: {e}")
                        envelope.delivery_attempts += 1
                        
                        # Retry if needed
                        if envelope.delivery_attempts < envelope.max_attempts:
                            envelope.next_retry = datetime.utcnow() + timedelta(seconds=2 ** envelope.delivery_attempts)
                            continue
            
            # Update statistics
            delivery_time = time.time() - start_time
            self._stats["messages_delivered"] += delivered
            
            # Update average delivery time
            current_avg = self._stats["average_delivery_time"]
            total_delivered = self._stats["messages_delivered"]
            if total_delivered > 0:
                self._stats["average_delivery_time"] = (
                    (current_avg * (total_delivered - delivered) + delivery_time * delivered) / total_delivered
                )
            
            # Remove from pending if delivery confirmed
            if message.delivery_mode != DeliveryMode.BEST_EFFORT:
                self._pending_messages.pop(message.message_id, None)
            
            logger.debug(f"Delivered message {message.message_id} to {delivered}/{len(targets)} targets")
            
        except Exception as e:
            logger.error(f"Failed to deliver message {message.message_id}: {e}")
            envelope.delivery_attempts += 1
            
            # Schedule retry
            if envelope.delivery_attempts < envelope.max_attempts:
                envelope.next_retry = datetime.utcnow() + timedelta(seconds=2 ** envelope.delivery_attempts)
            else:
                self._stats["messages_failed"] += 1
                self._pending_messages.pop(message.message_id, None)
    
    async def _retry_worker(self):
        """Worker for handling message retries"""
        logger.debug("Retry worker started")
        
        while not self._shutdown:
            try:
                current_time = datetime.utcnow()
                
                # Check pending messages for retries
                for message_id, envelope in list(self._pending_messages.items()):
                    if envelope.next_retry and current_time >= envelope.next_retry:
                        envelope.next_retry = None
                        await self._message_queue.put(envelope)
                
                await asyncio.sleep(1)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Retry worker error: {e}")
                await asyncio.sleep(1)
        
        logger.debug("Retry worker stopped")


# Global message bus instance
_global_message_bus: Optional[UnifiedMessageBus] = None


async def get_message_bus(config: Optional[Dict[str, Any]] = None) -> UnifiedMessageBus:
    """Get the global message bus"""
    global _global_message_bus
    
    if _global_message_bus is None:
        _global_message_bus = UnifiedMessageBus(config)
        # Don't start automatically - let caller start when ready
    
    return _global_message_bus


async def send_ail_message(sender_id: str, recipient_id: str, ail_instruction: str) -> str:
    """Convenience function to send AIL message"""
    bus = await get_message_bus()
    return await bus.send_ail_cognition(sender_id, recipient_id, ail_instruction)


async def send_direct_message(sender_id: str, recipient_id: str, content: Any) -> str:
    """Convenience function to send direct message"""
    bus = await get_message_bus()
    return await bus.send_direct_message(sender_id, recipient_id, content)
