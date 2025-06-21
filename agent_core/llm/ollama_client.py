"""
Ollama LLM Client for LANS
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
import httpx

from ..core.config import LANSConfig

class OllamaClient:
    """Client for interacting with Ollama LLM server"""
    
    def __init__(self, config: LANSConfig):
        self.config = config
        self.base_url = config.ollama_base_url
        self.model = config.model or config.default_model
        self.client = httpx.AsyncClient(timeout=60.0)
        self.connection_timeout = 60.0  # Default connection timeout
        self.max_retries = 3  # Default retry count
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None, max_retries: int = 3) -> str:
        """Generate a response from the LLM with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                messages = []
                
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                messages.append({"role": "user", "content": prompt})
                
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens,
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["message"]["content"]
                else:
                    last_error = f"Ollama API error: {response.status_code} - {response.text}"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                        continue
                    raise Exception(last_error)
                    
            except httpx.TimeoutException as e:
                last_error = f"Request timeout: {str(e)}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
            except httpx.ConnectError as e:
                last_error = f"Connection error: {str(e)}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                    
        raise Exception(f"Failed to generate response after {max_retries} attempts. Last error: {last_error}")
    
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured JSON response"""
        system_prompt = f"""
        You are a helpful AI assistant. Respond with valid JSON that matches this schema:
        {json.dumps(schema, indent=2)}
        
        Only return the JSON, no additional text or formatting.
        """
        
        response = await self.generate_response(prompt, system_prompt)
        
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: try to parse entire response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\\nResponse: {response}")
    
    async def check_connection(self) -> bool:
        """Check if Ollama server is accessible"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except:
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    def set_connection_timeout(self, timeout_seconds: float):
        """Set the connection timeout for HTTP requests."""
        self.connection_timeout = timeout_seconds
        # Update the httpx client timeout
        self.client = httpx.AsyncClient(timeout=timeout_seconds)
    
    def set_max_retries(self, max_retries: int):
        """Set the maximum number of retries for failed requests."""
        self.max_retries = max_retries
    
    async def health_check(self) -> bool:
        """Check if the Ollama server is available and healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False