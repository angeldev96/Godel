"""
Configuration and API key management for LLM integration
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

class LLMProvider(Enum):
    """Supported LLM providers"""
    LLAMA = "llama"
    OPENAI = "openai"

class Config:
    """Configuration management for LLM API integration"""
    
    def __init__(self):
        # API Keys
        self.llama_api_key = self._get_api_key("LLAMA_API_KEY")
        self.openai_api_key = self._get_api_key("OPENAI_API_KEY")
        
        # API Base URLs
        self.llama_api_base_url = "https://api.llmapi.com"
        self.openai_api_base_url = "https://api.openai.com/v1"
        
        # Default models for each provider
        self.default_models = {
            LLMProvider.LLAMA: "llama3.2-3b",
            LLMProvider.OPENAI: "gpt-3.5-turbo"  # ChatGPT 3.5 Turbo
        }
        
        # Global model selection (if set, overrides task-specific models)
        self.global_model_provider = None
        self.global_model_name = None
        
        # Task-specific model configurations
        self.task_models = {
            "citation_checking": {
                "provider": LLMProvider.LLAMA,
                "model": "llama3.2-3b"
            },
            "citation_validation": {
                "provider": LLMProvider.OPENAI,
                "model": "gpt-3.5-turbo"  # ChatGPT 3.5 Turbo
            },
            "document_analysis": {
                "provider": LLMProvider.LLAMA,
                "model": "llama3.2-3b"
            }
        }
    
    def _get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from environment variable or config file"""
        # First try environment variable
        api_key = os.getenv(key_name)
        if api_key:
            return api_key
        
        # Then try config file in parent directory (root)
        config_file = Path(__file__).parent.parent / '.env'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith(f'{key_name}='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                print(f"Warning: Could not read config file: {e}")
        
        return None
    
    def set_api_key(self, provider: LLMProvider, api_key: str):
        """Set API key for a specific provider"""
        if provider == LLMProvider.LLAMA:
            os.environ['LLAMA_API_KEY'] = api_key
            self.llama_api_key = api_key
        elif provider == LLMProvider.OPENAI:
            os.environ['OPENAI_API_KEY'] = api_key
            self.openai_api_key = api_key
    
    def save_api_key_to_file(self, provider: LLMProvider, api_key: str):
        """Save API key to .env file"""
        config_file = Path(__file__).parent.parent / '.env'
        key_name = f"{provider.value.upper()}_API_KEY"
        
        try:
            # Read existing content
            existing_lines = []
            if config_file.exists():
                with open(config_file, 'r') as f:
                    existing_lines = f.readlines()
            
            # Update or add the key
            key_found = False
            for i, line in enumerate(existing_lines):
                if line.startswith(f'{key_name}='):
                    existing_lines[i] = f'{key_name}={api_key}\n'
                    key_found = True
                    break
            
            if not key_found:
                existing_lines.append(f'{key_name}={api_key}\n')
            
            # Write back to file
            with open(config_file, 'w') as f:
                f.writelines(existing_lines)
            
            print(f"✅ {provider.value.title()} API key saved to {config_file}")
        except Exception as e:
            print(f"❌ Failed to save {provider.value} API key: {e}")
    
    def is_provider_configured(self, provider: LLMProvider) -> bool:
        """Check if a specific provider is configured"""
        if provider == LLMProvider.LLAMA:
            return self.llama_api_key is not None
        elif provider == LLMProvider.OPENAI:
            return self.openai_api_key is not None
        return False
    
    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for a specific provider"""
        if provider == LLMProvider.LLAMA:
            return self.llama_api_key
        elif provider == LLMProvider.OPENAI:
            return self.openai_api_key
        return None
    
    def get_api_base_url(self, provider: LLMProvider) -> str:
        """Get API base URL for a specific provider"""
        if provider == LLMProvider.LLAMA:
            return self.llama_api_base_url
        elif provider == LLMProvider.OPENAI:
            return self.openai_api_base_url
        return ""
    
    def set_global_model(self, provider: LLMProvider, model_name: str):
        """Set a global model that will be used for all tasks"""
        self.global_model_provider = provider
        self.global_model_name = model_name
        print(f"✅ Global model set to {provider.value}:{model_name}")
    
    def clear_global_model(self):
        """Clear global model setting"""
        self.global_model_provider = None
        self.global_model_name = None
        print("✅ Global model setting cleared")
    
    def set_task_model(self, task: str, provider: LLMProvider, model_name: str):
        """Set model for a specific task"""
        self.task_models[task] = {
            "provider": provider,
            "model": model_name
        }
        print(f"✅ Task '{task}' model set to {provider.value}:{model_name}")
    
    def get_model_for_task(self, task: str) -> Dict[str, Any]:
        """Get the appropriate model configuration for a task"""
        # If global model is set, use it
        if self.global_model_provider and self.global_model_name:
            return {
                "provider": self.global_model_provider,
                "model": self.global_model_name
            }
        
        # Otherwise use task-specific model
        if task in self.task_models:
            return self.task_models[task]
        
        # Fallback to default Llama model
        return {
            "provider": LLMProvider.LLAMA,
            "model": self.default_models[LLMProvider.LLAMA]
        }
    
    def list_available_providers(self) -> Dict[str, bool]:
        """List all available providers and their configuration status"""
        return {
            "llama": self.is_provider_configured(LLMProvider.LLAMA),
            "openai": self.is_provider_configured(LLMProvider.OPENAI)
        }
    
    def list_task_configurations(self) -> Dict[str, Dict[str, Any]]:
        """List all task configurations"""
        return self.task_models.copy()
    
    def get_global_model_info(self) -> Optional[Dict[str, Any]]:
        """Get global model information if set"""
        if self.global_model_provider and self.global_model_name:
            return {
                "provider": self.global_model_provider,
                "model": self.global_model_name
            }
        return None

# Global config instance
config = Config() 