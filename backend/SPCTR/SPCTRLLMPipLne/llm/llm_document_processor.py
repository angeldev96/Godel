"""
Main LLM Document Processor - Integrates anchor token pipeline with LLM API
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add parent directory to path to import from core and config folders
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config, LLMProvider
from llm.llm_client import LLMClient, LLMClientFactory
from core.xml_to_anchored_txt import xml_to_anchored_txt
from core.anchored_txt_to_xml import anchored_txt_to_xml
from core.extract_docx_xml import extract_docx_xml
from core.repackage_docx_xml import repackage_docx_xml
from llm.legal_citation_checker import LegalCitationChecker
from utils.metadata_manager import MetadataManager

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
    # Check if any provider is configured
    available_providers = config.list_available_providers()
    if not any(available_providers.values()):
        print("❌ No API keys configured. Please configure at least one provider.")
        set_handshake_status('failed')
        return False
    
    # The constructor should have auto-configured the client
    if not processor.client:
        print("❌ Failed to auto-configure client")
        set_handshake_status('failed')
        return False
    
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
    
    def __init__(self, provider: Optional[LLMProvider] = None, api_key: Optional[str] = None, 
                 model: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.client = None
        self.citation_checker = None
        self.working_dir = Path.cwd()
        self.metadata_manager = MetadataManager(self.working_dir)
        
        # Initialize client if provider and API key are provided
        if provider and api_key:
            self.client = LLMClient(provider, api_key, model)
            self.citation_checker = LegalCitationChecker(api_key=api_key, model=model, provider=provider)
        else:
            # Try to initialize from config - prioritize OpenAI over Llama
            available_providers = config.list_available_providers()
            
            # Try OpenAI first if available
            if available_providers.get("openai", False):
                provider = LLMProvider.OPENAI
                api_key = config.get_api_key(provider)
                if api_key:
                    self.provider = provider
                    self.api_key = api_key
                    self.model = model or config.default_models[provider]
                    self.client = LLMClient(provider, api_key, self.model)
                    self.citation_checker = LegalCitationChecker(api_key=api_key, model=self.model, provider=provider)
                    print(f"✅ Auto-configured {provider.value} client")
                    return
            
            # Fall back to Llama if OpenAI not available
            for provider_name, is_configured in available_providers.items():
                if is_configured:
                    provider = LLMProvider(provider_name)
                    api_key = config.get_api_key(provider)
                    if api_key:
                        self.provider = provider
                        self.api_key = api_key
                        self.model = model or config.default_models[provider]
                        self.client = LLMClient(provider, api_key, self.model)
                        self.citation_checker = LegalCitationChecker(api_key=api_key, model=self.model, provider=provider)
                        print(f"✅ Auto-configured {provider.value} client")
                        break
    
    def setup_api_key(self, provider: LLMProvider, api_key: str, model: Optional[str] = None):
        """Setup API key for the processor"""
        self.provider = provider
        self.api_key = api_key
        self.model = model
        
        # Save to config
        config.set_api_key(provider, api_key)
        config.save_api_key_to_file(provider, api_key)
        
        # Initialize clients
        self.client = LLMClient(provider, api_key, model)
        self.citation_checker = LegalCitationChecker(api_key=api_key, model=model, provider=provider)
        print(f"✅ API key configured successfully for {provider.value}")
    
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
        Process a document through the complete LLM pipeline with metadata tracking
        
        Args:
            docx_path: Path to input DOCX file
            instruction: Editing instruction for the LLM
            output_suffix: Suffix for output files
            temperature: LLM temperature setting
            max_tokens: Maximum tokens for LLM response
            
        Returns:
            Path to the edited DOCX file, or None if failed
        """
        # Create metadata for this processing operation
        metadata = self.metadata_manager.create_document_metadata(docx_path)
        processing_id = metadata["processing_id"]
        
        print(f"🆔 Processing ID: {processing_id}")
        print(f"📄 Document: {metadata['original_file']['name']}")
        print(f"⏰ Start Time: {metadata['processing']['start_time']}")
        print(f"📝 Instruction: {instruction}")
        
        if not self.client:
            error_msg = "No API client configured"
            print(f"❌ {error_msg}")
            metadata = self.metadata_manager.add_pipeline_step(metadata, "document_processing", 
                                                              docx_path, None, "failed", error_msg)
            self.metadata_manager.save_metadata(metadata)
            return None
            
        docx_path_obj = Path(docx_path)
        if not docx_path_obj.exists():
            error_msg = f"Document not found: {docx_path}"
            print(f"❌ {error_msg}")
            metadata = self.metadata_manager.add_pipeline_step(metadata, "document_processing", 
                                                              docx_path, None, "failed", error_msg)
            self.metadata_manager.save_metadata(metadata)
            return None
        
        try:
            # Step 1: Extract XML from DOCX
            print("🔧 Step 1: Extracting XML...")
            xml_file = extract_docx_xml(str(docx_path_obj))
            if not xml_file:
                error_msg = "Failed to extract XML"
                print(f"❌ {error_msg}")
                metadata = self.metadata_manager.add_pipeline_step(metadata, "extract_xml", 
                                                                  docx_path, None, "failed", error_msg)
                self.metadata_manager.save_metadata(metadata)
                return None
            
            metadata = self.metadata_manager.add_pipeline_step(metadata, "extract_xml", 
                                                              docx_path, xml_file, "completed")
            
            # Step 2: Convert XML to anchored TXT
            print("🔗 Step 2: Converting to anchored TXT...")
            anchored_txt_file = xml_to_anchored_txt(xml_file)
            if not anchored_txt_file:
                error_msg = "Failed to convert to anchored TXT"
                print(f"❌ {error_msg}")
                metadata = self.metadata_manager.add_pipeline_step(metadata, "convert_to_anchored_txt", 
                                                                  xml_file, None, "failed", error_msg)
                self.metadata_manager.save_metadata(metadata)
                return None
            
            metadata = self.metadata_manager.add_pipeline_step(metadata, "convert_to_anchored_txt", 
                                                              xml_file, anchored_txt_file, "completed")
            
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
            edited_txt_file = self.metadata_manager.create_output_filename(
                docx_path, processing_id, "edited_anchored", ".txt"
            )
            with open(edited_txt_file, 'w', encoding='utf-8') as f:
                f.write(edited_text)
            
            metadata = self.metadata_manager.add_pipeline_step(metadata, "llm_editing", 
                                                              anchored_txt_file, edited_txt_file, "completed")
            
            # Step 6: Convert back to XML
            print("🔄 Step 4: Converting back to XML...")
            reconstructed_xml = anchored_txt_to_xml(
                str(edited_txt_file), 
                xml_file
            )
            if not reconstructed_xml:
                error_msg = "Failed to reconstruct XML"
                print(f"❌ {error_msg}")
                metadata = self.metadata_manager.add_pipeline_step(metadata, "convert_to_xml", 
                                                                  edited_txt_file, None, "failed", error_msg)
                self.metadata_manager.save_metadata(metadata)
                return None
            
            metadata = self.metadata_manager.add_pipeline_step(metadata, "convert_to_xml", 
                                                              edited_txt_file, reconstructed_xml, "completed")
            
            # Step 7: Repackage as DOCX
            print("📋 Step 5: Repackaging as DOCX...")
            output_docx = repackage_docx_xml(
                str(docx_path_obj), 
                reconstructed_xml
            )
            
            if output_docx:
                metadata = self.metadata_manager.add_pipeline_step(metadata, "repackage_docx", 
                                                                  reconstructed_xml, output_docx, "completed")
                
                # Save metadata
                metadata_file = self.metadata_manager.save_metadata(metadata)
                
                # Print summary
                self.metadata_manager.print_processing_summary(metadata)
                
                print(f"✅ Document processing complete!")
                print(f"📁 Output file: {output_docx}")
                return output_docx
            else:
                error_msg = "Failed to create output DOCX"
                print(f"❌ {error_msg}")
                metadata = self.metadata_manager.add_pipeline_step(metadata, "repackage_docx", 
                                                                  reconstructed_xml, None, "failed", error_msg)
                self.metadata_manager.save_metadata(metadata)
                return None
                
        except Exception as e:
            error_msg = f"Document processing failed: {e}"
            print(f"❌ {error_msg}")
            metadata = self.metadata_manager.add_pipeline_step(metadata, "document_processing", 
                                                              docx_path, None, "failed", error_msg)
            self.metadata_manager.save_metadata(metadata)
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
                       debug: bool = False, enable_reasoning: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """
        Check legal citations in a document with metadata tracking
        
        Args:
            docx_path: Path to DOCX file
            output_file: Optional output file for results
            debug: Enable debug output
            enable_reasoning: Enable reasoning-based second-pass validation
            
        Returns:
            Citation analysis results
        """
        # Create metadata for this processing operation
        metadata = self.metadata_manager.create_document_metadata(docx_path)
        processing_id = metadata["processing_id"]
        
        print(f"🆔 Processing ID: {processing_id}")
        print(f"📄 Document: {metadata['original_file']['name']}")
        print(f"⏰ Start Time: {metadata['processing']['start_time']}")
        
        try:
            if not self.citation_checker:
                # Try to create citation checker with available provider
                available_providers = config.list_available_providers()
                for provider_name, is_configured in available_providers.items():
                    if is_configured:
                        provider = LLMProvider(provider_name)
                        api_key = config.get_api_key(provider)
                        if api_key:
                            self.citation_checker = LegalCitationChecker(api_key=api_key, provider=provider)
                            break
                
                if not self.citation_checker:
                    error_msg = "No API key configured. Please configure at least one provider."
                    print(f"❌ {error_msg}")
                    metadata = self.metadata_manager.add_pipeline_step(metadata, "citation_checking", 
                                                                      docx_path, None, "failed", error_msg)
                    self.metadata_manager.save_metadata(metadata)
                    return None
            
            # Generate output filename with metadata if not provided
            if not output_file:
                output_file = self.metadata_manager.create_output_filename(
                    docx_path, processing_id, "citations", ".json"
                )
            
            # Add initial step
            metadata = self.metadata_manager.add_pipeline_step(metadata, "citation_checking_start", 
                                                              docx_path, None, "started")
            
            # Perform citation checking
            results = self.citation_checker.check_citations_from_docx(docx_path, output_file, debug, enable_reasoning)
            
            # Add completion step
            metadata = self.metadata_manager.add_pipeline_step(metadata, "citation_checking_complete", 
                                                              docx_path, output_file, "completed")
            
            # Save metadata
            metadata_file = self.metadata_manager.save_metadata(metadata)
            
            # Print summary
            self.metadata_manager.print_processing_summary(metadata)
            
            if results and self.citation_checker:
                self.citation_checker.print_results_summary(results)
            
            return results
            
        except Exception as e:
            error_msg = f"Citation checking failed: {e}"
            print(f"❌ {error_msg}")
            metadata = self.metadata_manager.add_pipeline_step(metadata, "citation_checking", 
                                                              docx_path, None, "failed", error_msg)
            self.metadata_manager.save_metadata(metadata)
            return None

    def check_citations_batched(self, docx_path: str, output_file: Optional[str] = None, 
                               debug: bool = False, batch_size: int = 5, 
                               context_overlap: int = 2, enable_reasoning: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """
        Check legal citations in a document using batched processing with context windows and metadata tracking
        
        Args:
            docx_path: Path to DOCX file
            output_file: Optional output file for results
            debug: Enable debug output
            batch_size: Number of paragraphs per batch
            context_overlap: Number of paragraphs to overlap between batches
            enable_reasoning: Enable reasoning-based second-pass validation
            
        Returns:
            Citation analysis results
        """
        # Create metadata for this processing operation
        metadata = self.metadata_manager.create_document_metadata(docx_path)
        processing_id = metadata["processing_id"]
        
        print(f"🆔 Processing ID: {processing_id}")
        print(f"📄 Document: {metadata['original_file']['name']}")
        print(f"⏰ Start Time: {metadata['processing']['start_time']}")
        print(f"📦 Batch Size: {batch_size}, Context Overlap: {context_overlap}")
        
        try:
            if not self.citation_checker:
                # Try to create citation checker with available provider
                available_providers = config.list_available_providers()
                for provider_name, is_configured in available_providers.items():
                    if is_configured:
                        provider = LLMProvider(provider_name)
                        api_key = config.get_api_key(provider)
                        if api_key:
                            self.citation_checker = LegalCitationChecker(api_key=api_key, provider=provider)
                            break
                
                if not self.citation_checker:
                    error_msg = "No API key configured. Please configure at least one provider."
                    print(f"❌ {error_msg}")
                    metadata = self.metadata_manager.add_pipeline_step(metadata, "batched_citation_checking", 
                                                                      docx_path, None, "failed", error_msg)
                    self.metadata_manager.save_metadata(metadata)
                    return None
            
            # Generate output filename with metadata if not provided
            if not output_file:
                output_file = self.metadata_manager.create_output_filename(
                    docx_path, processing_id, "citations_batched", ".json"
                )
            
            # Add initial step
            metadata = self.metadata_manager.add_pipeline_step(metadata, "batched_citation_checking_start", 
                                                              docx_path, None, "started")
            
            # Perform batched citation checking
            results = self.citation_checker.check_citations_batched_with_context(
                docx_path, output_file, debug, batch_size, context_overlap
            )
            
            # Add completion step
            metadata = self.metadata_manager.add_pipeline_step(metadata, "batched_citation_checking_complete", 
                                                              docx_path, output_file, "completed")
            
            # Save metadata
            metadata_file = self.metadata_manager.save_metadata(metadata)
            
            # Print summary
            self.metadata_manager.print_processing_summary(metadata)
            
            if results and self.citation_checker:
                self.citation_checker.print_results_summary(results)
            
            return results
            
        except Exception as e:
            error_msg = f"Batched citation checking failed: {e}"
            print(f"❌ {error_msg}")
            metadata = self.metadata_manager.add_pipeline_step(metadata, "batched_citation_checking", 
                                                              docx_path, None, "failed", error_msg)
            self.metadata_manager.save_metadata(metadata)
            return None

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("LLM Document Processor")
        print("=" * 40)
        print("Usage:")
        print("  python llm_document_processor.py setup <provider> <api_key> [model]")
        print("  python llm_document_processor.py handshake")
        print("  python llm_document_processor.py test")
        print("  python llm_document_processor.py test-connection")
        print("  python llm_document_processor.py edit <docx_file> <instruction>")
        print("  python llm_document_processor.py analyze <docx_file> [analysis_type]")
        print("  python llm_document_processor.py check-citations <docx_file> [--output-path <output.json>] [--debug] [--reasoning|--no-reasoning]")
        print("  python llm_document_processor.py check-citations-batched <docx_file> [--output-path <output.json>] [--debug] [--batch-size <5>] [--context-overlap <2>] [--reasoning|--no-reasoning]")
        print("  python llm_document_processor.py prompt-editor")
        print("  python llm_document_processor.py metadata <docx_file> [--show-versions] [--show-latest] [--processing-id <id>]")
        print("  python llm_document_processor.py cleanup-metadata [--days <30>]")
        print("\nAnalysis types: general, legal, technical, summary")
        print("Providers: llama, openai")
        print("\nMetadata Commands:")
        print("  metadata <docx_file> --show-versions    # Show all processing versions")
        print("  metadata <docx_file> --show-latest      # Show latest processing version")
        print("  metadata <docx_file> --processing-id <id> # Show specific processing metadata")
        print("  cleanup-metadata --days <30>            # Clean up old metadata files")
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
        if len(sys.argv) < 4:
            print("❌ Provider and API key required for setup")
            print("Usage: python llm_document_processor.py setup <provider> <api_key> [model]")
            sys.exit(1)
        provider_name = sys.argv[2]
        api_key = sys.argv[3]
        model = sys.argv[4] if len(sys.argv) > 4 else None
        
        try:
            provider = LLMProvider(provider_name)
        except ValueError:
            print(f"❌ Invalid provider: {provider_name}. Valid providers: llama, openai")
            sys.exit(1)
        
        processor = LLMDocumentProcessor()
        processor.setup_api_key(provider, api_key, model)
        set_handshake_status('unknown')
        
    elif command == "handshake":
        perform_handshake()
        sys.exit(0)
    
    elif command == "test-connection":
        processor = LLMDocumentProcessor()
        if not processor.client:
            print("❌ No API keys configured. Please configure at least one provider.")
            sys.exit(1)
        
        processor.test_api_connection()
        sys.exit(0)
    
    elif command == "metadata":
        if len(sys.argv) < 3:
            print("❌ Please specify a DOCX file path")
            sys.exit(1)
        
        docx_path = sys.argv[2]
        processor = LLMDocumentProcessor()
        
        # Parse optional arguments
        show_versions = False
        show_latest = False
        processing_id = None
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--show-versions":
                show_versions = True
                i += 1
            elif sys.argv[i] == "--show-latest":
                show_latest = True
                i += 1
            elif sys.argv[i] == "--processing-id" and i + 1 < len(sys.argv):
                processing_id = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        # Handle metadata commands
        if processing_id:
            # Show specific processing metadata
            metadata = processor.metadata_manager.load_metadata(processing_id)
            if metadata:
                processor.metadata_manager.print_processing_summary(metadata)
            else:
                print(f"❌ No metadata found for processing ID: {processing_id}")
        elif show_versions:
            # Show all versions
            versions = processor.metadata_manager.find_document_versions(docx_path)
            if versions:
                print(f"\n📋 Found {len(versions)} processing versions for: {Path(docx_path).name}")
                print("=" * 60)
                for i, version in enumerate(versions, 1):
                    print(f"{i}. Processing ID: {version['processing_id']}")
                    print(f"   Start Time: {version['processing']['start_time']}")
                    print(f"   Duration: {version['processing'].get('duration_seconds', 0):.2f} seconds")
                    print(f"   Status: {version['status']}")
                    print(f"   Steps: {len(version['pipeline_steps'])}")
                    print()
            else:
                print(f"❌ No processing versions found for: {docx_path}")
        elif show_latest:
            # Show latest version
            latest = processor.metadata_manager.get_latest_version(docx_path)
            if latest:
                processor.metadata_manager.print_processing_summary(latest)
            else:
                print(f"❌ No processing versions found for: {docx_path}")
        else:
            # Show latest version by default
            latest = processor.metadata_manager.get_latest_version(docx_path)
            if latest:
                processor.metadata_manager.print_processing_summary(latest)
            else:
                print(f"❌ No processing versions found for: {docx_path}")
    
    elif command == "cleanup-metadata":
        # Parse optional arguments
        days_to_keep = 30
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--days" and i + 1 < len(sys.argv):
                days_to_keep = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        processor = LLMDocumentProcessor()
        processor.metadata_manager.cleanup_old_metadata(days_to_keep)
        sys.exit(0)
    
    processor = LLMDocumentProcessor()
    
    if command == "test":
        available_providers = config.list_available_providers()
        if not any(available_providers.values()):
            print("❌ No API keys configured. Please configure at least one provider.")
            sys.exit(1)
        processor.test_api_connection()
        
    elif command == "edit":
        if len(sys.argv) < 4:
            print("❌ Document path and instruction required")
            sys.exit(1)
        available_providers = config.list_available_providers()
        if not any(available_providers.values()):
            print("❌ No API keys configured. Please configure at least one provider.")
            sys.exit(1)
        
        docx_path = sys.argv[2]
        instruction = sys.argv[3]
        processor.process_document(docx_path, instruction)
        
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("❌ Document path required")
            sys.exit(1)
        available_providers = config.list_available_providers()
        if not any(available_providers.values()):
            print("❌ No API keys configured. Please configure at least one provider.")
            sys.exit(1)
        
        docx_path = sys.argv[2]
        analysis_type = sys.argv[3] if len(sys.argv) > 3 else "general"
        processor.analyze_document(docx_path, analysis_type)
        
    elif command == "check-citations":
        if len(sys.argv) < 3:
            print("❌ Please specify a DOCX file path")
            return
        
        docx_path = sys.argv[2]
        
        # Parse optional arguments
        output_file = None
        debug = False
        enable_reasoning = None  # None means use default setting
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--output-path" and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--debug":
                debug = True
                i += 1
            elif sys.argv[i] == "--reasoning":
                enable_reasoning = True
                i += 1
            elif sys.argv[i] == "--no-reasoning":
                enable_reasoning = False
                i += 1
            else:
                # Treat as positional output file (backward compatibility)
                if output_file is None:
                    output_file = sys.argv[i]
                i += 1
        
        processor = LLMDocumentProcessor()
        results = processor.check_citations(docx_path, output_file, debug, enable_reasoning)
        
        if results and processor.citation_checker:
            processor.citation_checker.print_results_summary(results)
    
    elif command == "check-citations-batched":
        if len(sys.argv) < 3:
            print("❌ Please specify a DOCX file path")
            return
        
        docx_path = sys.argv[2]
        
        # Parse optional arguments
        output_file = None
        debug = False
        batch_size = 5
        context_overlap = 2
        enable_reasoning = None  # None means use default setting
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--output-path" and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--debug":
                debug = True
                i += 1
            elif sys.argv[i] == "--batch-size" and i + 1 < len(sys.argv):
                batch_size = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--context-overlap" and i + 1 < len(sys.argv):
                context_overlap = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--reasoning":
                enable_reasoning = True
                i += 1
            elif sys.argv[i] == "--no-reasoning":
                enable_reasoning = False
                i += 1
            else:
                # Treat as positional output file (backward compatibility)
                if output_file is None:
                    output_file = sys.argv[i]
                i += 1
        
        processor = LLMDocumentProcessor()
        results = processor.check_citations_batched(docx_path, output_file, debug, batch_size, context_overlap, enable_reasoning)
        
        if results and processor.citation_checker:
            processor.citation_checker.print_results_summary(results)
    
    elif command == "prompt-editor":
        try:
            from llm.prompt_editor import PromptEditor
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
        print("Run without arguments to see usage information.")
        sys.exit(1)

if __name__ == "__main__":
    main() 