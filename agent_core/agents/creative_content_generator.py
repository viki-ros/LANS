"""
Creative Content Generator for LANS
Handles requests for letters, stories, documents, and other creative content
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..llm.ollama_client import OllamaClient


class CreativeContentGenerator:
    """
    Specialized agent for generating creative content like letters, stories, documents
    """
    
    def __init__(self, llm_client: OllamaClient, mcp_client=None):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.logger = logging.getLogger(__name__)
        
        # Creative writing prompts and templates
        self.content_templates = {
            "letter": {
                "system_prompt": """You are a skilled creative writer specializing in heartfelt, eloquent letters. 
                Write with emotion, authenticity, and beautiful language. Structure your letters with:
                - A warm, personal greeting
                - Emotional opening that sets the tone
                - Body paragraphs that tell a story or express feelings
                - Specific examples and vivid imagery
                - A meaningful conclusion
                - Appropriate closing and signature
                
                Use rich, expressive language that conveys genuine emotion.""",
                
                "user_prompt_template": """Write {content_description}.
                
                Make it:
                - Heartfelt and genuine
                - Beautifully written with rich language
                - Emotionally resonant
                - Well-structured and flowing
                - Appropriate length for the content
                
                Content request: {user_request}"""
            },
            
            "story": {
                "system_prompt": """You are a talented storyteller who creates engaging, well-crafted narratives.
                Your stories have clear structure, compelling characters, vivid settings, and meaningful themes.
                Use descriptive language, dialogue, and pacing to create immersive experiences.""",
                
                "user_prompt_template": """Create {content_description}.
                
                Include:
                - Engaging opening that hooks the reader
                - Well-developed characters and setting
                - Clear narrative arc with conflict and resolution
                - Vivid descriptions and dialogue
                - Satisfying conclusion
                
                Story request: {user_request}"""
            },
            
            "document": {
                "system_prompt": """You are a professional technical writer who creates clear, well-organized documents.
                Your writing is informative, accessible, and properly structured with headings, sections, and examples.""",
                
                "user_prompt_template": """Create {content_description}.
                
                Make it:
                - Well-organized with clear structure
                - Informative and comprehensive
                - Easy to read and understand
                - Properly formatted
                - Professional in tone
                
                Document request: {user_request}"""
            },
            
            "general": {
                "system_prompt": """You are a versatile creative writer who adapts your style to the specific content requested.
                Write with clarity, creativity, and appropriate tone for the intended purpose and audience.""",
                
                "user_prompt_template": """Create {content_description}.
                
                Requirements:
                - Match the appropriate tone and style
                - Be creative and engaging
                - Structure content logically
                - Use vivid and expressive language
                
                Content request: {user_request}"""
            }
        }
    
    async def generate_content(self, user_request: str, content_type: str = "general", 
                             output_file: Optional[str] = None, workspace_path: str = "./") -> Dict[str, Any]:
        """
        Generate creative content based on user request
        """
        self.logger.info(f"Generating creative content: {content_type}")
        
        try:
            # Get appropriate template
            template = self.content_templates.get(content_type, self.content_templates["general"])
            
            # Prepare prompts
            system_prompt = template["system_prompt"]
            
            # Create content description for template
            content_description = self._create_content_description(user_request, content_type)
            
            user_prompt = template["user_prompt_template"].format(
                content_description=content_description,
                user_request=user_request
            )
            
            self.logger.info(f"Using LLM to generate {content_type} content")
            
            # Generate content using LLM
            from ..models import AgentType
            response = await self.llm_client.generate(
                prompt=f"{system_prompt}\n\nUser Request: {user_prompt}",
                agent_type=AgentType.CREATIVE_AGENT,
                temperature=0.8  # Higher creativity for content generation
            )
            
            generated_content = response
            
            if not generated_content:
                raise Exception("LLM failed to generate content")
            
            # Determine output filename if not provided
            if not output_file:
                output_file = self._generate_filename(user_request, content_type)
            
            # Write content to file if MCP client available
            file_path = f"{workspace_path.rstrip('/')}/{output_file}"
            
            if self.mcp_client:
                await self.mcp_client.write_file(file_path, generated_content)
                self.logger.info(f"Content written to: {file_path}")
            else:
                # Fallback to local file writing
                import os
                os.makedirs(workspace_path, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(generated_content)
                self.logger.info(f"Content written locally to: {file_path}")
            
            return {
                "success": True,
                "content": generated_content,
                "file_path": file_path,
                "content_type": content_type,
                "word_count": len(generated_content.split()),
                "character_count": len(generated_content),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate creative content: {e}")
            return {
                "success": False,
                "error": str(e),
                "content_type": content_type
            }
    
    def _create_content_description(self, user_request: str, content_type: str) -> str:
        """Create a description of what content to generate"""
        if content_type == "letter":
            return "a heartfelt, eloquent letter"
        elif content_type == "story":
            return "an engaging, well-crafted story"
        elif content_type == "document":
            return "a professional, well-organized document"
        else:
            return "creative content"
    
    def _generate_filename(self, user_request: str, content_type: str) -> str:
        """Generate appropriate filename for the content"""
        # Extract key words from request
        words = user_request.lower().split()
        key_words = []
        
        # Look for important words
        important_words = ["letter", "story", "document", "viki", "creator", "gratitude", "lans"]
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) > 3 and (clean_word in important_words or len(key_words) < 3):
                key_words.append(clean_word)
        
        # Create filename
        if key_words:
            filename = "_".join(key_words[:3])
        else:
            filename = content_type
        
        # Add appropriate extension
        extension = ".txt"
        if content_type in ["document", "story"]:
            extension = ".md"
        
        return f"{filename}{extension}"
    
    async def get_content_suggestions(self, partial_request: str) -> List[str]:
        """Get suggestions for content creation based on partial input"""
        suggestions = []
        
        request_lower = partial_request.lower()
        
        if "letter" in request_lower:
            suggestions.extend([
                "write a heartfelt letter to a friend",
                "compose a thank you letter",
                "draft a professional business letter",
                "create a letter of recommendation"
            ])
        
        if "story" in request_lower:
            suggestions.extend([
                "write a short story about adventure",
                "create a science fiction story",
                "compose a children's story",
                "write a mystery story"
            ])
        
        if any(word in request_lower for word in ["document", "report", "guide"]):
            suggestions.extend([
                "create a user guide",
                "write a technical document",
                "draft a project report",
                "compose a how-to guide"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions
