"""
Advanced DOCX Text Extractor for Legal Documents
Preserves formatting information crucial for LLM processing
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
import re
from dataclasses import dataclass
from pathlib import Path


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


class DocxExtractor:
    """Advanced DOCX text extractor that preserves formatting"""
    
    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path)
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'w14': 'http://schemas.microsoft.com/office/word/2010/wordml'
        }
        
    def extract_text_with_formatting(self) -> str:
        """Extract text with formatting preserved as XML-like tags"""
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as zip_file:
                # Extract document.xml
                document_xml = zip_file.read('word/document.xml')
                root = ET.fromstring(document_xml)
                
                # Extract text with formatting
                formatted_texts = self._extract_paragraphs(root)
                
                # Convert to tagged text
                tagged_text = self._convert_to_tagged_text(formatted_texts)
                
                return tagged_text
                
        except Exception as e:
            raise Exception(f"Error extracting text from {self.docx_path}: {str(e)}")
    
    def _extract_paragraphs(self, root: ET.Element) -> List[List[FormattedText]]:
        """Extract paragraphs with their formatting"""
        paragraphs = []
        
        for paragraph in root.findall('.//w:p', self.namespaces):
            paragraph_texts = []
            
            # Get paragraph justification
            justification = self._get_paragraph_justification(paragraph)
            
            for run in paragraph.findall('.//w:r', self.namespaces):
                text_elem = run.find('.//w:t', self.namespaces)
                if text_elem is not None and text_elem.text:
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
                            justification=justification
                        )
                    else:
                        formatted_text = FormattedText(
                            text=text_elem.text,
                            justification=justification
                        )
                    
                    paragraph_texts.append(formatted_text)
            
            if paragraph_texts:
                paragraphs.append(paragraph_texts)
        
        return paragraphs
    
    def _get_paragraph_justification(self, paragraph: ET.Element) -> Optional[str]:
        """Get paragraph justification"""
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
        return 'left'  # default
    
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
        """Convert formatted text to tagged text format"""
        tagged_lines = []
        
        for paragraph in paragraphs:
            paragraph_text = ""
            
            for formatted_text in paragraph:
                # Apply formatting tags
                text = formatted_text.text
                
                # Handle special characters
                text = text.replace('&', '&amp;')
                text = text.replace('<', '&lt;')
                text = text.replace('>', '&gt;')
                
                # Apply formatting tags
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
                
                paragraph_text += text
            
            # Add paragraph justification
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
                    # Skip the separator footnote
                    if footnote.get('w:id') == '-1':
                        continue
                    
                    footnote_text = ""
                    for run in footnote.findall('.//w:r', self.namespaces):
                        text_elem = run.find('.//w:t', self.namespaces)
                        if text_elem is not None and text_elem.text:
                            footnote_text += text_elem.text
                    
                    if footnote_text.strip():
                        footnotes.append(footnote_text.strip())
                
                return footnotes
                
        except Exception as e:
            print(f"Warning: Could not extract footnotes: {str(e)}")
            return []


def extract_docx_text(docx_path: str, include_footnotes: bool = True) -> Dict[str, str]:
    """
    Extract text from DOCX file with formatting preserved
    
    Args:
        docx_path: Path to the DOCX file
        include_footnotes: Whether to include footnotes in the output
    
    Returns:
        Dictionary with 'main_text' and optionally 'footnotes'
    """
    extractor = DocxExtractor(docx_path)
    
    # Extract main text with formatting
    main_text = extractor.extract_text_with_formatting()
    
    result = {'main_text': main_text}
    
    # Extract footnotes if requested
    if include_footnotes:
        footnotes = extractor.extract_footnotes()
        if footnotes:
            result['footnotes'] = '\n\n'.join(footnotes)
    
    return result


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
            print(result['footnotes'])
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 