"""
Unified AgentOS - Complete Architecture
======================================

A unified agent operating system that provides a complete cognitive architecture
for intelligent agents. This package includes both foundational components
(Phase 1) and advanced cognitive capabilities (Phase 2):

Phase 1 Foundation:
- AgentRuntime: Unified agent lifecycle management
- MemoryInterface: Unified memory access and operations
- MessageBus: Unified communication and message routing
- AgentRegistry: Centralized agent identity and discovery

Phase 2 Cognitive Architecture:
- CognitiveEngine: Core cognitive processing and reasoning
- AttentionManager: Focus and priority management
- LearningLoop: Adaptive learning and knowledge integration
- EnhancedAILProcessor: Cognitive-aware inter-agent communication

This complete architecture addresses critical issues:
1. Fragmented memory access across multiple systems
2. Missing cognitive loops for continuous learning
3. Inconsistent agent identity and session management
4. Complex initialization chains that are error-prone
5. Communication architecture bottlenecks
6. Lack of sophisticated reasoning and decision-making
7. Absence of attention management and focus control
8. Missing adaptive learning capabilities
9. Limited inter-agent collaboration and knowledge sharing
"""

from .agent_runtime import (
    AgentRuntime,
    AgentRegistry,
    Agent,
    AgentProfile,
    AgentContext,
    AgentState,
    AgentCapability,
    get_global_registry,
    get_global_runtime,
    create_agent
)

from .memory_interface import (
    UnifiedMemoryInterface,
    MemoryItem,
    MemoryQuery,
    MemoryType,
    MemoryStats,
    MemoryCache,
    get_memory_interface,
    store_memory,
    retrieve_memories
)

from .message_bus import (
    UnifiedMessageBus,
    Message,
    MessageHandler,
    MessageType,
    MessagePriority,
    DeliveryMode,
    MessageSubscription,
    get_message_bus,
    send_ail_message,
    send_direct_message
)

from .cognitive_engine import (
    CognitiveEngine,
    CognitiveProcessType,
    CognitiveState,
    CognitiveContext,
    CognitiveProcess,
    CognitiveResult,
    get_cognitive_engine,
    process_cognitive_request
)

from .attention_manager import (
    AttentionManager,
    AttentionType,
    AttentionScope,
    FocusState,
    AttentionTarget,
    AttentionFilter,
    AttentionContext,
    AttentionState,
    get_attention_manager,
    set_agent_focus,
    filter_agent_information
)

from .learning_loop import (
    LearningLoop,
    LearningType,
    LearningMode,
    KnowledgeType,
    LearningExperience,
    LearningPattern,
    KnowledgeItem,
    LearningGoal,
    LearningState,
    get_learning_loop,
    add_agent_experience
)

from .enhanced_ail_processor import (
    EnhancedAILProcessor,
    AILMessageType,
    CognitiveIntentType,
    AILCognitiveContext,
    EnhancedAILMessage,
    AILProcessingResult,
    get_enhanced_ail_processor,
    send_cognitive_request,
    share_knowledge
)

__version__ = "2.0.0"
__author__ = "LANS Team"

__all__ = [
    # Agent Runtime
    "AgentRuntime",
    "AgentRegistry", 
    "Agent",
    "AgentProfile",
    "AgentContext",
    "AgentState",
    "AgentCapability",
    "get_global_registry",
    "get_global_runtime",
    "create_agent",
    
    # Memory Interface
    "UnifiedMemoryInterface",
    "MemoryItem",
    "MemoryQuery",
    "MemoryType",
    "MemoryStats",
    "MemoryCache",
    "get_memory_interface",
    "store_memory",
    "retrieve_memories",
    
    # Message Bus
    "UnifiedMessageBus",
    "Message",
    "MessageHandler",
    "MessageType",
    "MessagePriority",
    "DeliveryMode",
    "MessageSubscription",
    "get_message_bus",
    "send_ail_message",
    "send_direct_message",
    
    # Cognitive Engine
    "CognitiveEngine",
    "CognitiveProcessType",
    "CognitiveState",
    "CognitiveContext",
    "CognitiveProcess",
    "CognitiveResult",
    "get_cognitive_engine",
    "process_cognitive_request",
    
    # Attention Manager
    "AttentionManager",
    "AttentionType",
    "AttentionScope",
    "FocusState",
    "AttentionTarget",
    "AttentionFilter",
    "AttentionContext",
    "AttentionState",
    "get_attention_manager",
    "set_agent_focus",
    "filter_agent_information",
    
    # Learning Loop
    "LearningLoop",
    "LearningType",
    "LearningMode",
    "KnowledgeType",
    "LearningExperience",
    "LearningPattern",
    "KnowledgeItem",
    "LearningGoal",
    "LearningState",
    "get_learning_loop",
    "add_agent_experience",
    
    # Enhanced AIL Processor
    "EnhancedAILProcessor",
    "AILMessageType",
    "CognitiveIntentType",
    "AILCognitiveContext",
    "EnhancedAILMessage",
    "AILProcessingResult",
    "get_enhanced_ail_processor",
    "send_cognitive_request",
    "share_knowledge"
]
