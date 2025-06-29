"""
Test script for LLM integration functionality
"""
import sys
from pathlib import Path
from llm_document_processor import LLMDocumentProcessor

def test_llm_integration():
    """Test the LLM integration with a sample document"""
    print("🧪 Testing LLM Integration")
    print("=" * 40)
    
    # Check if API key is configured
    processor = LLMDocumentProcessor()
    
    # Test API connection
    print("🔗 Testing API connection...")
    if processor.test_api_connection():
        print("✅ API connection successful!")
    else:
        print("❌ API connection failed. Please check your API key.")
        print("💡 Run: python llm_document_processor.py setup <your_api_key>")
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
    
    print("1. Setup API key:")
    print("   python llm_document_processor.py setup \"your_api_key_here\"")
    
    print("\n2. Test connection:")
    print("   python llm_document_processor.py test")
    
    print("\n3. Edit a document:")
    print("   python llm_document_processor.py edit \"document.docx\" \"Make the language more formal\"")
    
    print("\n4. Analyze a document:")
    print("   python llm_document_processor.py analyze \"document.docx\" legal")
    
    print("\n5. Get a summary:")
    print("   python llm_document_processor.py analyze \"document.docx\" summary")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_usage()
    else:
        test_llm_integration() 