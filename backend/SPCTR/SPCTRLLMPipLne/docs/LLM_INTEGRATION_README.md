# LLM Integration for Document Processing

This module provides seamless integration with the Llama LLM API for intelligent document editing and analysis using the anchor token pipeline.

## Overview

The LLM integration enables:
- **Intelligent Document Editing**: Send documents to LLM with specific editing instructions
- **Document Analysis**: Get AI-powered insights and summaries
- **Secure API Key Management**: Protected storage and environment variable support
- **Complete Pipeline Integration**: End-to-end processing from DOCX to LLM and back

## Quick Start

### 1. Setup API Key

```bash
# Set your Llama API key
python llm_document_processor.py setup "your_api_key_here"
```

### 2. Test Connection

```bash
# Verify API connection
python llm_document_processor.py test
```

### 3. Edit a Document

```bash
# Edit a document with specific instruction
python llm_document_processor.py edit "document.docx" "Make the language more formal and professional"
```

### 4. Analyze a Document

```bash
# Get general analysis
python llm_document_processor.py analyze "document.docx"

# Get legal analysis
python llm_document_processor.py analyze "document.docx" legal

# Get technical analysis
python llm_document_processor.py analyze "document.docx" technical

# Get summary
python llm_document_processor.py analyze "document.docx" summary
```

## API Configuration

### Environment Variables

Set your API key as an environment variable:
```bash
export LLAMA_API_KEY="your_api_key_here"
```

### Configuration File

The system automatically creates a `.env` file in the project directory:
```
LLAMA_API_KEY=your_api_key_here
```

**⚠️ Security Note**: The `.env` file is automatically added to `.gitignore` to prevent accidental commits.

## Core Components

### 1. `config.py`
Manages API key configuration and environment variables.

**Features:**
- Environment variable support
- Secure `.env` file storage
- Automatic key validation
- Cross-platform compatibility

### 2. `llm_client.py`
Direct API client for Llama LLM integration.

**Methods:**
- `chat_completion()`: Basic chat completion
- `edit_document()`: Document editing with anchor tokens
- `analyze_document()`: Document analysis
- `test_connection()`: API connectivity test

### 3. `llm_document_processor.py`
Main processor integrating anchor token pipeline with LLM API.

**Features:**
- Complete document processing pipeline
- CLI interface for easy use
- Multiple analysis types
- Error handling and logging

## API Endpoints

The integration uses the Llama API at `https://api.llmapi.com`:

### Chat Completions
```
POST /chat/completions
```

**Request Format:**
```json
{
  "model": "llama3.2-3b",
  "messages": [
    {
      "role": "system",
      "content": "You are a document editing assistant..."
    },
    {
      "role": "user", 
      "content": "Instruction: Make text more formal\n\nDocument: <A001>..."
    }
  ],
  "temperature": 0.3,
  "max_tokens": 2000
}
```

## Document Editing

### Supported Instructions

The LLM can handle various editing instructions:

- **Style Changes**: "Make the language more formal/casual"
- **Content Editing**: "Add a conclusion paragraph"
- **Formatting**: "Convert to bullet points"
- **Translation**: "Translate to Spanish"
- **Summarization**: "Summarize each paragraph"
- **Custom Edits**: Any specific editing instruction

### Example Usage

```python
from llm_document_processor import LLMDocumentProcessor

processor = LLMDocumentProcessor()

# Edit document
result = processor.process_document(
    "legal_document.docx",
    "Make the language more formal and add section headers",
    temperature=0.3
)

# Analyze document
analysis = processor.analyze_document(
    "legal_document.docx", 
    analysis_type="legal"
)
```

## Document Analysis

### Analysis Types

1. **General**: Overall document analysis and themes
2. **Legal**: Legal arguments, citations, procedural elements
3. **Technical**: Technical terms, concepts, and specifications
4. **Summary**: Concise summary of main points

### Analysis Output

Each analysis generates a text file with the same name as the document:
- `document.general_analysis.txt`
- `document.legal_analysis.txt`
- `document.technical_analysis.txt`
- `document.summary_analysis.txt`

## Error Handling

The system includes comprehensive error handling:

- **API Connection Errors**: Network and authentication issues
- **Document Processing Errors**: File format and parsing issues
- **LLM Response Errors**: Invalid or empty responses
- **Configuration Errors**: Missing API keys

## Security Features

1. **API Key Protection**: Stored in `.env` file (gitignored)
2. **Environment Variables**: Secure runtime configuration
3. **Input Validation**: Sanitized document processing
4. **Error Logging**: No sensitive data in error messages

## Performance Optimization

### Token Management
- Efficient anchor token format (minimal overhead)
- Configurable max_tokens for cost control
- Temperature settings for creativity vs. consistency

### Batch Processing
- Process multiple documents sequentially
- Reuse API connections when possible
- Parallel processing support (future enhancement)

## Troubleshooting

### Common Issues

1. **API Key Not Configured**
   ```
   ❌ API key not configured. Run 'setup' first.
   ```
   **Solution**: Run `python llm_document_processor.py setup "your_key"`

2. **Connection Failed**
   ```
   ❌ API connection failed
   ```
   **Solution**: Check internet connection and API key validity

3. **Document Not Found**
   ```
   ❌ Document not found: document.docx
   ```
   **Solution**: Verify file path and permissions

4. **Processing Failed**
   ```
   ❌ Document processing failed: [error]
   ```
   **Solution**: Check document format and try with smaller files

### Debug Mode

Enable verbose logging by modifying the processor:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Streaming Responses**: Real-time LLM output
2. **Batch Processing**: Multiple document handling
3. **Custom Models**: Support for different LLM models
4. **Web Interface**: GUI for document processing
5. **Advanced Analytics**: Detailed document insights
6. **Template System**: Predefined editing templates

## API Rate Limits

The Llama API may have rate limits. The system includes:
- Automatic retry logic
- Exponential backoff
- Request queuing (future)
- Rate limit monitoring

## Cost Optimization

To minimize API costs:
- Use lower `max_tokens` for simple edits
- Set `temperature=0.1` for consistent results
- Process documents in chunks for large files
- Cache analysis results when possible

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify API key and connection
3. Test with simple documents first
4. Review error logs for details 