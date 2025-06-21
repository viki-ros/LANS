#!/usr/bin/env python3
"""
LANS Optimized Multi-Model Parallel Execution System
- Uses qwen3:8b as reasoning planner (more reliable than devstral)
- Multiple execution models working in parallel 
- Improved timeout handling and fallback strategies
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys

# Add LANS to path
sys.path.append('.')

from agent_core.core.config import LANSConfig
from agent_core.llm.ollama_client import OllamaClient

class ModelRole(Enum):
    """Model roles in the parallel system"""
    PLANNER = "planner"           # Task planning and allocation
    EXECUTION = "execution"       # Fast parallel execution
    SPECIALIST = "specialist"     # Specialized lightweight tasks

@dataclass
class ExecutionModel:
    """Execution model configuration"""
    name: str
    role: ModelRole
    max_concurrent: int
    avg_time: float
    reliability: float
    specialties: List[str] = field(default_factory=list)
    is_available: bool = True

@dataclass
class ExecutionTask:
    """Task for parallel execution"""
    task_id: str
    content: str
    task_type: str  # 'analysis', 'code', 'planning', 'query'
    priority: int = 5
    assigned_model: Optional[str] = None
    result: Optional[str] = None
    execution_time: Optional[float] = None
    status: str = "pending"

class LANSParallelExecutor:
    """Optimized parallel execution system with intelligent load balancing"""
    
    def __init__(self):
        self.config = LANSConfig()
        self.logger = logging.getLogger(__name__)
        
        # Model configuration based on test results
        self.models = {
            # Reasoning/Planning model (reliable, shows thinking)
            "qwen3:8b": ExecutionModel(
                name="qwen3:8b",
                role=ModelRole.PLANNER,
                max_concurrent=2,
                avg_time=25.0,
                reliability=8.0,
                specialties=["planning", "complex_analysis", "reasoning"]
            ),
            
            # Primary execution models (parallel workers)
            "deepseek-coder:6.7b": ExecutionModel(
                name="deepseek-coder:6.7b", 
                role=ModelRole.EXECUTION,
                max_concurrent=4,  # High concurrency for reliable model
                avg_time=10.0,
                reliability=10.0,
                specialties=["code", "technical", "implementation"]
            ),
            
            "qwen2.5:latest": ExecutionModel(
                name="qwen2.5:latest",
                role=ModelRole.EXECUTION, 
                max_concurrent=3,
                avg_time=8.0,
                reliability=9.0,
                specialties=["analysis", "queries", "general"]
            ),
            
            # Specialist for quick tasks
            "phi4-mini:latest": ExecutionModel(
                name="phi4-mini:latest",
                role=ModelRole.SPECIALIST,
                max_concurrent=4,  # Fast lightweight model
                avg_time=5.0,
                reliability=9.0,
                specialties=["quick_tasks", "simple_queries", "summaries"]
            )
        }
        
        self.clients = {}
        self.stats = {}
        self.task_queue = asyncio.Queue()
        self.max_total_concurrent = 10  # System-wide limit
    
    async def initialize(self):
        """Initialize and test all models"""
        print("🚀 Initializing LANS Parallel Execution System")
        print("=" * 55)
        
        working_models = 0
        total_capacity = 0
        
        for model_name, model_config in self.models.items():
            print(f"\\n📡 Testing {model_name} ({model_config.role.value})...")
            
            try:
                self.config.model = model_name
                client = OllamaClient(self.config)
                
                # Quick connection test with timeout
                start_time = time.time()
                response = await asyncio.wait_for(
                    client.generate_response("Test. Reply 'OK'.", max_retries=1),
                    timeout=15.0  # 15 second timeout
                )
                connection_time = time.time() - start_time
                
                if response and 'ok' in response.lower():
                    print(f"   ✅ Ready ({connection_time:.2f}s): {model_config.specialties}")
                    self.clients[model_name] = client
                    self.stats[model_name] = {
                        'tasks_completed': 0,
                        'total_time': 0.0,
                        'errors': 0
                    }
                    working_models += 1
                    total_capacity += model_config.max_concurrent
                else:
                    print(f"   ⚠️  Connected but unexpected response: {response[:50]}")
                    self.clients[model_name] = client
                    self.stats[model_name] = {'tasks_completed': 0, 'total_time': 0.0, 'errors': 0}
                    working_models += 1
                    total_capacity += model_config.max_concurrent
                    
            except asyncio.TimeoutError:
                print(f"   ❌ Timeout - model too slow for real-time use")
                model_config.is_available = False
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                model_config.is_available = False
        
        print(f"\\n🎯 System Ready:")
        print(f"   Working Models: {working_models}/{len(self.models)}")
        print(f"   Total Capacity: {total_capacity} concurrent tasks")
        print(f"   Planner Available: {'✅' if self._get_planner() else '❌'}")
        print(f"   Execution Workers: {len(self._get_execution_models())}")
        
        return working_models > 0
    
    def _get_planner(self) -> Optional[str]:
        """Get the planning model"""
        for name, config in self.models.items():
            if config.role == ModelRole.PLANNER and config.is_available and name in self.clients:
                return name
        return None
    
    def _get_execution_models(self) -> List[str]:
        """Get available execution models"""
        return [
            name for name, config in self.models.items()
            if config.role == ModelRole.EXECUTION and config.is_available and name in self.clients
        ]
    
    async def create_execution_plan(self, user_request: str) -> List[ExecutionTask]:
        """Create a simple, reliable execution plan"""
        print(f"\\n🧠 Creating execution plan for: {user_request[:80]}...")
        
        planner = self._get_planner()
        
        if planner and planner in self.clients:
            try:
                # Try intelligent planning with timeout
                return await asyncio.wait_for(
                    self._intelligent_planning(user_request, planner),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print("   ⚠️  Intelligent planning timed out, using fallback")
            except Exception as e:
                print(f"   ⚠️  Planning failed: {e}, using fallback")
        
        # Fallback: simple task decomposition
        return self._create_simple_plan(user_request)
    
    async def _intelligent_planning(self, user_request: str, planner: str) -> List[ExecutionTask]:
        """Use planner model for intelligent task breakdown"""
        client = self.clients[planner]
        execution_models = self._get_execution_models()
        
        planning_prompt = f"""
        Break this request into 2-4 parallel tasks that can be executed simultaneously:
        
        Request: {user_request}
        
        Available models: {execution_models}
        
        Create tasks as JSON:
        [
          {{"task_id": "analysis", "content": "analyze X", "task_type": "analysis"}},
          {{"task_id": "implementation", "content": "create Y", "task_type": "code"}},
          {{"task_id": "planning", "content": "plan Z", "task_type": "planning"}}
        ]
        
        Keep tasks focused and parallel-executable.
        """
        
        response = await client.generate_response(planning_prompt, max_retries=1)
        
        # Parse JSON response
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            task_data = json.loads(response[json_start:json_end])
            
            tasks = []
            for i, task_info in enumerate(task_data):
                task = ExecutionTask(
                    task_id=task_info.get('task_id', f'task_{i+1}'),
                    content=task_info.get('content', ''),
                    task_type=task_info.get('task_type', 'general'),
                    priority=task_info.get('priority', 5)
                )
                # Assign model based on task type
                task.assigned_model = self._select_model_for_task_type(task.task_type)
                tasks.append(task)
            
            print(f"   ✅ Created {len(tasks)} intelligent tasks")
            return tasks
        else:
            raise Exception("Could not parse task JSON")
    
    def _create_simple_plan(self, user_request: str) -> List[ExecutionTask]:
        """Create simple fallback execution plan"""
        print("   📝 Using simple task decomposition")
        
        execution_models = self._get_execution_models()
        if not execution_models:
            return [ExecutionTask("fallback", user_request, "general")]
        
        # Simple breakdown: analysis + implementation + summary
        tasks = [
            ExecutionTask(
                task_id="analysis",
                content=f"Analyze and break down this request: {user_request}",
                task_type="analysis",
                assigned_model=execution_models[0]
            ),
            ExecutionTask(
                task_id="implementation", 
                content=f"Provide implementation details for: {user_request}",
                task_type="code",
                assigned_model=execution_models[0] if len(execution_models) == 1 else execution_models[1]
            )
        ]
        
        # Add third task if we have more models
        if len(execution_models) > 1:
            tasks.append(ExecutionTask(
                task_id="summary",
                content=f"Summarize key points and recommendations for: {user_request}",
                task_type="summary",
                assigned_model=execution_models[-1]
            ))
        
        print(f"   ✅ Created {len(tasks)} simple tasks")
        return tasks
    
    def _select_model_for_task_type(self, task_type: str) -> str:
        """Select best model for task type"""
        execution_models = self._get_execution_models()
        
        if task_type == "code" and "deepseek-coder:6.7b" in execution_models:
            return "deepseek-coder:6.7b"
        elif task_type in ["summary", "quick"] and "phi4-mini:latest" in self.clients:
            return "phi4-mini:latest"
        elif execution_models:
            return execution_models[0]
        else:
            # Fallback to any available model
            available = [name for name, config in self.models.items() if config.is_available]
            return available[0] if available else "qwen2.5:latest"
    
    async def execute_tasks_parallel(self, tasks: List[ExecutionTask]) -> Dict[str, Any]:
        """Execute tasks in parallel with intelligent load balancing"""
        print(f"\\n⚡ Executing {len(tasks)} tasks in parallel...")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_total_concurrent)
        
        async def execute_single_task(task: ExecutionTask) -> Tuple[str, Dict[str, Any]]:
            async with semaphore:
                return await self._execute_task(task)
        
        # Execute all tasks concurrently
        start_time = time.time()
        
        # Use asyncio.gather for better error handling
        try:
            results = await asyncio.gather(
                *[execute_single_task(task) for task in tasks],
                return_exceptions=True
            )
            
            # Process results
            task_results = {}
            successful = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_id = tasks[i].task_id
                    task_results[task_id] = {
                        'status': 'failed',
                        'error': str(result),
                        'execution_time': 0
                    }
                    print(f"   ❌ Task {task_id} failed: {result}")
                else:
                    task_id, task_result = result
                    task_results[task_id] = task_result
                    successful += 1
                    print(f"   ✅ Task {task_id} completed ({task_result.get('execution_time', 0):.2f}s)")
            
            total_time = time.time() - start_time
            
            print(f"\\n📊 Parallel Execution Results:")
            print(f"   Successful: {successful}/{len(tasks)}")
            print(f"   Total Time: {total_time:.2f}s")
            print(f"   Speedup: {(sum(t.get('execution_time', 0) for t in task_results.values()) / total_time):.2f}x")
            
            return {
                'results': task_results,
                'total_time': total_time,
                'successful_tasks': successful,
                'total_tasks': len(tasks)
            }
            
        except Exception as e:
            print(f"   ❌ Parallel execution failed: {e}")
            return {'results': {}, 'total_time': 0, 'successful_tasks': 0, 'total_tasks': len(tasks)}
    
    async def _execute_task(self, task: ExecutionTask) -> Tuple[str, Dict[str, Any]]:
        """Execute a single task"""
        if not task.assigned_model or task.assigned_model not in self.clients:
            # Auto-assign model
            execution_models = self._get_execution_models()
            task.assigned_model = execution_models[0] if execution_models else list(self.clients.keys())[0]
        
        client = self.clients[task.assigned_model]
        start_time = time.time()
        
        try:
            # Create task-specific system prompt
            if task.task_type == "analysis":
                system_prompt = "You are an expert analyst. Provide clear, structured analysis."
            elif task.task_type == "code":
                system_prompt = "You are a senior developer. Provide working code with explanations."
            elif task.task_type == "planning":
                system_prompt = "You are a strategic planner. Create actionable plans."
            else:
                system_prompt = "You are a helpful assistant. Provide clear, concise responses."
            
            # Execute with timeout
            response = await asyncio.wait_for(
                client.generate_response(task.content, system_prompt, max_retries=1),
                timeout=60.0  # 1 minute timeout per task
            )
            
            execution_time = time.time() - start_time
            
            # Update stats
            self.stats[task.assigned_model]['tasks_completed'] += 1
            self.stats[task.assigned_model]['total_time'] += execution_time
            
            return task.task_id, {
                'status': 'success',
                'result': response,
                'execution_time': execution_time,
                'model_used': task.assigned_model
            }
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.stats[task.assigned_model]['errors'] += 1
            
            return task.task_id, {
                'status': 'failed',
                'error': 'Task timeout',
                'execution_time': execution_time,
                'model_used': task.assigned_model
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.stats[task.assigned_model]['errors'] += 1
            
            return task.task_id, {
                'status': 'failed', 
                'error': str(e),
                'execution_time': execution_time,
                'model_used': task.assigned_model
            }
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        performance = {
            'models': {},
            'total_capacity': 0,
            'total_completed': 0,
            'average_time': 0.0
        }
        
        total_time = 0.0
        total_tasks = 0
        
        for model_name, model_config in self.models.items():
            if model_name in self.stats:
                stats = self.stats[model_name]
                avg_time = stats['total_time'] / max(stats['tasks_completed'], 1)
                
                performance['models'][model_name] = {
                    'role': model_config.role.value,
                    'completed_tasks': stats['tasks_completed'],
                    'errors': stats['errors'],
                    'average_time': avg_time,
                    'max_concurrent': model_config.max_concurrent,
                    'specialties': model_config.specialties,
                    'available': model_config.is_available
                }
                
                if model_config.is_available:
                    performance['total_capacity'] += model_config.max_concurrent
                
                total_time += stats['total_time']
                total_tasks += stats['tasks_completed']
        
        performance['total_completed'] = total_tasks
        performance['average_time'] = total_time / max(total_tasks, 1)
        
        return performance
    
    async def close(self):
        """Close all clients"""
        for client in self.clients.values():
            try:
                await client.close()
            except:
                pass

async def demo_parallel_execution():
    """Demonstrate the parallel execution system"""
    
    executor = LANSParallelExecutor()
    
    try:
        # Initialize
        if not await executor.initialize():
            print("❌ System initialization failed")
            return
        
        # Test cases
        requests = [
            "Create a Python web API with user authentication using FastAPI and JWT tokens",
            "Design a database schema for an e-commerce platform with products, users, and orders",
            "Implement a machine learning model for sentiment analysis with preprocessing and evaluation"
        ]
        
        print("\\n" + "=" * 55)
        print("🎯 PARALLEL EXECUTION DEMO")
        print("=" * 55)
        
        for i, request in enumerate(requests, 1):
            print(f"\\n🚀 Request {i}: {request[:60]}...")
            
            # Create execution plan
            tasks = await executor.create_execution_plan(request)
            
            # Execute in parallel
            results = await executor.execute_tasks_parallel(tasks)
            
            # Show results summary
            print(f"\\n📋 Results Summary:")
            for task_id, result in results['results'].items():
                if result['status'] == 'success':
                    print(f"   ✅ {task_id}: {len(result['result'])} chars in {result['execution_time']:.2f}s")
                else:
                    print(f"   ❌ {task_id}: {result['error']}")
        
        # Final performance report
        performance = executor.get_system_performance()
        print(f"\\n🏆 SYSTEM PERFORMANCE SUMMARY")
        print(f"   Total Capacity: {performance['total_capacity']} concurrent tasks")
        print(f"   Tasks Completed: {performance['total_completed']}")
        print(f"   Average Time: {performance['average_time']:.2f}s per task")
        
        print("\\n📊 Model Performance:")
        for model, stats in performance['models'].items():
            if stats['completed_tasks'] > 0:
                print(f"   {model}: {stats['completed_tasks']} tasks, {stats['average_time']:.2f}s avg")
        
    finally:
        await executor.close()

if __name__ == "__main__":
    asyncio.run(demo_parallel_execution())
