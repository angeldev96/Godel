"""
Multi-provider LLM API client supporting Llama and OpenAI
"""
import json
import requests
import time
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
from config.config import config, LLMProvider

# Import OpenAI SDK if available
try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageParam
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam
else:
    ChatCompletionMessageParam = Any

class LLMClient:
    """Unified client for multiple LLM providers"""
    
    def __init__(self, provider: LLMProvider, api_key: Optional[str] = None, 
                 model: Optional[str] = None, base_url: Optional[str] = None, 
                 timeout: int = 120):
        self.provider = provider
        self.api_key = api_key or config.get_api_key(provider)
        self.model = model or config.default_models[provider]
        self.base_url = base_url or config.get_api_base_url(provider)
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError(f"API key is required for {provider.value}. Set {provider.value.upper()}_API_KEY environment variable or pass api_key parameter.")
        
        # Set up headers based on provider
        if provider == LLMProvider.OPENAI:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:  # Llama
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
    
    def _make_request(self, endpoint: str, data: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Make API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 {self.provider.value.title()} API request attempt {attempt + 1}/{max_retries}")
                response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ {self.provider.value.title()} API request failed with status {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"⏳ Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return None
                        
            except requests.exceptions.Timeout:
                print(f"⏰ {self.provider.value.title()} request timed out (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All retry attempts failed due to timeout for {self.provider.value}")
                    return None
            except Exception as e:
                print(f"❌ {self.provider.value.title()} API request error: {e}")
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
            raise Exception(f"{self.provider.value.title()} API request failed")
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
            raise Exception(f"Document editing failed with {self.provider.value}")
        
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
            raise Exception(f"Document analysis failed with {self.provider.value}")
        
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

class OpenAIClient:
    """Client for OpenAI using the official openai Python SDK"""
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if not OPENAI_SDK_AVAILABLE:
            raise ImportError("openai package is not installed. Please install it with 'pip install openai'.")
        self.api_key = api_key or config.get_api_key(LLMProvider.OPENAI)
        self.model = model or config.default_models[LLMProvider.OPENAI]
        self.client = OpenAI(api_key=self.api_key)

    def chat_completion(self, messages: List["ChatCompletionMessageParam"], temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        try:
            print(f"[OpenAIClient] Sending chat messages to model {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=float(temperature),
                max_tokens=int(max_tokens)
            )
            print("[OpenAIClient] Received response from OpenAI.")
            return {
                "choices": [
                    {"message": {"content": response.choices[0].message.content}}
                ]
            }
        except Exception as e:
            print(f"[OpenAIClient] Exception during chat_completion: {e}")
            raise

    def test_connection(self) -> bool:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'API is working' and nothing else."}
                ],
                temperature=0.1,
                max_tokens=50
            )
            content = response.choices[0].message.content
            return content is not None and "API is working" in content
        except Exception as e:
            print(f"[OpenAIClient] Exception during test_connection: {e}")
            return False

class LLMClientFactory:
    """Factory for creating LLM clients with appropriate configuration"""
    
    @staticmethod
    def create_client_for_task(task: str, api_key: Optional[str] = None, 
                              model: Optional[str] = None) -> Any:
        """Create an LLM client configured for a specific task"""
        model_config = config.get_model_for_task(task)
        provider = model_config["provider"]
        task_model = model or model_config["model"]
        
        if provider == LLMProvider.OPENAI:
            return OpenAIClient(api_key=api_key, model=task_model)
        else:
            return LLMClient(
                provider=provider,
                api_key=api_key,
                model=task_model
            )
    
    @staticmethod
    def create_client(provider: LLMProvider, api_key: Optional[str] = None, 
                     model: Optional[str] = None) -> Any:
        """Create an LLM client for a specific provider"""
        if provider == LLMProvider.OPENAI:
            return OpenAIClient(api_key=api_key, model=model)
        else:
            return LLMClient(
                provider=provider,
                api_key=api_key,
                model=model
            ) 