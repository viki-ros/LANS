"""
Intelligent Coordinator - AIL/GMCP/AgentOS Architecture Implementation
CRITICAL: Only user↔AI uses natural language, all agent↔agent uses AIL
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

# Add global_mcp_server to path for AIL/GMCP/AgentOS imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "global_mcp_server"))

from .llm.ollama_client import OllamaClient
from .models import AgentType
from .lans_context import LANSContext

# Import AIL/GMCP/AgentOS components
try:
    from global_mcp_server.core.agentos_kernel import AgentOSKernel
    from global_mcp_server.api.client import GMCPClient
    from global_mcp_server.config import load_config
    AGENTOS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AgentOS/GMCP components not available: {e}")
    AGENTOS_AVAILABLE = False


class AgentCapability(Enum):
    """Available agent capabilities"""
    PLANNING = "planning"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    FILE_OPERATIONS = "file_operations"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"
    PROJECT_MANAGEMENT = "project_management"
    DATA_PROCESSING = "data_processing"
    WEB_DEVELOPMENT = "web_development"
    API_DEVELOPMENT = "api_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    DESIGN = "design"
    OPTIMIZATION = "optimization"


class AgentProfile:
    """Profile of an available agent with its capabilities"""
    
    def __init__(self, name: str, capabilities: List[AgentCapability], 
                 specialties: List[str] = None, max_concurrent_tasks: int = 3):
        self.name = name
        self.capabilities = capabilities
        self.specialties = specialties or []
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks = 0
        self.success_rate = 1.0
        self.avg_completion_time = 60.0  # seconds


class TaskAssignment:
    """Assignment of a task to specific agents"""
    
    def __init__(self, task_id: str, description: str, assigned_agents: List[str],
                 required_capabilities: List[AgentCapability], priority: int = 5,
                 estimated_duration: float = 60.0):
        self.task_id = task_id
        self.description = description
        self.assigned_agents = assigned_agents
        self.required_capabilities = required_capabilities
        self.priority = priority
        self.estimated_duration = estimated_duration
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.dependencies = []
        self.outputs = {}


class IntelligentCoordinator:
    """
    Intelligent coordinator implementing proper AIL/GMCP/AgentOS architecture.
    
    CRITICAL ARCHITECTURE PRINCIPLE:
    - User ↔ AI: Natural Language (this coordinator)
    - Agent ↔ Agent: AIL (Agent Instruction Language) via AgentOS Kernel
    """
    
    def __init__(self, llm_client: OllamaClient):
        self.llm_client = llm_client
        self.available_agents = self._initialize_agent_profiles()
        self.active_assignments = []
        self.completed_assignments = []
        
        # Initialize AIL/GMCP/AgentOS components
        self.agentos_kernel = None
        self.gmcp_client = None
        self.agent_id = f"intelligent_coordinator_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if AGENTOS_AVAILABLE:
            asyncio.create_task(self._initialize_agentos_components())
    
    async def _initialize_agentos_components(self):
        """Initialize AgentOS Kernel and GMCP client for proper AIL communication"""
        try:
            # Load configuration
            config = load_config()
            
            # Initialize AgentOS Kernel
            self.agentos_kernel = AgentOSKernel(config)
            await self.agentos_kernel.initialize()
            
            # Initialize GMCP Client
            self.gmcp_client = GMCPClient("http://localhost:8080")
            self.gmcp_client.configure_agent(
                agent_id=self.agent_id,
                user_id="lans_system"
            )
            
            # Register with GMCP
            await self.gmcp_client.register_agent(
                agent_type="intelligent_coordinator",
                capabilities=["task_analysis", "agent_coordination", "ail_translation"]
            )
            
            print(f"✅ AgentOS/GMCP initialized for coordinator {self.agent_id}")
            
        except Exception as e:
            print(f"⚠️  Failed to initialize AgentOS/GMCP: {e}")
            self.agentos_kernel = None
            self.gmcp_client = None
        
    def _initialize_agent_profiles(self) -> Dict[str, AgentProfile]:
        """Initialize available agent profiles with their capabilities"""
        
        agents = {
            "master_planner": AgentProfile(
                name="master_planner",
                capabilities=[AgentCapability.PLANNING, AgentCapability.PROJECT_MANAGEMENT, AgentCapability.ANALYSIS],
                specialties=["task decomposition", "dependency analysis", "resource planning"]
            ),
            
            "creative_writer": AgentProfile(
                name="creative_writer", 
                capabilities=[AgentCapability.CREATIVE_WRITING, AgentCapability.DOCUMENTATION],
                specialties=["letters", "stories", "emails", "creative content", "technical writing"]
            ),
            
            "code_architect": AgentProfile(
                name="code_architect",
                capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.PLANNING, AgentCapability.DESIGN],
                specialties=["software architecture", "code design", "best practices", "patterns"]
            ),
            
            "full_stack_developer": AgentProfile(
                name="full_stack_developer",
                capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.WEB_DEVELOPMENT, AgentCapability.API_DEVELOPMENT],
                specialties=["React", "FastAPI", "Node.js", "Python", "JavaScript", "full-stack applications"]
            ),
            
            "mobile_developer": AgentProfile(
                name="mobile_developer",
                capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.MOBILE_DEVELOPMENT],
                specialties=["React Native", "Flutter", "mobile apps", "cross-platform"]
            ),
            
            "file_manager": AgentProfile(
                name="file_manager",
                capabilities=[AgentCapability.FILE_OPERATIONS],
                specialties=["file creation", "folder management", "file organization", "file operations"]
            ),
            
            "qa_engineer": AgentProfile(
                name="qa_engineer",
                capabilities=[AgentCapability.TESTING, AgentCapability.ANALYSIS],
                specialties=["unit testing", "integration testing", "test automation", "quality assurance"]
            ),
            
            "data_scientist": AgentProfile(
                name="data_scientist",
                capabilities=[AgentCapability.DATA_PROCESSING, AgentCapability.ANALYSIS, AgentCapability.CODE_GENERATION],
                specialties=["data analysis", "machine learning", "visualization", "Python", "pandas", "numpy"]
            ),
            
            "conversational_ai": AgentProfile(
                name="conversational_ai",
                capabilities=[AgentCapability.CONVERSATION, AgentCapability.RESEARCH],
                specialties=["dialogue", "questions", "explanations", "research", "knowledge"]
            ),
            
            "optimizer": AgentProfile(
                name="optimizer",
                capabilities=[AgentCapability.OPTIMIZATION, AgentCapability.ANALYSIS],
                specialties=["performance optimization", "code optimization", "system optimization"]
            )
        }
        
        return agents
    
    async def process_query(self, user_query: str, workspace: str = "./workspace") -> Dict[str, Any]:
        """
        Intelligently process any user query by:
        1. Analyzing the query to understand intent and requirements
        2. Decomposing into tasks if needed
        3. Dynamically assigning appropriate agents
        4. Executing the plan
        5. Returning results
        """
        
        print(f"🧠 Analyzing query: {user_query}")
        
        # Step 1: Analyze the query
        analysis = await self._analyze_query(user_query)
        
        # Step 2: Decide on approach (simple vs complex)
        if analysis["complexity"] == "simple":
            return await self._handle_simple_request(user_query, analysis, workspace)
        else:
            return await self._handle_complex_request(user_query, analysis, workspace)
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query using AIL if available, otherwise fallback to direct LLM.
        This maintains user↔AI natural language while enabling AIL for analysis.
        """
        
        # Try AIL-based analysis first
        if self.agentos_kernel:
            try:
                ail_analysis_instruction = f'(QUERY {{"intent": "Analyze user request: {query}", "mode": "analysis"}})'
                
                ail_result = await self._execute_ail_instruction(
                    ail_instruction=ail_analysis_instruction,
                    context={"operation": "query_analysis", "user_query": query}
                )
                
                if ail_result["success"]:
                    # Convert AIL result to analysis format
                    return self._convert_ail_to_analysis(ail_result, query)
                    
            except Exception as e:
                print(f"⚠️  AIL analysis failed: {e}, falling back to direct LLM")
        
        # Fallback to direct LLM analysis
        return await self._direct_llm_analysis(query)
    
    def _convert_ail_to_analysis(self, ail_result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Convert AIL query result to analysis format"""
        
        try:
            # Extract meaningful analysis from AIL result
            result_data = ail_result.get("result", {})
            
            # Use pattern matching on the original query for classification
            query_lower = query.lower()
            
            if any(word in query_lower for word in ["app", "application", "website", "api", "software", "calculator", "program"]):
                category = "software_project"
                capabilities = ["code_generation", "planning"]
                complexity = "moderate"
            elif any(word in query_lower for word in ["write", "letter", "email", "story", "poem"]):
                category = "creative_content"
                capabilities = ["creative_writing"]
                complexity = "simple"
            elif any(word in query_lower for word in ["folder", "directory", "file"]):
                category = "file_operation"
                capabilities = ["file_operations"]
                complexity = "simple"
            else:
                category = "conversation"
                capabilities = ["conversation"]
                complexity = "simple"
            
            return {
                "intent": f"User wants to {query}",
                "complexity": complexity,
                "category": category,
                "required_capabilities": capabilities,
                "estimated_tasks": 1 if complexity == "simple" else 3,
                "deliverables": ["requested output"],
                "suggested_approach": f"Handle as {category} via AIL",
                "reasoning": "AIL-enhanced analysis with pattern matching",
                "ail_powered": True
            }
            
        except Exception as e:
            print(f"⚠️  Failed to convert AIL result: {e}")
            return self._fallback_analysis(query)
    
    async def _direct_llm_analysis(self, query: str) -> Dict[str, Any]:
        """Direct LLM analysis as fallback"""
        
        analysis_prompt = f"""
Analyze this user request and provide a structured analysis:

USER REQUEST: "{query}"

Provide analysis in this JSON format:
{{
    "intent": "primary goal of the request",
    "complexity": "simple|moderate|complex",
    "category": "creative_content|software_project|file_operation|conversation|data_task|other", 
    "required_capabilities": ["capability1", "capability2"],
    "estimated_tasks": 1-10,
    "deliverables": ["what should be created/delivered"],
    "suggested_approach": "how this should be handled",
    "reasoning": "why this approach makes sense"
}}

Available capabilities: {[cap.value for cap in AgentCapability]}

Be intelligent about categorization:
- "write a letter" = creative_content + simple
- "create a web app" = software_project + complex  
- "create folder" = file_operation + simple
- "explain quantum physics" = conversation + simple
- "analyze this data" = data_task + moderate
"""

        try:
            response = await self.llm_client.generate(
                prompt=analysis_prompt,
                agent_type=AgentType.COORDINATOR,
                temperature=0.1
            )
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                print(f"📊 Analysis: {analysis['category']} - {analysis['complexity']} - {analysis['intent']}")
                return analysis
            else:
                # Fallback analysis
                return self._fallback_analysis(query)
                
        except Exception as e:
            print(f"⚠️  Analysis failed: {e}, using fallback")
            return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback analysis using simple heuristics"""
        
        query_lower = query.lower()
        
        # Simple pattern matching - prioritize software development over simple file operations
        if any(word in query_lower for word in ["app", "application", "website", "api", "software", "calculator", "program"]):
            category = "software_project" 
            capabilities = ["code_generation", "planning"]
        elif any(word in query_lower for word in ["write", "letter", "email", "story", "poem"]):
            category = "creative_content"
            capabilities = ["creative_writing"]
        elif any(word in query_lower for word in ["folder", "directory"]) and not any(word in query_lower for word in ["app", "application", "calculator"]):
            category = "file_operation"
            capabilities = ["file_operations"]
        elif "file" in query_lower and not any(word in query_lower for word in ["app", "application", "calculator", "code"]):
            category = "file_operation" 
            capabilities = ["file_operations"]
        else:
            category = "conversation"
            capabilities = ["conversation"]
        
        complexity = "simple" if len(query.split()) < 10 else "moderate"
        
        return {
            "intent": f"User wants to {query}",
            "complexity": complexity,
            "category": category,
            "required_capabilities": capabilities,
            "estimated_tasks": 1,
            "deliverables": ["requested output"],
            "suggested_approach": f"Handle as {category}",
            "reasoning": "Pattern-based fallback analysis"
        }
    
    async def _handle_simple_request(self, query: str, analysis: Dict[str, Any], workspace: str) -> Dict[str, Any]:
        """Handle simple requests with single agent assignment"""
        
        print(f"⚡ Handling simple request: {analysis['category']}")
        
        # Find best agent for this request
        best_agent = self._select_best_agent(analysis["required_capabilities"])
        
        if not best_agent:
            return {
                "success": False,
                "error": f"No suitable agent found for capabilities: {analysis['required_capabilities']}"
            }
        
        print(f"🤖 Assigned to: {best_agent.name}")
        
        # Execute with the selected agent
        result = await self._execute_with_agent(best_agent, query, analysis, workspace)
        
        # Extract the actual response content from the result
        response_content = ""
        if result.get("success") and "content" in result:
            response_content = result["content"]
        elif result.get("success") and "response" in result:
            response_content = result["response"]
        elif result.get("success") and "result" in result:
            response_content = str(result["result"])
        else:
            response_content = str(result)
        
        return {
            "success": result.get("success", True),
            "approach": "simple_single_agent",
            "assigned_agent": best_agent.name,
            "agent_type": best_agent.name,
            "category": analysis.get("category"),
            "complexity": analysis.get("complexity"),
            "analysis": analysis,
            "result": result,
            "response": response_content,
            "files_created": result.get("files_created", []),
            "execution_steps": [f"Analyzed query", f"Selected {best_agent.name}", "Executed task"]
        }
    
    async def _handle_complex_request(self, query: str, analysis: Dict[str, Any], workspace: str) -> Dict[str, Any]:
        """Handle complex requests with multi-agent coordination"""
        
        print(f"🏗️  Handling complex request: {analysis['category']}")
        
        # Step 1: Create detailed task plan
        task_plan = await self._create_task_plan(query, analysis)
        
        # Step 2: Assign agents to tasks
        assignments = self._assign_agents_to_tasks(task_plan)
        
        # Step 3: Execute tasks in optimal order
        results = await self._execute_task_assignments(assignments, workspace)
        
        return {
            "success": True,
            "approach": "multi_agent_coordination",
            "task_plan": task_plan,
            "assignments": [{"task": a.description, "agents": a.assigned_agents} for a in assignments],
            "results": results,
            "analysis": analysis
        }
    
    async def _create_task_plan(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use AI to create a detailed task breakdown"""
        
        planning_prompt = f"""
Break down this complex request into specific tasks:

USER REQUEST: "{query}"
ANALYSIS: {json.dumps(analysis, indent=2)}

Create a task breakdown in JSON format:
{{
    "tasks": [
        {{
            "id": "task_1",
            "description": "specific task description",
            "required_capabilities": ["capability1", "capability2"],
            "priority": 1-10,
            "estimated_duration": seconds,
            "dependencies": ["task_id1", "task_id2"],
            "deliverables": ["what this task produces"]
        }}
    ]
}}

Make tasks specific and actionable. Each task should have clear deliverables.
Available capabilities: {[cap.value for cap in AgentCapability]}
"""

        try:
            response = await self.llm_client.generate(
                prompt=planning_prompt,
                agent_type=AgentType.PLANNING,
                temperature=0.2
            )
            
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                task_plan = json.loads(json_match.group())
                print(f"📋 Created plan with {len(task_plan['tasks'])} tasks")
                return task_plan["tasks"]
            else:
                return self._create_simple_task_plan(query, analysis)
                
        except Exception as e:
            print(f"⚠️  Task planning failed: {e}, using simple plan")
            return self._create_simple_task_plan(query, analysis)
    
    def _create_simple_task_plan(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a simple fallback task plan"""
        
        return [{
            "id": "main_task",
            "description": f"Complete: {query}",
            "required_capabilities": analysis["required_capabilities"],
            "priority": 5,
            "estimated_duration": 120.0,
            "dependencies": [],
            "deliverables": analysis["deliverables"]
        }]
    
    def _select_best_agent(self, required_capabilities: List[str]) -> Optional[AgentProfile]:
        """Select the best agent for the required capabilities"""
        
        # Convert string capabilities to enum
        cap_enums = []
        for cap_str in required_capabilities:
            try:
                cap_enums.append(AgentCapability(cap_str))
            except ValueError:
                continue
        
        if not cap_enums:
            return None
        
        # Score agents based on capability match and availability
        scored_agents = []
        
        for agent in self.available_agents.values():
            # Check if agent has required capabilities
            matching_caps = len(set(cap_enums) & set(agent.capabilities))
            total_required = len(cap_enums)
            
            if matching_caps == 0:
                continue
            
            # Calculate score
            capability_score = matching_caps / total_required
            availability_score = max(0, (agent.max_concurrent_tasks - agent.current_tasks) / agent.max_concurrent_tasks)
            performance_score = agent.success_rate
            
            total_score = (capability_score * 0.5) + (availability_score * 0.3) + (performance_score * 0.2)
            
            scored_agents.append((total_score, agent))
        
        # Return best agent
        if scored_agents:
            # Sort by score only (first element of tuple) to avoid AgentProfile comparison
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            return scored_agents[0][1]
        
        return None
    
    def _assign_agents_to_tasks(self, tasks: List[Dict[str, Any]]) -> List[TaskAssignment]:
        """Assign optimal agents to each task"""
        
        assignments = []
        
        for task in tasks:
            # Find best agents for this task
            required_caps = [cap for cap in task["required_capabilities"] if cap in [c.value for c in AgentCapability]]
            best_agent = self._select_best_agent(required_caps)
            
            if best_agent:
                assignment = TaskAssignment(
                    task_id=task["id"],
                    description=task["description"],
                    assigned_agents=[best_agent.name],
                    required_capabilities=[AgentCapability(cap) for cap in required_caps if cap in [c.value for c in AgentCapability]],
                    priority=task.get("priority", 5),
                    estimated_duration=task.get("estimated_duration", 60.0)
                )
                assignment.dependencies = task.get("dependencies", [])
                assignments.append(assignment)
                
                # Update agent load
                best_agent.current_tasks += 1
        
        return assignments
    
    async def _execute_with_agent(self, agent: AgentProfile, query: str, analysis: Dict[str, Any], workspace: str) -> Dict[str, Any]:
        """
        Execute a request with a specific agent using proper AIL communication.
        This enforces agent↔agent communication via AIL instead of direct LLM calls.
        """
        
        print(f"🔤 Converting to AIL for agent: {agent.name}")
        
        # Translate user request to AIL instruction based on agent capabilities
        ail_instruction = self._translate_to_ail_instruction(
            agent_name=agent.name,
            task_description=query,
            metadata={
                "workspace": workspace,
                "category": analysis.get("category"),
                "complexity": analysis.get("complexity")
            }
        )
        
        # Execute via AgentOS Kernel (proper AIL communication)
        ail_result = await self._execute_ail_instruction(
            ail_instruction=ail_instruction,
            context={
                "agent_name": agent.name,
                "capabilities": [cap.value for cap in agent.capabilities],
                "workspace": workspace,
                "user_query": query,
                "analysis": analysis
            }
        )
        
        if not ail_result["success"]:
            # If AIL execution failed, fall back to capability-specific handlers
            print(f"⚠️  AIL execution failed, falling back to direct handlers")
            return await self._fallback_to_direct_execution(agent, query, analysis, workspace)
        
        # Process AIL result for user consumption (translate back to natural language)
        return await self._process_ail_result_for_user(ail_result, agent, query, workspace)
    
    async def _fallback_to_direct_execution(self, agent: AgentProfile, query: str, analysis: Dict[str, Any], workspace: str) -> Dict[str, Any]:
        """Fallback to direct execution when AIL is not available"""
        
        # Route to appropriate handler based on agent capabilities
        if AgentCapability.CREATIVE_WRITING in agent.capabilities:
            return await self._execute_creative_writing(query, workspace)
        elif AgentCapability.FILE_OPERATIONS in agent.capabilities:
            return await self._execute_file_operation(query, workspace)
        elif AgentCapability.CODE_GENERATION in agent.capabilities:
            return await self._execute_code_generation(query, workspace)
        elif AgentCapability.CONVERSATION in agent.capabilities:
            return await self._execute_conversation(query)
        elif AgentCapability.PLANNING in agent.capabilities or AgentCapability.ANALYSIS in agent.capabilities:
            return await self._execute_analysis_planning(query, workspace)
        else:
            return {"success": False, "error": f"No handler for agent {agent.name}"}
    
    async def _process_ail_result_for_user(self, ail_result: Dict[str, Any], agent: AgentProfile, query: str, workspace: str) -> Dict[str, Any]:
        """Process AIL execution result and format for user consumption (natural language)"""
        
        try:
            result_data = ail_result.get("result", {})
            
            # Handle different types of AIL results
            if isinstance(result_data, dict):
                if "content" in result_data:
                    content = result_data["content"]
                elif "response" in result_data:
                    content = result_data["response"]
                else:
                    content = str(result_data)
            else:
                content = str(result_data)
            
            # Create files if this was a content creation task
            files_created = []
            if AgentCapability.CREATIVE_WRITING in agent.capabilities or AgentCapability.CODE_GENERATION in agent.capabilities:
                files_created = await self._save_content_to_file(content, query, workspace)
            
            return {
                "success": True,
                "content": content,
                "response": content,
                "ail_execution": True,
                "cognition_id": ail_result.get("cognition_id"),
                "execution_time_ms": ail_result.get("execution_time_ms", 0),
                "operation_type": ail_result.get("operation_type"),
                "files_created": files_created,
                "agent_name": agent.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process AIL result: {e}",
                "raw_ail_result": ail_result
            }
    
    async def _execute_creative_writing(self, query: str, workspace: str) -> Dict[str, Any]:
        """Execute creative writing task"""
        
        # Get LANS context for the creative writer
        lans_context = LANSContext.get_agent_context("creative_writer", AgentType.CREATIVE_AGENT)
        
        writing_prompt = f"""
{lans_context}

=== CREATIVE WRITING TASK ===
The user has requested: "{query}"

As LANS's creative writing specialist, write the requested content. Be creative, engaging, and fulfill their specific request.
- If it's a letter, make it heartfelt and personal
- If it's a story, make it engaging with good structure  
- If it's an email, make it professional yet warm
- If asked about LANS, you can reference your role as part of the LANS system

Provide ONLY the content they requested, no additional commentary.
"""

        try:
            response = await self.llm_client.generate(
                prompt=writing_prompt,
                agent_type=AgentType.CODING,
                temperature=0.7
            )
            
            content = response.strip()
            
            # Save to file
            import os
            from pathlib import Path
            
            os.makedirs(workspace, exist_ok=True)
            
            # Generate filename from query
            import re
            filename = re.sub(r'[^\w\s-]', '', query.lower())
            filename = re.sub(r'[-\s]+', '_', filename)[:50] + ".txt"
            filepath = Path(workspace) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "content": content,
                "file_path": str(filepath),
                "word_count": len(content.split()),
                "content_type": "creative_writing"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Creative writing failed: {e}"}
    
    async def _execute_file_operation(self, query: str, workspace: str) -> Dict[str, Any]:
        """Execute file operation"""
        
        import os
        from pathlib import Path
        
        try:
            query_lower = query.lower()
            
            if "folder" in query_lower or "directory" in query_lower:
                # Extract folder name - handle various patterns
                words = query.split()
                folder_name = "new_folder"
                
                # Look for patterns like "folder called X", "folder named X", or "folder X"
                for i, word in enumerate(words):
                    if word.lower() in ["folder", "directory"]:
                        # Check if next word is "called" or "named"
                        if i + 2 < len(words) and words[i + 1].lower() in ["called", "named"]:
                            folder_name = words[i + 2]
                            break
                        # Or direct pattern "folder X"
                        elif i + 1 < len(words) and words[i + 1].lower() not in ["called", "named"]:
                            folder_name = words[i + 1]
                            break
                
                folder_path = Path(workspace) / folder_name
                os.makedirs(folder_path, exist_ok=True)
                
                return {
                    "success": True,
                    "operation": "create_folder",
                    "folder_path": str(folder_path)
                }
            
            elif "file" in query_lower:
                # Extract filename - handle various patterns
                words = query.split()
                filename = "new_file.txt"
                
                # Look for patterns like "file called X", "file named X", or "file X"
                for i, word in enumerate(words):
                    if word.lower() == "file":
                        # Check if next word is "called" or "named"
                        if i + 2 < len(words) and words[i + 1].lower() in ["called", "named"]:
                            filename = words[i + 2]
                            break
                        # Or direct pattern "file X"
                        elif i + 1 < len(words) and words[i + 1].lower() not in ["called", "named"]:
                            filename = words[i + 1]
                            break
                
                if not "." in filename:
                    filename += ".txt"
                
                os.makedirs(workspace, exist_ok=True)
                file_path = Path(workspace) / filename
                
                # Generate simple content
                content = f"# {filename}\n\nCreated by LANS on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "operation": "create_file", 
                    "file_path": str(file_path),
                    "content_preview": content[:100]
                }
            
            else:
                return {"success": False, "error": "Unknown file operation"}
                
        except Exception as e:
            return {"success": False, "error": f"File operation failed: {e}"}
    
    async def _execute_code_generation(self, query: str, workspace: str) -> Dict[str, Any]:
        """Execute code generation task"""
        
        # Get LANS context for the code architect
        lans_context = LANSContext.get_agent_context("code_architect", AgentType.CODING)
        
        code_prompt = f"""
{lans_context}

=== CODE GENERATION TASK ===
The user has requested: "{query}"

As LANS's code architect, create a complete, working application based on their request. You should:

1. Create the main application file with complete functionality
2. Include proper error handling and user-friendly interface
3. Add comments explaining the code
4. Make it executable and ready to run

For a calculator app, create a Python script that:
- Has a simple command-line interface
- Supports basic arithmetic operations (add, subtract, multiply, divide)
- Handles user input validation and errors
- Has a clean, user-friendly interface

Provide ONLY the complete Python code, no additional commentary or markdown formatting.
"""

        try:
            response = await self.llm_client.generate(
                prompt=code_prompt,
                agent_type=AgentType.CODING,
                temperature=0.1  # Lower temperature for more consistent code
            )
            
            if response:
                # Determine file name and extension based on query
                import re
                from pathlib import Path
                
                # Extract app name or use default
                app_name = "calculator"
                if "calculator" in query.lower():
                    app_name = "calculator"
                elif "app" in query.lower():
                    # Try to extract app name
                    words = query.lower().split()
                    for i, word in enumerate(words):
                        if word == "app" and i > 0:
                            app_name = words[i-1]
                            break
                
                filename = f"{app_name}.py"
                filepath = Path(workspace) / filename
                
                # Ensure we have valid Python code
                if "def " in response or "import " in response or "print(" in response:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(response)
                    
                    # Make it executable
                    import stat
                    filepath.chmod(filepath.stat().st_mode | stat.S_IEXEC)
                    
                    return {
                        "success": True,
                        "code_file": str(filepath),
                        "filename": filename,
                        "lines_of_code": len(response.split('\n')),
                        "content_type": "python_application",
                        "executable": True
                    }
                else:
                    return {"success": False, "error": "Generated content doesn't appear to be valid code"}
            else:
                return {"success": False, "error": "Failed to generate code"}
                
        except Exception as e:
            return {"success": False, "error": f"Code generation failed: {e}"}
    
    async def _execute_conversation(self, query: str) -> Dict[str, Any]:
        """Execute conversational response"""
        
        conversation_prompt = f"""
You are LANS, a helpful AI assistant. The user has asked: "{query}"

Provide a helpful, informative, and friendly response. Be conversational but professional.
"""

        try:
            response = await self.llm_client.generate(
                prompt=conversation_prompt,
                agent_type=AgentType.COORDINATOR,
                temperature=0.6
            )
            
            return {
                "success": True,
                "response": response.strip(),
                "type": "conversation"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Conversation failed: {e}"}
    
    async def _execute_analysis_planning(self, query: str, workspace: str) -> Dict[str, Any]:
        """Execute analysis and planning tasks"""
        
        planning_prompt = f"""
You are a strategic planning and analysis expert. The user has requested: "{query}"

Provide a thorough analysis and explanation. If it's about system evolution or technical concepts,
give detailed insights with concrete examples. Be informative and well-structured.

Focus on delivering valuable information and insights that directly address their request.
"""

        try:
            response = await self.llm_client.generate(
                prompt=planning_prompt,
                agent_type=AgentType.COORDINATOR,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            if response:
                # For complex analysis, save to file
                import re
                from pathlib import Path
                from datetime import datetime
                
                # Create filename from query
                filename = re.sub(r'[^\w\s-]', '', query).strip()
                filename = re.sub(r'[-\s]+', '_', filename)[:50] + "_analysis.txt"
                filepath = Path(workspace) / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response)
                
                return {
                    "success": True,
                    "analysis": response,
                    "file_path": str(filepath),
                    "word_count": len(response.split()),
                    "content_type": "analysis_planning"
                }
            else:
                return {"success": False, "error": "Failed to generate analysis"}
                
        except Exception as e:
            return {"success": False, "error": f"Analysis planning failed: {e}"}
    
    async def _execute_task_assignments(self, assignments: List[TaskAssignment], workspace: str) -> List[Dict[str, Any]]:
        """Execute multiple task assignments in optimal order"""
        
        # For now, execute sequentially
        # TODO: Implement proper dependency resolution and parallel execution
        
        results = []
        
        for assignment in assignments:
            print(f"🔄 Executing: {assignment.description}")
            
            # Find agent profile
            agent_name = assignment.assigned_agents[0] if assignment.assigned_agents else None
            agent = self.available_agents.get(agent_name)
            
            if agent:
                # Create a simple query for this task
                task_query = assignment.description
                analysis = {"category": "task_execution"}
                
                result = await self._execute_with_agent(agent, task_query, analysis, workspace)
                result["task_id"] = assignment.task_id
                result["assigned_agent"] = agent_name
                results.append(result)
                
                # Update assignment status
                assignment.status = "completed" if result.get("success") else "failed"
                assignment.outputs = result
                
                # Update agent load
                agent.current_tasks = max(0, agent.current_tasks - 1)
            else:
                results.append({
                    "success": False,
                    "error": f"Agent {agent_name} not found",
                    "task_id": assignment.task_id
                })
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        
        agent_status = {}
        for name, agent in self.available_agents.items():
            agent_status[name] = {
                "capabilities": [cap.value for cap in agent.capabilities],
                "current_tasks": agent.current_tasks,
                "max_tasks": agent.max_concurrent_tasks,
                "success_rate": agent.success_rate,
                "specialties": agent.specialties
            }
        return {
            "agents": agent_status,
            "active_assignments": len(self.active_assignments),
            "completed_assignments": len(self.completed_assignments),
            "total_agents": len(self.available_agents)
        }
    
    def _translate_to_ail_instruction(self, agent_name: str, task_description: str, metadata: Dict[str, Any] = None) -> str:
        """
        Translate a natural language task into proper AIL instruction.
        This enforces the architecture principle: agent↔agent communication uses AIL.
        """
        
        # Determine the appropriate AIL operation based on agent type and task
        # Order matters - more specific patterns first!
        
        if any(word in task_description.lower() for word in ["script", "code", "app", "calculator", "website", "program", "python", "javascript", "function"]):
            # Code generation task - use proper AIL format with tool entity
            ail_instruction = f'(EXECUTE [code_generator] ["{task_description}"])'
            
        elif any(word in task_description.lower() for word in ["write", "letter", "email", "story", "creative"]):
            # Creative writing task - use proper AIL format with tool entity  
            ail_instruction = f'(EXECUTE [creative_writer] ["{task_description}"])'
            
        elif any(word in task_description.lower() for word in ["folder", "directory"]) and not any(word in task_description.lower() for word in ["script", "code", "app"]):
            # File operation task - ONLY if it's specifically about folders/directories, not code
            dir_name = task_description.replace("create a directory named ", "").replace("create folder called ", "").replace("Create folder called ", "").replace("Create a folder called ", "").strip()
            ail_instruction = f'(EXECUTE [shell] ["mkdir -p {dir_name}"])'
            
        elif any(word in task_description.lower() for word in ["plan", "break down", "analyze"]):
            # Planning/analysis task
            goal = metadata.get("goal", task_description) if metadata else task_description
            ail_instruction = f'(PLAN {{"goal": "{goal}"}} (EXECUTE [planner] ["{task_description}"]))'
            
        else:
            # General conversation/query task
            ail_instruction = f'(QUERY {{"intent": "{task_description}"}})'
        
        return ail_instruction
    
    async def _execute_ail_instruction(self, ail_instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an AIL instruction via AgentOS Kernel.
        This is the core of proper agent-to-agent AIL communication.
        """
        
        if not self.agentos_kernel:
            # Fallback to direct LLM if AgentOS not available
            print("⚠️  AgentOS not available, falling back to direct LLM")
            return await self._fallback_execution(ail_instruction, context)
        
        try:
            print(f"🔤 Executing AIL: {ail_instruction}")
            
            # Execute the AIL cognition via AgentOS Kernel
            result = await self.agentos_kernel.execute_cognition(
                ail_code=ail_instruction,
                agent_id=self.agent_id,
                user_id="lans_system",
                context=context or {}
            )
            
            # Store the interaction in GMCP if available
            if self.gmcp_client:
                await self._store_ail_interaction(ail_instruction, result)
            
            return {
                "success": result.success,
                "result": result.result,
                "execution_time_ms": result.execution_time_ms,
                "operation_type": result.operation_type,
                "cognition_id": result.cognition_id
            }
            
        except Exception as e:
            print(f"❌ AIL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ail_instruction": ail_instruction
            }
    
    async def _store_ail_interaction(self, ail_instruction: str, result: Any):
        """Store AIL interaction in GMCP for learning and context"""
        try:
            if self.gmcp_client:
                await self.gmcp_client.store_episodic_memory(
                    content=f"AIL Execution: {ail_instruction}",
                    context={
                        "type": "ail_execution",
                        "instruction": ail_instruction,
                        "success": getattr(result, 'success', False),
                        "operation_type": getattr(result, 'operation_type', 'unknown'),
                        "execution_time_ms": getattr(result, 'execution_time_ms', 0)
                    },
                    importance_score=0.7,
                    memory_type="ail_coordination"
                )
        except Exception as e:
            print(f"⚠️  Failed to store AIL interaction in GMCP: {e}")
    
    async def _fallback_execution(self, ail_instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback execution when AgentOS is not available"""
        
        # Extract the task from AIL instruction for direct LLM execution
        import re
        
        # Try to extract task description from AIL instruction
        task_match = re.search(r'\["([^"]+)"\]', ail_instruction)
        if task_match:
            task_description = task_match.group(1)
        else:
            task_description = ail_instruction
        
        try:
            response = await self.llm_client.generate(
                prompt=f"Complete this task: {task_description}",
                agent_type=AgentType.COORDINATOR,
                temperature=0.3
            )
            
            return {
                "success": True,
                "result": response,
                "fallback": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    async def _save_content_to_file(self, content: str, query: str, workspace: str) -> List[str]:
        """Save generated content to file and return file paths"""
        try:
            import os
            import re
            from pathlib import Path
            
            os.makedirs(workspace, exist_ok=True)
            
            # Generate filename from query
            filename = re.sub(r'[^\w\s-]', '', query.lower())
            filename = re.sub(r'[-\s]+', '_', filename)[:50]
            
            # Determine extension based on content type
            if any(word in query.lower() for word in ["code", "app", "calculator", "program"]):
                if "python" in content.lower() or "def " in content:
                    filename += ".py"
                elif "html" in content.lower() or "<html" in content:
                    filename += ".html"
                elif "javascript" in content.lower() or "function " in content:
                    filename += ".js"
                else:
                    filename += ".txt"
            else:
                filename += ".txt"
            
            filepath = Path(workspace) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return [str(filepath)]
            
        except Exception as e:
            print(f"⚠️  Failed to save content to file: {e}")
            return []
