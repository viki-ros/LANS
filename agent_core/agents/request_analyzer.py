"""
Request Analyzer Agent - Analyzes natural language requests
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from ..llm.ollama_client import OllamaClient

@dataclass
class RequestAnalysis:
    """Analysis result of a user request"""
    original_request: str
    request_type: str  # file_creation, folder_creation, code_generation, project_creation, general
    description: str
    language: Optional[str] = None
    target_file: Optional[str] = None
    target_folder: Optional[str] = None
    file_content: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    requirements: List[str] = None
    commands_to_run: List[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.commands_to_run is None:
            self.commands_to_run = []

class RequestAnalyzer:
    """Analyzes user requests to determine intent and extract information"""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm_client = llm_client
    
    async def analyze(self, user_request: str) -> RequestAnalysis:
        """Analyze a user request and return structured analysis"""
        
        analysis_schema = {
            "request_type": "string (one of: file_creation, folder_creation, code_generation, project_creation, general)",
            "description": "string (detailed description of what the user wants)",
            "language": "string (programming language if applicable, null otherwise)",
            "target_file": "string (filename if creating a specific file, null otherwise)",
            "target_folder": "string (folder name if creating a folder, null otherwise)",
            "file_content": "string (simple file content if it can be determined directly, null otherwise)",
            "project_name": "string (project name if creating a project, null otherwise)",
            "project_type": "string (type of project: web_app, cli_tool, desktop_app, etc., null otherwise)",
            "requirements": "array of strings (specific requirements or features)",
            "commands_to_run": "array of strings (commands that should be executed after creation)",
            "confidence": "number (confidence level 0-1)"
        }
        
        analysis_prompt = f"""
        Analyze this user request and extract structured information:
        
        User Request: "{user_request}"
        
        Determine:
        1. What type of request this is (file creation, folder creation, code generation, project creation, or general)
        2. What programming language is involved (if any)
        3. What files or folders should be created
        4. What the content should be (for simple cases)
        5. What commands might need to be run afterward
        
        Examples:
        - "create folder my_project" → folder_creation
        - "create file hello.py with a greeting function" → file_creation
        - "build a calculator app" → project_creation
        - "write a Python script to process CSV files" → code_generation
        - "what is the weather today" → general
        
        Be specific about filenames and include appropriate file extensions.
        For project creation, suggest a reasonable project name and type.
        """
        
        try:
            result = await self.llm_client.generate_structured_response(
                analysis_prompt, 
                analysis_schema
            )
            
            return RequestAnalysis(
                original_request=user_request,
                request_type=result.get("request_type", "general"),
                description=result.get("description", user_request),
                language=result.get("language"),
                target_file=result.get("target_file"),
                target_folder=result.get("target_folder"),
                file_content=result.get("file_content"),
                project_name=result.get("project_name"),
                project_type=result.get("project_type"),
                requirements=result.get("requirements", []),
                commands_to_run=result.get("commands_to_run", []),
                confidence=result.get("confidence", 0.5)
            )
            
        except Exception as e:
            # Fallback to basic analysis
            return self._basic_analysis(user_request)
    
    def _basic_analysis(self, user_request: str) -> RequestAnalysis:
        """Basic fallback analysis when LLM fails"""
        request_lower = user_request.lower()
        
        # Simple pattern matching
        if "create folder" in request_lower or "make folder" in request_lower:
            # Extract folder name
            words = user_request.split()
            folder_name = None
            for i, word in enumerate(words):
                if word.lower() in ["folder", "directory"]:
                    if i + 1 < len(words):
                        folder_name = words[i + 1]
                    break
            
            return RequestAnalysis(
                original_request=user_request,
                request_type="folder_creation",
                description=f"Create folder: {folder_name or 'new_folder'}",
                target_folder=folder_name or "new_folder",
                confidence=0.8
            )
        
        elif "create file" in request_lower or "make file" in request_lower:
            # Extract filename
            words = user_request.split()
            file_name = None
            for i, word in enumerate(words):
                if word.lower() == "file":
                    if i + 1 < len(words):
                        file_name = words[i + 1]
                    break
            
            return RequestAnalysis(
                original_request=user_request,
                request_type="file_creation",
                description=f"Create file: {file_name or 'new_file.txt'}",
                target_file=file_name or "new_file.txt",
                confidence=0.7
            )
        
        elif any(lang in request_lower for lang in ["python", "javascript", "java", "cpp", "rust"]):
            # Code generation request
            language = None
            for lang in ["python", "javascript", "java", "cpp", "rust"]:
                if lang in request_lower:
                    language = lang
                    break
            
            return RequestAnalysis(
                original_request=user_request,
                request_type="code_generation",
                description=user_request,
                language=language,
                confidence=0.6
            )
        
        elif any(word in request_lower for word in ["app", "application", "project", "build", "create"]):
            # Project creation request
            return RequestAnalysis(
                original_request=user_request,
                request_type="project_creation",
                description=user_request,
                project_name="generated_project",
                confidence=0.5
            )
        
        else:
            # General request
            return RequestAnalysis(
                original_request=user_request,
                request_type="general",
                description=user_request,
                confidence=0.3
            )