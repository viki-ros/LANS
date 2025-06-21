#!/usr/bin/env python3
"""
LANS Intelligent Model Router
Routes AIL operations to the most suitable LLM based on task complexity and type
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging

class ModelCapability(Enum):
    """Model capability types"""
    RELIABLE = "reliable"          # Fast, consistent, production-ready
    REASONING = "reasoning"        # Deep thinking, explicit reasoning
    CREATIVE = "creative"          # Creative tasks, brainstorming
    TECHNICAL = "technical"        # Code generation, technical tasks

class TaskComplexity(Enum):
    """Task complexity levels"""
    LOW = 1      # Simple queries, basic operations
    MEDIUM = 2   # Standard tasks, moderate reasoning
    HIGH = 3     # Complex problem solving, multi-step reasoning

class LLMModelRouter:
    """Intelligent router for selecting optimal LLM model based on task requirements"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Model capabilities based on updated analysis with new models
        self.model_profiles = {
            "deepseek-coder:6.7b": {
                "capabilities": [ModelCapability.RELIABLE, ModelCapability.TECHNICAL],
                "reliability_score": 10,
                "reasoning_depth": 3,
                "speed_score": 9,
                "best_for": ["EXECUTE", "QUERY", "code_generation", "production"],
                "connection_stability": 100,  # percentage
                "average_response_time": 8.0,  # seconds
                "role": "task_executor"
            },
            "qwen2.5:latest": {
                "capabilities": [ModelCapability.REASONING, ModelCapability.CREATIVE],
                "reliability_score": 8,  # To be tested
                "reasoning_depth": 7,
                "speed_score": 6,
                "best_for": ["PLAN", "ANALYZE", "complex_reasoning", "creative_tasks"],
                "connection_stability": 90,   # To be verified
                "average_response_time": 20.0,  # Estimated
                "shows_thinking": True,
                "role": "primary_reasoner"
            },
            "phi4-mini:latest": {
                "capabilities": [ModelCapability.REASONING, ModelCapability.RELIABLE],
                "reliability_score": 7,  # To be tested
                "reasoning_depth": 5,
                "speed_score": 8,
                "best_for": ["quick_reasoning", "backup_tasks"],
                "connection_stability": 85,   # To be verified
                "average_response_time": 12.0,  # Estimated
                "role": "backup_reasoner"
            },
            "devstral:latest": {
                "capabilities": [ModelCapability.REASONING, ModelCapability.TECHNICAL],
                "reliability_score": 6,  # Previous issues noted
                "reasoning_depth": 6,
                "speed_score": 4,
                "best_for": ["complex_technical_reasoning"],
                "connection_stability": 70,   # To be verified
                "average_response_time": 25.0,
                "role": "fallback_reasoner"
            },
            # Legacy models - keeping for reference but not primary choices
            "qwen3:8b": {
                "capabilities": [ModelCapability.REASONING],
                "reliability_score": 4,
                "reasoning_depth": 6,
                "speed_score": 3,
                "best_for": [],
                "connection_stability": 30,
                "status": "legacy",
                "role": "deprecated"
            },
            "deepseek-r1:8b": {
                "capabilities": [ModelCapability.REASONING],
                "reliability_score": 5,
                "reasoning_depth": 8,
                "speed_score": 3,
                "best_for": [],
                "connection_stability": 50,
                "status": "legacy",
                "role": "deprecated"
            }
        }
        
        # Updated model assignments
        self.task_executor = "deepseek-coder:6.7b"  # Always use for execution
        self.primary_reasoner = "qwen2.5:latest"    # Primary reasoning model
        self.backup_reasoner = "phi4-mini:latest"   # Backup reasoning
        self.fallback_reasoner = "devstral:latest"  # Last resort reasoning
        self.default_model = "deepseek-coder:6.7b"  # Safe default
        
    def select_model_for_ail_operation(self, operation: str, context: Dict[str, Any] = None) -> str:
        """Select the best model for an AIL operation"""
        context = context or {}
        
        # Determine task complexity
        complexity = self._assess_task_complexity(operation, context)
        
        # AIL operation-specific routing
        if operation == "PLAN":
            return self._select_for_planning(complexity, context)
        elif operation == "ANALYZE":
            return self._select_for_analysis(complexity, context)
        elif operation == "EXECUTE":
            return self._select_for_execution(complexity, context)
        elif operation == "QUERY":
            return self._select_for_query(complexity, context)
        elif operation == "COMMUNICATE":
            return self._select_for_communication(complexity, context)
        else:
            # Unknown operation - use reliable default
            return self.default_model
    
    def _assess_task_complexity(self, operation: str, context: Dict[str, Any]) -> TaskComplexity:
        """Assess the complexity of a task"""
        
        # Check for complexity indicators in context
        if context.get("complexity") == "high":
            return TaskComplexity.HIGH
        elif context.get("complexity") == "low":
            return TaskComplexity.LOW
        
        # Operation-based complexity assessment
        high_complexity_ops = ["PLAN", "ANALYZE"]
        medium_complexity_ops = ["COMMUNICATE", "QUERY"]
        low_complexity_ops = ["EXECUTE"]
        
        if operation in high_complexity_ops:
            return TaskComplexity.HIGH
        elif operation in medium_complexity_ops:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.LOW
    
    def _select_for_planning(self, complexity: TaskComplexity, context: Dict[str, Any]) -> str:
        """Select model for PLAN operations"""
        if complexity == TaskComplexity.HIGH and context.get("allow_slow_reasoning", False):
            # Use reasoning model for complex planning if time permits
            if self._is_model_available("deepseek-r1:8b"):
                self.logger.info("Selected deepseek-r1:8b for complex planning (with reasoning)")
                return "deepseek-r1:8b"
        
        # Default to reliable model for most planning tasks
        self.logger.info("Selected deepseek-coder:6.7b for planning (reliable)")
        return "deepseek-coder:6.7b"
    
    def _select_for_analysis(self, complexity: TaskComplexity, context: Dict[str, Any]) -> str:
        """Select model for ANALYZE operations"""
        if complexity == TaskComplexity.HIGH and context.get("show_reasoning", False):
            # Use reasoning model for complex analysis if reasoning transparency is needed
            if self._is_model_available("deepseek-r1:8b"):
                self.logger.info("Selected deepseek-r1:8b for complex analysis (with thinking)")
                return "deepseek-r1:8b"
        
        # Default to reliable model for most analysis
        self.logger.info("Selected deepseek-coder:6.7b for analysis (reliable)")
        return "deepseek-coder:6.7b"
    
    def _select_for_execution(self, complexity: TaskComplexity, context: Dict[str, Any]) -> str:
        """Select model for EXECUTE operations"""
        # Always use reliable model for execution - speed and reliability are key
        self.logger.info("Selected deepseek-coder:6.7b for execution (speed + reliability)")
        return "deepseek-coder:6.7b"
    
    def _select_for_query(self, complexity: TaskComplexity, context: Dict[str, Any]) -> str:
        """Select model for QUERY operations"""
        # Use reliable model for most queries - speed matters for queries
        self.logger.info("Selected deepseek-coder:6.7b for query (speed)")
        return "deepseek-coder:6.7b"
    
    def _select_for_communication(self, complexity: TaskComplexity, context: Dict[str, Any]) -> str:
        """Select model for COMMUNICATE operations"""
        # Use reliable model for communication - clarity and speed
        self.logger.info("Selected deepseek-coder:6.7b for communication (clarity)")
        return "deepseek-coder:6.7b"
    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if a model is available and stable"""
        if model_name not in self.model_profiles:
            return False
        
        profile = self.model_profiles[model_name]
        
        # Check if model is marked as unstable
        if profile.get("status") == "unstable":
            self.logger.warning(f"Model {model_name} marked as unstable")
            return False
        
        # Check connection stability threshold
        if profile.get("connection_stability", 0) < 50:
            self.logger.warning(f"Model {model_name} has low connection stability")
            return False
        
        return True
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        return self.model_profiles.get(model_name, {})
    
    def get_best_models_for_capability(self, capability: ModelCapability) -> List[str]:
        """Get models best suited for a specific capability"""
        suitable_models = []
        
        for model_name, profile in self.model_profiles.items():
            if capability in profile.get("capabilities", []):
                if self._is_model_available(model_name):
                    suitable_models.append((
                        model_name, 
                        profile.get("reliability_score", 0)
                    ))
        
        # Sort by reliability score
        suitable_models.sort(key=lambda x: x[1], reverse=True)
        return [model[0] for model in suitable_models]
    
    def recommend_model_for_use_case(self, use_case: str) -> str:
        """Recommend a model for a specific use case"""
        use_case_mapping = {
            "production_api": "deepseek-coder:6.7b",
            "educational_reasoning": "deepseek-r1:8b",
            "code_generation": "deepseek-coder:6.7b", 
            "complex_analysis": "deepseek-r1:8b",
            "quick_queries": "deepseek-coder:6.7b",
            "debugging": "deepseek-r1:8b",
            "real_time": "deepseek-coder:6.7b"
        }
        
        recommended = use_case_mapping.get(use_case, self.default_model)
        
        # Verify the recommended model is available
        if not self._is_model_available(recommended):
            self.logger.warning(f"Recommended model {recommended} not available, using default")
            return self.default_model
        
        return recommended
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics and model health"""
        stats = {
            "available_models": [],
            "unstable_models": [],
            "default_model": self.default_model,
            "model_health": {}
        }
        
        for model_name, profile in self.model_profiles.items():
            health_score = (
                profile.get("reliability_score", 0) * 0.4 +
                profile.get("connection_stability", 0) / 10 * 0.6
            )
            
            stats["model_health"][model_name] = {
                "health_score": round(health_score, 1),
                "reliability": profile.get("reliability_score", 0),
                "stability": profile.get("connection_stability", 0),
                "reasoning_depth": profile.get("reasoning_depth", 0),
                "speed_score": profile.get("speed_score", 0)
            }
            
            if self._is_model_available(model_name):
                stats["available_models"].append(model_name)
            else:
                stats["unstable_models"].append(model_name)
        
        return stats

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    router = LLMModelRouter()
    
    print("🧠 LANS Intelligent Model Router Demo")
    print("=" * 50)
    
    # Test different AIL operations
    test_cases = [
        ("PLAN", {"complexity": "high", "allow_slow_reasoning": True}),
        ("EXECUTE", {"complexity": "low"}),
        ("ANALYZE", {"complexity": "high", "show_reasoning": True}),
        ("QUERY", {"complexity": "medium"}),
        ("COMMUNICATE", {"complexity": "low"})
    ]
    
    print("\\nAIL Operation Routing:")
    for operation, context in test_cases:
        selected = router.select_model_for_ail_operation(operation, context)
        print(f"  {operation}: {selected}")
    
    print("\\nUse Case Recommendations:")
    use_cases = ["production_api", "educational_reasoning", "code_generation", "real_time"]
    for use_case in use_cases:
        recommended = router.recommend_model_for_use_case(use_case)
        print(f"  {use_case}: {recommended}")
    
    print("\\nModel Health Summary:")
    stats = router.get_routing_stats()
    print(f"  Available: {len(stats['available_models'])} models")
    print(f"  Unstable: {len(stats['unstable_models'])} models")
    print(f"  Default: {stats['default_model']}")
    
    print("\\n✅ Model Router Ready for LANS Integration!")
