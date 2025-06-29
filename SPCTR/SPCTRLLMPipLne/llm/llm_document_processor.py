"""
Main LLM Document Processor - Integrates anchor token pipeline with LLM API
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add parent directory to path to import from core and config folders
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config
from llm.llm_client import LLMClient
from core.xml_to_anchored_txt import xml_to_anchored_txt
from core.anchored_txt_to_xml import anchored_txt_to_xml
from core.extract_docx_xml import extract_docx_xml
from core.repackage_docx_xml import repackage_docx_xml
from llm.legal_citation_checker import LegalCitationChecker

HANDSHAKE_STATUS_FILE = Path(__file__).parent.parent / '.llm_handshake_status.json'

def get_handshake_status():
    if HANDSHAKE_STATUS_FILE.exists():
        try:
            with open(HANDSHAKE_STATUS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('status', 'unknown')
        except Exception:
            return 'unknown'
    return 'unknown'

def set_handshake_status(status):
    try:
        with open(HANDSHAKE_STATUS_FILE, 'w') as f:
            json.dump({'status': status}, f)
    except Exception as e:
        print(f"Warning: Could not save handshake status: {e}")

def perform_handshake():
    processor = LLMDocumentProcessor()
    if not config.is_configured() or not config.api_key:
        print("❌ API key not configured. Run 'setup' first.")
        set_handshake_status('failed')
        return False
    processor.setup_api_key(str(config.api_key))
    print("🤝 Performing handshake with LLM API...")
    result = processor.test_api_connection()
    if result:
        print("✅ Handshake successful!")
        set_handshake_status('success')
        return True
    else:
        print("❌ Handshake failed!")
        set_handshake_status('failed')
        return False

class LLMDocumentProcessor:
    """Main processor for LLM-powered document editing"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or get from config
        if api_key:
            self.api_key = api_key
        elif config.is_configured() and config.api_key:
            self.api_key = config.api_key
        else:
            self.api_key = None
            
        self.client = None
        self.working_dir = Path.cwd()
        if self.api_key:
            self.client = LLMClient(self.api_key)
        self.citation_checker = None
    
    def setup_api_key(self, api_key: str):
        """Setup API key for the processor"""
        config.set_api_key(api_key)
        config.save_api_key_to_file(api_key)
        self.api_key = api_key
        self.client = LLMClient(api_key)
        self.citation_checker = LegalCitationChecker(api_key)
        print("✅ API key configured successfully")
    
    def test_api_connection(self) -> bool:
        """Test the LLM API connection"""
        if not self.client:
            print("❌ No API client configured")
            return False
            
        print("🔗 Testing LLM API connection...")
        try:
            if self.client.test_connection():
                print("✅ API connection successful!")
                return True
            else:
                print("❌ API connection failed")
                return False
        except Exception as e:
            print(f"❌ API connection error: {e}")
            return False
    
    def process_document(
        self, 
        docx_path: str, 
        instruction: str,
        output_suffix: str = "_llm_edited",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        Process a document through the complete LLM pipeline
        
        Args:
            docx_path: Path to input DOCX file
            instruction: Editing instruction for the LLM
            output_suffix: Suffix for output files
            temperature: LLM temperature setting
            max_tokens: Maximum tokens for LLM response
            
        Returns:
            Path to the edited DOCX file, or None if failed
        """
        if not self.client:
            print("❌ No API client configured")
            return None
            
        docx_path_obj = Path(docx_path)
        if not docx_path_obj.exists():
            print(f"❌ Document not found: {docx_path}")
            return None
        
        try:
            print(f"📄 Processing document: {docx_path_obj.name}")
            print(f"📝 Instruction: {instruction}")
            
            # Step 1: Extract XML from DOCX
            print("🔧 Step 1: Extracting XML...")
            xml_file = extract_docx_xml(str(docx_path_obj))
            if not xml_file:
                print("❌ Failed to extract XML")
                return None
            
            # Step 2: Convert XML to anchored TXT
            print("🔗 Step 2: Converting to anchored TXT...")
            anchored_txt_file = xml_to_anchored_txt(xml_file)
            if not anchored_txt_file:
                print("❌ Failed to convert to anchored TXT")
                return None
            
            # Step 3: Read anchored text
            with open(anchored_txt_file, 'r', encoding='utf-8') as f:
                anchored_text = f.read()
            
            # Step 4: Send to LLM for editing
            print("🤖 Step 3: Sending to LLM for editing...")
            edited_text = self.client.edit_document(
                anchored_text, 
                instruction, 
                temperature, 
                max_tokens
            )
            
            # Step 5: Save edited text
            edited_txt_file = docx_path_obj.with_suffix(f'{output_suffix}.anchored.txt')
            with open(edited_txt_file, 'w', encoding='utf-8') as f:
                f.write(edited_text)
            
            # Step 6: Convert back to XML
            print("🔄 Step 4: Converting back to XML...")
            reconstructed_xml = anchored_txt_to_xml(
                str(edited_txt_file), 
                xml_file
            )
            if not reconstructed_xml:
                print("❌ Failed to reconstruct XML")
                return None
            
            # Step 7: Repackage as DOCX
            print("📋 Step 5: Repackaging as DOCX...")
            output_docx = repackage_docx_xml(
                str(docx_path_obj), 
                reconstructed_xml
            )
            
            if output_docx:
                print(f"✅ Document processing complete!")
                print(f"📁 Output file: {output_docx}")
                return output_docx
            else:
                print("❌ Failed to create output DOCX")
                return None
                
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            return None
    
    def analyze_document(
        self, 
        docx_path: str, 
        analysis_type: str = "general",
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Analyze a document using the LLM
        
        Args:
            docx_path: Path to input DOCX file
            analysis_type: Type of analysis ("general", "legal", "technical", "summary")
            temperature: LLM temperature setting
            max_tokens: Maximum tokens for LLM response
            
        Returns:
            Analysis results as string, or None if failed
        """
        if not self.client:
            print("❌ No API client configured")
            return None
            
        docx_path_obj = Path(docx_path)
        if not docx_path_obj.exists():
            print(f"❌ Document not found: {docx_path}")
            return None
        
        try:
            print(f"📄 Analyzing document: {docx_path_obj.name}")
            print(f"🔍 Analysis type: {analysis_type}")
            
            # Extract XML and convert to anchored TXT
            xml_file = extract_docx_xml(str(docx_path_obj))
            if not xml_file:
                return None
            
            anchored_txt_file = xml_to_anchored_txt(xml_file)
            if not anchored_txt_file:
                return None
            
            # Read anchored text
            with open(anchored_txt_file, 'r', encoding='utf-8') as f:
                anchored_text = f.read()
            
            # Send to LLM for analysis
            print("🤖 Sending to LLM for analysis...")
            analysis = self.client.analyze_document(
                anchored_text, 
                analysis_type, 
                temperature, 
                max_tokens
            )
            
            # Save analysis
            analysis_file = docx_path_obj.with_suffix(f'.{analysis_type}_analysis.txt')
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(analysis)
            
            print(f"✅ Analysis complete!")
            print(f"📁 Analysis file: {analysis_file}")
            return analysis
            
        except Exception as e:
            print(f"❌ Document analysis failed: {e}")
            return None

    def check_citations(self, docx_path: str, output_file: Optional[str] = None, 
                       debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        Check legal citations in a document
        
        Args:
            docx_path: Path to DOCX file
            output_file: Optional output file for results
            debug: Enable debug output
            
        Returns:
            Citation analysis results
        """
        if not self.citation_checker:
            # Use self.api_key if available, otherwise use config
            api_key_to_use = self.api_key if self.api_key else (config.api_key if config.is_configured() else None)
            if not api_key_to_use:
                print("❌ No API key configured. Run 'setup' first.")
                return None
            self.citation_checker = LegalCitationChecker(api_key_to_use)
        
        return self.citation_checker.check_citations_from_docx(docx_path, output_file, debug)

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("LLM Document Processor")
        print("=" * 40)
        print("Usage:")
        print("  python llm_document_processor.py setup <api_key>")
        print("  python llm_document_processor.py handshake")
        print("  python llm_document_processor.py test")
        print("  python llm_document_processor.py test-connection")
        print("  python llm_document_processor.py edit <docx_file> <instruction>")
        print("  python llm_document_processor.py analyze <docx_file> [analysis_type]")
        print("  python llm_document_processor.py check-citations <docx_file> [output.json] [--debug]")
        print("  python llm_document_processor.py prompt-editor")
        print("\nAnalysis types: general, legal, technical, summary")
        # On startup, check handshake status
        status = get_handshake_status()
        if status == 'success':
            print("🤝 Handshake status: SUCCESS (no need to retry)")
        elif status == 'failed':
            print("🤝 Handshake status: FAILED (no need to retry)")
        else:
            print("🤝 Handshake status: UNKNOWN. Performing handshake...")
            perform_handshake()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        if len(sys.argv) < 3:
            print("❌ API key required for setup")
            sys.exit(1)
        api_key = sys.argv[2]
        processor = LLMDocumentProcessor()
        processor.setup_api_key(api_key)
        set_handshake_status('unknown')
        
    elif command == "handshake":
        perform_handshake()
        sys.exit(0)
    
    elif command == "test-connection":
        processor = LLMDocumentProcessor()
        if not config.is_configured() or not config.api_key:
            print("❌ API key not configured. Run 'setup' first.")
            sys.exit(1)
        processor.setup_api_key(str(config.api_key))
        processor.test_api_connection()
        sys.exit(0)
    
    processor = LLMDocumentProcessor()
    
    if command == "test":
        if not config.is_configured():
            print("❌ API key not configured. Run 'setup' first.")
            sys.exit(1)
        processor.test_api_connection()
        
    elif command == "edit":
        if len(sys.argv) < 4:
            print("❌ Document path and instruction required")
            sys.exit(1)
        if not config.is_configured():
            print("❌ API key not configured. Run 'setup' first.")
            sys.exit(1)
        
        docx_path = sys.argv[2]
        instruction = sys.argv[3]
        processor.process_document(docx_path, instruction)
        
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("❌ Document path required")
            sys.exit(1)
        if not config.is_configured():
            print("❌ API key not configured. Run 'setup' first.")
            sys.exit(1)
        
        docx_path = sys.argv[2]
        analysis_type = sys.argv[3] if len(sys.argv) > 3 else "general"
        processor.analyze_document(docx_path, analysis_type)
        
    elif command == "check-citations":
        if len(sys.argv) < 3:
            print("❌ Please specify a DOCX file path")
            return
        
        docx_path = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        debug = "--debug" in sys.argv
        
        processor = LLMDocumentProcessor()
        results = processor.check_citations(docx_path, output_file, debug)
        
        if results and processor.citation_checker:
            processor.citation_checker.print_results_summary(results)
    
    elif command == "prompt-editor":
        # Import and run the prompt editor
        try:
            # Try to import the prompt editor
            import importlib.util
            spec = importlib.util.spec_from_file_location("prompt_editor", Path(__file__).parent / "prompt_editor.py")
            if spec and spec.loader:
                prompt_editor_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(prompt_editor_module)
                PromptEditor = prompt_editor_module.PromptEditor
            else:
                raise ImportError("Could not load prompt_editor.py")
            
            editor = PromptEditor()
            
            if len(sys.argv) < 3:
                print("Prompt Editor - Manage LLM prompts")
                print("=" * 40)
                print("Usage:")
                print("  python llm_document_processor.py prompt-editor list                    # List all prompts")
                print("  python llm_document_processor.py prompt-editor show <prompt_name>      # Show prompt content")
                print("  python llm_document_processor.py prompt-editor edit <prompt_name>      # Edit prompt file")
                print("  python llm_document_processor.py prompt-editor create <prompt_name>    # Create new prompt")
                print()
                print("Examples:")
                print("  python llm_document_processor.py prompt-editor list")
                print("  python llm_document_processor.py prompt-editor show legal_citation")
                print("  python llm_document_processor.py prompt-editor edit legal_citation")
                return
            
            subcommand = sys.argv[2].lower()
            
            if subcommand == "list":
                editor.list_prompts()
            
            elif subcommand == "show":
                if len(sys.argv) < 4:
                    print("❌ Please specify a prompt name")
                    return
                editor.show_prompt(sys.argv[3])
            
            elif subcommand == "edit":
                if len(sys.argv) < 4:
                    print("❌ Please specify a prompt name")
                    return
                custom_editor = sys.argv[4] if len(sys.argv) > 4 else None
                editor.edit_prompt(sys.argv[3], custom_editor)
            
            elif subcommand == "create":
                if len(sys.argv) < 4:
                    print("❌ Please specify a prompt name")
                    return
                template = sys.argv[4] if len(sys.argv) > 4 else "basic"
                editor.create_prompt(sys.argv[3], template)
            
            else:
                print(f"❌ Unknown subcommand: {subcommand}")
                print("Use 'list', 'show', 'edit', or 'create'")
                
        except ImportError:
            print("❌ Prompt editor not available")
            print("💡 Create prompt_editor.py to enable prompt management")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: setup, test, handshake, edit, analyze, check-citations, prompt-editor")

if __name__ == "__main__":
    main() 