# Reasoning-Based Citation Validation

This document describes the reasoning-based citation validation system that provides second-pass analysis using OpenAI's reasoning models (o4-mini, o3, etc.) to improve citation accuracy.

## 🧠 Overview

The reasoning validation system addresses common issues with first-pass citation analysis:

- **Uncertain citations**: When the LLM is unsure about citation validity
- **Incorrect error detection**: False positives or missed errors
- **Poor correction suggestions**: When the LLM knows there's an error but suggests wrong fixes
- **Complex citations**: Citations that require deeper Bluebook analysis

## 🏗️ Architecture

```
First-Pass Analysis (Llama/OpenAI)
           ↓
    Citation Detection
           ↓
    Basic Validation
           ↓
    Flag Citations for Reasoning
           ↓
Second-Pass Analysis (OpenAI Reasoning Models)
           ↓
    Deep Bluebook Analysis
           ↓
    Context-Aware Validation
           ↓
    Improved Results
```

## 🔧 Components

### 1. ReasoningCitationValidator

**File**: `llm/reasoning_citation_validator.py`

**Purpose**: Second-pass citation validation using OpenAI reasoning models

**Key Features**:
- **Smart filtering**: Only validates citations that need deeper analysis
- **Context extraction**: Provides surrounding text for better analysis
- **Multiple effort levels**: Low, medium, high reasoning effort
- **Batch processing**: Efficient handling of multiple citations
- **Robust parsing**: Handles various response formats from reasoning models

### 2. Integration with LegalCitationChecker

**File**: `llm/legal_citation_checker.py`

**Purpose**: Seamless integration of reasoning validation into existing pipeline

**Key Features**:
- **Automatic detection**: Identifies citations needing reasoning validation
- **Fallback handling**: Graceful degradation when reasoning is unavailable
- **Configurable**: Enable/disable reasoning per request
- **Performance optimization**: Only applies reasoning to problematic citations

## 🚀 Usage

### Basic Usage

```bash
# Enable reasoning validation (default)
python llm_document_processor.py check-citations document.docx --reasoning

# Disable reasoning validation
python llm_document_processor.py check-citations document.docx --no-reasoning

# With debug output
python llm_document_processor.py check-citations document.docx --reasoning --debug
```

### Batched Processing

```bash
# Batched processing with reasoning
python llm_document_processor.py check-citations-batched document.docx --reasoning --batch-size 5

# With custom parameters
python llm_document_processor.py check-citations-batched document.docx \
  --reasoning \
  --batch-size 3 \
  --context-overlap 2 \
  --debug
```

### Standalone Reasoning Validator

```bash
# Validate existing citations
python llm/reasoning_citation_validator.py validate citations.json original_text.txt output.json

# With custom effort level
python llm/reasoning_citation_validator.py validate citations.json original_text.txt output.json --effort high

# With batch processing
python llm/reasoning_citation_validator.py validate citations.json original_text.txt output.json --batch-size 3
```

### Testing

```bash
# Run test suite
python test_reasoning_validation.py
```

## ⚙️ Configuration

### API Key Setup

1. **Set OpenAI API Key**:
   ```bash
   python model_selector.py
   # Select option 3: Configure OpenAI API key
   ```

2. **Environment Variable**:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

3. **Configuration File**:
   ```bash
   # Add to .env file
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Model Selection

**Default Model**: `o4-mini` (recommended for most use cases)

**Available Models**:
- `o4-mini`: Fast, cost-effective reasoning
- `o3`: Higher quality reasoning (slower, more expensive)
- `o3-mini`: Balanced option

**Effort Levels**:
- `low`: Fast, economical (fewer reasoning tokens)
- `medium`: Balanced speed and accuracy (default)
- `high`: Maximum reasoning depth (most tokens)

## 📊 Citation Filtering Logic

The system automatically determines which citations need reasoning validation:

### Citations That Need Reasoning

1. **Uncertain Status**: `status == "Uncertain"`
2. **Error Without Details**: `status == "Error"` and `errors == []`
3. **Suspicious Corrections**: `status == "Error"` but `orig == suggested`
4. **Complex Patterns**: Citations matching complex legal patterns:
   - Federal statutes: `\d+ U\.S\.C\.`
   - Federal regulations: `\d+ C\.F\.R\.`
   - Constitutional citations: `U\.S\. Const\.`
   - Federal cases: `\d+ F\.\d+`
   - Supreme Court cases: `\d+ S\.Ct\.`
5. **Long Citations**: Citations with more than 8 words

### Citations That Skip Reasoning

1. **Clear Correct**: `status == "Correct"` with no errors
2. **Clear Errors**: `status == "Error"` with specific error details
3. **Simple Citations**: Short, straightforward citations
4. **Non-Legal Text**: Document headers, plain text, etc.

## 🔍 Reasoning Process

### 1. Context Extraction

The system extracts context around each citation:

```python
# Extract 200 characters before and after citation
context_start = max(0, citation_start - 200)
context_end = min(len(text), citation_end + 200)
context = text[context_start:context_end]
```

### 2. Reasoning Prompt

Comprehensive prompt for deep analysis:

```
You are a legal citation expert with deep knowledge of Bluebook citation rules.

## CITATION TO ANALYZE:
- Original Citation: "28 U.S.C. § 636"
- Current Status: Uncertain
- Citation Type: statute-code
- Current Errors: []
- Current Suggestion: "28 U.S.C. § 636"

## CONTEXT:
The citation appears in this context:
[context with highlighted citation]

## YOUR TASK:
Perform a comprehensive analysis considering:
1. Citation Identification
2. Citation Type
3. Bluebook Compliance
4. Error Detection
5. Correction Accuracy

## OUTPUT FORMAT:
Return analysis in JSON format with reasoning_summary
```

### 3. Response Parsing

Robust parsing with multiple fallback strategies:

1. **Markdown Code Blocks**: Extract from ````json` blocks
2. **Direct JSON**: Parse if response starts with `{`
3. **Pattern Matching**: Find JSON objects in response
4. **Validation**: Ensure required fields are present

## 📈 Performance Considerations

### Token Usage

**Reasoning Models**: Use additional reasoning tokens before generating output

**Estimated Costs** (per citation):
- **Low effort**: ~500-1000 reasoning tokens
- **Medium effort**: ~1000-2000 reasoning tokens  
- **High effort**: ~2000-5000 reasoning tokens

### Rate Limiting

- **Batch processing**: 1-second delay between batches
- **Error handling**: Exponential backoff for API failures
- **Timeout management**: 120-second timeout per request

### Optimization Tips

1. **Use appropriate effort levels**:
   - `low` for simple validations
   - `medium` for most cases
   - `high` for complex citations only

2. **Batch processing**: Process multiple citations together
3. **Selective validation**: Only validate citations that need it
4. **Caching**: Consider caching results for repeated citations

## 🛠️ Troubleshooting

### Common Issues

1. **"No OpenAI client available"**
   - Configure OpenAI API key
   - Check API key permissions
   - Verify OpenAI SDK installation

2. **"Reasoning incomplete - ran out of tokens"**
   - Increase `max_output_tokens`
   - Use lower effort level
   - Reduce batch size

3. **"Failed to parse reasoning response"**
   - Check API response format
   - Enable debug mode for details
   - Verify model availability

4. **"Reasoning validation failed"**
   - Check network connectivity
   - Verify API key validity
   - Check rate limits

### Debug Mode

Enable debug output for detailed troubleshooting:

```bash
python llm_document_processor.py check-citations document.docx --reasoning --debug
```

Debug output includes:
- Citation filtering decisions
- API request details
- Response parsing steps
- Error details

## 📋 Output Format

### Enhanced Citation Results

```json
{
  "anchor": "P-00001",
  "start_offset": 15,
  "end_offset": 45,
  "type": "statute-code",
  "status": "Correct",
  "errors": [],
  "orig": "28 U.S.C. § 636",
  "suggested": "28 U.S.C. § 636",
  "reasoning_summary": "This is a correctly formatted federal statute citation. The title (28), code (U.S.C.), and section symbol (§) are properly formatted according to Bluebook Rule 12.3."
}
```

### Analysis Summary

```json
{
  "analysis_summary": {
    "total_citations_found": 15,
    "citations_with_errors": 3,
    "citations_correct": 12,
    "reasoning_validation_applied": true,
    "citations_validated_with_reasoning": 5
  }
}
```

## 🔮 Future Enhancements

### Planned Features

1. **Custom Reasoning Prompts**: User-defined validation rules
2. **Citation Learning**: Improve accuracy over time
3. **Multi-Model Validation**: Use multiple reasoning models
4. **Citation Database**: Reference known correct citations
5. **Performance Metrics**: Track validation accuracy

### Integration Opportunities

1. **Document Editors**: Real-time citation validation
2. **Legal Research Tools**: Citation verification
3. **Academic Writing**: Citation compliance checking
4. **Compliance Systems**: Automated legal document review

## 📚 References

- [OpenAI Reasoning Models Documentation](https://platform.openai.com/docs/models/reasoning)
- [Bluebook Citation Manual](https://www.legalbluebook.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Reasoning Best Practices](https://platform.openai.com/docs/guides/reasoning-best-practices) 