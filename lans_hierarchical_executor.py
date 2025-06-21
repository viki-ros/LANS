#!/usr/bin/env python3
"""
LANS Hierarchical Multi-Model Execution System
- Large parameter model (devstral) as high-level planner and task allocator
- Multiple execution models working in parallel for optimal performance
- Intelligent task distribution and result aggregation
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
from concurrent.futures import as_completed

# Add LANS to path
sys.path.append('.')

from agent_core.core.config import LANSConfig
from agent_core.llm.ollama_client import OllamaClient
from global_mcp_server.core.agentos_kernel import AgentOSKernel

class ModelRole(Enum):
    """Model roles in the hierarchical system"""
    PLANNER = "planner"           # High-level planning and task allocation
    REASONING = "reasoning"       # Complex reasoning and analysis
    EXECUTION = "execution"       # Fast task execution
    SPECIALIST = "specialist"     # Specialized tasks (code, creative, etc.)

@dataclass
class ModelCapabilities:
    """Model capabilities and performance metrics"""
    model_name: str
    role: ModelRole
    max_parallel_tasks: int = 1
    avg_response_time: float = 10.0
    reliability_score: float = 5.0
    specializations: List[str] = field(default_factory=list)
    connection_stable: bool = True

@dataclass
class Task:
    """Task to be executed by the system"""
    task_id: str
    operation: str
    content: str
    priority: int = 5  # 1-10, 10 = highest
    complexity: int = 5  # 1-10, 10 = most complex
    assigned_model: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    result: Optional[Any] = None
    execution_time: Optional[float] = None
    status: str = "pending"  # pending, executing, completed, failed

class LANSHierarchicalExecutor:
    """Hierarchical multi-model execution system with intelligent task allocation"""
    
    def __init__(self):
        self.config = LANSConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize model hierarchy based on available models
        self.model_hierarchy = self._initialize_model_hierarchy()
        self.model_clients = {}
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.execution_stats = {}
        
        # Execution control
        self.max_concurrent_tasks = 6  # Total system-wide concurrency
        self.running_tasks = {}
        
    def _initialize_model_hierarchy(self) -> Dict[str, ModelCapabilities]:
        """Initialize the model hierarchy based on available models"""
        return {
            # High-level planner (largest model)
            "devstral:latest": ModelCapabilities(
                model_name="devstral:latest",
                role=ModelRole.PLANNER,
                max_parallel_tasks=2,  # Conservative for large model
                avg_response_time=25.0,
                reliability_score=8.0,
                specializations=["planning", "task_allocation", "strategy", "architecture"]
            ),
            
            # Reasoning model
            "qwen3:8b": ModelCapabilities(
                model_name="qwen3:8b", 
                role=ModelRole.REASONING,
                max_parallel_tasks=2,
                avg_response_time=30.0,
                reliability_score=7.0,
                specializations=["analysis", "complex_reasoning", "problem_solving"],
                connection_stable=True  # Will test dynamically
            ),
            
            # Primary execution models (parallel workers)
            "deepseek-coder:6.7b": ModelCapabilities(
                model_name="deepseek-coder:6.7b",
                role=ModelRole.EXECUTION,
                max_parallel_tasks=3,  # High concurrency for reliable model
                avg_response_time=8.0,
                reliability_score=10.0,
                specializations=["code", "technical", "fast_execution"]
            ),
            
            "qwen2.5:latest": ModelCapabilities(
                model_name="qwen2.5:latest",
                role=ModelRole.EXECUTION,
                max_parallel_tasks=2,
                avg_response_time=12.0,
                reliability_score=8.0,
                specializations=["general", "queries", "analysis"]
            ),
            
            # Specialist model
            "phi4-mini:latest": ModelCapabilities(
                model_name="phi4-mini:latest",
                role=ModelRole.SPECIALIST,
                max_parallel_tasks=3,  # Fast small model
                avg_response_time=5.0,
                reliability_score=9.0,
                specializations=["quick_tasks", "simple_queries", "lightweight"]
            )
        }
    
    async def initialize(self):
        """Initialize all model clients and test connections"""
        print("🚀 Initializing LANS Hierarchical Multi-Model System...")
        print("=" * 60)
        
        for model_name, capabilities in self.model_hierarchy.items():
            print(f"\\n📡 Testing {model_name} ({capabilities.role.value})...")
            
            try:
                self.config.model = model_name
                client = OllamaClient(self.config)
                
                # Test connection with simple prompt
                start_time = time.time()
                response = await client.generate_response("Test connection. Respond with 'OK'.")
                connection_time = time.time() - start_time
                
                if response and len(response) > 0:
                    print(f"   ✅ Connected ({connection_time:.2f}s): {response[:50]}...")
                    self.model_clients[model_name] = client
                    self.execution_stats[model_name] = {
                        'tasks_completed': 0,
                        'total_time': 0.0,
                        'errors': 0,
                        'avg_response_time': connection_time
                    }
                else:
                    print(f"   ❌ Failed: Empty response")
                    capabilities.connection_stable = False
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                capabilities.connection_stable = False
        
        # Show system status
        available_models = [name for name, cap in self.model_hierarchy.items() if cap.connection_stable]
        total_capacity = sum(cap.max_parallel_tasks for cap in self.model_hierarchy.values() if cap.connection_stable)
        
        print(f"\\n🎯 System Status:")
        print(f"   Available Models: {len(available_models)}/{len(self.model_hierarchy)}")
        print(f"   Total Parallel Capacity: {total_capacity} concurrent tasks")
        print(f"   Planner: {'✅' if self._get_planner_model() else '❌'}")
        print(f"   Execution Workers: {len(self._get_execution_models())}")
        
    def _get_planner_model(self) -> Optional[str]:
        """Get the high-level planner model"""
        for model_name, cap in self.model_hierarchy.items():
            if cap.role == ModelRole.PLANNER and cap.connection_stable:
                return model_name
        return None
    
    def _get_execution_models(self) -> List[str]:
        """Get available execution models"""
        return [
            model_name for model_name, cap in self.model_hierarchy.items()
            if cap.role == ModelRole.EXECUTION and cap.connection_stable
        ]
    
    def _get_reasoning_models(self) -> List[str]:
        """Get available reasoning models"""
        return [
            model_name for model_name, cap in self.model_hierarchy.items()
            if cap.role == ModelRole.REASONING and cap.connection_stable
        ]
    
    async def plan_and_allocate_tasks(self, user_request: str) -> List[Task]:
        """Use planner model to break down request into tasks and allocate them"""
        print(f"\\n🧠 High-Level Planning: {user_request[:100]}...")
        
        planner_model = self._get_planner_model()
        if not planner_model:
            raise Exception("No planner model available")
        
        client = self.model_clients[planner_model]
        
        # Get available execution capacity
        execution_models = self._get_execution_models()
        reasoning_models = self._get_reasoning_models()
        
        planning_prompt = f"""
        You are a high-level AI task planner and allocator. Break down this user request into specific, executable tasks.
        
        User Request: {user_request}
        
        Available Execution Models: {execution_models}
        Available Reasoning Models: {reasoning_models}
        
        Create a task breakdown with:
        1. Task decomposition (break complex request into smaller tasks)
        2. Priority assignment (1-10, 10=highest)
        3. Complexity assessment (1-10, 10=most complex)
        4. Model allocation recommendations
        
        Respond with a JSON array of tasks:
        [
          {{
            "task_id": "task_1",
            "operation": "EXECUTE|QUERY|ANALYZE|PLAN",
            "content": "specific task description",
            "priority": 8,
            "complexity": 6,
            "recommended_model": "model_name",
            "reasoning": "why this model for this task"
          }}
        ]
        
        Focus on parallel execution where possible. Use execution models for straightforward tasks, reasoning models for complex analysis.
        """
        
        try:
            response = await client.generate_response(planning_prompt)
            
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                task_data = json.loads(response[json_start:json_end])
                
                # Convert to Task objects
                tasks = []
                for i, task_info in enumerate(task_data):
                    task = Task(
                        task_id=task_info.get('task_id', f'task_{i+1}'),
                        operation=task_info.get('operation', 'EXECUTE'),
                        content=task_info.get('content', ''),
                        priority=task_info.get('priority', 5),
                        complexity=task_info.get('complexity', 5),
                        assigned_model=task_info.get('recommended_model')
                    )
                    tasks.append(task)
                
                print(f"   ✅ Generated {len(tasks)} tasks for parallel execution")
                for task in tasks:
                    print(f"      {task.task_id}: {task.content[:60]}... → {task.assigned_model}")
                
                return tasks
            else:
                raise Exception("Could not parse task breakdown JSON")
                
        except Exception as e:
            print(f"   ❌ Planning failed: {e}")
            # Fallback: create simple task
            return [Task(
                task_id="fallback_task",
                operation="EXECUTE",
                content=user_request,
                priority=5,
                complexity=5,
                assigned_model=self._get_execution_models()[0] if self._get_execution_models() else None
            )]
    
    async def execute_tasks_parallel(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks in parallel using multiple models"""
        print(f"\\n⚡ Executing {len(tasks)} tasks in parallel...")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        # Execute all tasks concurrently
        async def execute_single_task(task: Task) -> Tuple[str, Any]:
            async with semaphore:
                return await self._execute_task(task)
        
        # Start all tasks
        start_time = time.time()
        task_futures = [execute_single_task(task) for task in tasks]
        
        # Wait for completion
        results = {}
        completed = 0
        
        for future in asyncio.as_completed(task_futures):
            try:
                task_id, result = await future
                results[task_id] = result
                completed += 1
                print(f"   ✅ Task {completed}/{len(tasks)} completed: {task_id}")
            except Exception as e:
                print(f"   ❌ Task failed: {e}")
        
        total_time = time.time() - start_time
        
        print(f"\\n📊 Parallel Execution Summary:")
        print(f"   Total Tasks: {len(tasks)}")
        print(f"   Completed: {len(results)}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Average Time per Task: {total_time/len(tasks):.2f}s")
        
        return {
            'results': results,
            'execution_time': total_time,
            'tasks_completed': len(results),
            'tasks_total': len(tasks)
        }
    
    async def _execute_task(self, task: Task) -> Tuple[str, Any]:
        """Execute a single task"""
        task.status = "executing"
        start_time = time.time()
        
        # Select best available model for this task
        model_name = self._select_best_model_for_task(task)
        if not model_name:
            raise Exception(f"No available model for task {task.task_id}")
        
        client = self.model_clients[model_name]
        
        try:
            # Execute based on operation type
            if task.operation == "ANALYZE":
                system_prompt = "You are an expert analyst. Provide detailed analysis and insights."
            elif task.operation == "PLAN":
                system_prompt = "You are a strategic planner. Create detailed, actionable plans."
            elif task.operation == "QUERY":
                system_prompt = "You are a knowledgeable assistant. Provide accurate, concise answers."
            else:  # EXECUTE
                system_prompt = "You are a task executor. Complete the requested task efficiently."
            
            response = await client.generate_response(task.content, system_prompt)
            
            # Update statistics
            execution_time = time.time() - start_time
            task.execution_time = execution_time
            task.result = response
            task.status = "completed"
            
            self.execution_stats[model_name]['tasks_completed'] += 1
            self.execution_stats[model_name]['total_time'] += execution_time
            
            return task.task_id, {
                'result': response,
                'execution_time': execution_time,
                'model_used': model_name,
                'status': 'success'
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            task.status = "failed"
            self.execution_stats[model_name]['errors'] += 1
            
            return task.task_id, {
                'error': str(e),
                'execution_time': execution_time,
                'model_used': model_name,
                'status': 'failed'
            }
    
    def _select_best_model_for_task(self, task: Task) -> Optional[str]:
        """Select the best available model for a specific task"""
        
        # If task has assigned model and it's available, use it
        if task.assigned_model and task.assigned_model in self.model_clients:
            cap = self.model_hierarchy[task.assigned_model]
            if cap.connection_stable:
                return task.assigned_model
        
        # Otherwise, select based on operation and complexity
        if task.operation in ["ANALYZE", "PLAN"] and task.complexity >= 7:
            # Use reasoning model for complex analysis/planning
            reasoning_models = self._get_reasoning_models()
            if reasoning_models:
                return reasoning_models[0]
        
        # Use execution models for other tasks
        execution_models = self._get_execution_models()
        if execution_models:
            # Select least loaded execution model
            return min(execution_models, 
                      key=lambda m: self.execution_stats[m]['tasks_completed'])
        
        # Fallback to any available model
        available = [name for name, cap in self.model_hierarchy.items() if cap.connection_stable]
        return available[0] if available else None
    
    async def aggregate_results(self, results: Dict[str, Any], original_request: str) -> str:
        """Use planner model to aggregate and synthesize results"""
        print("\\n🔗 Aggregating results with planner model...")
        
        planner_model = self._get_planner_model()
        if not planner_model:
            return self._simple_aggregation(results)
        
        client = self.model_clients[planner_model]
        
        # Prepare results summary for aggregation
        results_summary = []
        for task_id, result in results['results'].items():
            if result['status'] == 'success':
                results_summary.append({
                    'task': task_id,
                    'result': result['result'][:500] + '...' if len(result['result']) > 500 else result['result'],
                    'model': result['model_used']
                })
        
        aggregation_prompt = f"""
        You are a high-level AI coordinator. Synthesize these parallel task results into a comprehensive response.
        
        Original Request: {original_request}
        
        Task Results:
        {json.dumps(results_summary, indent=2)}
        
        Provide a coherent, comprehensive response that:
        1. Addresses the original request completely
        2. Integrates insights from all successful tasks
        3. Maintains logical flow and coherence
        4. Highlights key findings or recommendations
        
        Focus on synthesis rather than just concatenation.
        """
        
        try:
            aggregated_response = await client.generate_response(aggregation_prompt)
            print("   ✅ Results successfully aggregated by planner")
            return aggregated_response
        except Exception as e:
            print(f"   ⚠️  Aggregation failed, using simple combination: {e}")
            return self._simple_aggregation(results)
    
    def _simple_aggregation(self, results: Dict[str, Any]) -> str:
        """Simple fallback aggregation"""
        successful_results = []
        for task_id, result in results['results'].items():
            if result['status'] == 'success':
                successful_results.append(f"Task {task_id}: {result['result']}")
        
        return "\\n\\n".join(successful_results)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'models': {},
            'system_capacity': 0,
            'total_tasks_completed': 0,
            'average_response_time': 0.0
        }
        
        total_time = 0.0
        total_tasks = 0
        
        for model_name, model_stats in self.execution_stats.items():
            cap = self.model_hierarchy[model_name]
            
            avg_time = (model_stats['total_time'] / max(model_stats['tasks_completed'], 1))
            
            stats['models'][model_name] = {
                'role': cap.role.value,
                'tasks_completed': model_stats['tasks_completed'],
                'total_time': model_stats['total_time'],
                'errors': model_stats['errors'],
                'average_response_time': avg_time,
                'max_parallel': cap.max_parallel_tasks,
                'connection_stable': cap.connection_stable
            }
            
            if cap.connection_stable:
                stats['system_capacity'] += cap.max_parallel_tasks
                
            total_time += model_stats['total_time']
            total_tasks += model_stats['tasks_completed']
        
        stats['total_tasks_completed'] = total_tasks
        stats['average_response_time'] = total_time / max(total_tasks, 1)
        
        return stats
    
    async def close(self):
        """Close all model clients"""
        for client in self.model_clients.values():
            try:
                await client.close()
            except:
                pass

async def demo_hierarchical_execution():
    """Demonstrate the hierarchical multi-model execution system"""
    
    executor = LANSHierarchicalExecutor()
    
    try:
        # Initialize system
        await executor.initialize()
        
        # Test cases
        test_requests = [
            "Create a comprehensive plan for building a web application with user authentication, database design, and deployment strategy",
            "Analyze the pros and cons of microservices vs monolithic architecture, provide code examples, and recommend best practices",
            "Design a machine learning pipeline for text classification, including data preprocessing, model selection, and evaluation metrics"
        ]
        
        print("\\n" + "=" * 60)
        print("🎯 HIERARCHICAL MULTI-MODEL EXECUTION DEMO")
        print("=" * 60)
        
        for i, request in enumerate(test_requests, 1):
            print(f"\\n🚀 Test Case {i}: {request[:80]}...")
            
            # Phase 1: Planning and task allocation
            tasks = await executor.plan_and_allocate_tasks(request)
            
            # Phase 2: Parallel execution
            results = await executor.execute_tasks_parallel(tasks)
            
            # Phase 3: Result aggregation
            final_response = await executor.aggregate_results(results, request)
            
            print(f"\\n📋 Final Response ({len(final_response)} chars):")
            print(f"   {final_response[:200]}...")
            
            # Show execution stats
            if i == 1:  # Show detailed stats for first test
                stats = executor.get_system_stats()
                print(f"\\n📊 System Performance:")
                for model, model_stats in stats['models'].items():
                    if model_stats['tasks_completed'] > 0:
                        print(f"   {model}: {model_stats['tasks_completed']} tasks, {model_stats['average_response_time']:.2f}s avg")
        
        # Final system summary
        final_stats = executor.get_system_stats()
        print(f"\\n🏆 HIERARCHICAL EXECUTION COMPLETE!")
        print(f"   Total System Capacity: {final_stats['system_capacity']} parallel tasks")
        print(f"   Total Tasks Completed: {final_stats['total_tasks_completed']}")
        print(f"   Average Response Time: {final_stats['average_response_time']:.2f}s")
        
    finally:
        await executor.close()

if __name__ == "__main__":
    asyncio.run(demo_hierarchical_execution())
