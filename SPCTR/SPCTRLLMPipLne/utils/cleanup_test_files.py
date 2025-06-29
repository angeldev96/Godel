"""
Clean up test files from anchor token pipeline testing
"""
import os
from pathlib import Path

def cleanup_test_files():
    """Remove test files created during pipeline testing"""
    test_patterns = [
        "*_raw.xml.txt",
        "*_raw.xml.anchored.txt", 
        "*_raw.xml.anchored.reconstructed.xml",
        "*_repackaged.docx"
    ]
    
    removed_count = 0
    for pattern in test_patterns:
        for file_path in Path("..").glob(pattern):
            try:
                file_path.unlink()
                print(f"🗑️  Removed: {file_path.name}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {file_path.name}: {e}")
    
    print(f"✅ Cleanup complete. Removed {removed_count} test files.")

if __name__ == "__main__":
    cleanup_test_files() 