"""
LLM API client for Llama integration
"""
import json
import requests
import time
from typing import List, Dict, Any, Optional
from config.config import config

class LLMClient:
    """Client for Llama LLM API integration"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: str = "https://api.llmapi.com", timeout: int = 120):
        self.api_key = api_key or config.api_key
        self.model = model or config.default_model
        self.base_url = base_url
        self.timeout = timeout  # Increased timeout to 2 minutes
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key:
            raise ValueError("API key is required. Set LLAMA_API_KEY environment variable or pass api_key parameter.")
    
    def _make_request(self, endpoint: str, data: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Make API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 API request attempt {attempt + 1}/{max_retries}")
                response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ API request failed with status {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"⏳ Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return None
                        
            except requests.exceptions.Timeout:
                print(f"⏰ Request timed out (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("❌ All retry attempts failed due to timeout")
                    return None
            except Exception as e:
                print(f"❌ API request error: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return None
        
        return None
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the LLM API
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            API response as dictionary
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = self._make_request("chat/completions", payload)
        if response is None:
            raise Exception("API request failed")
        return response
    
    def edit_document(
        self, 
        text: str, 
        instruction: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Edit a document based on an instruction
        
        Args:
            text: Document text to edit
            instruction: Editing instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Edited text
        """
        messages = [
            {"role": "system", "content": "You are a document editor. Edit the text according to the instruction while preserving the original structure and formatting."},
            {"role": "user", "content": f"Instruction: {instruction}\n\nText to edit:\n{text}"}
        ]
        
        response = self._make_request("chat/completions", {
            "model": self.model, 
            "messages": messages, 
            "temperature": temperature, 
            "max_tokens": max_tokens
        })
        
        if response is None:
            raise Exception("Document editing failed")
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            return content.strip()
        else:
            raise Exception("No content in API response")
    
    def analyze_document(
        self, 
        text: str, 
        analysis_type: str = "general",
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Analyze a document
        
        Args:
            text: Document text to analyze
            analysis_type: Type of analysis
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Analysis results
        """
        analysis_prompts = {
            "general": "Provide a general analysis of this document.",
            "legal": "Provide a legal analysis of this document.",
            "technical": "Provide a technical analysis of this document.",
            "summary": "Provide a concise summary of this document."
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        
        messages = [
            {"role": "system", "content": "You are a document analyst."},
            {"role": "user", "content": f"{prompt}\n\nDocument:\n{text}"}
        ]
        
        response = self._make_request("chat/completions", {
            "model": self.model, 
            "messages": messages, 
            "temperature": temperature, 
            "max_tokens": max_tokens
        })
        
        if response is None:
            raise Exception("Document analysis failed")
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            return content.strip()
        else:
            raise Exception("No content in API response")
    
    def test_connection(self) -> bool:
        """Test API connection with a simple request"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, API is working!' and nothing else."}
            ]
            
            response = self.chat_completion(messages, temperature=0.1, max_tokens=50)
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                return "API is working" in content
            return False
            
        except Exception:
            return False 