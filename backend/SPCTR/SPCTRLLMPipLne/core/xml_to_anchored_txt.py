"""
Convert XML to TXT with invisible anchor tokens for LLM processing
"""
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import sys

def xml_to_anchored_txt(xml_path, output_txt=None):
    """Convert XML to TXT with anchor tokens for each paragraph"""
    xml_path = Path(xml_path)
    if not xml_path.exists():
        print(f"❌ File not found: {xml_path}")
        return None
    
    if output_txt is None:
        output_txt = xml_path.with_suffix('.anchored.txt')
    
    # Parse XML
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    root = ET.fromstring(xml_content)
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    # Extract paragraphs with anchor tokens
    anchored_text = []
    paragraph_counter = 0
    
    for paragraph in root.findall('.//w:p', namespaces):
        paragraph_counter += 1
        anchor_token = f"⟦P-{paragraph_counter:05d}⟧"
        
        # Extract text from this paragraph
        paragraph_text = extract_paragraph_text(paragraph, namespaces)
        
        # Add anchor token at the beginning of paragraph
        anchored_text.append(f"{anchor_token}{paragraph_text}")
    
    # Join paragraphs with double newlines
    final_text = '\n\n'.join(anchored_text)
    
    # Save to file
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    print(f"✅ Converted XML to anchored TXT: {output_txt}")
    print(f"📊 Added {paragraph_counter} anchor tokens")
    return str(output_txt)

def extract_paragraph_text(paragraph, namespaces):
    """Extract text from a paragraph, keeping only essential formatting"""
    text_parts = []
    
    for run in paragraph.findall('.//w:r', namespaces):
        run_text = ""
        
        # Get run properties for formatting
        rPr = run.find('.//w:rPr', namespaces)
        formatting_tags = []
        
        if rPr is not None:
            # Check for essential formatting
            if rPr.find('.//w:b', namespaces) is not None:
                formatting_tags.append('<bold>')
            if rPr.find('.//w:i', namespaces) is not None:
                formatting_tags.append('<italic>')
            if rPr.find('.//w:u', namespaces) is not None:
                formatting_tags.append('<underline>')
            if rPr.find('.//w:smallCaps', namespaces) is not None:
                formatting_tags.append('<smallcaps>')
            
            # Check for superscript (important for footnotes)
            vert_align = rPr.find('.//w:vertAlign', namespaces)
            if vert_align is not None and vert_align.get('w:val') == 'superscript':
                formatting_tags.append('<superscript>')
        
        # Extract text content
        for text_elem in run.findall('.//w:t', namespaces):
            if text_elem.text:
                # Preserve exact whitespace
                text = text_elem.text
                run_text += text
        
        # Check for tabs
        if run.find('.//w:tab', namespaces) is not None:
            run_text += "\t"
        
        # Check for footnote references
        footnote_ref = run.find('.//w:footnoteReference', namespaces)
        if footnote_ref is not None:
            ref_id = footnote_ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if ref_id:
                run_text += f"[{ref_id}]"
        
        # Apply formatting tags if any
        if formatting_tags:
            for tag in formatting_tags:
                run_text = f"{tag}{run_text}</{tag[1:]}"
        
        if run_text:
            text_parts.append(run_text)
    
    return ''.join(text_parts)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python xml_to_anchored_txt.py <input.xml> [output.txt]")
        sys.exit(1)
    xml_to_anchored_txt(*sys.argv[1:]) 