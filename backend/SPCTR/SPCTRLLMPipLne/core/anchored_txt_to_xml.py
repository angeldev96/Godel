"""
Convert anchored TXT back to XML for reconstruction
"""
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import sys

def anchored_txt_to_xml(txt_path, original_xml_path, output_xml=None):
    """Convert anchored TXT back to XML using original as template"""
    txt_path = Path(txt_path)
    original_xml_path = Path(original_xml_path)
    
    if not txt_path.exists():
        print(f"❌ TXT file not found: {txt_path}")
        return
    if not original_xml_path.exists():
        print(f"❌ Original XML file not found: {original_xml_path}")
        return
    
    if output_xml is None:
        output_xml = txt_path.with_suffix('.reconstructed.xml')
    
    # Read the anchored text
    with open(txt_path, 'r', encoding='utf-8') as f:
        anchored_text = f.read()
    
    # Parse the original XML to get structure
    with open(original_xml_path, 'r', encoding='utf-8') as f:
        original_xml = f.read()
    
    original_root = ET.fromstring(original_xml)
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    # Split anchored text into paragraphs
    paragraphs = re.split(r'⟦P-\d{5}⟧', anchored_text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # Get original paragraphs
    original_paragraphs = original_root.findall('.//w:p', namespaces)
    
    # Reconstruct XML
    reconstructed_xml = reconstruct_xml_with_anchored_text(
        original_root, original_paragraphs, paragraphs, namespaces
    )
    
    # Save reconstructed XML
    with open(output_xml, 'w', encoding='utf-8') as f:
        f.write(reconstructed_xml)
    
    print(f"✅ Converted anchored TXT to XML: {output_xml}")

def reconstruct_xml_with_anchored_text(original_root, original_paragraphs, anchored_paragraphs, namespaces):
    """Reconstruct XML using original structure and anchored text"""
    # Create a copy of the original root
    new_root = ET.Element(original_root.tag, original_root.attrib)
    
    # Copy all namespaces
    for key, value in original_root.attrib.items():
        if key.startswith('xmlns'):
            new_root.set(key, value)
    
    # Find the body element
    body = original_root.find('.//w:body', namespaces)
    if body is None:
        print("❌ No body element found in original XML")
        return ET.tostring(original_root, encoding='unicode')
    
    new_body = ET.SubElement(new_root, body.tag, body.attrib)
    
    # Process each paragraph
    for i, (orig_para, anchored_text) in enumerate(zip(original_paragraphs, anchored_paragraphs)):
        # Create new paragraph with original properties
        new_para = ET.SubElement(new_body, orig_para.tag, orig_para.attrib)
        
        # Copy paragraph properties (justification, spacing, etc.)
        pPr = orig_para.find('.//w:pPr', namespaces)
        if pPr is not None:
            new_pPr = ET.SubElement(new_para, pPr.tag, pPr.attrib)
            for child in pPr:
                new_pPr.append(ET.fromstring(ET.tostring(child)))
        
        # Reconstruct runs from anchored text
        reconstruct_runs_from_text(new_para, anchored_text, orig_para, namespaces)
    
    # Convert to string with proper formatting
    ET.indent(new_root, space="  ")
    return ET.tostring(new_root, encoding='unicode')

def reconstruct_runs_from_text(new_para, anchored_text, orig_para, namespaces):
    """Reconstruct runs from anchored text while preserving formatting"""
    # Parse formatting tags from anchored text
    formatting_pattern = r'<(bold|italic|underline|smallcaps|superscript)>(.*?)</\1>'
    
    # Split text by formatting tags
    parts = re.split(formatting_pattern, anchored_text)
    
    for i in range(0, len(parts), 3):
        if i + 2 < len(parts):
            format_type = parts[i + 1]
            text_content = parts[i + 2]
        else:
            format_type = None
            text_content = parts[i] if i < len(parts) else ""
        
        if not text_content.strip():
            continue
        
        # Create run
        run = ET.SubElement(new_para, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
        
        # Add run properties if formatting is needed
        if format_type:
            rPr = ET.SubElement(run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
            
            if format_type == 'bold':
                ET.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}b')
            elif format_type == 'italic':
                ET.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}i')
            elif format_type == 'underline':
                ET.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}u', {'w:val': 'single'})
            elif format_type == 'smallcaps':
                ET.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}smallCaps')
            elif format_type == 'superscript':
                ET.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vertAlign', {'w:val': 'superscript'})
        
        # Add text element
        text_elem = ET.SubElement(run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        text_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        text_elem.text = text_content

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python anchored_txt_to_xml.py <anchored.txt> <original.xml> [output.xml]")
        sys.exit(1)
    anchored_txt_to_xml(*sys.argv[1:]) 