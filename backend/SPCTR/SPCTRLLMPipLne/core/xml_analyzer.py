# -*- coding: utf-8 -*-
"""
XML Analyzer - Examine complete DOCX XML structure
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
import json

class DocxXmlAnalyzer:
    """Analyze complete XML structure of DOCX files"""
    
    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
            'w15': 'http://schemas.microsoft.com/office/word/2012/wordml'
        }
    
    def analyze_complete_structure(self) -> Dict[str, Any]:
        """Analyze the complete XML structure of the DOCX"""
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as zip_file:
                analysis = {
                    'files': {},
                    'document_structure': {},
                    'formatting_data': {},
                    'spacing_info': {},
                    'list_info': {},
                    'footnote_info': {}
                }
                
                # Analyze all XML files
                for filename in zip_file.namelist():
                    if filename.endswith('.xml'):
                        analysis['files'][filename] = self._analyze_xml_file(zip_file, filename)
                
                # Extract specific formatting data
                if 'word/document.xml' in analysis['files']:
                    doc_xml = zip_file.read('word/document.xml')
                    doc_root = ET.fromstring(doc_xml)
                    analysis['document_structure'] = self._analyze_document_structure(doc_root)
                    analysis['formatting_data'] = self._analyze_formatting_data(doc_root)
                    analysis['spacing_info'] = self._analyze_spacing_data(doc_root)
                    analysis['list_info'] = self._analyze_list_data(doc_root)
                
                # Analyze footnotes
                if 'word/footnotes.xml' in analysis['files']:
                    footnotes_xml = zip_file.read('word/footnotes.xml')
                    footnotes_root = ET.fromstring(footnotes_xml)
                    analysis['footnote_info'] = self._analyze_footnotes(footnotes_root)
                
                return analysis
                
        except Exception as e:
            print(f"Error analyzing DOCX: {str(e)}")
            return {}
    
    def _analyze_xml_file(self, zip_file: zipfile.ZipFile, filename: str) -> Dict[str, Any]:
        """Analyze a single XML file"""
        try:
            xml_content = zip_file.read(filename)
            root = ET.fromstring(xml_content)
            
            return {
                'size': len(xml_content),
                'root_tag': root.tag,
                'child_elements': [child.tag for child in root],
                'has_text': self._has_text_content(root),
                'has_formatting': self._has_formatting_elements(root)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _has_text_content(self, element: ET.Element) -> bool:
        """Check if element contains text"""
        for child in element.iter():
            if child.text and child.text.strip():
                return True
        return False
    
    def _has_formatting_elements(self, element: ET.Element) -> bool:
        """Check if element contains formatting"""
        formatting_tags = ['w:b', 'w:i', 'w:u', 'w:jc', 'w:ind', 'w:spacing', 'w:numPr']
        for child in element.iter():
            if any(tag in child.tag for tag in formatting_tags):
                return True
        return False
    
    def _analyze_document_structure(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze document structure"""
        structure = {
            'paragraphs': 0,
            'runs': 0,
            'text_elements': 0,
            'tabs': 0,
            'footnote_refs': 0
        }
        
        for elem in root.iter():
            if 'p' in elem.tag:
                structure['paragraphs'] += 1
            elif 'r' in elem.tag:
                structure['runs'] += 1
            elif 't' in elem.tag:
                structure['text_elements'] += 1
            elif 'tab' in elem.tag:
                structure['tabs'] += 1
            elif 'footnoteReference' in elem.tag:
                structure['footnote_refs'] += 1
        
        return structure
    
    def _analyze_formatting_data(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze formatting data"""
        formatting = {
            'bold_runs': 0,
            'italic_runs': 0,
            'underline_runs': 0,
            'justified_paragraphs': {'left': 0, 'center': 0, 'right': 0, 'justify': 0},
            'font_sizes': set(),
            'font_names': set()
        }
        
        for paragraph in root.findall('.//w:p', self.namespaces):
            # Check justification
            pPr = paragraph.find('.//w:pPr', self.namespaces)
            if pPr is not None:
                jc = pPr.find('.//w:jc', self.namespaces)
                if jc is not None:
                    val = jc.get('w:val', 'left')
                    if val in formatting['justified_paragraphs']:
                        formatting['justified_paragraphs'][val] += 1
            
            # Check run formatting
            for run in paragraph.findall('.//w:r', self.namespaces):
                rPr = run.find('.//w:rPr', self.namespaces)
                if rPr is not None:
                    if rPr.find('.//w:b', self.namespaces) is not None:
                        formatting['bold_runs'] += 1
                    if rPr.find('.//w:i', self.namespaces) is not None:
                        formatting['italic_runs'] += 1
                    if rPr.find('.//w:u', self.namespaces) is not None:
                        formatting['underline_runs'] += 1
                    
                    # Font size
                    sz = rPr.find('.//w:sz', self.namespaces)
                    if sz is not None:
                        formatting['font_sizes'].add(sz.get('w:val'))
                    
                    # Font name
                    rFonts = rPr.find('.//w:rFonts', self.namespaces)
                    if rFonts is not None:
                        font_name = rFonts.get('w:ascii') or rFonts.get('w:eastAsia')
                        if font_name:
                            formatting['font_names'].add(font_name)
        
        # Convert sets to lists for JSON serialization
        formatting['font_sizes'] = list(formatting['font_sizes'])
        formatting['font_names'] = list(formatting['font_names'])
        
        return formatting
    
    def _analyze_spacing_data(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze spacing and whitespace data"""
        spacing = {
            'paragraph_spacing': [],
            'run_spacing': [],
            'text_spacing': [],
            'tab_stops': [],
            'indentation': []
        }
        
        for paragraph in root.findall('.//w:p', self.namespaces):
            pPr = paragraph.find('.//w:pPr', self.namespaces)
            if pPr is not None:
                # Paragraph spacing
                spacing_elem = pPr.find('.//w:spacing', self.namespaces)
                if spacing_elem is not None:
                    spacing['paragraph_spacing'].append({
                        'before': spacing_elem.get('w:before'),
                        'after': spacing_elem.get('w:after'),
                        'line': spacing_elem.get('w:line'),
                        'lineRule': spacing_elem.get('w:lineRule')
                    })
                
                # Indentation
                ind = pPr.find('.//w:ind', self.namespaces)
                if ind is not None:
                    spacing['indentation'].append({
                        'left': ind.get('w:left'),
                        'right': ind.get('w:right'),
                        'firstLine': ind.get('w:firstLine'),
                        'hanging': ind.get('w:hanging')
                    })
                
                # Tab stops
                tabs = pPr.find('.//w:tabs', self.namespaces)
                if tabs is not None:
                    for tab in tabs.findall('.//w:tab', self.namespaces):
                        spacing['tab_stops'].append({
                            'pos': tab.get('w:pos'),
                            'val': tab.get('w:val'),
                            'leader': tab.get('w:leader')
                        })
            
            # Text spacing within runs
            for run in paragraph.findall('.//w:r', self.namespaces):
                rPr = run.find('.//w:rPr', self.namespaces)
                if rPr is not None:
                    spacing_elem = rPr.find('.//w:spacing', self.namespaces)
                    if spacing_elem is not None:
                        spacing['run_spacing'].append({
                            'val': spacing_elem.get('w:val'),
                            'before': spacing_elem.get('w:before'),
                            'after': spacing_elem.get('w:after')
                        })
                
                # Text content spacing
                for text_elem in run.findall('.//w:t', self.namespaces):
                    if text_elem.text:
                        # Analyze whitespace patterns
                        text = text_elem.text
                        if '  ' in text:  # Double spaces
                            spacing['text_spacing'].append({
                                'type': 'double_space',
                                'text': repr(text),
                                'length': len(text)
                            })
                        elif text.startswith(' ') or text.endswith(' '):
                            spacing['text_spacing'].append({
                                'type': 'trailing_space',
                                'text': repr(text),
                                'length': len(text)
                            })
        
        return spacing
    
    def _analyze_list_data(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze list and numbering data"""
        lists = {
            'numbered_lists': 0,
            'bullet_lists': 0,
            'list_levels': set(),
            'list_ids': set()
        }
        
        for paragraph in root.findall('.//w:p', self.namespaces):
            pPr = paragraph.find('.//w:pPr', self.namespaces)
            if pPr is not None:
                numPr = pPr.find('.//w:numPr', self.namespaces)
                if numPr is not None:
                    # Get list level
                    ilvl = numPr.find('.//w:ilvl', self.namespaces)
                    if ilvl is not None:
                        level = int(ilvl.get('w:val', 0))
                        lists['list_levels'].add(level)
                    
                    # Get list ID
                    numId = numPr.find('.//w:numId', self.namespaces)
                    if numId is not None:
                        list_id = numId.get('w:val')
                        lists['list_ids'].add(list_id)
                    
                    # Determine list type by examining text
                    for run in paragraph.findall('.//w:r', self.namespaces):
                        text_elem = run.find('.//w:t', self.namespaces)
                        if text_elem is not None and text_elem.text:
                            text = text_elem.text.strip()
                            if text in ['•', '◦', '▪', '▫', '-', '*']:
                                lists['bullet_lists'] += 1
                                break
                            elif text and text[0].isdigit() and '.' in text:
                                lists['numbered_lists'] += 1
                                break
        
        # Convert sets to lists
        lists['list_levels'] = list(lists['list_levels'])
        lists['list_ids'] = list(lists['list_ids'])
        
        return lists
    
    def _analyze_footnotes(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze footnote data"""
        footnotes = {
            'total_footnotes': 0,
            'footnote_ids': [],
            'footnote_lengths': []
        }
        
        for footnote in root.findall('.//w:footnote', self.namespaces):
            ref_id = footnote.get('w:id')
            if ref_id and ref_id not in ['-1', '0']:  # Skip separators
                footnotes['total_footnotes'] += 1
                footnotes['footnote_ids'].append(ref_id)
                
                # Get footnote text length
                text_length = 0
                for run in footnote.findall('.//w:r', self.namespaces):
                    text_elem = run.find('.//w:t', self.namespaces)
                    if text_elem is not None and text_elem.text:
                        text_length += len(text_elem.text)
                
                footnotes['footnote_lengths'].append(text_length)
        
        return footnotes

def analyze_docx_xml(docx_path: str) -> Dict[str, Any]:
    """Analyze DOCX XML structure"""
    analyzer = DocxXmlAnalyzer(docx_path)
    return analyzer.analyze_complete_structure()

if __name__ == "__main__":
    # Test with the sample document
    analysis = analyze_docx_xml("Stately 24-118 Order Instanity Eval.docx")
    
    print("🔍 DOCX XML Analysis Results")
    print("=" * 50)
    
    # Print summary
    print(f"📁 Files analyzed: {len(analysis['files'])}")
    print(f"📄 Document structure: {analysis['document_structure']}")
    print(f"🎨 Formatting data: {analysis['formatting_data']}")
    print(f"📏 Spacing info: {len(analysis['spacing_info']['text_spacing'])} spacing patterns found")
    print(f"📋 List info: {analysis['list_info']}")
    print(f"📝 Footnote info: {analysis['footnote_info']}")
    
    # Save detailed analysis
    with open('docx_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: docx_analysis.json")
