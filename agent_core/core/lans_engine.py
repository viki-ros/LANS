"""
LANS Engine - Core processing engine for natural language requests
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import re

from .config import LANSConfig
from .result import LANSResult
from ..llm.ollama_client import OllamaClient
from ..agents.request_analyzer import RequestAnalyzer
from ..agents.code_generator import CodeGenerator
from ..agents.file_manager import FileManager

class LANSEngine:
    """Main LANS processing engine"""
    
    def __init__(self, config: LANSConfig):
        self.config = config
        self.llm_client = OllamaClient(config)
        self.request_analyzer = RequestAnalyzer(self.llm_client)
        self.code_generator = CodeGenerator(self.llm_client)
        self.file_manager = FileManager(config.workspace)
        self.timeout = 30.0  # Default timeout in seconds
        
    async def initialize(self):
        """Initialize the LANS engine and all components."""
        try:
            # Initialize LLM client
            if hasattr(self.llm_client, 'initialize'):
                await self.llm_client.initialize()
            
            # Validate workspace
            if not self.config.workspace.exists():
                self.config.workspace.mkdir(parents=True, exist_ok=True)
            
            # Additional initialization as needed
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LANS engine: {e}")
    
    def set_timeout(self, timeout_seconds: float):
        """Set the timeout for operations."""
        self.timeout = timeout_seconds
        
        # Propagate timeout to components
        if hasattr(self.llm_client, 'set_timeout'):
            self.llm_client.set_timeout(timeout_seconds)
    
    async def process_request(self, user_prompt: str) -> LANSResult:
        """Process a natural language request"""
        start_time = time.time()
        result = LANSResult()
        
        try:
            # Step 1: Analyze the request
            analysis = await self.request_analyzer.analyze(user_prompt)
            
            if self.config.verbose:
                print(f"Analysis: {analysis}")
            
            # Step 2: Generate appropriate response based on request type
            if analysis.request_type == "file_creation":
                await self._handle_file_creation(analysis, result)
            elif analysis.request_type == "folder_creation":
                await self._handle_folder_creation(analysis, result)
            elif analysis.request_type == "code_generation":
                await self._handle_code_generation(analysis, result)
            elif analysis.request_type == "project_creation":
                await self._handle_project_creation(analysis, result)
            else:
                await self._handle_general_request(analysis, result)
            
            # Step 3: Execute any necessary commands
            if analysis.commands_to_run:
                await self._execute_commands(analysis.commands_to_run, result)
            
            result.execution_time = time.time() - start_time
            result.model_used = self.config.model
            
            if not result.error:
                result.set_success()
                
        except Exception as e:
            result.set_error(f"Processing failed: {str(e)}")
            
        return result
    
    async def process_ail_instruction(self, ail_instruction: str) -> LANSResult:
        """Process a raw AIL instruction directly"""
        start_time = time.time()
        result = LANSResult()
        
        try:
            # Try to detect if we have intelligent_coordinator
            try:
                from ..intelligent_coordinator import IntelligentCoordinator
                coordinator = IntelligentCoordinator(self.llm_client)
                # Allow time for the coordinator to initialize
                await asyncio.sleep(2)
                
                # Execute the AIL instruction
                ail_result = await coordinator._execute_ail_instruction(ail_instruction)
                
                if ail_result.get("success", False):
                    result.set_success()
                    result.message = str(ail_result.get("result", "Operation completed"))
                else:
                    result.set_error(f"AIL execution failed: {ail_result.get('error', 'Unknown error')}")
            except (ImportError, AttributeError) as e:
                result.set_error(f"AIL processing not available: {str(e)}")
            
            result.execution_time = time.time() - start_time
            result.model_used = self.config.model
            
        except Exception as e:
            result.set_error(f"AIL processing failed: {str(e)}")
            
        return result
    
    async def _handle_file_creation(self, analysis, result: LANSResult):
        """Handle file creation requests"""
        file_path = self.config.workspace / analysis.target_file
        
        if analysis.file_content:
            # Content provided in analysis
            content = analysis.file_content
        else:
            # Generate content using LLM
            content = await self.code_generator.generate_file_content(
                analysis.target_file, 
                analysis.description
            )
        
        # Create the file
        await self.file_manager.create_file(file_path, content)
        result.add_file_created(file_path)
        result.message = f"Created file: {file_path}"
    
    async def _handle_folder_creation(self, analysis, result: LANSResult):
        """Handle folder creation requests"""
        folder_path = self.config.workspace / analysis.target_folder
        
        # Create the folder
        await self.file_manager.create_directory(folder_path)
        result.add_directory_created(folder_path)
        result.message = f"Created folder: {folder_path}"
    
    async def _handle_code_generation(self, analysis, result: LANSResult):
        """Handle code generation requests"""
        # Generate code based on the request
        generated_code = await self.code_generator.generate_code(
            analysis.language,
            analysis.description,
            analysis.requirements
        )
        
        # Determine file name and extension
        file_name = analysis.target_file or self._generate_filename(analysis)
        file_path = self.config.workspace / file_name
        
        # Create the file with generated code
        await self.file_manager.create_file(file_path, generated_code)
        result.add_file_created(file_path)
        result.message = f"Generated code file: {file_path}"
    
    async def _handle_project_creation(self, analysis, result: LANSResult):
        """Handle full project creation requests"""
        project_name = analysis.project_name or "generated_project"
        project_path = self.config.workspace / project_name
        
        # Generate project structure
        project_structure = await self.code_generator.generate_project(
            analysis.project_type,
            analysis.description,
            analysis.requirements
        )
        
        # Create project directory
        await self.file_manager.create_directory(project_path)
        result.add_directory_created(project_path)
        
        # Create all project files
        for file_path, content in project_structure.items():
            full_path = project_path / file_path
            await self.file_manager.create_file(full_path, content)
            result.add_file_created(full_path)
        
        result.message = f"Created project: {project_path}"
    
    async def _handle_general_request(self, analysis, result: LANSResult):
        """Handle general requests that don't fit other categories"""
        # Generate a response using the LLM
        response = await self.llm_client.generate_response(
            f"User request: {analysis.original_request}\n"
            f"Analysis: {analysis.description}\n"
            f"Please provide a helpful response or suggest what files/code to create."
        )
        
        result.message = response
    
    async def _execute_commands(self, commands: List[str], result: LANSResult):
        """Execute system commands safely"""
        for command in commands:
            if self._is_safe_command(command):
                try:
                    # Execute command
                    process = await asyncio.create_subprocess_shell(
                        command,
                        cwd=self.config.workspace,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    output = stdout.decode() + stderr.decode()
                    
                    result.add_command_executed(command, output)
                    
                except Exception as e:
                    result.add_command_executed(command, f"Error: {str(e)}")
            else:
                result.add_command_executed(command, "Command blocked for security")
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute"""
        if not self.config.sandbox_enabled:
            return True
        
        # Check against allowed commands
        command_parts = command.split()
        if not command_parts:
            return False
        
        base_command = command_parts[0]
        return base_command in self.config.allowed_commands
    
    def _generate_filename(self, analysis) -> str:
        """Generate a filename based on analysis"""
        if analysis.language:
            extensions = {
                "python": ".py",
                "javascript": ".js",
                "typescript": ".ts",
                "html": ".html",
                "css": ".css",
                "java": ".java",
                "cpp": ".cpp",
                "c": ".c",
                "rust": ".rs",
                "go": ".go",
            }
            ext = extensions.get(analysis.language.lower(), ".txt")
        else:
            ext = ".txt"
        
        # Generate name from description
        name = re.sub(r'[^a-zA-Z0-9_]', '_', analysis.description.lower())
        name = re.sub(r'_+', '_', name)[:30]  # Limit length
        
        return f"{name}{ext}"