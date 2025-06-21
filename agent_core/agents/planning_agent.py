"""
Planning Agent - Strategic task decomposition and planning for software project generation.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import (
    Task, TaskStatus, AgentType, GenerationRequest, 
    ProjectSpec, AgentMessage, ProjectState
)
from ..llm.ollama_client import OllamaClient


class PlanningAgent:
    """
    Strategic planning agent that analyzes requirements and creates execution plans.
    
    Responsibilities:
    - Analyze user requirements (NL → structured tasks)
    - Break down complex software project requirements into subtasks  
    - Create dependency graphs and execution order
    - Handle error recovery strategies
    - Generate test scenarios and validation criteria
    """
    
    def __init__(self, llm_client: OllamaClient):
        self.llm_client = llm_client
        self.agent_type = AgentType.PLANNING
        
        # Planning templates for different project types
        self.project_templates = {
            "web_app": ["setup_project", "create_backend", "create_frontend", "add_database", "test_integration"],
            "api": ["setup_project", "create_endpoints", "add_authentication", "add_database", "test_api"],
            "cli_tool": ["setup_project", "create_main", "add_commands", "add_config", "test_cli"],
            "desktop_app": ["setup_project", "create_ui", "add_logic", "add_resources", "test_app"],
            "library": ["setup_project", "create_modules", "add_tests", "add_docs", "test_library"],
            "game": ["setup_project", "create_engine", "add_assets", "add_gameplay", "test_game"],
            "data_science": ["setup_project", "data_pipeline", "analysis", "visualization", "test_pipeline"],
            "mobile_app": ["setup_project", "create_ui", "add_navigation", "add_features", "test_mobile"],
            "calculator": ["setup_project", "create_main", "add_operations", "add_ui", "test_calculator"],
            "simple": ["setup_project", "implement_core", "add_tests", "validate"]
        }
    
    async def analyze_requirements(self, request: GenerationRequest) -> ProjectSpec:
        """Analyze user requirements and generate a software project specification."""
        
        system_prompt = """You are an expert software architect and project planning agent. Analyze the user's requirements and create a detailed project specification.

Key responsibilities:
1. Identify the type of software project needed (web app, API, CLI tool, desktop app, etc.)
2. Determine required dependencies and technologies
3. Specify project structure and components
4. Choose appropriate programming language and frameworks
5. Suggest project architecture and patterns

Respond with a JSON object containing the project specification."""

        user_prompt = f"""
Analyze this software project request: "{request.user_prompt}"

Create a detailed project specification including:
- Project name (clean, descriptive)
- Description
- Project type (web_app, api, cli_tool, desktop_app, library, game, data_science, mobile_app, calculator, simple, etc.)
- Primary programming language (python, javascript, java, rust, go, etc.)
- Framework (if applicable: fastapi, flask, react, vue, electron, etc.)
- Dependencies (packages/libraries needed)
- Features (list of main features to implement)
- Project structure (directories and main files)
- Configuration (environment, build settings, etc.)

Consider:
- Modern best practices and patterns
- Popular and well-maintained frameworks
- Appropriate testing approach
- Documentation requirements
- Security considerations

Output as JSON matching ProjectSpec format.
"""

        response = await self.llm_client.generate(
            user_prompt,
            agent_type=self.agent_type,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        try:
            # Parse JSON response
            spec_data = json.loads(response)
            project_spec = ProjectSpec(**spec_data)
            return project_spec
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to basic project if parsing fails
            return ProjectSpec(
                name=self._generate_project_name(request.user_prompt),
                description=request.user_prompt,
                project_type="simple",
                language="python"
            )
    
    async def create_task_plan(self, project_spec: ProjectSpec, request: GenerationRequest) -> List[Task]:
        """Create a detailed task execution plan for the project generation."""
        
        system_prompt = """You are a software project planning expert. Create a detailed task breakdown for generating the specified project.

Tasks should be:
1. Specific and actionable
2. Properly ordered with dependencies
3. Include validation steps
4. Cover all aspects of software project creation

Each task should specify what needs to be implemented and any dependencies on other tasks."""

        user_prompt = f"""
Create a detailed task plan for generating this software project:

Project Specification:
{project_spec.model_dump_json(indent=2)}

User Requirements: "{request.user_prompt}"

Generate tasks covering:
1. Project structure setup (directories, config files)
2. Core implementation
3. Dependencies and imports
4. Configuration files
5. Documentation
6. Tests
7. Build/deployment setup
8. Validation

Output as JSON array of tasks with:
- id: unique identifier (format: task_001, task_002, etc.)
- description: clear task description
- dependencies: list of task IDs this depends on
- metadata: additional task-specific information

Order tasks logically with proper dependencies.
"""

        response = await self.llm_client.generate(
            user_prompt,
            agent_type=self.agent_type,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        try:
            # Parse JSON response
            tasks_data = json.loads(response)
            tasks = []
            
            for i, task_data in enumerate(tasks_data):
                task = Task(
                    id=task_data.get("id", f"task_{i+1:03d}"),
                    description=task_data.get("description", f"Task {i+1}"),
                    dependencies=task_data.get("dependencies", []),
                    metadata=task_data.get("metadata", {})
                )
                tasks.append(task)
            
            return tasks
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to template-based planning
            return self._create_template_plan(project_spec)
    
    def _create_template_plan(self, project_spec: ProjectSpec) -> List[Task]:
        """Create a plan based on project type templates."""
        
        # Determine project type from specification
        project_type = project_spec.project_type
        if project_type not in self.project_templates:
            # Try to infer from description
            desc_lower = project_spec.description.lower()
            if "web" in desc_lower or "website" in desc_lower:
                project_type = "web_app"
            elif "api" in desc_lower:
                project_type = "api"
            elif "cli" in desc_lower or "command" in desc_lower:
                project_type = "cli_tool"
            elif "calculator" in desc_lower:
                project_type = "calculator"
            elif "app" in desc_lower:
                project_type = "desktop_app"
            else:
                project_type = "simple"
        
        # Get template tasks
        template_tasks = self.project_templates.get(project_type, self.project_templates["simple"])
        
        tasks = []
        for i, task_desc in enumerate(template_tasks):
            task_id = f"task_{i+1:03d}"
            dependencies = [f"task_{i:03d}"] if i > 0 else []
            
            task = Task(
                id=task_id,
                description=f"{task_desc.replace('_', ' ').title()} - {project_spec.description}",
                dependencies=dependencies,
                metadata={"template_task": task_desc, "project_type": project_type}
            )
            tasks.append(task)
        
        return tasks
    
    async def create_recovery_plan(self, failed_task: Task, error_context: Dict[str, Any]) -> List[Task]:
        """Create a recovery plan when a task fails."""
        
        system_prompt = """You are a debugging and recovery expert. Analyze the failed task and create a recovery plan."""
        
        user_prompt = f"""
A task has failed during project generation:

Failed Task: {failed_task.description}
Error Context: {json.dumps(error_context, indent=2)}

Create a recovery plan with specific tasks to:
1. Diagnose the root cause
2. Fix the underlying issue
3. Retry or recreate the failed component
4. Validate the fix

Output as JSON array of recovery tasks.
"""

        response = await self.llm_client.generate(
            user_prompt,
            agent_type=self.agent_type,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        try:
            recovery_data = json.loads(response)
            recovery_tasks = []
            
            for i, task_data in enumerate(recovery_data):
                task = Task(
                    id=f"recovery_{failed_task.id}_{i+1}",
                    description=task_data.get("description", f"Recovery step {i+1}"),
                    dependencies=task_data.get("dependencies", []),
                    metadata={
                        "recovery_for": failed_task.id,
                        "original_error": error_context
                    }
                )
                recovery_tasks.append(task)
            
            return recovery_tasks
            
        except Exception:
            # Simple fallback recovery
            return [
                Task(
                    id=f"recovery_{failed_task.id}_1",
                    description=f"Retry {failed_task.description}",
                    dependencies=[],
                    metadata={"recovery_for": failed_task.id}
                )
            ]
    
    def _generate_project_name(self, user_prompt: str) -> str:
        """Generate a valid project name from user prompt."""
        # Simple name generation - remove special chars, convert to snake_case
        import re
        name = re.sub(r'[^\w\s]', '', user_prompt.lower())
        name = re.sub(r'\s+', '_', name.strip())
        return name[:50] if name else "generated_project"
