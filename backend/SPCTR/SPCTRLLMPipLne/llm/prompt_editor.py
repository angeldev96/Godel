"""
Prompt Editor - Manage LLM prompts
"""
import os
from pathlib import Path
from typing import Optional

class PromptEditor:
    """Simple prompt editor for managing LLM prompts"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
    
    def list_prompts(self):
        """List all available prompts"""
        print("Available prompts:")
        for file in self.config_dir.glob("*.txt"):
            print(f"  - {file.stem}")
    
    def show_prompt(self, prompt_name: str):
        """Show prompt content"""
        prompt_file = self.config_dir / f"{prompt_name}.txt"
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                print(f"Content of {prompt_name}:")
                print("=" * 40)
                print(f.read())
        else:
            print(f"❌ Prompt '{prompt_name}' not found")
    
    def edit_prompt(self, prompt_name: str, custom_editor: Optional[str] = None):
        """Edit prompt file"""
        prompt_file = self.config_dir / f"{prompt_name}.txt"
        if prompt_file.exists():
            editor = custom_editor or os.environ.get('EDITOR', 'notepad')
            os.system(f"{editor} {prompt_file}")
        else:
            print(f"❌ Prompt '{prompt_name}' not found")
    
    def create_prompt(self, prompt_name: str, template: str = "basic"):
        """Create new prompt"""
        prompt_file = self.config_dir / f"{prompt_name}.txt"
        if prompt_file.exists():
            print(f"❌ Prompt '{prompt_name}' already exists")
            return
        
        # Basic template
        if template == "basic":
            content = f"""You are a helpful assistant for {prompt_name}.

Please provide clear, accurate, and helpful responses.

User: {{user_input}}
Assistant:"""
        else:
            content = f"# {prompt_name}\n\nAdd your prompt content here."
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created prompt '{prompt_name}'") 