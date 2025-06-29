"""
DOCX Reconstructor - Converts enhanced text back to DOCX format
Preserves formatting, justification, tabs, and footnotes
"""

import re
import zipfile
import html
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ParsedText:
    text: str
    is_bold: bool = False
    is_italic: bool = False
    is_underline: bool = False
    is_small_caps: bool = False
    is_superscript: bool = False
    is_subscript: bool = False
    font_size: Optional[int] = None
    font_name: Optional[str] = None
    justification: Optional[str] = None
    tab_count: int = 0
    tab_spacing: int = 0
    is_footnote: bool = False
    footnote_content: Optional[str] = None

class DocxReconstructor:
    def __init__(self):
        self.footnotes: List[str] = []
        self.footnote_counter = 1
    def reconstruct_docx(self, enhanced_text: str, output_path: str) -> str:
        paragraphs = self._parse_enhanced_text(enhanced_text)
        docx_path = self._create_docx_structure(paragraphs, output_path)
        return docx_path
    def _parse_enhanced_text(self, enhanced_text: str) -> List[List[ParsedText]]:
        paragraphs = []
        para_texts = enhanced_text.split('\n\n')
        for para_text in para_texts:
            if not para_text.strip():
                continue
            parsed_paragraph = self._parse_paragraph(para_text)
            if parsed_paragraph:
                paragraphs.append(parsed_paragraph)
        return paragraphs
    def _parse_paragraph(self, para_text: str) -> List[ParsedText]:
        parsed_texts = []
        justification = None
        justify_match = re.search(r'<justify_(\w+)>(.*?)</justify_\w+>', para_text, re.DOTALL)
        if justify_match:
            justification = justify_match.group(1)
            para_text = justify_match.group(2)
        para_text = self._parse_tabbed_content(para_text, parsed_texts)
        para_text = self._parse_formatting_tags(para_text, parsed_texts, justification)
        para_text = self._parse_footnotes(para_text, parsed_texts)
        if para_text.strip():
            parsed_texts.append(ParsedText(text=para_text.strip(), justification=justification))
        return parsed_texts
    def _parse_tabbed_content(self, text: str, parsed_texts: List[ParsedText]) -> str:
        tab_pattern = r'<tabbed_content(?: count="(\d+)"(?: spacing="(\d+)")?)?>(.*?)</tabbed_content>'
        def replace_tabbed(match):
            count = int(match.group(1)) if match.group(1) else 1
            spacing = int(match.group(2)) if match.group(2) else 0
            content = match.group(3)
            parsed_texts.append(ParsedText(
                text="\t" * count,
                tab_count=count,
                tab_spacing=spacing
            ))
            if content.strip():
                parsed_texts.append(ParsedText(text=content.strip()))
            return ""
        return re.sub(tab_pattern, replace_tabbed, text, flags=re.DOTALL)
    def _parse_formatting_tags(self, text: str, parsed_texts: List[ParsedText], justification: Optional[str]) -> str:
        formatting_patterns = [
            ('<bold>(.*?)</bold>', 'is_bold'),
            ('<italic>(.*?)</italic>', 'is_italic'),
            ('<underline>(.*?)</underline>', 'is_underline'),
            ('<smallcaps>(.*?)</smallcaps>', 'is_small_caps'),
            ('<superscript>(.*?)</superscript>', 'is_superscript'),
            ('<subscript>(.*?)</subscript>', 'is_subscript'),
            (r'<font_size=(\d+)>(.*?)</font_size>', 'font_size'),
            (r"<font_name='([^']*)'>(.*?)</font_name>", 'font_name')
        ]
        for pattern, attr_name in formatting_patterns:
            def replace_formatting(match):
                if attr_name == 'font_size':
                    value = int(match.group(1))
                    content = match.group(2)
                    parsed_texts.append(ParsedText(
                        text=content,
                        font_size=value,
                        justification=justification
                    ))
                elif attr_name == 'font_name':
                    value = match.group(1)
                    content = match.group(2)
                    parsed_texts.append(ParsedText(
                        text=content,
                        font_name=value,
                        justification=justification
                    ))
                else:
                    content = match.group(1)
                    kwargs = {attr_name: True, 'justification': justification}
                    parsed_texts.append(ParsedText(text=content, **kwargs))
                return ""
            text = re.sub(pattern, replace_formatting, text, flags=re.DOTALL)
        return text
    def _parse_footnotes(self, text: str, parsed_texts: List[ParsedText]) -> str:
        footnote_pattern = r'\(Footnote: (.*?)\)'
        def replace_footnote(match):
            footnote_content = match.group(1)
            self.footnotes.append(footnote_content)
            parsed_texts.append(ParsedText(
                text=f"[{self.footnote_counter}]",
                is_footnote=True,
                footnote_content=footnote_content
            ))
            self.footnote_counter += 1
            return ""
        return re.sub(footnote_pattern, replace_footnote, text, flags=re.DOTALL)
    def _create_docx_structure(self, paragraphs: List[List[ParsedText]], output_path: str) -> str:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_file, 'w') as zip_file:
            self._add_content_types(zip_file)
            self._add_relationships(zip_file)
            self._add_main_document(zip_file, paragraphs)
            if self.footnotes:
                self._add_footnotes(zip_file)
            self._add_required_files(zip_file)
        return str(output_file)
    def _add_content_types(self, zip_file: zipfile.ZipFile):
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    <Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>
    <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
    <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
    <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
    <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
    <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
        zip_file.writestr('[Content_Types].xml', content_types)
    def _add_relationships(self, zip_file: zipfile.ZipFile):
        relationships = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
        zip_file.writestr('_rels/.rels', relationships)
        doc_relationships = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
    <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
</Relationships>'''
        zip_file.writestr('word/_rels/document.xml.rels', doc_relationships)
    def _add_main_document(self, zip_file: zipfile.ZipFile, paragraphs: List[List[ParsedText]]):
        document_xml = self._create_document_xml(paragraphs)
        zip_file.writestr('word/document.xml', document_xml)
    def _create_document_xml(self, paragraphs: List[List[ParsedText]]) -> str:
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
            '<w:body>'
        ]
        for paragraph in paragraphs:
            xml_parts.append(self._create_paragraph_xml(paragraph))
        xml_parts.extend(['</w:body>', '</w:document>'])
        return ''.join(xml_parts)
    def _create_paragraph_xml(self, paragraph: List[ParsedText]) -> str:
        if not paragraph:
            return ""
        justification = paragraph[0].justification if paragraph else None
        xml_parts = ['<w:p>']
        if justification and justification != 'left':
            xml_parts.append(f'<w:pPr><w:jc w:val="{justification}"/></w:pPr>')
        for parsed_text in paragraph:
            xml_parts.append(self._create_run_xml(parsed_text))
        xml_parts.append('</w:p>')
        return ''.join(xml_parts)
    def _create_run_xml(self, parsed_text: ParsedText) -> str:
        xml_parts = ['<w:r>']
        run_props = []
        if parsed_text.is_bold:
            run_props.append('<w:b/>')
        if parsed_text.is_italic:
            run_props.append('<w:i/>')
        if parsed_text.is_underline:
            run_props.append('<w:u w:val="single"/>')
        if parsed_text.is_small_caps:
            run_props.append('<w:smallCaps/>')
        if parsed_text.is_superscript:
            run_props.append('<w:vertAlign w:val="superscript"/>')
        if parsed_text.is_subscript:
            run_props.append('<w:vertAlign w:val="subscript"/>')
        if parsed_text.font_size:
            run_props.append(f'<w:sz w:val="{parsed_text.font_size}"/>')
        if parsed_text.font_name:
            run_props.append(f'<w:rFonts w:ascii="{parsed_text.font_name}"/>')
        if run_props:
            xml_parts.append(f'<w:rPr>{"" .join(run_props)}</w:rPr>')
        if parsed_text.is_footnote:
            if parsed_text.footnote_content is not None:
                xml_parts.append(f'<w:footnoteReference w:id="{self.footnotes.index(parsed_text.footnote_content) + 1}"/>')
        elif parsed_text.tab_count > 0:
            for _ in range(parsed_text.tab_count):
                xml_parts.append('<w:tab/>')
            if parsed_text.tab_spacing > 0:
                xml_parts.append(f'<w:t xml:space="preserve">{" " * parsed_text.tab_spacing}</w:t>')
        else:
            # Decode HTML entities and escape XML characters
            text = html.unescape(parsed_text.text)
            # Remove XML tags from the text (like <bold>, <italic>, etc.)
            text = re.sub(r'<[^>]+>', '', text)
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_parts.append(f'<w:t xml:space="preserve">{text}</w:t>')
        xml_parts.append('</w:r>')
        return ''.join(xml_parts)
    def _add_footnotes(self, zip_file: zipfile.ZipFile):
        footnotes_xml = self._create_footnotes_xml()
        zip_file.writestr('word/footnotes.xml', footnotes_xml)
    def _create_footnotes_xml(self) -> str:
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>',
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
        ]
        for i, footnote_content in enumerate(self.footnotes, 1):
            # Decode HTML entities in footnote content
            footnote_content = html.unescape(footnote_content)
            footnote_content = footnote_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_parts.append(f'<w:footnote w:id="{i}">')
            xml_parts.append('<w:p>')
            xml_parts.append('<w:r>')
            xml_parts.append(f'<w:t>{footnote_content}</w:t>')
            xml_parts.append('</w:r>')
            xml_parts.append('</w:p>')
            xml_parts.append('</w:footnote>')
        xml_parts.append('</w:footnotes>')
        return ''.join(xml_parts)
    def _add_required_files(self, zip_file: zipfile.ZipFile):
        settings = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:zoom w:percent="100"/>
    <w:defaultTabStop w:val="720"/>
</w:settings>'''
        zip_file.writestr('word/settings.xml', settings)
        styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:docDefaults>
        <w:rPrDefault>
            <w:rPr>
                <w:rFonts w:ascii="Calibri" w:eastAsia="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
                <w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="ar-SA"/>
            </w:rPr>
        </w:rPrDefault>
    </w:docDefaults>
</w:styles>'''
        zip_file.writestr('word/styles.xml', styles)
        font_table = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:font w:name="Calibri">
        <w:panose1 w:val="020F0502020204030204"/>
        <w:charset w:val="00"/>
        <w:family w:val="swiss"/>
        <w:pitch w:val="variable"/>
        <w:sig w:usb0="E00002FF" w:usb1="4000ACFF" w:usb2="00000001" w:usb3="00000000" w:csb0="0000019F" w:csb1="00000000"/>
    </w:font>
</w:fonts>'''
        zip_file.writestr('word/fontTable.xml', font_table)
        core_props = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dc:title></dc:title>
    <dc:subject></dc:subject>
    <dc:creator>SPCTR LLM Pipeline</dc:creator>
    <cp:keywords></cp:keywords>
    <dc:description></dc:description>
    <cp:lastModifiedBy>SPCTR LLM Pipeline</cp:lastModifiedBy>
    <cp:revision>1</cp:revision>
    <dcterms:created xsi:type="dcterms:W3CDTF">2024-01-01T00:00:00Z</dcterms:created>
    <dcterms:modified xsi:type="dcterms:W3CDTF">2024-01-01T00:00:00Z</dcterms:modified>
</cp:coreProperties>'''
        zip_file.writestr('docProps/core.xml', core_props)
        app_props = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
    <Template>Normal.dotm</Template>
    <TotalTime>0</TotalTime>
    <Pages>1</Pages>
    <Words>0</Words>
    <Characters>0</Characters>
    <Application>Microsoft Word</Application>
    <DocSecurity>0</DocSecurity>
    <Lines>0</Lines>
    <Paragraphs>0</Paragraphs>
    <ScaleCrop>false</ScaleCrop>
    <Company></Company>
    <LinksUpToDate>false</LinksUpToDate>
    <CharactersWithSpaces>0</CharactersWithSpaces>
    <SharedDoc>false</SharedDoc>
    <HyperlinksChanged>false</HyperlinksChanged>
    <AppVersion>16.0000</AppVersion>
</Properties>'''
        zip_file.writestr('docProps/app.xml', app_props)

def reconstruct_docx_from_enhanced_text(enhanced_text_path: str, output_path: str) -> str:
    with open(enhanced_text_path, 'r', encoding='utf-8') as f:
        enhanced_text = f.read()
    if "MAIN TEXT" in enhanced_text:
        main_text_end = enhanced_text.find("------------------------------------------------------------")
        if main_text_end != -1:
            main_text = enhanced_text[main_text_end + 60:]
        else:
            main_text = enhanced_text
    else:
        main_text = enhanced_text
    reconstructor = DocxReconstructor()
    docx_path = reconstructor.reconstruct_docx(main_text, output_path)
    print(f"✅ DOCX reconstructed successfully: {docx_path}")
    return docx_path
if __name__ == "__main__":
    script_dir = Path(__file__).parent
    enhanced_text_file = script_dir / "llm_input_debug.txt"
    output_docx = script_dir / "reconstructed_document.docx"
    
    try:
        if not enhanced_text_file.exists():
            print(f"❌ Enhanced text file not found: {enhanced_text_file}")
            print("Please run test_enhanced_features.py first to generate llm_input_debug.txt")
            exit(1)
            
        docx_path = reconstruct_docx_from_enhanced_text(str(enhanced_text_file), str(output_docx))
        print(f"Reconstruction completed: {docx_path}")
        print(f"✅ You can now open {output_docx} in Word to compare with the original document")
    except Exception as e:
        print(f"Reconstruction failed: {str(e)}")
