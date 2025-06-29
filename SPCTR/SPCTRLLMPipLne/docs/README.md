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
├── core/                           # Core document processing modules
│   ├── extract_docx_xml.py         # Extract raw XML from DOCX files
│   ├── xml_to_anchored_txt.py      # Convert XML to anchored text with tokens
│   ├── anchored_txt_to_xml.py      # Convert anchored text back to XML
│   ├── repackage_docx_xml.py       # Reconstruct DOCX from modified XML
│   ├── docx_extractor.py           # Enhanced DOCX text extraction with formatting
│   ├── docx_reconstructor.py       # DOCX reconstruction with formatting preservation
│   └── xml_analyzer.py             # XML structure analysis and debugging
│
├── llm/                            # LLM integration and processing
│   ├── llm_client.py               # LLM API client with retry logic and timeout handling
│   ├── llm_document_processor.py   # Main CLI interface for all LLM operations
│   ├── legal_citation_checker.py   # Legal citation analysis with Bluebook compliance
│   ├── token_estimator.py          # Token counting, batching, and context management
│   └── prompt_editor.py            # Utility for managing and editing LLM prompts
│
├── config/                         # Configuration and settings
│   ├── config.py                   # API key management and global settings
│   └── legal_citation_prompt.txt   # Configurable prompt for citation analysis
│
├── utils/                          # Utility scripts and testing
│   ├── cleanup_test_files.py       # Cleanup utility for temporary files
│   └── test_llm_integration.py     # Test script for LLM API integration
│
├── docs/                           # Documentation
│   ├── README.md                   # This file - main project documentation
│   ├── ANCHOR_PIPELINE_README.md   # Technical details of XML preservation system
│   ├── LLM_INTEGRATION_README.md   # LLM API setup and usage guide
│   └── COMPLETE_SYSTEM_README.md   # Complete system architecture overview
│
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Python dependencies
└── .llm_handshake_status.json     # API connection status cache
```

## 🔧 Core Module Details

### `core/` - Document Processing Pipeline

**`extract_docx_xml.py`**
- Extracts the raw `word/document.xml` from DOCX files
- Saves XML as `.txt` file for processing
- Returns the output file path for pipeline integration

**`xml_to_anchored_txt.py`**
- Converts XML to text with invisible anchor tokens (`<A001>`, `<A002>`, etc.)
- Preserves formatting tags (`<bold>`, `<italic>`, `<underline>`, etc.)
- Maintains paragraph structure and document hierarchy
- Essential for LLM processing with context preservation

**`anchored_txt_to_xml.py`**
- Converts processed anchored text back to XML format
- Reconstructs document structure from LLM-modified text
- Preserves all formatting and anchor tokens

**`repackage_docx_xml.py`**
- Reconstructs complete DOCX files from modified XML
- Maintains all original document properties and relationships
- Enables round-trip document processing

**`docx_extractor.py`**
- Advanced DOCX text extraction with enhanced formatting preservation
- Handles justification, tabs, footnotes, and complex formatting
- Extracts footnotes as inline parentheticals
- Preserves superscript numbers and special formatting

**`docx_reconstructor.py`**
- Reconstructs DOCX files with enhanced formatting preservation
- Maintains original document structure and properties
- Handles complex formatting elements and relationships

**`xml_analyzer.py`**
- Analyzes XML structure for debugging and development
- Provides detailed insights into document formatting
- Useful for troubleshooting and optimization

## 🤖 LLM Module Details

### `llm/` - AI Integration and Processing

**`llm_client.py`**
- LLM API client with robust error handling and retry logic
- Supports chat completion, document editing, and analysis
- Configurable timeouts and connection management
- Handles API responses and JSON parsing

**`llm_document_processor.py`**
- Main CLI interface for all LLM-powered operations
- Commands: setup, test, handshake, edit, analyze, check-citations, prompt-editor
- Integrates all pipeline components for seamless operation
- Provides debug mode and comprehensive error reporting

**`legal_citation_checker.py`**
- Bluebook-compliant legal citation analysis
- Identifies citation errors and provides corrections
- Supports batching for large documents
- Returns structured JSON results with detailed analysis

**`token_estimator.py`**
- Intelligent token counting and context management
- Determines when batching is needed for large documents
- Optimizes API usage and prevents token limit errors
- Provides detailed token analysis and utilization statistics

**`prompt_editor.py`**
- Utility for managing and editing LLM prompts
- Supports listing, viewing, editing, and creating prompts
- Enables easy customization of LLM behavior
- Integrates with main processor for seamless prompt management

## ⚙️ Configuration Details

### `config/` - Settings and Configuration

**`config.py`**
- API key management with environment variable support
- Global settings for model, timeout, and base URL
- Secure key storage and retrieval
- Configuration validation and error handling

**`legal_citation_prompt.txt`**
- Configurable prompt for legal citation analysis
- Defines Bluebook rules and error detection criteria
- Specifies JSON output format and analysis structure
- Easily editable for customization

## 🛠️ Utility Details

### `utils/` - Helper Scripts and Testing

**`cleanup_test_files.py`**
- Removes temporary and test files
- Cleans up intermediate processing files
- Maintains clean project directory

**`test_llm_integration.py`**
- Tests LLM API connectivity and functionality
- Validates API key configuration
- Provides basic integration testing

## 📚 Documentation Details

### `docs/` - Comprehensive Documentation

**`README.md`** (This file)
- Main project documentation and user guide
- Installation and usage instructions
- Feature overview and command reference

**`ANCHOR_PIPELINE_README.md`**
- Technical details of XML preservation system
- Anchor token implementation and usage
- Pipeline architecture and data flow

**`LLM_INTEGRATION_README.md`**
- LLM API setup and configuration guide
- Model selection and parameter tuning
- Troubleshooting and best practices

**`COMPLETE_SYSTEM_README.md`**
- Complete system architecture overview
- Component interaction and data flow
- Development and extension guidelines

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
   python llm/llm_document_processor.py setup
   ```
   Or manually create a `.env` file:
   ```
   LLAMA_API_KEY=your-api-key-here
   ```

## 🚀 Quick Start

### Basic Document Processing
```bash
# Extract XML from DOCX
python core/extract_docx_xml.py "document.docx"

# Convert to anchored text
python core/xml_to_anchored_txt.py "document_raw.xml.txt"

# Reconstruct DOCX
python core/repackage_docx_xml.py "document.docx" "document_raw.xml.txt"
```

### LLM-Powered Analysis
```bash
# Test API connection
python llm/llm_document_processor.py handshake

# Check legal citations
python llm/llm_document_processor.py check-citations "document.docx" --debug

# Edit document
python llm/llm_document_processor.py edit "document.docx" "Make the text more formal"

# Analyze document
python llm/llm_document_processor.py analyze "document.docx" legal
```

### Prompt Management
```bash
# List available prompts
python llm/llm_document_processor.py prompt-editor list

# View citation prompt
python llm/llm_document_processor.py prompt-editor show legal_citation

# Edit citation prompt
python llm/llm_document_processor.py prompt-editor edit legal_citation

# Create new prompt
python llm/llm_document_processor.py prompt-editor create custom_analysis
```

## 📋 Command Reference

### Main Processor Commands (`llm/llm_document_processor.py`)
- `setup` - Configure API key
- `test` - Test API connection
- `handshake` - Verify API connectivity
- `edit <docx> <instruction>` - Edit document with LLM
- `analyze <docx> [type]` - Analyze document (general/legal/technical/summary)
- `check-citations <docx> [output.json] [--debug]` - Check legal citations
- `prompt-editor` - Manage LLM prompts

### Core Processing Commands
- `core/extract_docx_xml.py <docx>` - Extract XML from DOCX
- `core/xml_to_anchored_txt.py <xml>` - Convert XML to anchored text
- `core/anchored_txt_to_xml.py <txt>` - Convert anchored text to XML
- `core/repackage_docx_xml.py <docx> <xml>` - Reconstruct DOCX

### Utility Commands
- `utils/cleanup_test_files.py` - Clean up temporary files
- `utils/test_llm_integration.py` - Test LLM integration

## 🔧 Configuration

### API Settings
The system uses a `.env` file for API configuration:
```
LLAMA_API_KEY=your-api-key-here
```

### Prompt Customization
All LLM prompts are stored in `config/` and can be easily edited:
- `config/legal_citation_prompt.txt` - Legal citation analysis rules
- Create additional prompts in `config/` for custom analysis types

### Model Settings
Default model settings can be modified in `config/config.py`:
- Model: `llama3.2-3b`
- Base URL: `https://api.llmapi.com`
- Timeout: 120 seconds
- Max tokens: 8000

## 🔍 Debugging

### Enable Debug Mode
Add `--debug` flag to any command for detailed output:
```bash
python llm/llm_document_processor.py check-citations "document.docx" --debug
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
1. Create new prompt file in `config/` for custom analysis
2. Add new command to `llm/llm_document_processor.py`
3. Update documentation in `docs/`
4. Test with various document types

### Development Workflow
1. Core processing modules in `core/`
2. LLM integration in `llm/`
3. Configuration in `config/`
4. Utilities in `utils/`
5. Documentation in `docs/`

## 📚 Additional Documentation

- `docs/ANCHOR_PIPELINE_README.md` - Technical details of XML preservation
- `docs/LLM_INTEGRATION_README.md` - LLM API setup and usage
- `docs/COMPLETE_SYSTEM_README.md` - Complete system architecture

## 🆘 Support

### Troubleshooting
1. Check API key configuration in `config/`
2. Verify document file paths
3. Enable debug mode for detailed logs
4. Check token limits for large documents

### Getting Help
- Review debug output for specific errors
- Check prompt files in `config/` for customization issues
- Verify API connectivity with handshake command
- Consult documentation in `docs/` folder

---

**Version**: 2.0  
**Last Updated**: December 2024  
**License**: MIT 