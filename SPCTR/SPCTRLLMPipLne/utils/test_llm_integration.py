"""
Test script for LLM integration functionality
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from llm.llm_document_processor import LLMDocumentProcessor
from config.config import config, LLMProvider

def test_llm_integration():
    """Test the LLM integration with a sample document"""
    print("🧪 Testing LLM Integration")
    print("=" * 40)
    
    # Check if any provider is configured
    available_providers = config.list_available_providers()
    if not any(available_providers.values()):
        print("❌ No API keys configured. Please configure at least one provider.")
        print("💡 Run: python model_selector.py to configure API keys")
        return False
    
    # Use the first available provider
    for provider_name, is_configured in available_providers.items():
        if is_configured:
            provider = LLMProvider(provider_name)
            api_key = config.get_api_key(provider)
            if api_key:
                processor = LLMDocumentProcessor(provider=provider, api_key=api_key)
                break
    
    # Test API connection
    print("🔗 Testing API connection...")
    if processor.test_api_connection():
        print("✅ API connection successful!")
    else:
        print("❌ API connection failed. Please check your API key.")
        print("💡 Run: python model_selector.py to configure API keys")
        return False
    
    # Test with a sample document if available
    test_doc = Path("../Stately 24-118 Order Instanity Eval.docx")
    if test_doc.exists():
        print(f"\n📄 Testing with document: {test_doc.name}")
        
        # Test document analysis
        print("🔍 Testing document analysis...")
        try:
            analysis = processor.analyze_document(
                str(test_doc), 
                analysis_type="summary",
                max_tokens=500
            )
            if analysis:
                print("✅ Document analysis successful!")
                print(f"📝 Analysis preview: {analysis[:200]}...")
            else:
                print("❌ Document analysis failed")
        except Exception as e:
            print(f"❌ Analysis error: {e}")
        
        # Test document editing (with a simple instruction)
        print("\n✏️ Testing document editing...")
        try:
            result = processor.process_document(
                str(test_doc),
                "Make the language slightly more formal",
                output_suffix="_test_edit",
                max_tokens=1000
            )
            if result:
                print("✅ Document editing successful!")
                print(f"📁 Edited document: {result}")
            else:
                print("❌ Document editing failed")
        except Exception as e:
            print(f"❌ Editing error: {e}")
    
    else:
        print("📄 No test document found. Place a DOCX file in the parent directory to test.")
    
    print("\n✅ LLM integration test complete!")

def demo_usage():
    """Demonstrate usage examples"""
    print("\n📚 Usage Examples:")
    print("=" * 40)
    
    print("1. Configure API keys:")
    print("   python model_selector.py")
    
    print("\n2. Test connection:")
    print("   python llm_document_processor.py test-connection")
    
    print("\n3. Edit a document:")
    print("   python llm_document_processor.py edit \"document.docx\" \"Make the language more formal\"")
    
    print("\n4. Analyze a document:")
    print("   python llm_document_processor.py analyze \"document.docx\" legal")
    
    print("\n5. Get a summary:")
    print("   python llm_document_processor.py analyze \"document.docx\" summary")
    
    print("\n6. Check citations:")
    print("   python run_citation_check.py \"document.docx\" --debug")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_usage()
    else:
        test_llm_integration() 