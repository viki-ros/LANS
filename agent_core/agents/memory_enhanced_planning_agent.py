"""
Enhanced Planning Agent with Global Memory Integration.
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
from ...global_mcp_server.api.client import GMCPClient
from ...global_mcp_server.api.agentos_integration import AgentOSIntegration


class MemoryEnhancedPlanningAgent:
    """
    Enhanced Planning Agent with persistent memory capabilities.
    
    This agent can:
    - Remember successful planning strategies
    - Learn from past project experiences  
    - Share knowledge with other planning agents
    - Build domain expertise over time
    - Provide context-aware recommendations
    """
    
    def __init__(self, llm_client: OllamaClient, memory_config: Dict[str, Any] = None):
        self.llm_client = llm_client
        self.agent_type = AgentType.PLANNING
        self.agent_id = f"planning_agent_{uuid.uuid4().hex[:8]}"
        
        # Initialize Global Memory connection
        memory_config = memory_config or {}
        self.gmcp_client = GMCPClient(
            base_url=memory_config.get("gmcp_url", "http://localhost:8001")
        )
        
        self.memory_integration = AgentOSIntegration(
            gmcp_client=self.gmcp_client,
            agent_name="planning_agent",
            agent_type="planning"
        )
        
        # Planning templates (enhanced with memory)
        self.project_templates = {
            "web_app": ["setup_project", "create_server", "add_database", "implement_auth", "test_endpoints"],
            "api_service": ["setup_project", "define_routes", "implement_handlers", "add_middleware", "test_api"],
            "cli_tool": ["setup_project", "define_commands", "implement_logic", "add_help", "test_cli"],
            "desktop_app": ["setup_project", "create_ui", "implement_logic", "package_app", "test_functionality"],
            "microservice": ["setup_project", "define_service", "implement_endpoints", "add_monitoring", "test_service"],
            "data_pipeline": ["setup_project", "define_schema", "implement_processors", "add_validation", "test_pipeline"]
        }
    
    async def initialize(self, user_id: str = None):
        """Initialize the agent with memory capabilities."""
        await self.memory_integration.initialize()
        
        # Remember basic software development knowledge on first startup
        await self._initialize_development_knowledge()
    
    async def analyze_requirements(self, request: GenerationRequest) -> ProjectSpec:
        """Analyze user requirements with memory-enhanced insights."""
        
        # First, recall relevant past experiences and knowledge
        memory_context = await self._gather_memory_context(request.user_prompt)
        
        # Enhanced system prompt with memory context
        system_prompt = self._build_memory_enhanced_system_prompt(memory_context)
        
        user_prompt = f"""
Analyze this software project request: "{request.user_prompt}"

Memory Context:
{self._format_memory_context(memory_context)}

Create a detailed package specification including:
- Package name (descriptive and compliant)
- Description
- Dependencies (required packages and libraries)
- Build type (language-specific build system)
- Components specifications (name, purpose, interfaces)
- APIs (endpoints, methods, interfaces)
- Services (background services, daemons) 
- Actions (automated tasks, workflows)

Consider:
- Best practices and naming conventions
- Standard libraries and frameworks when possible
- Appropriate architecture patterns
- Testing requirements
- Past successful patterns from memory

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
            package_spec = ProjectSpec(**spec_data)
            
            # Remember this requirement analysis for future reference
            if self.memory_integration:
                await self.memory_integration.remember_task_execution(
                    task_description=f"Analyzed requirements for: {request.user_prompt}",
                    approach="Memory-enhanced LLM analysis with past context",
                    outcome="success",
                    metrics={"spec_complexity": len(spec_data.get("dependencies", [])) + len(spec_data.get("nodes", []))}
                )
            
            return package_spec
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to basic package if parsing fails
            fallback_spec = ProjectSpec(
                name=self._generate_package_name(request.user_prompt),
                description=request.user_prompt,
                build_type="ament_python"
            )
            
            # Remember the failure for learning
            if self.memory_integration:
                await self.memory_integration.remember_task_execution(
                    task_description=f"Analyzed requirements for: {request.user_prompt}",
                    approach="Memory-enhanced LLM analysis with fallback",
                    outcome="partial_failure", 
                    metrics={"error": str(e), "fallback_used": True}
                )
            
            return fallback_spec
    
    async def create_task_plan(self, package_spec: ProjectSpec, request: GenerationRequest) -> List[Task]:
        """Create a detailed task execution plan with memory-guided optimization."""
        
        # Recall similar successful project patterns
        similar_projects = await self._recall_similar_projects(package_spec, request)
        
        # Get applicable planning strategies
        planning_strategies = await self._recall_planning_strategies(package_spec.build_type)
        
        system_prompt = f"""You are a software project planning expert with access to successful past patterns.

Planning Context from Memory:
{self._format_similar_projects(similar_projects)}

Proven Strategies:
{self._format_planning_strategies(planning_strategies)}

Create tasks that are:
1. Specific and actionable
2. Properly ordered with dependencies
3. Include validation steps
4. Cover all aspects of ROS 2 package creation
5. Learn from past successful approaches

Each task should specify what needs to be implemented and any dependencies on other tasks."""

        user_prompt = f"""
Create a detailed task plan for generating this ROS 2 package:

Package Specification:
{package_spec.model_dump_json(indent=2)}

User Requirements: "{request.user_prompt}"

Generate tasks covering:
1. Package structure setup (package.xml, CMakeLists.txt/setup.py)
2. Node implementation
3. Interface definitions (if needed)
4. Configuration files
5. Launch files
6. Tests
7. Documentation
8. Build validation

Output as JSON array of tasks with:
- id: unique identifier
- description: clear task description
- dependencies: list of task IDs this depends on
- metadata: additional task-specific information

Order tasks logically with proper dependencies and incorporate lessons from similar past projects.
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
            
            for task_data in tasks_data:
                task = Task(
                    id=task_data.get("id", str(uuid.uuid4())),
                    description=task_data.get("description", ""),
                    dependencies=task_data.get("dependencies", []),
                    metadata=task_data.get("metadata", {})
                )
                tasks.append(task)
            
            # Remember this planning approach
            if self.memory_integration:
                await self.memory_integration.remember_task_execution(
                    task_description=f"Created task plan for {package_spec.name}",
                    approach="Memory-guided task planning with similar project patterns",
                    outcome="success",
                    metrics={
                        "task_count": len(tasks),
                        "complexity_score": len([t for t in tasks if t.dependencies]),
                        "memory_references": len(similar_projects)
                    }
                )
            
            return tasks
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to template-based planning
            fallback_tasks = self._create_template_tasks(package_spec)
            
            # Remember the fallback usage
            if self.memory_integration:
                await self.memory_integration.remember_task_execution(
                    task_description=f"Created task plan for {package_spec.name}",
                    approach="Template-based fallback planning",
                    outcome="partial_failure",
                    metrics={"error": str(e), "fallback_tasks": len(fallback_tasks)}
                )
            
            return fallback_tasks
    
    async def create_error_recovery_plan(self, failed_task: Task, error_info: Dict[str, Any]) -> List[Task]:
        """Create a recovery plan using memory of past error resolutions."""
        
        # Recall similar error scenarios and their resolutions
        similar_errors = await self._recall_error_patterns(failed_task, error_info)
        
        system_prompt = f"""You are a ROS 2 debugging expert with access to past error resolution patterns.

Error Resolution History:
{self._format_error_patterns(similar_errors)}

Focus on:
1. Root cause analysis using past similar cases
2. Incremental fixes that have worked before
3. Alternative approaches from memory
4. Validation steps to prevent recurrence

Create specific recovery tasks that address the error based on proven solutions."""

        user_prompt = f"""
Task failed: {failed_task.description}
Error information: {json.dumps(error_info, indent=2)}

Similar Past Errors and Resolutions:
{json.dumps(similar_errors, indent=2)}

Create a recovery plan with specific tasks to:
1. Fix the immediate error using proven approaches
2. Verify the fix works with past validation methods
3. Prevent similar errors using learned patterns
4. Continue with the original plan

Output as JSON array of recovery tasks.
"""

        response = await self.llm_client.generate(
            user_prompt,
            agent_type=self.agent_type,
            system_prompt=system_prompt,
            temperature=0.2
        )
        
        try:
            tasks_data = json.loads(response)
            recovery_tasks = []
            
            for task_data in tasks_data:
                task = Task(
                    id=f"recovery_{uuid.uuid4().hex[:8]}",
                    description=task_data.get("description", ""),
                    dependencies=task_data.get("dependencies", []),
                    metadata={
                        "recovery_for": failed_task.id,
                        "error_type": error_info.get("type", "unknown"),
                        "memory_guided": True,
                        **task_data.get("metadata", {})
                    }
                )
                recovery_tasks.append(task)
            
            # Remember this error recovery for future reference
            if self.memory_integration:
                await self.memory_integration.remember_task_execution(
                    task_description=f"Error recovery for: {failed_task.description}",
                    approach="Memory-guided error recovery",
                    outcome="recovery_planned",
                    metrics={
                        "original_error": error_info.get("type", "unknown"),
                        "recovery_tasks": len(recovery_tasks),
                        "similar_cases_found": len(similar_errors)
                    }
                )
            
            return recovery_tasks
            
        except Exception as e:
            # Fallback recovery task
            fallback_task = Task(
                id=f"recovery_{uuid.uuid4().hex[:8]}",
                description=f"Manual investigation required for failed task: {failed_task.description}",
                metadata={"recovery_for": failed_task.id, "manual": True, "memory_unavailable": True}
            )
            return [fallback_task]
    
    async def share_expertise(self, target_agent_id: str, domain: str = "software_planning"):
        """Share planning expertise with other agents."""
        if self.memory_integration:
            return await self.memory_integration.share_successful_approach(target_agent_id, domain)
    
    async def get_planning_insights(self, days_back: int = 30):
        """Get insights from planning activities."""
        if self.memory_integration:
            return await self.gmcp_client.get_insights(hours_back=days_back * 24)
        return {}
    
    # Private memory helper methods
    
    async def _gather_memory_context(self, user_prompt: str) -> Dict[str, Any]:
        """Gather relevant memory context for planning."""
        try:
            # Recall similar problems and their solutions
            similar_problems = await self.memory_integration.recall_similar_problems(
                problem=user_prompt,
                max_results=5
            )
            
            # Get relevant skills for software development
            relevant_skills = await self.memory_integration.get_relevant_skills(
                task_domain="software_development",
                max_skills=10
            )
            
            return {
                "similar_problems": similar_problems,
                "relevant_skills": relevant_skills,
                "project_templates": self.project_templates
            }
            
        except Exception as e:
            # Graceful fallback if memory is unavailable
            return {
                "similar_problems": [],
                "relevant_skills": [],
                "project_templates": self.project_templates
            }

    def _build_memory_enhanced_system_prompt(self, memory_context: Dict[str, Any]) -> str:
        """Build a system prompt enhanced with memory context."""
        base_prompt = """You are an expert software planning agent with access to persistent memory of past successful projects.

Your role is to analyze user requirements and create detailed, actionable plans for software project generation.

Consider:
1. Software development best practices and conventions
2. Past successful strategies from memory
3. Common patterns and templates
4. Dependency management
5. Testing and validation approaches"""

        if memory_context.get("similar_problems"):
            base_prompt += "\n\nPast Similar Solutions:\n"
            for problem in memory_context["similar_problems"][:3]:
                metadata = problem.get("metadata", {})
                base_prompt += f"- Problem: {metadata.get('problem', 'N/A')}\n"
                base_prompt += f"  Solution approach: {metadata.get('solution', 'N/A')[:200]}...\n"
        
        if memory_context.get("relevant_skills"):
            base_prompt += "\n\nRelevant Skills Available:\n"
            for skill in memory_context["relevant_skills"][:5]:
                metadata = skill.get("metadata", {})
                base_prompt += f"- {metadata.get('skill_name', 'Unknown')}: {metadata.get('procedure', 'N/A')[:100]}...\n"
        
        return base_prompt

    def _format_memory_context(self, memory_context: Dict[str, Any]) -> str:
        """Format memory context for inclusion in prompts."""
        context_str = ""
        
        if memory_context.get("similar_problems"):
            context_str += "Similar Past Projects:\n"
            for i, problem in enumerate(memory_context["similar_problems"][:3], 1):
                metadata = problem.get("metadata", {})
                context_str += f"{i}. {metadata.get('problem', 'N/A')}\n"
                context_str += f"   Success factors: {metadata.get('context', {}).get('success_factors', 'N/A')}\n"
        
        if memory_context.get("relevant_skills"):
            context_str += "\nAvailable Skills:\n"
            for i, skill in enumerate(memory_context["relevant_skills"][:5], 1):
                metadata = skill.get("metadata", {})
                context_str += f"{i}. {metadata.get('skill_name', 'Unknown')}\n"
        
        return context_str

    async def _initialize_development_knowledge(self):
        """Initialize basic software development knowledge in memory."""
        try:
            # Store basic software development concepts
            development_concepts = [
                ("api", "Application Programming Interface for communication between software components"),
                ("database", "Structured storage system for persistent data management"),
                ("authentication", "Process of verifying user identity and access permissions"),
                ("testing", "Systematic validation of software functionality and behavior"),
                ("deployment", "Process of making software available for use in production environment"),
                ("configuration", "Settings and parameters that control software behavior")
            ]
            
            for concept, definition in development_concepts:
                await self.memory_integration.client.store_memory(
                    memory_type="semantic",
                    content=definition,
                    metadata={
                        "concept": f"dev_{concept}",
                        "definition": definition,
                        "domain": "software_development",
                        "source": "initialization"
                    },
                    importance_score=0.9
                )
            
        except Exception as e:
            # Non-critical - continue without memory initialization
            pass

    async def remember_successful_plan(self, request: GenerationRequest, package_spec: ProjectSpec, tasks: List[Task]):
        """Remember a successful planning outcome."""
        try:
            planning_details = {
                "user_request": request.user_prompt,
                "package_name": package_spec.package_name,
                "package_type": getattr(package_spec, 'build_type', 'unknown'),
                "nodes_count": len(package_spec.nodes) if package_spec.nodes else 0,
                "topics_count": len(package_spec.topics) if package_spec.topics else 0,
                "services_count": len(package_spec.services) if package_spec.services else 0,
                "tasks_count": len(tasks),
                "success_factors": [
                    "Clear requirement analysis",
                    "Appropriate ROS 2 patterns",
                    "Proper dependency management",
                    "Comprehensive task breakdown"
                ]
            }
            
            solution_summary = f"""Successfully planned ROS 2 package '{package_spec.package_name}':
- {len(package_spec.nodes or [])} nodes
- {len(package_spec.topics or [])} topics  
- {len(package_spec.services or [])} services
- {len(tasks)} implementation tasks
- Build type: {getattr(package_spec, 'build_type', 'unknown')}"""

            await self.memory_integration.remember_successful_solution(
                problem=request.user_prompt,
                solution=solution_summary,
                context=planning_details
            )
            
        except Exception as e:
            # Non-critical - continue without memory storage
            pass

    async def learn_from_planning_error(self, request: GenerationRequest, error: str, attempted_approach: str):
        """Learn from planning errors."""
        try:
            error_context = {
                "user_request": request.user_prompt,
                "error_type": "planning_error",
                "attempted_approach": attempted_approach,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_integration.learn_from_error(
                error=error,
                attempted_solution=attempted_approach,
                context=error_context
            )
            
        except Exception as e:
            # Non-critical - continue without memory storage
            pass
    
    # Existing methods (same as before)
    def _generate_package_name(self, prompt: str) -> str:
        """Generate a ROS 2 compliant package name from user prompt."""
        import re
        
        words = re.findall(r'\b\w+\b', prompt.lower())
        filtered_words = [w for w in words if w not in {'a', 'an', 'the', 'for', 'of', 'with', 'to', 'and', 'or'}]
        
        name_parts = filtered_words[:3] if filtered_words else ['custom']
        name = '_'.join(name_parts)
        
        name = re.sub(r'[^a-z0-9_]', '_', name)
        if name[0].isdigit():
            name = f"pkg_{name}"
        
        return name
    
    def _create_template_tasks(self, package_spec: ProjectSpec) -> List[Task]:
        """Create tasks based on project type templates."""
        project_type = "web_app"
        
        if package_spec.project_type:
            project_type = package_spec.project_type
        elif "api" in package_spec.name.lower() or "service" in package_spec.name.lower():
            project_type = "api_service"
        elif "cli" in package_spec.name.lower() or "command" in package_spec.name.lower():
            project_type = "cli_tool"
        
        template_tasks = self.project_templates.get(project_type, self.project_templates["web_app"])
        
        tasks = []
        for i, task_name in enumerate(template_tasks):
            task = Task(
                id=f"task_{i+1:03d}",
                description=task_name.replace('_', ' ').title(),
                dependencies=[f"task_{i:03d}"] if i > 0 else [],
                metadata={"template": project_type, "order": i}
            )
            tasks.append(task)
        
        return tasks
