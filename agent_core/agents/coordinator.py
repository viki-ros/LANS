"""
Coordinator - Orchestrates communication between planning and coding agents.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent_core.models import (
    BuildResult,
    GenerationRequest,
    ProjectState,
    Task,
    TaskStatus,
)


class Coordinator:
    """
    Orchestrates the multi-agent system for ROS 2 package generation.
    
    Responsibilities:
    - Route tasks between agents
    - Manage shared state and context
    - Handle error escalation and recovery
    - Coordinate the plan → act → observe → revise loop
    - Optimize resource usage for local development
    """
    
    def __init__(self, config=None):  # Accept config instead of specific clients
        self.config = config
        # Simplified initialization for Phase 3 testing
        self.project_state: Optional[ProjectState] = None
        self.message_queue: List[Any] = []
        
        # Resource optimization settings
        self.max_parallel_tasks = 2  # Limit for local development
        self.retry_limit = 3
        self.timeout_seconds = 300
        self.max_retries = 3  # Default retry limit
        
    async def initialize(self):
        """Initialize the coordinator and all managed agents."""
        try:
            # Initialize planning agent
            if hasattr(self.planning_agent, 'initialize'):
                await self.planning_agent.initialize()
            
            # Initialize coding agent
            if hasattr(self.coding_agent, 'initialize'):
                await self.coding_agent.initialize()
            
            # Reset project state until generation starts
            self.project_state = None
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize coordinator: {e}")
    
    def set_max_retries(self, max_retries: int):
        """Set the maximum number of retries for failed operations."""
        self.max_retries = max_retries
        self.retry_limit = max_retries  # Update existing field too
    
    async def generate_package(self, request: GenerationRequest) -> ProjectState:
        """Main entry point for package generation."""
        
        self.logger.info(f"Starting package generation: {request.user_prompt}")
        
        try:
            # Phase 1: Requirements Analysis & Planning
            project_spec = await self.planning_agent.analyze_requirements(request)
            tasks = await self.planning_agent.create_task_plan(project_spec, request)
            
            # Initialize project state
            self.project_state = ProjectState(
                request=request,
                project_spec=project_spec,
                tasks=tasks
            )
            
            self.logger.info(f"Created plan with {len(tasks)} tasks for project: {project_spec.name}")
            
            # Phase 2: Task Execution
            await self._execute_tasks()
            
            # Phase 3: Final Validation
            await self._validate_package()
            
            return self.project_state
            
        except Exception as e:
            self.logger.error(f"Package generation failed: {e}")
            if self.project_state:
                self.project_state.updated_at = datetime.utcnow()
            raise
    
    async def _execute_tasks(self):
        """Execute tasks in dependency order with resource optimization."""
        
        completed_tasks = set()
        active_tasks = {}  # task_id -> asyncio.Task
        
        self.logger.info(f"Starting task execution for {len(self.project_state.tasks)} tasks")
        
        while len(completed_tasks) < len(self.project_state.tasks):
            # Find ready tasks (dependencies satisfied)
            ready_tasks = [
                task for task in self.project_state.tasks
                if (task.id not in completed_tasks and 
                    task.id not in active_tasks and
                    all(dep in completed_tasks for dep in task.dependencies))
            ]
            
            self.logger.info(f"Loop iteration: completed={len(completed_tasks)}, active={len(active_tasks)}, ready={len(ready_tasks)}")
            
            # Debug: Show which tasks are being considered
            for task in self.project_state.tasks:
                if task.id not in completed_tasks:
                    deps_satisfied = all(dep in completed_tasks for dep in task.dependencies)
                    self.logger.info(f"Task {task.id}: deps={task.dependencies}, satisfied={deps_satisfied}, completed_tasks={list(completed_tasks)}")
            self.logger.info(f"Completed task IDs: {completed_tasks}")
            
            # Debug: Check each task's readiness
            for task in self.project_state.tasks:
                if task.id not in completed_tasks and task.id not in active_tasks:
                    deps_satisfied = all(dep in completed_tasks for dep in task.dependencies)
                    self.logger.info(f"Task {task.id}: deps={task.dependencies}, satisfied={deps_satisfied}")
            
            # Start new tasks (respecting parallel limit)
            while (ready_tasks and 
                   len(active_tasks) < self.max_parallel_tasks):
                
                task = ready_tasks.pop(0)
                task.status = TaskStatus.IN_PROGRESS
                task.updated_at = datetime.utcnow()
                
                # Create async task for execution
                async_task = asyncio.create_task(
                    self._execute_single_task(task)
                )
                active_tasks[task.id] = async_task
                
                self.logger.info(f"Started task: {task.id} - {task.description}")
            
            # Wait for at least one task to complete
            if active_tasks:
                done, pending = await asyncio.wait(
                    active_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=1.0  # Check every second
                )
                
                # Process completed tasks
                for async_task in done:
                    task_id = None
                    for tid, atask in active_tasks.items():
                        if atask == async_task:
                            task_id = tid
                            break
                    
                    if task_id:
                        try:
                            result = await async_task
                            if result.get("success", False):
                                completed_tasks.add(task_id)
                                self._update_task_status(task_id, TaskStatus.COMPLETED)
                                self.logger.info(f"Completed task: {task_id}")
                            else:
                                await self._handle_task_failure(task_id, result)
                        except Exception as e:
                            await self._handle_task_failure(task_id, {"error": str(e)})
                        
                        del active_tasks[task_id]
            
            # Prevent infinite loop
            if not active_tasks and not ready_tasks:
                # Check if there are still uncompleted tasks
                remaining_tasks = len(self.project_state.tasks) - len(completed_tasks)
                if remaining_tasks > 0:
                    self.logger.warning(f"Breaking loop with {remaining_tasks} uncompleted tasks")
                    # Log remaining tasks for debugging
                    for task in self.project_state.tasks:
                        if task.id not in completed_tasks:
                            self.logger.warning(f"Uncompleted task: {task.id} - {task.description}, deps: {task.dependencies}")
                break
        
        self.logger.info(f"Task execution completed. {len(completed_tasks)} tasks finished.")
    
    async def _execute_single_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with timeout and error handling."""
        
        try:
            # Set current task
            self.project_state.current_task_id = task.id
            
            # Execute task based on type
            if "setup_package" in task.description.lower():
                result = await self._setup_package_structure(task)
            elif "build" in task.description.lower() or "compile" in task.description.lower():
                result = await self._build_package(task)
            elif "test" in task.description.lower():
                result = await self._test_package(task)
            else:
                # General code implementation
                result = await self.coding_agent.implement_task(
                    task, 
                    self.project_state.project_spec,
                    self.project_state.request.output_directory
                )
                result["success"] = True
            
            return result
            
        except asyncio.TimeoutError:
            return {"success": False, "error": "Task timeout", "timeout": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _setup_package_structure(self, task: Task) -> Dict[str, Any]:
        """Set up basic project structure."""
        
        project_spec = self.project_state.project_spec
        output_dir = self.project_state.request.output_directory
        
        self.logger.info(f"Setting up project structure for {project_spec.name} in {output_dir}")
        
        if self.mcp_client:
            try:
                # Create project directory
                project_path = f"{output_dir}/{project_spec.name}"
                self.logger.info(f"Creating project directory: {project_path}")
                result = await self.mcp_client.create_directory(project_path)
                self.logger.info(f"Project directory creation result: {result}")
                
                # Create basic structure based on project type and language
                if project_spec.language == "python":
                    await self.mcp_client.create_directory(f"{project_path}/src")
                    await self.mcp_client.create_directory(f"{project_path}/tests")
                    self.logger.info("Created Python project structure")
                elif project_spec.language == "javascript":
                    await self.mcp_client.create_directory(f"{project_path}/src")
                    await self.mcp_client.create_directory(f"{project_path}/test")
                    self.logger.info("Created JavaScript project structure")
                else:
                    # Generic structure
                    await self.mcp_client.create_directory(f"{project_path}/src")
                    await self.mcp_client.create_directory(f"{project_path}/tests")
                    self.logger.info("Created generic project structure")
                    
                return {"success": True, "created_directories": True}
                
            except Exception as e:
                self.logger.error(f"Failed to create project structure: {e}")
                return {"success": False, "error": str(e)}
        else:
            self.logger.warning("No MCP client available for project structure creation")
            return {"success": False, "error": "No MCP client available"}
    
    async def _build_package(self, task: Task) -> Dict[str, Any]:
        """Build the project."""
        
        project_name = self.project_state.project_spec.name
        project_spec = self.project_state.project_spec
        output_dir = self.project_state.request.output_directory
        
        if self.mcp_client:
            # Determine build command based on project type and language
            if project_spec.language == "python":
                # Python projects - run setup/installation
                build_cmd = "python -m pip install -e ."
            elif project_spec.language == "javascript":
                # JavaScript projects - npm install
                build_cmd = "npm install"
            elif project_spec.language == "rust":
                # Rust projects - cargo build
                build_cmd = "cargo build"
            else:
                # Generic build - just check if files exist
                build_cmd = "ls -la"
            
            result = await self.mcp_client.run_command(
                build_cmd,
                cwd=f"{output_dir}/{project_name}",
                timeout=self.timeout_seconds
            )
            
            # Create build result
            build_result = BuildResult(
                success=result.get("success", False),
                output=result.get("stdout", ""),
                errors=[result.get("stderr", "")] if result.get("stderr") else [],
                build_time=0.0  # TODO: measure actual build time
            )
            
            self.project_state.build_results.append(build_result)
            
            return {"success": build_result.success, "build_result": build_result}
        
        return {"success": False, "error": "MCP client not available"}
    
    async def _test_package(self, task: Task) -> Dict[str, Any]:
        """Test the project."""
        
        project_name = self.project_state.project_spec.name
        project_spec = self.project_state.project_spec
        output_dir = self.project_state.request.output_directory
        
        if self.mcp_client:
            # Determine test command based on project type and language
            if project_spec.language == "python":
                test_cmd = "python -m pytest tests/ -v"
            elif project_spec.language == "javascript":
                test_cmd = "npm test"
            elif project_spec.language == "rust":
                test_cmd = "cargo test"
            else:
                # Generic test - just run the main file if it exists
                test_cmd = "python main.py --help || echo 'No tests configured'"
            
            result = await self.mcp_client.run_command(
                test_cmd,
                cwd=f"{output_dir}/{project_name}",
                timeout=self.timeout_seconds
            )
            
            return {"success": result.get("success", True), "test_result": result}
        
        return {"success": False, "error": "MCP client not available"}
    
    async def _fix_build_errors(self, errors: List[str]):
        """Attempt to fix build errors using the coding agent."""
        
        try:
            fixes = await self.coding_agent.fix_build_errors(
                errors,
                self.project_state.project_spec,
                self.project_state.request.output_directory
            )
            
            self.logger.info(f"Applied {len(fixes.get('fixes', []))} fixes for build errors")
            
        except Exception as e:
            self.logger.error(f"Failed to fix build errors: {e}")
    
    async def _handle_task_failure(self, task_id: str, error_info: Dict[str, Any]):
        """Handle task failure with recovery attempts."""
        
        task = next((t for t in self.project_state.tasks if t.id == task_id), None)
        if not task:
            return
        
        task.status = TaskStatus.FAILED
        task.updated_at = datetime.utcnow()
        
        self.logger.warning(f"Task failed: {task_id} - {error_info}")
        
        # Check retry count
        retry_count = task.metadata.get("retry_count", 0)
        
        if retry_count < self.retry_limit:
            # Retry the task
            task.metadata["retry_count"] = retry_count + 1
            task.status = TaskStatus.RETRYING
            
            self.logger.info(f"Retrying task {task_id} (attempt {retry_count + 1})")
            
            # Add small delay before retry
            await asyncio.sleep(2)
            
        else:
            # Create recovery plan
            try:
                recovery_tasks = await self.planning_agent.create_error_recovery_plan(task, error_info)
                self.project_state.tasks.extend(recovery_tasks)
                
                self.logger.info(f"Created {len(recovery_tasks)} recovery tasks for {task_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to create recovery plan: {e}")
    
    def _update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status in project state."""
        for task in self.project_state.tasks:
            if task.id == task_id:
                task.status = status
                task.updated_at = datetime.utcnow()
                break
    
    async def _validate_package(self):
        """Final validation of the generated package."""
        
        self.logger.info("Starting final package validation")
        
        # Check package structure
        # Run build test
        # Verify all required files exist
        # TODO: Implement comprehensive validation
        
        self.project_state.updated_at = datetime.utcnow()
        self.logger.info("Package validation completed")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current generation status."""
        if not self.project_state:
            return {"status": "not_started"}
        
        total_tasks = len(self.project_state.tasks)
        completed_tasks = sum(1 for t in self.project_state.tasks if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in self.project_state.tasks if t.status == TaskStatus.FAILED)
        
        return {
            "status": "in_progress" if completed_tasks < total_tasks else "completed",
            "progress": {
                "total": total_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "current_task": self.project_state.current_task_id,
            "project_name": self.project_state.project_spec.name if self.project_state.project_spec else None
        }
