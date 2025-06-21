# LANS Project System-Level Architecture and Feature Report

*Generated: June 18, 2025*

## 0. Vision and Objectives

My ambition for LANS is to build an integrated cognitive environment where multiple LLM-based agents collaborate seamlessly on user-defined tasks. Leveraging a Global Memory & Cognitive Processing (GMCP) layer and the Agent Instruction Language (AIL), LANS aims to:

- Coordinate a team of AI agents working together as a cohesive unit
- Minimize token usage and communication overhead via efficient AIL scripts
- Provide long-term shared memory so agents retain awareness of teammates’ capabilities, roles, and past interactions
- Deliver end-to-end task execution driven by user prompts, with agents planning, executing, and verifying results as a team

This vision underpins the system architecture and guides future development toward truly collaborative AI workflows.

---

## 0.1 Three Key Pillars of LANS

LANS is founded on three interlocking pillars that enable robust multi-agent collaboration, cognitive processing, and efficient instruction:

1. **AgentOS Kernel**
   - The execution engine for AIL scripts, responsible for parsing, planning, and dispatching agent tasks.
   - Manages tool registration, cognitive workflows, and integrates subcomponents (memory, LLM clients).

2. **GMCP Layer (Global Memory & Cognitive Processing)**
   - Centralized memory management across episodic, semantic, and procedural stores.
   - Provides unified APIs for storing, retrieving, and auditing memories with overfitting prevention.

3. **AIL (Agent Instruction Language)**
   - A domain-specific, token-efficient language for orchestrating multi-step cognitive operations.
   - Enables concise expression of QUERY, EXECUTE, PLAN, communication, error handling, and async flows.

---

## 1. Introduction
This document provides a high-level overview of the LANS (Large Artificial Neural System) project architecture, core modules, interactions, and key features. It is intended to complement the atomic code study and issue reports by illustrating the system design and feature set.

## 2. Architectural Overview

The LANS system is organized into the following major layers and components:

1. **AgentOS Kernel**
   - **Role**: Orchestrates execution of Agent Instruction Language (AIL) cognitions, coordinates memory operations, tool invocations, and multi-step plans.
   - **Key Classes**: `AgentOSKernel`, `ToolRegistry`, `QueryPlanner`, `CognitionResult`, `QueryPlan`.
   - **Responsibilities**:
     - Parse and validate AIL scripts (`AILParser`).
     - Plan and execute queries over memory (`QueryPlanner`).
     - Dispatch operations (QUERY, EXECUTE, PLAN, COMMUNICATE, advanced ops: LET, TRY, AWAIT, SANDBOXED_EXECUTE, CLARIFY, EVENT).
     - Register and execute tools (built-in shell/json tools, AI-powered tools).
     - Log cognition executions to persistent storage.

2. **Global Memory Manager**
   - **Role**: Provides a unified interface for storing and retrieving different memory types.
   - **Key Classes**: `GlobalMemoryManager`, `MemoryQuery`, `MemoryItem`.
   - **Memory Types**:
     - **EpisodicMemory**: Sequence of experiences (timestamps, sessions).
     - **SemanticMemory**: Facts and concepts with relations, confidence scores.
     - **ProceduralMemory**: Skills and methods with usage tracking, success rates.
   - **Responsibilities**:
     - Coordinate memory upserts (store) with overfitting prevention.
     - Perform retrieval (text-based and vector similarity searches).
     - Maintain statistics and audits.

3. **Memory Types (Knowledge Stores)**
   - **Episodic Memory**: Temporal logs of interactions.
   - **Semantic Memory**: Concept definitions, relations, embedding-based knowledge search.
   - **Procedural Memory**: How-to knowledge, skill recommendations, usage history.

4. **Agent Modules (Core Logic)**
   - **PlanningAgent**: Analyzes requirements, generates `ProjectSpec`, creates task breakdowns, and recovery plans.
   - **CodingAgent**: Implements tasks by generating files, directories, and commands via LLM or templates; fixes code errors.
   - **RequestAnalyzer**: Interprets user requests into structured `RequestAnalysis` objects (intent, file targets, commands).
   - **CodeGenerator**: Generates file contents, code snippets, or full project structures from descriptions and requirements.

5. **LLM Integration**
   - **OllamaClient**: Primary client for model inference using Ollama servers.
   - Agents and tools leverage LLM calls for specification analysis, code generation, parsing complex intents, and more.

6. **Storage and Persistence**
   - **DatabaseManager**: Abstracts database interactions (PostgreSQL or SQLite) for memories, cognitions, and variables.
   - **Variable Storage**: Supports LET operations with scoped variables saved and cleaned up per cognition.

7. **Utilities and Support**
   - **EmbeddingGenerator**: Wraps external embedding service for vector representations.
   - **OverfittingPreventionManager**: Analyzes memory inputs to prevent redundant or low-value memory storage.
   - **AI Tools**: `RealAICodeGenerator`, `RealAICreativeWriter`, `RealAIAnalyzer` as optional tools.

8. **Configuration and Initialization**
   - **LANSConfig**: Holds global settings (LLM endpoints, model names, timeouts).
   - **initialize()** methods across components ensure proper setup (DB schema, embedding services, memory handlers).

## 3. Component Interactions

```text
+------------------+       +------------------------+      +------------------+
|  AgentOS Kernel  | <---> |  GlobalMemoryManager   | <--> |  Memory Types    |
|  (AIL parsing,   |       |  (store/retrieve APIs) |      |  (episodic,      |
|   tool registry) |       +------------------------+      |   semantic,      |
+------------------+                                      |   procedural)    |
       |  ^                                            +-->|                  |
       v  |                                            |   +------------------+
+------------------+   calls    +-------------+       |
|  Agent Modules   |----------->|  Ollama     |-------+  
|  (planning,      |            |  Client     |          
|   coding,        |<-----------|  (LLM API)  |          
|   analysis,      |            +-------------+          
|   code generator)|                                    
+------------------+                                    
```

- **Agent Modules** invoke **AgentOSKernel** to execute high-level AIL workflows.
- **Kernel** interacts with **MemoryManager** for storage and retrieval of memories.
- **MemoryManager** delegates to specialized memory type classes.
- **Agents** and **Kernel** use **OllamaClient** for LLM-driven tasks.
- **DatabaseManager** underlies persistent storage of memories and cognition logs.

## 4. Key Features

- **Agent Instruction Language (AIL v3.1)**: Domain-specific language for cognitive workflows (QUERY, EXECUTE, PLAN, LET, TRY, ON-FAIL, AWAIT, SANDBOXED-EXECUTE, CLARIFY, EVENT).
- **Multi-Modal Memory System**:
  - Episodic: Timeline of events
  - Semantic: Conceptual knowledge with relations
  - Procedural: Skill and task routines
- **Overfitting Prevention**: Ensures memory quality by rejecting low-value or redundant entries.
- **LLM-Driven Planning and Coding**: Agents leverage LLMs for architecture design, task breakdown, code generation, and error fixing.
- **Tool Registry**: Pluggable tool execution framework for shell commands, JSON formatting, and AI-powered tools.
- **Query Planner**: Intelligent planning engine for memory queries with modes (standard, exploratory, connection).
- **Variable Scoping and TRY/ON-FAIL**: Built-in support for variable binding, asynchronous operations, and structured error recovery.
- **Sandboxed Execution**: Configurable resource limits for safe tool operations.
- **Metrics and Audits**: Built-in tracking of memory operations, query counts, and audit scheduling.
- **Extensible Architecture**: Modular memory types, agents, and tool registration for future expansion.

## 5. Conclusion and Next Steps
- The system-level architecture supports cognitive workflows across planning, memory retrieval, and code generation.
- Key areas for improvement (see issues report): input validation, error handling, performance tuning, and security hardening.
- Next phase: implement priority fixes from `CODE_ANALYSIS_ISSUES_REPORT.md` and extend monitoring and observability.

## 6. Alignment with Vision

This section evaluates how the current LANS architecture and features align with the stated vision and objectives.

| Vision Objective                                               | Implementation Status                                  | Notes / Gaps                                               |
|----------------------------------------------------------------|-------------------------------------------------------|------------------------------------------------------------|
| **Multi-Agent Collaboration**                                  | ✅ Supported via AIL [COMMUNICATE] and ToolRegistry    | Agents can exchange messages, but richer team coordination and direct peer discovery may be added. |
| **Efficient Communication (Token Savings)**                    | ✅ AIL scripting reduces verbosity                      | Further optimization (macro operations, compression) could enhance efficiency. |
| **Global Memory & Cognitive Processing (GMCP) Layer**         | ✅ Implemented in GlobalMemoryManager                  | Memory consolidation across agent contexts works; consider shared memory caching for performance. |
| **Long-Term Shared Memory**                                    | ✅ Episodic, Semantic, Procedural memory types          | Retention policies and cross-agent memory merges are in place; audit workflows can be extended. |
| **End-to-End Task Execution Driven by User Prompts**           | ✅ Agents handle planning, implementation, error recovery | Integration flows exist; orchestrator could expose higher-level APIs for multi-agent workflows. |
| **Agent Awareness of Team Capabilities & Past Interactions**   | ✅ Causality tracking and memory history available      | Dashboard or introspection APIs could surface profiles and histories to agents. |
| **Scalable & Extensible Architecture**                        | ✅ Modular components and clear interfaces              | Future plug-ins (new memory types, agents, tools) supported; CI/CD integration recommended. |

**Summary**: The current LANS architecture closely aligns with the vision:
- AIL provides concise orchestration for multi-agent collaboration.
- The GMCP layer and memory subsystems offer robust long-term memory.
- Agents cover planning, coding, analysis, and code generation stages.

**Improvement Opportunities**:
1. Enhance peer-to-peer coordination patterns (agent discovery, group planning).
2. Add compression or macro features to AIL for further token savings.
3. Develop introspection endpoints so agents can query teammates’ profiles.
4. Build higher-level orchestrator APIs to submit comprehensive multi-agent workflows.

---
