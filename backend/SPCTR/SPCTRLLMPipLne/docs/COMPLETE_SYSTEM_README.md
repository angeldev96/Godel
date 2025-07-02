# Complete Document Processing System

A comprehensive solution for intelligent document processing using anchor tokens and LLM integration.

## 🎯 Overview

This system provides:
- **Perfect Format Preservation**: Round-trip DOCX conversion with 100% fidelity
- **LLM-Friendly Processing**: Clean text with minimal token overhead
- **Intelligent Editing**: AI-powered document modification and analysis
- **Secure API Integration**: Protected API key management
- **Complete Pipeline**: End-to-end processing from DOCX to LLM and back

## 🏗️ Architecture

```
DOCX Document
     ↓
Extract XML (extract_docx_xml.py)
     ↓
Add Anchor Tokens (xml_to_anchored_txt.py)
     ↓
Clean LLM Text with <A001>, <A002> tokens
     ↓
Send to LLM API (llm_client.py)
     ↓
Receive Edited Text
     ↓
Reconstruct XML (anchored_txt_to_xml.py)
     ↓
Repackage DOCX (repackage_docx_xml.py)
     ↓
Final Edited Document
```

## 🚀 Quick Start

### 1. Setup API Key
```bash
python llm_document_processor.py setup "your_llama_api_key"
```

### 2. Test Connection
```bash
python llm_document_processor.py test
```

### 3. Process a Document
```bash
# Edit document
python llm_document_processor.py edit "document.docx" "Make the language more formal"

# Analyze document
python llm_document_processor.py analyze "document.docx" legal
```

## 📁 File Structure

```
SPCTRLLMPipLne/
├── Core Pipeline
│   ├── extract_docx_xml.py              # DOCX → XML
│   ├── xml_to_anchored_txt.py           # XML → Anchored TXT
│   ├── anchored_txt_to_xml.py           # Anchored TXT → XML
│   └── repackage_docx_xml.py            # XML → DOCX
│
├── LLM Integration
│   ├── config.py                        # API key management
│   ├── llm_client.py                    # LLM API client
│   └── llm_document_processor.py        # Main processor
│
├── Documentation
│   ├── ANCHOR_PIPELINE_README.md        # Anchor token details
│   ├── LLM_INTEGRATION_README.md        # LLM integration guide
│   └── COMPLETE_SYSTEM_README.md        # This file
│
├── Testing & Utilities
│   ├── test_llm_integration.py          # LLM integration tests
│   ├── cleanup_test_files.py            # Test file cleanup
│   └── requirements.txt                 # Dependencies
│
└── Security
    ├── .gitignore                       # Protects API keys
    └── .env                             # API key storage (auto-created)
```

## 🔧 Core Components

### Anchor Token Pipeline

**Purpose**: Convert DOCX to LLM-friendly text while preserving formatting

**Key Features**:
- Compact anchor tokens (`<A001>`, `<A002>`, etc.)
- Essential formatting preservation (bold, italic, underline, etc.)
- Perfect round-trip conversion
- Minimal token overhead

**Usage**:
```bash
# Extract XML
python extract_docx_xml.py "document.docx"

# Convert to anchored TXT
python xml_to_anchored_txt.py "document_raw.xml.txt"

# Convert back to XML
python anchored_txt_to_xml.py "document_raw.xml.anchored.txt" "document_raw.xml.txt"

# Repackage as DOCX
python repackage_docx_xml.py "document.docx" "document_raw.xml.anchored.reconstructed.xml"
```

### LLM Integration

**Purpose**: Intelligent document editing and analysis

**Key Features**:
- Secure API key management
- Document editing with instructions
- Multiple analysis types
- Error handling and logging

**Usage**:
```bash
# Setup API key
python llm_document_processor.py setup "your_api_key"

# Edit document
python llm_document_processor.py edit "document.docx" "Make text more formal"

# Analyze document
python llm_document_processor.py analyze "document.docx" legal
```

## 🎨 Supported Features

### Document Formatting
- ✅ **Bold text**
- ✅ *Italic text*
- ✅ <u>Underlined text</u>
- ✅ SMALL CAPS
- ✅ Superscript¹
- ✅ Tab characters
- ✅ Whitespace preservation
- ✅ Paragraph justification
- ✅ Lists and bullet points

### LLM Capabilities
- 📝 **Document Editing**: Style changes, content modification
- 🔍 **Document Analysis**: Legal, technical, general analysis
- 📊 **Summarization**: Key points and insights
- 🌐 **Translation**: Multi-language support
- 📋 **Formatting**: Structure and layout changes

## 🔒 Security

### API Key Protection
- Environment variable support
- Secure `.env` file storage
- Automatic `.gitignore` protection
- No hardcoded keys

### Data Privacy
- Local processing (no document upload)
- Secure API communication
- Input validation and sanitization
- Error logging without sensitive data

## 📊 Performance

### Token Efficiency
- Compact anchor tokens (3-4 characters each)
- Minimal XML overhead in LLM prompts
- Configurable token limits
- Cost-optimized processing

### Processing Speed
- Fast XML extraction and parsing
- Efficient anchor token generation
- Optimized API communication
- Parallel processing ready

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
python llm_document_processor.py setup "your_llama_api_key"
```

### 3. Test Installation
```bash
python test_llm_integration.py
```

## 📖 Usage Examples

### Basic Document Editing
```bash
# Make language more formal
python llm_document_processor.py edit "contract.docx" "Make the language more formal and professional"

# Add section headers
python llm_document_processor.py edit "report.docx" "Add clear section headers for each major topic"

# Convert to bullet points
python llm_document_processor.py edit "list.docx" "Convert the numbered list to bullet points"
```

### Document Analysis
```bash
# Legal analysis
python llm_document_processor.py analyze "contract.docx" legal

# Technical summary
python llm_document_processor.py analyze "manual.docx" technical

# General summary
python llm_document_processor.py analyze "report.docx" summary
```

### Advanced Processing
```python
from llm_document_processor import LLMDocumentProcessor

processor = LLMDocumentProcessor()

# Custom editing with parameters
result = processor.process_document(
    "document.docx",
    "Translate to Spanish while maintaining formal tone",
    temperature=0.2,
    max_tokens=3000
)

# Custom analysis
analysis = processor.analyze_document(
    "document.docx",
    analysis_type="legal",
    max_tokens=1500
)
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Not Configured**
   ```
   ❌ API key not configured. Run 'setup' first.
   ```
   **Solution**: `python llm_document_processor.py setup "your_key"`

2. **Connection Failed**
   ```
   ❌ API connection failed
   ```
   **Solution**: Check internet and API key validity

3. **Document Not Found**
   ```
   ❌ Document not found: document.docx
   ```
   **Solution**: Verify file path and permissions

4. **Processing Failed**
   ```
   ❌ Document processing failed: [error]
   ```
   **Solution**: Check document format and try smaller files

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Advanced Features

### Custom Anchor Tokens
Modify `xml_to_anchored_txt.py` to use different token formats:
```python
# Change from <A001> to <P1>
anchor_token = f"<P{paragraph_counter}>"
```

### Custom LLM Prompts
Modify `llm_client.py` to use different system prompts:
```python
system_prompt = """Your custom prompt here..."""
```

### Batch Processing
Process multiple documents:
```python
documents = ["doc1.docx", "doc2.docx", "doc3.docx"]
for doc in documents:
    processor.process_document(doc, "Make formal")
```

## 🔮 Future Enhancements

1. **Web Interface**: GUI for document processing
2. **Batch Processing**: Multiple document handling
3. **Custom Models**: Support for different LLM providers
4. **Advanced Analytics**: Detailed document insights
5. **Template System**: Predefined editing templates
6. **Streaming Responses**: Real-time LLM output
7. **Version Control**: Document change tracking
8. **Collaboration**: Multi-user editing support

## 📞 Support

### Documentation
- `ANCHOR_PIPELINE_README.md`: Anchor token details
- `LLM_INTEGRATION_README.md`: LLM integration guide
- `test_llm_integration.py`: Test examples

### Testing
```bash
# Run integration tests
python test_llm_integration.py

# Show usage examples
python test_llm_integration.py demo
```

### Error Reporting
1. Check troubleshooting section
2. Verify API key and connection
3. Test with simple documents
4. Review error logs
5. Check file permissions

## 📄 License

This project is designed for document processing and LLM integration. Ensure compliance with your API provider's terms of service.

---

**🎉 Ready to process documents intelligently!** 

You can use the following command to check citations:
```bash
python llm_document_processor.py check-citations "..\\Stately 24-118 Order Instanity Eval.docx" --debug
``` 