"""
Extract the raw document.xml from a DOCX file and save as .txt
"""
import zipfile
from pathlib import Path
import sys

def extract_docx_xml(docx_path, output_txt=None):
    docx_path = Path(docx_path)
    if not docx_path.exists():
        print(f"❌ File not found: {docx_path}")
        return None
    if output_txt is None:
        output_txt = docx_path.with_name(f"{docx_path.stem}_raw.xml.txt")
    else:
        output_txt = Path(output_txt)
    with zipfile.ZipFile(docx_path, 'r') as z:
        if 'word/document.xml' not in z.namelist():
            print("❌ word/document.xml not found in DOCX!")
            return None
        xml_bytes = z.read('word/document.xml')
        xml_text = xml_bytes.decode('utf-8')
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(xml_text)
    print(f"✅ Extracted word/document.xml to: {output_txt}")
    return str(output_txt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_docx_xml.py <input.docx> [output.txt]")
        sys.exit(1)
    extract_docx_xml(*sys.argv[1:]) 