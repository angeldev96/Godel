# SPCTR LLM Pipeline

A comprehensive document processing pipeline that extracts text from Word documents (.docx) with enhanced formatting preservation and integrates with LLM APIs for advanced document analysis and editing.

## 🚀 Features

### Core Document Processing
- **Enhanced DOCX Extraction**: Preserves text justification, tabs, footnotes, and formatting
- **XML Preservation**: Maintains 100% of original XML structure with anchor tokens
- **Round-trip Fidelity**: Extract → Process → Reconstruct with perfect formatting preservation
- **Batch Processing**: Handle large documents with intelligent batching

### LLM Integration
- **Legal Citation Checking**: Bluebook-compliant citation analysis with detailed error reporting
- **Document Editing**: AI-powered document modification with instruction following
- **Document Analysis**: Multiple analysis types (general, legal, technical, summary)
- **Configurable Prompts**: Easy-to-edit prompt files for customization

### Developer Tools
- **Prompt Editor**: Built-in utility for managing and editing LLM prompts
- **API Management**: Secure API key storage and connection testing
- **Debug Mode**: Comprehensive logging and error reporting
- **Token Estimation**: Intelligent batching based on model limits

## 📁 Project Structure

```
SPCTRLLMPipLne/
├── Core Processing/
│   ├── extract_docx_xml.py          # Extract raw XML from DOCX
│   ├── xml_to_anchored_txt.py       # Convert XML to anchored text
│   ├── anchored_txt_to_xml.py       # Convert anchored text back to XML
│   └── repackage_docx_xml.py        # Reconstruct DOCX from XML
│
├── LLM Integration/
│   ├── llm_client.py                # LLM API client with retry logic
│   ├── llm_document_processor.py    # Main CLI interface
│   ├── legal_citation_checker.py    # Legal citation analysis
│   └── token_estimator.py           # Token counting and batching
│
├── Configuration/
│   ├── config.py                    # API key and settings management
│   ├── legal_citation_prompt.txt    # Configurable citation analysis prompt
│   └── prompt_editor.py             # Prompt management utility
│
├── Utilities/
│   ├── xml_analyzer.py              # XML structure analysis
│   └── cleanup_test_files.py        # Cleanup utility
│
└── Documentation/
    ├── README.md                    # This file
    ├── ANCHOR_PIPELINE_README.md    # Technical details
    ├── LLM_INTEGRATION_README.md    # LLM setup guide
    └── COMPLETE_SYSTEM_README.md    # Complete system overview
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SPCTRLLMPipLne
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**
   ```bash
   python llm_document_processor.py setup
   ```
   Or manually create a `.env` file:
   ```
   LLAMA_API_KEY=your-api-key-here
   ```

## 🚀 Quick Start

### Basic Document Processing
```bash
# Extract XML from DOCX
python extract_docx_xml.py "document.docx"

# Convert to anchored text
python xml_to_anchored_txt.py "document_raw.xml.txt"

# Reconstruct DOCX
python repackage_docx_xml.py "document.docx" "document_raw.xml.txt"
```

### LLM-Powered Analysis
```bash
# Test API connection
python llm_document_processor.py handshake

# Check legal citations
python llm_document_processor.py check-citations "document.docx" --debug

# Edit document
python llm_document_processor.py edit "document.docx" "Make the text more formal"

# Analyze document
python llm_document_processor.py analyze "document.docx" legal
```

### Prompt Management
```bash
# List available prompts
python llm_document_processor.py prompt-editor list

# View citation prompt
python llm_document_processor.py prompt-editor show legal_citation

# Edit citation prompt
python llm_document_processor.py prompt-editor edit legal_citation

# Create new prompt
python llm_document_processor.py prompt-editor create custom_analysis
```

## 📋 Command Reference

### Main Processor Commands
- `setup` - Configure API key
- `test` - Test API connection
- `handshake` - Verify API connectivity
- `edit <docx> <instruction>` - Edit document with LLM
- `analyze <docx> [type]` - Analyze document (general/legal/technical/summary)
- `check-citations <docx> [output.json] [--debug]` - Check legal citations
- `prompt-editor` - Manage LLM prompts

### Prompt Editor Commands
- `list` - List all available prompts
- `show <name>` - Show prompt content
- `edit <name>` - Edit prompt file
- `create <name>` - Create new prompt

## 🔧 Configuration

### API Settings
The system uses a `.env` file for API configuration:
```
LLAMA_API_KEY=your-api-key-here
```

### Prompt Customization
All LLM prompts are stored in `.txt` files and can be easily edited:
- `legal_citation_prompt.txt` - Legal citation analysis rules
- `document_edit_prompt.txt` - Document editing instructions
- `document_analyze_prompt.txt` - Document analysis guidelines

### Model Settings
Default model settings can be modified in `config.py`:
- Model: `llama3.2-3b`
- Base URL: `https://api.llmapi.com`
- Timeout: 120 seconds
- Max tokens: 8000

## 🔍 Debugging

### Enable Debug Mode
Add `--debug` flag to any command for detailed output:
```bash
python llm_document_processor.py check-citations "document.docx" --debug
```

### Common Issues
1. **API Timeout**: Increased timeout to 120 seconds with retry logic
2. **JSON Parsing**: Enhanced JSON extraction from LLM responses
3. **Token Limits**: Automatic batching for large documents
4. **API Key Issues**: Multiple fallback methods for key loading

### Log Files
- API responses are logged in debug mode
- Token analysis shows utilization statistics
- Error messages include detailed context

## 📊 Performance

### Token Management
- Automatic token counting and estimation
- Intelligent batching for large documents
- Context window utilization tracking
- Safety margins to prevent overflows

### Processing Speed
- XML extraction: ~1-2 seconds per document
- LLM processing: Varies by document size and API response time
- Batching: Reduces API calls for large documents

## 🔒 Security

### API Key Protection
- Keys stored in `.env` file (not in code)
- Environment variable fallback
- No key logging in debug output
- Secure key masking in logs

### Data Privacy
- Local processing by default
- No data sent to external services except LLM API
- Temporary files cleaned up automatically

## 🤝 Contributing

### Code Organization
- Modular design for easy extension
- Clear separation of concerns
- Comprehensive error handling
- Type hints for better IDE support

### Adding New Features
1. Create new prompt file for custom analysis
2. Add new command to main processor
3. Update documentation
4. Test with various document types

## 📚 Documentation

- `ANCHOR_PIPELINE_README.md` - Technical details of XML preservation
- `LLM_INTEGRATION_README.md` - LLM API setup and usage
- `COMPLETE_SYSTEM_README.md` - Complete system architecture

## 🆘 Support

### Troubleshooting
1. Check API key configuration
2. Verify document file paths
3. Enable debug mode for detailed logs
4. Check token limits for large documents

### Getting Help
- Review debug output for specific errors
- Check prompt files for customization issues
- Verify API connectivity with handshake command

---

**Version**: 2.0  
**Last Updated**: December 2024  
**License**: MIT 