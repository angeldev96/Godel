"""
Repackage a DOCX using a replacement document.xml from a .txt file
"""
import zipfile
from pathlib import Path
import sys
import shutil

def repackage_docx_xml(original_docx, xml_txt, output_docx=None):
    original_docx = Path(original_docx)
    xml_txt = Path(xml_txt)
    if not original_docx.exists():
        print(f"❌ File not found: {original_docx}")
        return
    if not xml_txt.exists():
        print(f"❌ File not found: {xml_txt}")
        return
    if output_docx is None:
        output_docx = original_docx.with_name(f"{original_docx.stem}_repackaged.docx")
    else:
        output_docx = Path(output_docx)
    # Copy the original DOCX to the output path
    shutil.copyfile(original_docx, output_docx)
    # Read the replacement XML
    with open(xml_txt, 'r', encoding='utf-8') as f:
        new_xml = f.read().encode('utf-8')
    # Replace document.xml in the new DOCX
    with zipfile.ZipFile(output_docx, 'a') as z:
        z.writestr('word/document.xml', new_xml)
    print(f"✅ Repackaged DOCX created: {output_docx}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python repackage_docx_xml.py <original.docx> <document_raw.xml.txt> [output.docx]")
        sys.exit(1)
    repackage_docx_xml(*sys.argv[1:]) 