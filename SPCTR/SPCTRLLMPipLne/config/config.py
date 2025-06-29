"""
Configuration and API key management for LLM integration
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration management for LLM API integration"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.api_base_url = "https://api.llmapi.com"
        self.default_model = "llama3.2-3b"
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variable or config file"""
        # First try environment variable
        api_key = os.getenv('LLAMA_API_KEY')
        if api_key:
            return api_key
        
        # Then try config file
        config_file = Path(__file__).parent / '.env'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith('LLAMA_API_KEY='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                print(f"Warning: Could not read config file: {e}")
        
        return None
    
    def set_api_key(self, api_key: str):
        """Set API key in environment variable"""
        os.environ['LLAMA_API_KEY'] = api_key
        self.api_key = api_key
    
    def save_api_key_to_file(self, api_key: str):
        """Save API key to .env file"""
        config_file = Path(__file__).parent / '.env'
        try:
            with open(config_file, 'w') as f:
                f.write(f'LLAMA_API_KEY={api_key}\n')
            print(f"✅ API key saved to {config_file}")
        except Exception as e:
            print(f"❌ Failed to save API key: {e}")
    
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return self.api_key is not None

# Global config instance
config = Config() 