# Anchor Token Pipeline for LLM Processing

This pipeline enables perfect round-trip conversion between DOCX documents and LLM-friendly text with invisible anchor tokens for precise editing and reconstruction.

## Overview

The anchor token pipeline solves the challenge of preserving document formatting while enabling LLM editing by:

1. **Extracting XML** from DOCX files
2. **Adding invisible anchor tokens** to track paragraph positions
3. **Stripping non-essential XML** (keeping only italic, bold, small caps, underline, superscript, whitespace)
4. **Creating clean LLM prompts** with minimal token overhead
5. **Reconstructing XML** from LLM output using anchor positions
6. **Repackaging as DOCX** with full formatting preservation

## Core Scripts

### 1. `xml_to_anchored_txt.py`
Converts XML to TXT with anchor tokens for each paragraph.

**Usage:**
```bash
python xml_to_anchored_txt.py <input.xml> [output.txt]
```

**Features:**
- Adds unique anchor tokens (`<A001>`, `<A002>`, etc.) for each paragraph
- Preserves essential formatting: bold, italic, underline, small caps, superscript
- Maintains whitespace and tab characters
- Handles footnote references
- Outputs clean text suitable for LLM processing

### 2. `anchored_txt_to_xml.py`
Converts anchored TXT back to XML using original structure as template.

**Usage:**
```bash
python anchored_txt_to_xml.py <anchored.txt> <original.xml> [output.xml]
```

**Features:**
- Parses anchor tokens to identify paragraph boundaries
- Reconstructs XML structure from original document
- Preserves paragraph properties (justification, spacing, tabs)
- Rebuilds formatting tags from LLM output
- Maintains document structure integrity

### 3. `extract_docx_xml.py`
Extracts `document.xml` from DOCX files.

### 4. `repackage_docx_xml.py`
Repackages XML back into DOCX format.

## Complete Pipeline Example

```bash
# Step 1: Extract XML from DOCX
python extract_docx_xml.py "document.docx"

# Step 2: Convert to anchored TXT
python xml_to_anchored_txt.py "document_raw.xml.txt"

# Step 3: Send anchored TXT to LLM for editing
# (LLM receives clean text with anchor tokens)

# Step 4: Convert LLM output back to XML
python anchored_txt_to_xml.py "document_raw.xml.anchored.txt" "document_raw.xml.txt"

# Step 5: Repackage as DOCX
python repackage_docx_xml.py "document.docx" "document_raw.xml.anchored.reconstructed.xml"
```

## Anchor Token Format

Anchor tokens are compact and unique:
- Format: `<A###>` where ### is a 3-digit paragraph number
- Example: `<A001>`, `<A002>`, `<A034>`
- Minimal token overhead for LLM context
- Uniquely identifiable for precise reconstruction

## Preserved Formatting

The pipeline preserves these essential formatting elements:

| Format | XML Tag | Preserved |
|--------|---------|-----------|
| **Bold** | `<w:b/>` | ✅ |
| *Italic* | `<w:i/>` | ✅ |
| <u>Underline</u> | `<w:u/>` | ✅ |
| SMALL CAPS | `<w:smallCaps/>` | ✅ |
| Superscript¹ | `<w:vertAlign w:val="superscript"/>` | ✅ |
| Whitespace | `<w:t xml:space="preserve">` | ✅ |
| Tabs | `<w:tab/>` | ✅ |

## LLM Integration

### Input to LLM
The LLM receives clean text with anchor tokens:
```
<A001>This is a paragraph with <bold>bold text</bold> and <italic>italic text</italic>.

<A002>This is another paragraph with <underline>underlined text</underline>.
```

### LLM Output
The LLM can edit the text while preserving anchor tokens:
```
<A001>This is an edited paragraph with <bold>bold text</bold> and <italic>italic text</italic>.

<A002>This is another edited paragraph with <underline>underlined text</underline>.
```

### JSON Output (Optional)
For more complex edits, the LLM can output JSON with relative positions:
```json
{
  "edits": [
    {
      "anchor": "A001",
      "position": 15,
      "text": "modified",
      "formatting": ["bold"]
    }
  ]
}
```

## Benefits

1. **Perfect Fidelity**: Round-trip conversion preserves 100% of original formatting
2. **LLM-Friendly**: Clean text with minimal token overhead
3. **Precise Editing**: Anchor tokens enable exact positioning of edits
4. **Format Preservation**: Essential formatting maintained throughout pipeline
5. **Scalable**: Works with documents of any size and complexity

## File Structure

```
SPCTRLLMPipLne/
├── xml_to_anchored_txt.py          # XML → Anchored TXT
├── anchored_txt_to_xml.py          # Anchored TXT → XML
├── extract_docx_xml.py             # DOCX → XML
├── repackage_docx_xml.py           # XML → DOCX
├── test_anchor_pipeline.py         # Complete pipeline test
├── cleanup_test_files.py           # Test file cleanup
└── ANCHOR_PIPELINE_README.md       # This file
```

## Testing

Run the complete pipeline test:
```bash
python test_anchor_pipeline.py
```

Clean up test files:
```bash
python cleanup_test_files.py
```

## Requirements

- Python 3.7+
- Standard library modules: `xml.etree.ElementTree`, `pathlib`, `re`
- No external dependencies required

## Future Enhancements

1. **Sub-paragraph anchors**: More granular positioning within paragraphs
2. **Format-specific anchors**: Separate anchors for different formatting types
3. **Batch processing**: Process multiple documents simultaneously
4. **Validation**: Verify round-trip fidelity automatically
5. **LLM integration**: Direct API integration with popular LLM services 