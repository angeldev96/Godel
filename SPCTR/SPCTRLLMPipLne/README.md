# SPCTR LLM Pipeline

## Overview

SPCTR (Specialized Processing and Contextual Text Recognition) is an advanced pipeline for processing legal documents with Large Language Models (LLMs). The system preserves crucial formatting information that is often lost when documents are processed by LLMs, ensuring that semantic meaning is maintained throughout the analysis process.

## Problem Statement

Legal documents contain formatting that carries significant semantic meaning:
- **Bold text** often indicates defined terms or important clauses
- **Italics** may indicate emphasis or foreign terms
- **Superscript** typically denotes footnote references
- **Small caps** often indicate section headers or defined terms
- **Justified text** is common in legal formatting
- **Footnotes** contain critical legal citations and references

When these formatting elements are lost during LLM processing, the model may miss crucial context and produce inaccurate analyses.

## Pipeline Architecture

```
User Upload (DOCX) → Advanced Text Extraction → Formatting Tagging → LLM Processing → Output Display
```

### 1. Document Upload
- Accepts `.docx` files from users
- Validates file format and structure

### 2. Advanced Text Extraction
- Extracts text while preserving all formatting information
- Handles complex document structures
- Extracts footnotes and references

### 3. Formatting Tagging
- Converts formatting to XML-like tags
- Preserves semantic meaning for LLM processing
- Maintains document structure and hierarchy

### 4. LLM Processing
- Passes tagged text to one or more LLMs
- Enables models to understand formatting context
- Supports multiple model comparison

### 5. Output Display
- Presents LLM analysis results
- Maintains formatting context in output
- Provides user-friendly interface

## Features

### Formatting Preservation
- **Bold Text**: `<bold>text</bold>`
- **Italic Text**: `<italic>text</italic>`
- **Underlined Text**: `<underline>text</underline>`
- **Small Caps**: `<smallcaps>TEXT</smallcaps>`
- **Superscript**: `<superscript>text</superscript>`
- **Subscript**: `<subscript>text</subscript>`
- **Font Information**: `<font_size=24>text</font_size>`
- **Justification**: `<justify_center>text</justify_center>`

### Document Processing
- Extracts main document text with formatting
- Separates and preserves footnotes
- Maintains paragraph structure
- Handles complex legal document layouts

### LLM Integration
- Supports multiple LLM providers (OpenAI, Anthropic, etc.)
- Configurable model selection
- Batch processing capabilities
- Result comparison and analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SingularityUS/SPCTRLLMPipLne.git
cd SPCTRLLMPipLne
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (for LLM APIs):
```bash
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
```

## Usage

### Basic Text Extraction

```python
from docx_extractor import extract_docx_text

# Extract text with formatting preserved
result = extract_docx_text("path/to/document.docx")

print("Main text:")
print(result['main_text'])

if 'footnotes' in result:
    print("Footnotes:")
    print(result['footnotes'])
```

### Command Line Usage

```bash
python docx_extractor.py path/to/document.docx
```

### Testing

Run the test script to see the extractor in action:

```bash
python test_extractor.py
```

## Example Output

Input document with formatting:
```
This is a bold and italic text in a legal document.
This contains a footnote reference¹ and another².
THIS IS SMALL CAPS TEXT
```

Extracted tagged text:
```xml
This is a <bold>bold</bold> and <italic>italic</italic> text in a legal document.

This contains a footnote reference<superscript>1</superscript> and another<superscript>2</superscript>.

<smallcaps>THIS IS SMALL CAPS TEXT</smallcaps>
```

## Project Structure

```
SPCTRLLMPipLne/
├── docx_extractor.py      # Core text extraction module
├── test_extractor.py      # Test and demonstration script
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── test_document.txt     # Test file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license information here]

## Contact

[Add contact information here]

## Roadmap

- [ ] Web interface for document upload
- [ ] Multiple LLM provider support
- [ ] Advanced formatting analysis
- [ ] Document comparison features
- [ ] Batch processing capabilities
- [ ] API endpoints for integration
- [ ] User authentication and management
- [ ] Result caching and optimization 