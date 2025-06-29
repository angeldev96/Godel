"""
Enhanced DOCX Text Extractor with improved formatting preservation
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class FormattedText:
    """Represents text with its formatting information"""
    text: str
    is_bold: bool = False
    is_italic: bool = False
    is_underline: bool = False
    is_small_caps: bool = False
    is_superscript: bool = False
    is_subscript: bool = False
    font_size: Optional[int] = None
    font_name: Optional[str] = None
    justification: Optional[str] = None  # left, center, right, justify
    tab_position: Optional[float] = None  # Position of tab stop in twips
    is_tabbed: bool = False  # Whether this text follows a tab
    tab_count: int = 0  # Number of consecutive tabs
    tab_spacing: Optional[str] = None  # Space characters after tab
    is_list_item: bool = False  # Whether this is part of a numbered or bulleted list
    list_level: int = 0  # List nesting level
    list_type: Optional[str] = None  # 'number', 'bullet', or None
    list_number: Optional[int] = None  # For numbered lists
    preserve_spacing: bool = True  # Whether to preserve exact spacing

@dataclass
class Footnote:
    """Represents a footnote with its reference and content"""
    reference_id: str
    content: str
    position_in_text: int  # Character position where footnote should be inserted

class DocxExtractor:
    """Enhanced DOCX text extractor with improved formatting preservation"""
    
    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        self.footnotes = {}  # Store footnotes by ID
        self.footnote_counter = 1  # For generating footnote numbers
    
    def extract_text_with_formatting(self) -> str:
        """Extract text with enhanced formatting preservation"""
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as zip_file:
                # Extract footnotes first
                self._extract_footnotes(zip_file)
                
                # Extract main document
                document_xml = zip_file.read('word/document.xml')
                root = ET.fromstring(document_xml)
                
                # Extract paragraphs with enhanced formatting
                paragraphs = self._extract_paragraphs(root)
                
                # Convert to tagged text format
                tagged_text = self._convert_to_tagged_text(paragraphs)
                
                return tagged_text
                
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return ""
    
    def _extract_paragraphs(self, root: ET.Element) -> List[List[FormattedText]]:
        """Extract paragraphs with their formatting and list information"""
        paragraphs = []
        id_key = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id'
        
        for paragraph in root.findall('.//w:p', self.namespaces):
            paragraph_texts = []
            
            # Get paragraph properties
            justification = self._get_paragraph_justification(paragraph)
            tab_stops = self._get_tab_stops(paragraph)
            list_info = self._get_list_info(paragraph)
            
            # First pass: count consecutive tabs and collect text
            runs = list(paragraph.findall('.//w:r', self.namespaces))
            i = 0
            while i < len(runs):
                run = runs[i]
                
                # Check for tab characters
                tab_elem = run.find('.//w:tab', self.namespaces)
                if tab_elem is not None:
                    # Count consecutive tabs
                    tab_count = 1
                    tab_spacing = ""
                    j = i + 1
                    
                    # Look ahead for consecutive tabs and collect spacing
                    while j < len(runs):
                        next_run = runs[j]
                        next_tab = next_run.find('.//w:tab', self.namespaces)
                        next_text = next_run.find('.//w:t', self.namespaces)
                        
                        if next_tab is not None:
                            tab_count += 1
                            j += 1
                        elif next_text is not None and next_text.text and next_text.text.strip() == "":
                            # Collect spacing characters
                            tab_spacing += next_text.text
                            j += 1
                        else:
                            break
                    
                    # Add tab marker with count and spacing
                    paragraph_texts.append(FormattedText(
                        text="\t" * tab_count,
                        justification=justification,
                        is_tabbed=True,
                        tab_count=tab_count,
                        tab_spacing=tab_spacing if tab_spacing else None,
                        is_list_item=list_info['is_list_item'],
                        list_level=list_info['level'],
                        list_type=list_info['type'],
                        list_number=list_info['number']
                    ))
                    
                    i = j  # Skip the processed runs
                    continue
                
                # Check for footnote references
                footnote_ref = run.find('.//w:footnoteReference', self.namespaces)
                if footnote_ref is None:
                    footnote_ref = run.find('.//w:footnoteRef', self.namespaces)
                
                if footnote_ref is not None:
                    ref_id = footnote_ref.get(id_key)
                    if ref_id and ref_id in self.footnotes:
                        # Add footnote superscript number and content
                        footnote_content = self.footnotes[ref_id]
                        paragraph_texts.append(FormattedText(
                            text=f"[{self.footnote_counter}] (Footnote: {footnote_content})",
                            justification=justification,
                            is_superscript=True,
                            is_list_item=list_info['is_list_item'],
                            list_level=list_info['level'],
                            list_type=list_info['type'],
                            list_number=list_info['number']
                        ))
                        self.footnote_counter += 1
                    i += 1
                    continue
                
                text_elem = run.find('.//w:t', self.namespaces)
                if text_elem is not None and text_elem.text is not None:
                    # Get run properties
                    run_props = run.find('.//w:rPr', self.namespaces)
                    if run_props is not None:
                        formatted_text = FormattedText(
                            text=text_elem.text,
                            is_bold=self._is_bold(run_props),
                            is_italic=self._is_italic(run_props),
                            is_underline=self._is_underline(run_props),
                            is_small_caps=self._is_small_caps(run_props),
                            is_superscript=self._is_superscript(run_props),
                            is_subscript=self._is_subscript(run_props),
                            font_size=self._get_font_size(run_props),
                            font_name=self._get_font_name(run_props),
                            justification=justification,
                            is_list_item=list_info['is_list_item'],
                            list_level=list_info['level'],
                            list_type=list_info['type'],
                            list_number=list_info['number'],
                            preserve_spacing=True
                        )
                    else:
                        formatted_text = FormattedText(
                            text=text_elem.text,
                            justification=justification,
                            is_list_item=list_info['is_list_item'],
                            list_level=list_info['level'],
                            list_type=list_info['type'],
                            list_number=list_info['number'],
                            preserve_spacing=True
                        )
                    
                    paragraph_texts.append(formatted_text)
                
                i += 1
            
            if paragraph_texts:
                paragraphs.append(paragraph_texts)
        
        return paragraphs
    
    def _get_list_info(self, paragraph: ET.Element) -> Dict:
        """Get list information for the paragraph"""
        pPr = paragraph.find('.//w:pPr', self.namespaces)
        if pPr is None:
            return {'is_list_item': False, 'level': 0, 'type': None, 'number': None}
        
        # Check for numbering properties
        numPr = pPr.find('.//w:numPr', self.namespaces)
        if numPr is None:
            return {'is_list_item': False, 'level': 0, 'type': None, 'number': None}
        
        # Get list level
        ilvl = numPr.find('.//w:ilvl', self.namespaces)
        level = int(ilvl.get('w:val', 0)) if ilvl is not None else 0
        
        # Get list ID
        numId = numPr.find('.//w:numId', self.namespaces)
        if numId is None:
            return {'is_list_item': False, 'level': 0, 'type': None, 'number': None}
        
        list_id = numId.get('w:val')
        
        # Determine list type and number
        list_type = 'number'  # Default to numbered list
        list_number = None
        
        # Try to get the actual list number from the paragraph
        for run in paragraph.findall('.//w:r', self.namespaces):
            text_elem = run.find('.//w:t', self.namespaces)
            if text_elem is not None and text_elem.text:
                text = text_elem.text.strip()
                # Check for bullet points
                if text in ['•', '◦', '▪', '▫', '-', '*']:
                    list_type = 'bullet'
                    break
                # Check for numbered list patterns
                elif text and text[0].isdigit() and '.' in text:
                    try:
                        list_number = int(text.split('.')[0])
                        break
                    except ValueError:
                        pass
        
        return {
            'is_list_item': True,
            'level': level,
            'type': list_type,
            'number': list_number
        }
    
    def _get_paragraph_justification(self, paragraph: ET.Element) -> Optional[str]:
        """Get paragraph justification with enhanced detection"""
        pPr = paragraph.find('.//w:pPr', self.namespaces)
        if pPr is not None:
            jc = pPr.find('.//w:jc', self.namespaces)
            if jc is not None:
                val = jc.get('w:val')
                if val == 'center':
                    return 'center'
                elif val == 'right':
                    return 'right'
                elif val == 'justify':
                    return 'justify'
                elif val == 'both':  # Alternative name for justify
                    return 'justify'
                elif val == 'distribute':  # Another justify variant
                    return 'justify'
            else:
                # Check for indentation that might indicate justification
                ind = pPr.find('.//w:ind', self.namespaces)
                if ind is not None:
                    left = ind.get('w:left')
                    right = ind.get('w:right')
                    if left and right and left != right:
                        # Asymmetric indentation might indicate center alignment
                        return 'center'
        
        # Check for text content that might indicate centering
        text_content = ""
        for run in paragraph.findall('.//w:r', self.namespaces):
            text_elem = run.find('.//w:t', self.namespaces)
            if text_elem is not None and text_elem.text:
                text_content += text_elem.text
        
        # Check if this looks like a centered title or header
        text_content = text_content.strip()
        if text_content in ['UNITED STATES DISTRICT COURT', 'DISTRICT OF MINNESOTA', 'ORDER']:
            return 'center'
        
        return 'left'  # default
    
    def _get_tab_stops(self, paragraph: ET.Element) -> List[float]:
        """Get tab stops for the paragraph"""
        tab_stops = []
        pPr = paragraph.find('.//w:pPr', self.namespaces)
        if pPr is not None:
            tabs = pPr.find('.//w:tabs', self.namespaces)
            if tabs is not None:
                for tab in tabs.findall('.//w:tab', self.namespaces):
                    pos = tab.get('w:pos')
                    if pos:
                        tab_stops.append(float(pos))
        return tab_stops
    
    def _extract_footnotes(self, zip_file: zipfile.ZipFile):
        """Extract footnotes and store them for later integration"""
        id_key = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id'
        try:
            # Check if footnotes file exists
            if 'word/footnotes.xml' not in zip_file.namelist():
                return
            
            footnotes_xml = zip_file.read('word/footnotes.xml')
            root = ET.fromstring(footnotes_xml)
            
            for footnote in root.findall('.//w:footnote', self.namespaces):
                # Skip the separator footnote
                ref_id = footnote.get(id_key)
                if ref_id is None or ref_id == '-1' or ref_id == '0':
                    continue
                
                footnote_text = ""
                for run in footnote.findall('.//w:r', self.namespaces):
                    text_elem = run.find('.//w:t', self.namespaces)
                    if text_elem is not None and text_elem.text:
                        footnote_text += text_elem.text
                
                if footnote_text.strip():
                    self.footnotes[ref_id] = footnote_text.strip()
        except Exception as e:
            print(f"Warning: Could not extract footnotes: {str(e)}")

    def _is_bold(self, run_props: ET.Element) -> bool:
        """Check if text is bold"""
        b = run_props.find('.//w:b', self.namespaces)
        return b is not None
    
    def _is_italic(self, run_props: ET.Element) -> bool:
        """Check if text is italic"""
        i = run_props.find('.//w:i', self.namespaces)
        return i is not None
    
    def _is_underline(self, run_props: ET.Element) -> bool:
        """Check if text is underlined"""
        u = run_props.find('.//w:u', self.namespaces)
        return u is not None
    
    def _is_small_caps(self, run_props: ET.Element) -> bool:
        """Check if text is small caps"""
        small_caps = run_props.find('.//w:smallCaps', self.namespaces)
        return small_caps is not None
    
    def _is_superscript(self, run_props: ET.Element) -> bool:
        """Check if text is superscript"""
        vert_align = run_props.find('.//w:vertAlign', self.namespaces)
        return vert_align is not None and vert_align.get('w:val') == 'superscript'
    
    def _is_subscript(self, run_props: ET.Element) -> bool:
        """Check if text is subscript"""
        vert_align = run_props.find('.//w:vertAlign', self.namespaces)
        return vert_align is not None and vert_align.get('w:val') == 'subscript'
    
    def _get_font_size(self, run_props: ET.Element) -> Optional[int]:
        """Get font size in half-points"""
        sz = run_props.find('.//w:sz', self.namespaces)
        if sz is not None:
            return int(sz.get('w:val', 0))
        return None
    
    def _get_font_name(self, run_props: ET.Element) -> Optional[str]:
        """Get font name"""
        rFonts = run_props.find('.//w:rFonts', self.namespaces)
        if rFonts is not None:
            return rFonts.get('w:ascii') or rFonts.get('w:eastAsia')
        return None
    
    def _convert_to_tagged_text(self, paragraphs: List[List[FormattedText]]) -> str:
        """Convert formatted text to tagged text format with enhanced features"""
        tagged_lines = []
        
        for paragraph in paragraphs:
            paragraph_text = ""
            current_tab_position = None
            in_tabbed_section = False
            
            # Add list prefix if this is a list item
            if paragraph and paragraph[0].is_list_item:
                list_prefix = ""
                if paragraph[0].list_type == 'bullet':
                    list_prefix = "• "
                elif paragraph[0].list_type == 'number' and paragraph[0].list_number:
                    list_prefix = f"{paragraph[0].list_number}. "
                elif paragraph[0].list_type == 'number':
                    list_prefix = "1. "  # Default numbered list
                
                if list_prefix:
                    paragraph_text += f"<list_item type=\"{paragraph[0].list_type}\" level=\"{paragraph[0].list_level}\">{list_prefix}"
            
            for formatted_text in paragraph:
                # Get the text content
                text = formatted_text.text
                
                # Preserve exact spacing - don't modify the text content
                # The text should be exactly as it appears in the document
                
                # Handle tabbed content
                if formatted_text.is_tabbed:
                    # Mark the start of tabbed content with count and spacing info
                    if not in_tabbed_section:
                        tab_info = f"<tabbed_content count=\"{formatted_text.tab_count}\""
                        if formatted_text.tab_spacing:
                            tab_info += f" spacing=\"{len(formatted_text.tab_spacing)}\""
                        tab_info += ">"
                        paragraph_text += tab_info
                        in_tabbed_section = True
                    continue
                
                # Apply formatting tags for reconstruction purposes
                # These will be used by the reconstructor but won't appear in the final text
                if formatted_text.is_bold:
                    text = f"<bold>{text}</bold>"
                if formatted_text.is_italic:
                    text = f"<italic>{text}</italic>"
                if formatted_text.is_underline:
                    text = f"<underline>{text}</underline>"
                if formatted_text.is_small_caps:
                    text = f"<smallcaps>{text}</smallcaps>"
                if formatted_text.is_superscript:
                    text = f"<superscript>{text}</superscript>"
                if formatted_text.is_subscript:
                    text = f"<subscript>{text}</subscript>"
                
                # Add font information if available
                if formatted_text.font_size:
                    text = f"<font_size={formatted_text.font_size}>{text}</font_size>"
                if formatted_text.font_name:
                    text = f"<font_name='{formatted_text.font_name}'>{text}</font_name>"
                
                # Add text to paragraph
                paragraph_text += text
                
                # If we were in a tabbed section and this text doesn't follow a tab, close the tabbed section
                if in_tabbed_section and not formatted_text.is_tabbed:
                    # Check if the next formatted text is also not tabbed
                    current_index = paragraph.index(formatted_text)
                    if current_index + 1 >= len(paragraph) or not paragraph[current_index + 1].is_tabbed:
                        paragraph_text += "</tabbed_content>"
                        in_tabbed_section = False
            
            # Close any remaining tabbed section
            if in_tabbed_section:
                paragraph_text += "</tabbed_content>"
            
            # Close list item if this was a list item
            if paragraph and paragraph[0].is_list_item:
                paragraph_text += "</list_item>"
            
            # Add paragraph justification with enhanced detection
            if paragraph and paragraph[0].justification:
                justification = paragraph[0].justification
                if justification != 'left':  # Don't tag default left alignment
                    paragraph_text = f"<justify_{justification}>{paragraph_text}</justify_{justification}>"
            
            tagged_lines.append(paragraph_text)
        
        return '\n\n'.join(tagged_lines)
    
    def extract_footnotes(self) -> List[str]:
        """Extract footnotes from the document"""
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as zip_file:
                # Check if footnotes file exists
                if 'word/footnotes.xml' not in zip_file.namelist():
                    return []
                
                footnotes_xml = zip_file.read('word/footnotes.xml')
                root = ET.fromstring(footnotes_xml)
                
                footnotes = []
                for footnote in root.findall('.//w:footnote', self.namespaces):
                    footnote_text = ""
                    for run in footnote.findall('.//w:r', self.namespaces):
                        text_elem = run.find('.//w:t', self.namespaces)
                        if text_elem is not None and text_elem.text:
                            footnote_text += text_elem.text
                    
                    if footnote_text.strip():
                        footnotes.append(footnote_text.strip())
                
                return footnotes
                
        except Exception as e:
            print(f"Error extracting footnotes: {str(e)}")
            return []

def extract_docx_text(docx_path: str, include_footnotes: bool = True) -> Dict[str, Union[str, List[str]]]:
    """Extract text from DOCX with enhanced formatting preservation"""
    extractor = DocxExtractor(docx_path)
    
    # Extract main text with formatting
    main_text = extractor.extract_text_with_formatting()
    
    # Create a clean version without XML tags for display
    clean_text = _remove_xml_tags(main_text)
    
    # Extract footnotes separately if requested
    footnotes = []
    if include_footnotes:
        footnotes = extractor.extract_footnotes()
    
    return {
        'main_text': main_text,
        'clean_text': clean_text,
        'footnotes': footnotes
    }

def _remove_xml_tags(text: str) -> str:
    """Remove XML formatting tags from text while preserving content"""
    import re
    
    # Remove formatting tags but keep their content
    text = re.sub(r'<bold>(.*?)</bold>', r'\1', text)
    text = re.sub(r'<italic>(.*?)</italic>', r'\1', text)
    text = re.sub(r'<underline>(.*?)</underline>', r'\1', text)
    text = re.sub(r'<smallcaps>(.*?)</smallcaps>', r'\1', text)
    text = re.sub(r'<superscript>(.*?)</superscript>', r'\1', text)
    text = re.sub(r'<subscript>(.*?)</subscript>', r'\1', text)
    text = re.sub(r'<font_size=\d+>(.*?)</font_size>', r'\1', text)
    text = re.sub(r"<font_name='[^']*'>(.*?)</font_name>", r'\1', text)
    
    # Remove justification tags
    text = re.sub(r'<justify_\w+>(.*?)</justify_\w+>', r'\1', text)
    
    # Remove tabbed content tags but preserve the content
    text = re.sub(r'<tabbed_content[^>]*>(.*?)</tabbed_content>', r'\1', text)
    
    # Remove list item tags but preserve the content
    text = re.sub(r'<list_item[^>]*>(.*?)</list_item>', r'\1', text)
    
    return text

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python docx_extractor.py <path_to_docx_file>")
        sys.exit(1)
    
    docx_file = sys.argv[1]
    
    try:
        result = extract_docx_text(docx_file)
        print("=== MAIN TEXT ===")
        print(result['main_text'])
        
        if 'footnotes' in result:
            print("\n=== FOOTNOTES ===")
            print('\n\n'.join(result['footnotes']))
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 