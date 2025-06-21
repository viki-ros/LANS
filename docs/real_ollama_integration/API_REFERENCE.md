# API Reference - Real Ollama LLM Multi-Agent System

## 📚 **API Overview**

This document provides comprehensive API reference for the Real Ollama LLM Multi-Agent Integration System, including classes, methods, parameters, and usage examples.

---

## 🤖 **RealOllamaAgent API**

### Class Definition

```python
class RealOllamaAgent:
    """
    Real LLM-powered agent with personality and specialization capabilities
    
    Provides direct integration with Ollama models for authentic AI interactions
    """
```

### Constructor

```python
def __init__(self, agent_id: str, model: str, profile: dict):
    """
    Initialize a real Ollama-powered agent
    
    Args:
        agent_id (str): Unique identifier for the agent
        model (str): Ollama model name (e.g., "deepseek-r1:8b") 
        profile (dict): Agent profile including personality traits and specializations
        
    Example:
        >>> agent = RealOllamaAgent(
        ...     agent_id="strategic_planner",
        ...     model="deepseek-r1:8b", 
        ...     profile=AGENT_PROFILES["strategic_planner"]
        ... )
    """
```

### Core Methods

#### `process_request()`

```python
def process_request(self, prompt: str, context: dict = None) -> dict:
    """
    Process a request using real LLM capabilities
    
    Args:
        prompt (str): The task or question to process
        context (dict, optional): Additional context including:
            - scenario: Current scenario information
            - phase: Current collaboration phase
            - previous_results: Results from other agents
            - complexity: Task complexity (1-10)
            
    Returns:
        dict: Processing result containing:
            - response: The agent's LLM-generated response
            - model_used: Ollama model that processed the request
            - tokens_used: Number of tokens consumed
            - success: Whether the request was successful
            - error: Error message if unsuccessful
            - cognitive_analysis: Real-time cognitive assessment
            
    Raises:
        OllamaConnectionError: When Ollama server is unreachable
        ModelNotFoundError: When specified model is not available
        PromptProcessingError: When prompt processing fails
        
    Example:
        >>> context = {"scenario": "system_design", "complexity": 8}
        >>> result = agent.process_request(
        ...     "Design a scalable microservices architecture", 
        ...     context
        ... )
        >>> print(result['response'])
        >>> print(f"Tokens used: {result['tokens_used']}")
    """
```

#### `get_cognitive_state()`

```python
def get_cognitive_state(self) -> dict:
    """
    Get current cognitive state of the agent
    
    Returns:
        dict: Cognitive state including:
            - experience_level: Accumulated experience (0.0+)
            - performance_score: Current performance rating (0.0-1.0)
            - adaptation_level: Learning adaptation capability (0.0-1.0)
            - total_interactions: Number of completed interactions
            - average_quality_score: Average response quality
            
    Example:
        >>> state = agent.get_cognitive_state()
        >>> print(f"Experience: {state['experience_level']:.2f}")
        >>> print(f"Performance: {state['performance_score']:.2f}")
    """
```

#### `update_cognitive_state()`

```python
def update_cognitive_state(self, analysis: dict) -> None:
    """
    Update agent's cognitive state based on interaction analysis
    
    Args:
        analysis (dict): Cognitive analysis from interaction containing:
            - prompt_complexity: Task difficulty assessment
            - response_quality_score: Quality of generated response
            - cognitive_load: Mental effort required
            - learning_opportunity: Areas for improvement
            
    Example:
        >>> analysis = {
        ...     "prompt_complexity": 7.5,
        ...     "response_quality_score": 0.85,
        ...     "cognitive_load": 0.6
        ... }
        >>> agent.update_cognitive_state(analysis)
    """
```

---

## 🎯 **RealMultiAgentOrchestrator API**

### Class Definition

```python
class RealMultiAgentOrchestrator:
    """
    Advanced orchestration system for coordinating real LLM agents
    
    Manages complex multi-agent scenarios with sophisticated collaboration
    """
```

### Constructor

```python
def __init__(self):
    """
    Initialize the multi-agent orchestrator with real agents
    
    Automatically sets up:
    - 4 real LLM agents with distinct personalities
    - Advanced multi-agent coordinator
    - Cognitive analysis engine
    - Enhanced test execution framework
    """
```

### Core Methods

#### `execute_scenario()`

```python
async def execute_scenario(self, scenario: dict) -> dict:
    """
    Execute a complete multi-agent scenario with real LLM interactions
    
    Args:
        scenario (dict): Scenario definition containing:
            - name: Scenario name
            - description: Task description
            - complexity: Difficulty level (1-10)
            - phases: List of collaboration phases (optional)
            
    Returns:
        dict: Comprehensive scenario results including:
            - success: Overall scenario success status
            - interactions: List of all agent interactions
            - collaboration_metrics: Multi-agent collaboration analysis
            - performance_metrics: Performance and efficiency data
            - cognitive_analysis: Learning and adaptation insights
            - total_tokens: Total tokens consumed across all agents
            - total_duration: Total execution time
            
    Example:
        >>> scenario = {
        ...     "name": "AI System Architecture",
        ...     "description": "Design a scalable AI system",
        ...     "complexity": 8
        ... }
        >>> result = await orchestrator.execute_scenario(scenario)
        >>> print(f"Success: {result['success']}")
        >>> print(f"Total tokens: {result['total_tokens']}")
    """
```

#### `execute_integration_test()`

```python
async def execute_integration_test(self) -> dict:
    """
    Execute comprehensive integration test with multiple scenarios
    
    Returns:
        dict: Complete integration test results including:
            - integration_summary: Overall test statistics
            - scenario_results: Detailed results for each scenario
            - agent_performance: Individual agent performance data
            - technical_achievements: Achievement validation
            - sophisticated_features_utilized: Feature usage analysis
            - integration_quality: Quality assessment metrics
            
    Example:
        >>> results = await orchestrator.execute_integration_test()
        >>> print(f"Success rate: {results['integration_summary']['integration_success_rate']}")
        >>> print(f"Total scenarios: {results['integration_summary']['total_scenarios']}")
    """
```

#### `get_agent()`

```python
def get_agent(self, agent_id: str) -> RealOllamaAgent:
    """
    Get a specific agent by ID
    
    Args:
        agent_id (str): Agent identifier (strategic_planner, code_specialist, etc.)
        
    Returns:
        RealOllamaAgent: The requested agent instance
        
    Raises:
        AgentNotFoundError: When agent ID doesn't exist
        
    Example:
        >>> planner = orchestrator.get_agent("strategic_planner")
        >>> print(planner.profile['name'])
    """
```

#### `get_all_agents()`

```python
def get_all_agents(self) -> dict[str, RealOllamaAgent]:
    """
    Get all available agents
    
    Returns:
        dict: Dictionary mapping agent IDs to agent instances
        
    Example:
        >>> agents = orchestrator.get_all_agents()
        >>> for agent_id, agent in agents.items():
        ...     print(f"{agent_id}: {agent.profile['name']}")
    """
```

---

## 🧠 **CognitiveAnalysisEngine API**

### Class Definition

```python
class CognitiveAnalysisEngine:
    """
    Real-time cognitive analysis for LLM interactions
    
    Provides sophisticated analysis of agent performance and learning
    """
```

### Core Methods

#### `analyze_interaction()`

```python
def analyze_interaction(self, agent_id: str, prompt: str, response: str, context: dict) -> dict:
    """
    Perform comprehensive cognitive analysis of an LLM interaction
    
    Args:
        agent_id (str): ID of the agent that generated the response
        prompt (str): Original prompt/request
        response (str): Agent's LLM-generated response  
        context (dict): Interaction context and metadata
        
    Returns:
        dict: Detailed cognitive analysis including:
            - prompt_complexity: Difficulty assessment (0-10)
            - response_length: Character count of response
            - response_quality_score: Quality rating (0-1)
            - specialization_relevance: How well response matches agent expertise
            - personality_expression: How well response reflects agent personality
            - cognitive_load: Mental effort estimation (0-1)
            - learning_opportunity: Identified learning areas
            
    Example:
        >>> analysis = engine.analyze_interaction(
        ...     agent_id="strategic_planner",
        ...     prompt="Design system architecture",
        ...     response="Based on requirements, I recommend...",
        ...     context={"scenario": "design", "complexity": 7}
        ... )
        >>> print(f"Quality score: {analysis['response_quality_score']}")
    """
```

#### `assess_collaboration()`

```python
def assess_collaboration(self, interactions: list) -> dict:
    """
    Assess the quality of multi-agent collaboration
    
    Args:
        interactions (list): List of agent interactions in sequence
        
    Returns:
        dict: Collaboration assessment including:
            - synergy_score: How well agents built on each other's work
            - complementarity: Effective use of different specializations
            - consistency: Coherence across agent responses
            - innovation: Creative enhancement through collaboration
            - total_agents_involved: Number of participating agents
            - total_interactions: Total interaction count
            - average_response_time: Mean response time across agents
            
    Example:
        >>> collaboration = engine.assess_collaboration(scenario_interactions)
        >>> print(f"Synergy score: {collaboration['synergy_score']}")
    """
```

---

## 🚀 **EnhancedTestExecutionFramework API**

### Class Definition

```python
class EnhancedTestExecutionFramework:
    """
    Comprehensive testing and performance tracking framework
    
    Provides advanced metrics collection and analysis capabilities
    """
```

### Core Methods

#### `execute_test()`

```python
async def execute_test(self, test_config: dict) -> dict:
    """
    Execute a comprehensive test with performance tracking
    
    Args:
        test_config (dict): Test configuration including:
            - test_type: Type of test to execute
            - scenarios: List of scenarios to test
            - metrics_to_collect: Specific metrics to track
            - performance_thresholds: Expected performance levels
            
    Returns:
        dict: Complete test results with performance metrics
        
    Example:
        >>> config = {
        ...     "test_type": "integration",
        ...     "scenarios": ["design", "optimization", "innovation"],
        ...     "metrics_to_collect": ["tokens", "quality", "collaboration"]
        ... }
        >>> results = await framework.execute_test(config)
    """
```

#### `collect_metrics()`

```python
def collect_metrics(self, interaction_data: dict) -> dict:
    """
    Collect comprehensive metrics from an interaction
    
    Args:
        interaction_data (dict): Raw interaction data
        
    Returns:
        dict: Processed metrics including performance indicators
    """
```

---

## 🔧 **Configuration Constants**

### Agent Profiles

```python
AGENT_PROFILES = {
    "strategic_planner": {
        "name": "Strategic Planning Agent",
        "role": "Senior Strategic Planner and System Architect",
        "model": "deepseek-r1:8b",
        "specialization": [
            "strategic_planning",
            "system_architecture", 
            "project_management",
            "risk_assessment"
        ],
        "personality_traits": {
            "analytical_thinking": 0.9,
            "strategic_vision": 0.9,
            "attention_to_detail": 0.8,
            "communication_clarity": 0.8,
            "risk_awareness": 0.9
        },
        "temperature": 0.2
    },
    
    "code_specialist": {
        "name": "Code Development Specialist", 
        "role": "Expert Software Developer and Code Architect",
        "model": "devstral:latest",
        "specialization": [
            "code_development",
            "debugging",
            "optimization",
            "code_review",
            "testing"
        ],
        "personality_traits": {
            "technical_precision": 0.9,
            "code_quality_focus": 0.9,
            "problem_solving": 0.8,
            "efficiency_oriented": 0.8,
            "documentation_thorough": 0.7
        },
        "temperature": 0.3
    },
    
    "creative_innovator": {
        "name": "Creative Innovation Agent",
        "role": "Creative Problem Solver and Innovation Catalyst", 
        "model": "qwen3:8b",
        "specialization": [
            "creative_problem_solving",
            "innovation",
            "brainstorming",
            "alternative_approaches",
            "user_experience"
        ],
        "personality_traits": {
            "creativity": 0.9,
            "open_mindedness": 0.9,
            "intuition": 0.8,
            "adaptability": 0.8,
            "experimental_approach": 0.8
        },
        "temperature": 0.7
    },
    
    "quality_guardian": {
        "name": "Quality Assurance Guardian",
        "role": "Quality Assurance Lead and System Validator",
        "model": "deepseek-r1:8b", 
        "specialization": [
            "quality_assurance",
            "testing_strategies",
            "validation",
            "metrics_analysis",
            "process_improvement"
        ],
        "personality_traits": {
            "attention_to_detail": 0.9,
            "systematic_approach": 0.9,
            "quality_focus": 0.9,
            "thoroughness": 0.8,
            "critical_thinking": 0.8
        },
        "temperature": 0.2
    }
}
```

### Test Scenarios

```python
TEST_SCENARIOS = [
    {
        "name": "AI System Architecture Design",
        "description": "Design a comprehensive AI system architecture for a multi-modal AI assistant with real-time learning capabilities, focusing on scalability, security, and user experience.",
        "complexity": 8,
        "expected_agents": ["strategic_planner", "code_specialist", "creative_innovator", "quality_guardian"],
        "phases": ["strategic_planning", "technical_implementation", "creative_enhancement", "quality_validation"]
    },
    
    {
        "name": "Code Optimization Challenge", 
        "description": "Optimize a complex distributed system for handling 1M+ concurrent users, including database optimization, caching strategies, and microservices architecture.",
        "complexity": 9,
        "expected_agents": ["strategic_planner", "code_specialist", "creative_innovator", "quality_guardian"],
        "phases": ["strategic_planning", "technical_implementation", "creative_enhancement", "quality_validation"]
    },
    
    {
        "name": "Innovation Lab Project",
        "description": "Develop an innovative solution for sustainable urban planning using AI, IoT sensors, and predictive analytics to optimize city resource allocation.",
        "complexity": 7,
        "expected_agents": ["strategic_planner", "code_specialist", "creative_innovator", "quality_guardian"], 
        "phases": ["strategic_planning", "technical_implementation", "creative_enhancement", "quality_validation"]
    }
]
```

---

## 🔍 **Error Handling**

### Exception Classes

```python
class OllamaConnectionError(Exception):
    """Raised when unable to connect to Ollama server"""
    pass

class ModelNotFoundError(Exception):
    """Raised when specified Ollama model is not available"""
    pass

class AgentNotFoundError(Exception):
    """Raised when requested agent ID doesn't exist"""
    pass

class PromptProcessingError(Exception):
    """Raised when prompt processing fails"""
    pass

class CognitiveAnalysisError(Exception):
    """Raised when cognitive analysis fails"""
    pass

class ScenarioExecutionError(Exception):
    """Raised when scenario execution encounters errors"""
    pass
```

### Error Response Format

```python
ERROR_RESPONSE_FORMAT = {
    "success": False,
    "error": {
        "type": "ErrorClassName",
        "message": "Human-readable error description", 
        "code": "ERROR_CODE",
        "details": {
            "agent_id": "agent_that_failed",
            "model": "model_being_used",
            "timestamp": "2025-06-13T06:35:11.715150+00:00",
            "context": {"additional": "context_data"}
        }
    },
    "retry_suggestion": "Suggested recovery action"
}
```

---

## 📊 **Response Formats**

### Successful Agent Response

```python
AGENT_RESPONSE_FORMAT = {
    "agent_id": "strategic_planner",
    "session_id": "uuid-string",
    "prompt": "Original request prompt",
    "response": "Agent's LLM-generated response",
    "model_used": "deepseek-r1:8b",
    "start_time": "2025-06-13T06:35:11.715150+00:00",
    "end_time": "2025-06-13T06:35:28.909453+00:00", 
    "tokens_used": 726,
    "success": True,
    "error": None,
    "cognitive_analysis": {
        "prompt_complexity": 7.5,
        "response_length": 559,
        "response_quality_score": 1.0,
        "specialization_relevance": 0.85,
        "personality_expression": 0.75,
        "cognitive_load": 0.6,
        "learning_opportunity": {
            "new_concepts": ["concept1", "concept2"],
            "skill_development": ["skill1"],
            "knowledge_gaps": []
        }
    }
}
```

### Scenario Execution Result

```python
SCENARIO_RESULT_FORMAT = {
    "scenario_name": "AI System Architecture Design",
    "task_description": "Design a comprehensive AI system...",
    "success": True,
    "interactions": [
        # List of agent interaction results
    ],
    "analysis": {
        "collaboration_metrics": {
            "total_agents_involved": 4,
            "total_interactions": 4,
            "successful_interactions": 4,
            "total_tokens": 2768,
            "total_duration": 107.1,
            "average_response_time": 26.775,
            "synergy_score": 0.85,
            "complementarity": 0.90,
            "consistency": 0.88,
            "innovation": 0.82
        },
        "performance_metrics": {
            "overall_quality_score": 0.91,
            "efficiency_score": 0.88,
            "collaboration_quality": 0.86
        }
    }
}
```

---

## 🛠️ **Usage Examples**

### Basic Agent Usage

```python
# Initialize a single agent
from real_ollama_agents import RealOllamaAgent, AGENT_PROFILES

agent = RealOllamaAgent(
    agent_id="strategic_planner",
    model="deepseek-r1:8b",
    profile=AGENT_PROFILES["strategic_planner"]
)

# Process a request
context = {
    "scenario": "system_design",
    "complexity": 7,
    "phase": "planning"
}

result = agent.process_request(
    "Design a microservices architecture for an e-commerce platform",
    context
)

print(f"Response: {result['response']}")
print(f"Tokens used: {result['tokens_used']}")
print(f"Quality score: {result['cognitive_analysis']['response_quality_score']}")
```

### Multi-Agent Orchestration

```python
# Initialize orchestrator
from real_ollama_agents import RealMultiAgentOrchestrator

orchestrator = RealMultiAgentOrchestrator()

# Execute a complex scenario
scenario = {
    "name": "System Optimization",
    "description": "Optimize system performance for high-load scenarios",
    "complexity": 8
}

result = await orchestrator.execute_scenario(scenario)

print(f"Scenario success: {result['success']}")
print(f"Total agents involved: {len(result['interactions'])}")
print(f"Total tokens: {result['collaboration_metrics']['total_tokens']}")

# Access individual interactions
for interaction in result['interactions']:
    agent_name = interaction['agent_id'].replace('_', ' ').title()
    print(f"{agent_name}: {interaction['tokens_used']} tokens")
```

### Integration Testing

```python
# Run comprehensive integration test
orchestrator = RealMultiAgentOrchestrator()

# Execute full integration test
results = await orchestrator.execute_integration_test()

# Access summary metrics
summary = results['integration_summary']
print(f"Test type: {summary['test_type']}")
print(f"Total scenarios: {summary['total_scenarios']}")
print(f"Success rate: {summary['integration_success_rate'] * 100}%")
print(f"Total tokens: {summary['total_tokens_processed']}")

# Access agent performance
for agent_id, performance in results['agent_performance'].items():
    profile = performance['profile']
    metrics = performance.get('metrics', {})
    
    print(f"\nAgent: {profile['name']}")
    print(f"Model: {profile['model']}")
    print(f"Interactions: {metrics.get('total_interactions', 0)}")
    print(f"Avg quality: {metrics.get('average_quality_score', 0):.3f}")
```

### Error Handling

```python
from real_ollama_agents import (
    RealOllamaAgent, 
    OllamaConnectionError,
    ModelNotFoundError
)

try:
    agent = RealOllamaAgent("test_agent", "nonexistent-model", {})
    result = agent.process_request("Test prompt")
    
except OllamaConnectionError as e:
    print(f"Connection error: {e}")
    # Implement retry logic or fallback
    
except ModelNotFoundError as e:
    print(f"Model error: {e}")
    # Switch to alternative model
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # General error handling
```

---

## 🔗 **Integration Points**

### Ollama Server Integration

```python
# Check Ollama server status
import ollama

try:
    client = ollama.Client()
    models = client.list()
    print("Available models:")
    for model in models['models']:
        print(f"  - {model['name']}")
except Exception as e:
    print(f"Ollama server not available: {e}")
```

### External System Integration

```python
# Example: Integrating with external monitoring
class ExternalMonitoringIntegration:
    def __init__(self, monitoring_endpoint):
        self.endpoint = monitoring_endpoint
    
    def send_metrics(self, interaction_result):
        """Send interaction metrics to external monitoring system"""
        metrics = {
            "agent_id": interaction_result['agent_id'],
            "tokens_used": interaction_result['tokens_used'],
            "response_time": interaction_result['duration'],
            "quality_score": interaction_result['cognitive_analysis']['response_quality_score']
        }
        # Send to external system
        requests.post(self.endpoint, json=metrics)
```

---

*This API reference provides comprehensive documentation for integrating with and extending the Real Ollama LLM Multi-Agent System.*

**API Version**: 1.0.0  
**Last Updated**: June 13, 2025  
**Compatibility**: Python 3.8+ with Ollama server
