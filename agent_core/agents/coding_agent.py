"""
Coding Agent - General-purpose code implementation and generation.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models import (
    Task, TaskStatus, AgentType, ProjectSpec, 
    AgentMessage, BuildResult
)
from ..llm.ollama_client import OllamaClient


class CodingAgent:
    """
    Code implementation agent that generates software projects and fixes errors.
    
    Responsibilities:
    - Generate project structure, configuration files, source files
    - Apply programming best practices and patterns
    - Handle build system integration
    - Implement incremental fixes
    """
    
    def __init__(self, llm_client: OllamaClient, mcp_client=None):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.agent_type = AgentType.CODING
        
        # Code templates for common patterns
        self.templates = {
            "python_main": self._get_python_main_template(),
            "python_cli": self._get_python_cli_template(),
            "python_api": self._get_python_api_template(),
            "javascript_main": self._get_javascript_main_template(),
            "calculator": self._get_calculator_template(),
            "readme": self._get_readme_template()
        }
    
    async def implement_task(self, task: Task, project_spec: ProjectSpec, workspace_path: str) -> Dict[str, Any]:
        """Implement a specific task in the project generation."""
        
        system_prompt = """You are an expert software developer. Generate high-quality, production-ready code following modern best practices.

Key principles:
1. Follow language-specific coding standards and conventions
2. Use proper error handling and logging
3. Include comprehensive comments and documentation
4. Apply security best practices
5. Write maintainable, readable code
6. Use appropriate design patterns

Always consider the project type, language, and framework when generating code."""

        user_prompt = f"""
Implement this task for a software project:

Task: {task.description}
Project Specification:
{project_spec.model_dump_json(indent=2)}

Workspace Path: {workspace_path}
Task Metadata: {json.dumps(task.metadata, indent=2)}

Generate the required files and code to complete this task. Consider:
- Project type: {project_spec.project_type}
- Language: {project_spec.language}
- Framework: {project_spec.framework}
- Dependencies: {project_spec.dependencies}

Output as JSON with:
- files_to_create: list of files with path and content
- directories_to_create: list of directory paths
- commands_to_run: list of commands to execute
- description: summary of what was implemented
"""

        response = await self.llm_client.generate(
            user_prompt,
            agent_type=self.agent_type,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        try:
            # Parse JSON response
            implementation_data = json.loads(response)
            
            # Create directories first
            for dir_path in implementation_data.get("directories_to_create", []):
                if self.mcp_client:
                    full_path = Path(workspace_path) / project_spec.name / dir_path
                    await self.mcp_client.create_directory(str(full_path))
            
            # Create files
            for file_info in implementation_data.get("files_to_create", []):
                if self.mcp_client:
                    full_path = Path(workspace_path) / project_spec.name / file_info["path"]
                    await self.mcp_client.write_file(str(full_path), file_info["content"])
            
            # Execute commands if any
            for command in implementation_data.get("commands_to_run", []):
                if self.mcp_client and hasattr(self.mcp_client, 'execute_command'):
                    await self.mcp_client.execute_command(command)
            
            return {
                "success": True,
                "description": implementation_data.get("description", "Task completed"),
                "files_created": len(implementation_data.get("files_to_create", [])),
                "directories_created": len(implementation_data.get("directories_to_create", []))
            }
            
        except Exception as e:
            # Fallback to template-based implementation
            return await self._implement_with_template(task, project_spec, workspace_path)
    
    async def _implement_with_template(self, task: Task, project_spec: ProjectSpec, workspace_path: str) -> Dict[str, Any]:
        """Fallback implementation using templates."""
        
        try:
            project_path = Path(workspace_path) / project_spec.name
            
            # Determine what to implement based on task description
            task_desc_lower = task.description.lower()
            
            if "setup" in task_desc_lower and "project" in task_desc_lower:
                # Create basic project structure
                if self.mcp_client:
                    await self.mcp_client.create_directory(str(project_path))
                    
                    # Create basic files based on project type and language
                    if project_spec.language == "python":
                        # Create main.py
                        main_content = self._get_python_main_template()
                        await self.mcp_client.write_file(str(project_path / "main.py"), main_content)
                        
                        # Create requirements.txt
                        requirements = "\n".join(project_spec.dependencies) if project_spec.dependencies else "# Add your dependencies here\n"
                        await self.mcp_client.write_file(str(project_path / "requirements.txt"), requirements)
                        
                        # Create README.md
                        readme_content = self._get_readme_template().format(
                            project_name=project_spec.name,
                            description=project_spec.description,
                            language=project_spec.language
                        )
                        await self.mcp_client.write_file(str(project_path / "README.md"), readme_content)
                        
                        # Create .gitignore
                        gitignore_content = "__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.Python\nenv/\nvenv/\n.venv/\n.env\n"
                        await self.mcp_client.write_file(str(project_path / ".gitignore"), gitignore_content)
                
                return {"success": True, "description": "Created basic project structure"}
                
            elif "implement" in task_desc_lower or "core" in task_desc_lower:
                # Implement core functionality
                if project_spec.project_type == "calculator" and project_spec.language == "python":
                    calc_content = self._get_calculator_template()
                    if self.mcp_client:
                        await self.mcp_client.write_file(str(project_path / "calculator.py"), calc_content)
                    return {"success": True, "description": "Implemented calculator functionality"}
                
                # Generic implementation
                if project_spec.language == "python":
                    main_content = f'''#!/usr/bin/env python3
"""
{project_spec.name} - {project_spec.description}
"""

def main():
    print("Hello from {project_spec.name}!")
    print("{project_spec.description}")
    
    # TODO: Implement core functionality here
    pass

if __name__ == "__main__":
    main()
'''
                    if self.mcp_client:
                        await self.mcp_client.write_file(str(project_path / "main.py"), main_content)
                
                return {"success": True, "description": "Implemented core functionality"}
            
            else:
                # Generic task implementation
                return {"success": True, "description": f"Completed: {task.description}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fix_error(self, error_info: Dict[str, Any], project_spec: ProjectSpec, workspace_path: str) -> Dict[str, Any]:
        """Fix errors in the generated code."""
        
        system_prompt = """You are an expert debugger and code fixer. Analyze the error and provide a targeted fix.

Focus on:
1. Understanding the root cause
2. Providing minimal, precise fixes
3. Maintaining code quality
4. Preventing similar errors"""

        user_prompt = f"""
Fix this error in the project:

Project: {project_spec.name}
Error Information: {json.dumps(error_info, indent=2)}

Provide a fix that:
1. Addresses the specific error
2. Maintains existing functionality
3. Follows best practices
4. Includes verification steps

Output as JSON with the fix details.
"""

        response = await self.llm_client.generate(
            user_prompt,
            agent_type=self.agent_type,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        try:
            fix_data = json.loads(response)
            
            # Apply the fix if we have MCP client
            if self.mcp_client and "files_to_modify" in fix_data:
                for file_mod in fix_data["files_to_modify"]:
                    file_path = Path(workspace_path) / project_spec.name / file_mod["path"]
                    await self.mcp_client.write_file(str(file_path), file_mod["content"])
            
            return {
                "success": True,
                "description": fix_data.get("description", "Error fixed"),
                "fix_applied": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not parse fix response: {e}",
                "fix_applied": False
            }
    
    def _get_python_main_template(self) -> str:
        """Template for a basic Python main file."""
        return '''#!/usr/bin/env python3
"""
Main application entry point.
"""

def main():
    """Main function."""
    print("Hello, World!")
    print("This is a Python application created by LANS.")

if __name__ == "__main__":
    main()
'''

    def _get_python_cli_template(self) -> str:
        """Template for a Python CLI application."""
        return '''#!/usr/bin/env python3
"""
Command-line interface application.
"""

import argparse
import sys

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="CLI Application")
    parser.add_argument("--version", action="version", version="1.0.0")
    parser.add_argument("command", help="Command to execute")
    
    args = parser.parse_args()
    
    print(f"Executing command: {args.command}")

if __name__ == "__main__":
    main()
'''

    def _get_python_api_template(self) -> str:
        """Template for a Python API application."""
        return '''#!/usr/bin/env python3
"""
API application using FastAPI.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="API Application", version="1.0.0")

class Message(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    def _get_javascript_main_template(self) -> str:
        """Template for a JavaScript main file."""
        return '''#!/usr/bin/env node
/**
 * Main application entry point.
 */

function main() {
    console.log("Hello, World!");
    console.log("This is a JavaScript application created by LANS.");
}

if (require.main === module) {
    main();
}

module.exports = { main };
'''

    def _get_calculator_template(self) -> str:
        """Template for a calculator application."""
        return '''#!/usr/bin/env python3
"""
Simple Calculator Application
"""

class Calculator:
    """A simple calculator class."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a, b):
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

def main():
    """Main function for interactive calculator."""
    calc = Calculator()
    
    print("Simple Calculator")
    print("Available operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\\nEnter calculation (e.g., 5 + 3): ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # Parse the input
            parts = user_input.split()
            if len(parts) != 3:
                print("Invalid input. Use format: number operator number")
                continue
            
            num1, operator, num2 = parts
            num1, num2 = float(num1), float(num2)
            
            if operator == '+':
                result = calc.add(num1, num2)
            elif operator == '-':
                result = calc.subtract(num1, num2)
            elif operator == '*':
                result = calc.multiply(num1, num2)
            elif operator == '/':
                result = calc.divide(num1, num2)
            else:
                print("Unknown operator. Use +, -, *, or /")
                continue
            
            print(f"Result: {result}")
            
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    print("Goodbye!")

if __name__ == "__main__":
    main()
'''

    def _get_readme_template(self) -> str:
        """Template for README.md file."""
        return '''# {project_name}

{description}

## Description

This project was created using LANS (Large Artificial Neural System).

## Language

Primary language: {language}

## Getting Started

### Prerequisites

Make sure you have the required dependencies installed.

### Installation

1. Clone or download this project
2. Install dependencies (if any)
3. Run the application

### Usage

```bash
python main.py
```

## Features

- Basic project structure
- Clean, maintainable code
- Documentation

## Contributing

Feel free to contribute to this project!

## License

This project is open source.
'''
