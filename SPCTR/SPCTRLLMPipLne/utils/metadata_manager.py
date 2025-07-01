"""
Metadata Manager - Adds timestamps and version tracking to document processing
"""
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import os

class MetadataManager:
    """Manages metadata for document processing operations"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        self.working_dir = working_dir or Path.cwd()
        self.metadata_dir = self.working_dir / ".metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
    def generate_processing_id(self) -> str:
        """Generate a unique processing ID based on timestamp and random elements"""
        timestamp = int(time.time() * 1000000)  # Microsecond precision
        return f"proc_{timestamp}"
    
    def create_document_metadata(self, docx_path: str, processing_id: Optional[str] = None) -> Dict[str, Any]:
        """Create metadata for a document processing operation"""
        docx_path_obj = Path(docx_path)
        processing_id = processing_id or self.generate_processing_id()
        
        # Calculate file hash for version tracking
        file_hash = self._calculate_file_hash(docx_path_obj)
        
        metadata = {
            "processing_id": processing_id,
            "original_file": {
                "path": str(docx_path_obj.absolute()),
                "name": docx_path_obj.name,
                "size_bytes": docx_path_obj.stat().st_size if docx_path_obj.exists() else 0,
                "hash": file_hash,
                "last_modified": datetime.fromtimestamp(docx_path_obj.stat().st_mtime).isoformat() if docx_path_obj.exists() else None
            },
            "processing": {
                "start_time": datetime.now().isoformat(),
                "timestamp": time.time(),
                "working_directory": str(self.working_dir.absolute())
            },
            "pipeline_steps": [],
            "output_files": [],
            "status": "started"
        }
        
        return metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        if not file_path.exists():
            return "file_not_found"
        
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            return f"hash_error_{str(e)}"
    
    def add_pipeline_step(self, metadata: Dict[str, Any], step_name: str, 
                         input_file: Optional[str] = None, output_file: Optional[str] = None,
                         status: str = "completed", error: Optional[str] = None) -> Dict[str, Any]:
        """Add a pipeline step to the metadata"""
        step = {
            "name": step_name,
            "timestamp": datetime.now().isoformat(),
            "input_file": input_file,
            "output_file": output_file,
            "status": status,
            "error": error
        }
        
        metadata["pipeline_steps"].append(step)
        
        # Add output file to metadata if provided
        if output_file:
            output_path = Path(output_file)
            if output_path.exists():
                output_info = {
                    "path": str(output_path.absolute()),
                    "name": output_path.name,
                    "size_bytes": output_path.stat().st_size,
                    "hash": self._calculate_file_hash(output_path),
                    "created": datetime.fromtimestamp(output_path.stat().st_ctime).isoformat()
                }
                metadata["output_files"].append(output_info)
        
        return metadata
    
    def save_metadata(self, metadata: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save metadata to file"""
        if not filename:
            processing_id = metadata["processing_id"]
            filename = f"{processing_id}_metadata.json"
        
        metadata_file = self.metadata_dir / filename
        
        # Add final processing info
        metadata["processing"]["end_time"] = datetime.now().isoformat()
        metadata["processing"]["duration_seconds"] = time.time() - metadata["processing"]["timestamp"]
        metadata["status"] = "completed"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata_file
    
    def load_metadata(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Load metadata by processing ID"""
        metadata_file = self.metadata_dir / f"{processing_id}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def find_document_versions(self, docx_path: str) -> List[Dict[str, Any]]:
        """Find all processing versions of a document"""
        docx_path_obj = Path(docx_path)
        docx_hash = self._calculate_file_hash(docx_path_obj)
        
        versions = []
        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Check if this metadata is for the same document
                if (metadata.get("original_file", {}).get("hash") == docx_hash or
                    metadata.get("original_file", {}).get("path") == str(docx_path_obj.absolute())):
                    versions.append(metadata)
            except Exception:
                continue
        
        # Sort by processing timestamp (newest first)
        versions.sort(key=lambda x: x["processing"]["timestamp"], reverse=True)
        return versions
    
    def get_latest_version(self, docx_path: str) -> Optional[Dict[str, Any]]:
        """Get the latest processing version of a document"""
        versions = self.find_document_versions(docx_path)
        return versions[0] if versions else None
    
    def add_timestamp_to_filename(self, original_path: str, suffix: str = "_processed") -> str:
        """Add timestamp to filename to prevent conflicts"""
        path_obj = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create new filename with timestamp
        new_name = f"{path_obj.stem}{suffix}_{timestamp}{path_obj.suffix}"
        return str(path_obj.parent / new_name)
    
    def create_output_filename(self, original_path: str, processing_id: str, 
                             output_type: str, extension: str = ".txt") -> str:
        """Create a standardized output filename with metadata"""
        path_obj = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        new_name = f"{path_obj.stem}_{output_type}_{processing_id}_{timestamp}{extension}"
        return str(path_obj.parent / new_name)
    
    def print_processing_summary(self, metadata: Dict[str, Any]):
        """Print a summary of the processing operation"""
        print("\n" + "="*60)
        print("📋 PROCESSING SUMMARY")
        print("="*60)
        print(f"🆔 Processing ID: {metadata['processing_id']}")
        print(f"📄 Document: {metadata['original_file']['name']}")
        print(f"⏰ Start Time: {metadata['processing']['start_time']}")
        print(f"⏱️  Duration: {metadata['processing'].get('duration_seconds', 0):.2f} seconds")
        print(f"📁 Working Directory: {metadata['processing']['working_directory']}")
        
        print(f"\n🔧 Pipeline Steps ({len(metadata['pipeline_steps'])}):")
        for i, step in enumerate(metadata['pipeline_steps'], 1):
            status_icon = "✅" if step['status'] == 'completed' else "❌"
            print(f"  {i}. {status_icon} {step['name']} - {step['timestamp']}")
            if step.get('error'):
                print(f"     Error: {step['error']}")
        
        print(f"\n📤 Output Files ({len(metadata['output_files'])}):")
        for output in metadata['output_files']:
            size_mb = output['size_bytes'] / (1024 * 1024)
            print(f"  📄 {output['name']} ({size_mb:.2f} MB)")
        
        print("="*60)
    
    def cleanup_old_metadata(self, days_to_keep: int = 30):
        """Clean up metadata files older than specified days"""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        cleaned_count = 0
        
        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            if metadata_file.stat().st_mtime < cutoff_time:
                try:
                    metadata_file.unlink()
                    cleaned_count += 1
                except Exception:
                    continue
        
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} old metadata files") 