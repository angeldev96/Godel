# SPCTR LLM Pipeline

A comprehensive document processing pipeline for extracting, analyzing, and editing Word documents (.docx) with advanced formatting preservation, LLM-powered legal citation checking, and **metadata tracking with timestamps**.

## 🚀 Features

- **Perfect Format Preservation**: Round-trip DOCX conversion with 100% fidelity
- **LLM-Friendly Processing**: Clean text with minimal token overhead
- **Legal Citation Checking**: Bluebook-compliant, with second-pass reasoning validation
- **Intelligent Editing**: AI-powered document modification and analysis
- **Batch Processing**: Handles large documents with intelligent batching
- **Secure API Integration**: Protected API key management
- **📋 Metadata Tracking**: Timestamp-based version control and processing history
- **🆔 Processing IDs**: Unique identifiers for each processing operation
- **📊 Processing Analytics**: Detailed step-by-step tracking and performance metrics

## 📁 Project Structure

```
SPCTRLLMPipLne/
├── core/                           # Core document processing modules
│   ├── extract_docx_xml.py         # Extract raw XML from DOCX files
│   ├── xml_to_anchored_txt.py      # Convert XML to anchored text with tokens
│   ├── anchored_txt_to_xml.py      # Convert anchored text back to XML
│   ├── repackage_docx_xml.py       # Reconstruct DOCX from modified XML
│   ├── docx_extractor.py           # Enhanced DOCX text extraction
│   ├── docx_reconstructor.py       # DOCX reconstruction
│   └── xml_analyzer.py             # XML structure analysis
│
├── llm/                            # LLM integration and processing
│   ├── llm_client.py               # LLM API client
│   ├── llm_document_processor.py   # Main CLI interface for all LLM operations
│   ├── legal_citation_checker.py   # Legal citation analysis
│   ├── reasoning_citation_validator.py # Second-pass reasoning validation
│   ├── token_estimator.py          # Token counting, batching, and context management
│   └── prompt_editor.py            # Utility for managing and editing LLM prompts
│
├── utils/                          # Utility modules
│   └── metadata_manager.py         # Metadata tracking and version control
│
├── config/                         # Configuration and settings
│   ├── config.py                   # API key management and global settings
│   └── legal_citation_prompt.txt   # Configurable prompt for citation analysis
│
├── docs/                           # Documentation
│   ├── README.md                   # This file - main project documentation
│   ├── ANCHOR_PIPELINE_README.md   # Technical details of XML preservation system
│   ├── LLM_INTEGRATION_README.md   # LLM API setup and usage guide
│   ├── COMPLETE_SYSTEM_README.md   # Complete system architecture overview
│   └── REASONING_VALIDATION_README.md # Reasoning validation system
│
├── .metadata/                      # Metadata storage (auto-created)
├── requirements.txt                # Python dependencies
└── .gitignore                      # Git ignore rules
```

## 🔧 Core Module Details

See `docs/COMPLETE_SYSTEM_README.md` and `docs/ANCHOR_PIPELINE_README.md` for technical details on the document processing pipeline.

## 🤖 LLM Module Details

- **Citation Checking**: See `llm/legal_citation_checker.py` and `llm/reasoning_citation_validator.py` for Bluebook-compliant and reasoning-based validation.
- **Main CLI**: Use `llm/llm_document_processor.py` for all LLM-powered operations.
- **Prompt Management**: Use `llm/prompt_editor.py` and edit prompts in `config/`.

## 🧠 Reasoning-Based Validation

See `docs/REASONING_VALIDATION_README.md` for details on the second-pass reasoning system that improves citation accuracy using OpenAI's advanced models.

## 📋 Metadata Tracking System

The pipeline now includes comprehensive metadata tracking that helps prevent confusion when processing the same document multiple times:

### Key Features:
- **🆔 Unique Processing IDs**: Each processing operation gets a unique identifier
- **⏰ Timestamp Tracking**: Start/end times and duration for each operation
- **📄 File Versioning**: Hash-based file identification to track document versions
- **🔧 Step-by-Step Tracking**: Detailed logging of each pipeline step
- **📊 Performance Metrics**: Processing time, file sizes, and success/failure status
- **📁 Output File Management**: Automatic tracking of all generated files

### Metadata Commands:
```bash
# View metadata for a document
python llm/llm_document_processor.py metadata "document.docx"

# Show all processing versions
python llm/llm_document_processor.py metadata "document.docx" --show-versions

# Show latest processing version
python llm/llm_document_processor.py metadata "document.docx" --show-latest

# Show specific processing by ID
python llm/llm_document_processor.py metadata "document.docx" --processing-id proc_1234567890

# Clean up old metadata files
python llm/llm_document_processor.py cleanup-metadata --days 30
```

### Example Metadata Output:
```
📋 PROCESSING SUMMARY
============================================================
🆔 Processing ID: proc_1703123456789
📄 Document: Stately 24-118 Order Instanity Eval.docx
⏰ Start Time: 2023-12-21T14:30:45.123456
⏱️  Duration: 12.34 seconds
📁 Working Directory: C:\Users\bsusl\SPCTR

🔧 Pipeline Steps (5):
  1. ✅ extract_xml - 2023-12-21T14:30:45.234567
  2. ✅ convert_to_anchored_txt - 2023-12-21T14:30:46.345678
  3. ✅ citation_checking_start - 2023-12-21T14:30:47.456789
  4. ✅ citation_checking_complete - 2023-12-21T14:30:57.567890
  5. ✅ metadata_save - 2023-12-21T14:30:57.678901

📤 Output Files (3):
  📄 Stately_24-118_Order_Instanity_Eval_raw.xml.txt (47.23 KB)
  📄 Stately_24-118_Order_Instanity_Eval_raw.xml.anchored.txt (7.45 KB)
  📄 Stately_24-118_Order_Instanity_Eval_citations_proc_1703123456789_20231221_143057.json (3.67 KB)
============================================================
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
   python llm/llm_document_processor.py setup
   # Or manually create a .env file
   # OPENAI_API_KEY=your-api-key-here
   ```

## 🚀 Quick Start

### Basic Document Processing
```bash
python core/extract_docx_xml.py "document.docx"
python core/xml_to_anchored_txt.py "document_raw.xml.txt"
python core/repackage_docx_xml.py "document.docx" "document_raw.xml.txt"
```

### LLM-Powered Analysis with Metadata Tracking
```bash
python llm/llm_document_processor.py handshake
python llm/llm_document_processor.py check-citations "document.docx" --reasoning --debug
python llm/llm_document_processor.py edit "document.docx" "Make the text more formal"
python llm/llm_document_processor.py analyze "document.docx" legal
```

### Metadata Management
```bash
# View processing history
python llm/llm_document_processor.py metadata "document.docx" --show-versions

# Check latest processing
python llm/llm_document_processor.py metadata "document.docx" --show-latest

# Clean up old metadata
python llm/llm_document_processor.py cleanup-metadata --days 30
```

### Prompt Management
```bash
python llm/llm_document_processor.py prompt-editor list
python llm/llm_document_processor.py prompt-editor show legal_citation
python llm/llm_document_processor.py prompt-editor edit legal_citation
python llm/llm_document_processor.py prompt-editor create custom_analysis
```

## 📋 Command Reference

### Main Processor Commands (`llm/llm_document_processor.py`)
- `setup` - Configure API key
- `test` - Test API connection
- `handshake` - Verify API connectivity
- `edit <docx> <instruction>` - Edit document with LLM
- `analyze <docx> [type]` - Analyze document (general/legal/technical/summary)
- `check-citations <docx> [output.json] [--debug] [--reasoning|--no-reasoning]` - Check legal citations (with optional reasoning validation)
- `check-citations-batched <docx> [--batch-size N] [--context-overlap N] [--reasoning|--no-reasoning]` - Batched citation checking
- `prompt-editor` - Manage LLM prompts
- `metadata <docx> [--show-versions] [--show-latest] [--processing-id <id>]` - View processing metadata
- `cleanup-metadata [--days <30>]` - Clean up old metadata files

### Core Processing Commands
- `core/extract_docx_xml.py <docx>` - Extract XML from DOCX
- `core/xml_to_anchored_txt.py <xml>` - Convert XML to anchored text
- `core/anchored_txt_to_xml.py <txt>` - Convert anchored text to XML
- `core/repackage_docx_xml.py <docx> <xml>` - Reconstruct DOCX

## ⚙️ Configuration

- API keys in `.env` or via `setup` command
- Prompts in `config/`
- Model settings in `config/config.py`
- Metadata stored in `.metadata/` directory (auto-created)

## 🧠 Reasoning Validation

The reasoning validation system uses OpenAI's advanced models (o4-mini, o3, etc.) for second-pass citation validation:

```bash
# Enable reasoning validation (default)
python llm/llm_document_processor.py check-citations "document.docx" --reasoning

# Disable reasoning validation
python llm/llm_document_processor.py check-citations "document.docx" --no-reasoning
```

## 📊 Metadata Benefits

### Version Control
- **Prevent Confusion**: Each processing operation is uniquely identified
- **Track Changes**: See when documents were processed and what changed
- **File Integrity**: Hash-based verification ensures you're working with the right version

### Quality Assurance
- **Processing History**: Complete audit trail of all operations
- **Performance Monitoring**: Track processing times and identify bottlenecks
- **Error Tracking**: Detailed error logs for debugging

### File Management
- **Automatic Organization**: Output files are automatically named with timestamps
- **Cleanup Tools**: Remove old metadata to keep workspace organized
- **Cross-Reference**: Link processing operations to specific file versions

## 🧪 Testing

Test the metadata functionality:
```bash
python test_metadata.py
```

## 🔮 Future Enhancements

1. **Web Interface**: GUI for document processing with metadata visualization
2. **Advanced Analytics**: Processing performance dashboards
3. **Collaboration Features**: Multi-user metadata tracking
4. **Integration APIs**: REST API for metadata access
5. **Export Capabilities**: Export metadata to various formats (CSV, JSON, etc.)

## 📞 Support

### Documentation
- `ANCHOR_PIPELINE_README.md`: Anchor token details
- `LLM_INTEGRATION_README.md`: LLM integration guide
- `REASONING_VALIDATION_README.md`: Reasoning validation system
- `test_metadata.py`: Metadata functionality test

### Error Reporting
1. Check troubleshooting section
2. Verify API key and connection
3. Test with simple documents
4. Review error logs and metadata
5. Check file permissions

## 📄 License

This project is designed for document processing and LLM integration. Ensure compliance with your API provider's terms of service.

---

**🎉 Ready to process documents intelligently with full metadata tracking!** 