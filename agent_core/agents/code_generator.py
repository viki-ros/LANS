"""
Code Generator Agent - Generates code based on requirements
"""

from typing import Dict, List
from ..llm.ollama_client import OllamaClient

class CodeGenerator:
    """Generates code and project structures"""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm_client = llm_client
    
    async def generate_file_content(self, filename: str, description: str) -> str:
        """Generate content for a specific file"""
        
        # Determine file type from extension
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        system_prompt = """
        You are an expert programmer. Generate clean, well-documented code.
        Always include appropriate comments and follow best practices.
        """
        
        prompt = f"""
        Create content for a file named "{filename}" with this description: {description}
        
        File extension: {file_ext}
        
        Requirements:
        - Write clean, readable code
        - Include appropriate comments
        - Follow best practices for the language
        - Make it functional and complete
        - If it's a configuration file, use appropriate format
        
        Only return the file content, no additional explanation.
        """
        
        return await self.llm_client.generate_response(prompt, system_prompt)
    
    async def generate_code(self, language: str, description: str, requirements: List[str]) -> str:
        """Generate code in a specific language"""
        
        system_prompt = f"""
        You are an expert {language} programmer. Write clean, efficient, and well-documented code.
        Follow {language} best practices and conventions.
        """
        
        requirements_text = "\\n".join(f"- {req}" for req in requirements) if requirements else "No specific requirements"
        
        prompt = f"""
        Write {language} code for: {description}
        
        Requirements:
        {requirements_text}
        
        Guidelines:
        - Write clean, readable code
        - Include docstrings/comments
        - Handle errors appropriately
        - Follow language conventions
        - Make it production-ready
        
        Only return the code, no additional explanation.
        """
        
        return await self.llm_client.generate_response(prompt, system_prompt)
    
    async def generate_project(self, project_type: str, description: str, requirements: List[str]) -> Dict[str, str]:
        """Generate a complete project structure"""
        
        system_prompt = """
        You are an expert software architect. Create complete, production-ready project structures.
        Always include proper configuration files, documentation, and best practices.
        """
        
        requirements_text = "\\n".join(f"- {req}" for req in requirements) if requirements else "No specific requirements"
        
        prompt = f"""
        Create a complete {project_type} project for: {description}
        
        Requirements:
        {requirements_text}
        
        Generate a project structure with:
        - Main application files
        - Configuration files (package.json, requirements.txt, etc.)
        - README.md with setup instructions
        - Basic tests if applicable
        - Proper folder structure
        
        Return the response as a JSON object where keys are file paths and values are file contents.
        Example:
        {{
            "main.py": "# Main application file\\nprint('Hello World')",
            "requirements.txt": "requests>=2.25.0",
            "README.md": "# Project Title\\n\\nDescription..."
        }}
        
        Only return the JSON, no additional text.
        """
        
        try:
            response = await self.llm_client.generate_response(prompt, system_prompt)
            
            # Try to parse as JSON
            import json
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: create basic structure
                return self._create_basic_project(project_type, description)
                
        except Exception as e:
            # Fallback to basic project structure
            return self._create_basic_project(project_type, description)
    
    def _create_basic_project(self, project_type: str, description: str) -> Dict[str, str]:
        """Create a basic project structure as fallback"""
        
        if project_type in ["web_app", "react", "frontend"]:
            return {
                "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description}</title>
</head>
<body>
    <div id="app">
        <h1>{description}</h1>
        <p>Welcome to your new web application!</p>
    </div>
    <script src="script.js"></script>
</body>
</html>""",
                "script.js": f"""// {description}
console.log('Application started');

// Add your JavaScript code here
document.addEventListener('DOMContentLoaded', function() {{
    console.log('DOM loaded');
}});""",
                "style.css": f"""/* {description} Styles */
body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}}

#app {{
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}""",
                "README.md": f"""# {description}

A web application created with LANS.

## Setup

1. Open `index.html` in your browser
2. Start developing!

## Features

- Basic HTML structure
- JavaScript functionality
- CSS styling
"""
            }
        
        elif project_type in ["python", "cli_tool", "script"]:
            return {
                "main.py": f"""#!/usr/bin/env python3
\"\"\"
{description}
\"\"\"

def main():
    \"\"\"Main function\"\"\"
    print("Welcome to {description}")
    # Add your code here

if __name__ == "__main__":
    main()
""",
                "requirements.txt": """# Add your dependencies here
# requests>=2.25.0
# click>=8.0.0
""",
                "README.md": f"""# {description}

A Python application created with LANS.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Usage

Run the application:
```bash
python main.py
```
"""
            }
        
        else:
            # Generic project
            return {
                "main.txt": f"# {description}\\n\\nThis is your new project created with LANS.",
                "README.md": f"""# {description}

A project created with LANS.

## Description

{description}

## Getting Started

1. Review the generated files
2. Customize as needed
3. Start building!
"""
            }