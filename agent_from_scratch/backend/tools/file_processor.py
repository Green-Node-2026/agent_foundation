import os
from pydantic import BaseModel, Field
from docx import Document
from pypdf import PdfReader
from PIL import Image
from pathlib import Path
from datetime import datetime
import io

# Consistent pathing
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"

class ProcessFileInput(BaseModel):
    filename: str = Field(..., description="The name of the file to process (from the [Attached File: ...] marker)")

class ListFilesInput(BaseModel):
    pass

def list_files() -> dict:
    """
    Lists all files currently available in the uploads directory with metadata.
    Includes 'modified_at' timestamp to help identify the latest uploads.
    """
    if not UPLOAD_DIR.exists():
        return {"files": [], "error": "Uploads directory does not exist."}
    
    files_info = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file():
            stats = f.stat()
            files_info.append({
                "name": f.name,
                "size_bytes": stats.st_size,
                "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "timestamp_raw": stats.st_mtime
            })
    
    # Sort by timestamp (newest first)
    files_info.sort(key=lambda x: x["timestamp_raw"], reverse=True)
    
    return {
        "files": files_info, 
        "count": len(files_info), 
        "path": str(UPLOAD_DIR),
        "note": "Files are sorted newest first."
    }

def process_file(filename: str) -> dict:
    """
    Detects the file format (PDF, DOCX, Image) and converts its content to Markdown.
    Use this tool when a user attaches a file and asks a question about its content.
    """
    upload_dir = "uploads"
    file_path = os.path.join(upload_dir, filename)

    if not os.path.exists(file_path):
        return {"error": f"File '{filename}' not found in uploads directory."}

    ext = os.path.splitext(filename)[1].lower()
    content = ""

    try:
        if ext == ".docx":
            doc = Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        
        elif ext == ".pdf":
            reader = PdfReader(file_path)
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text())
            content = "\n\n--- Page Break ---\n\n".join(pages)

        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            # For now, we return metadata for images. 
            # In a full implementation, this could involve OCR or Multimodal LLM calls.
            with Image.open(file_path) as img:
                content = f"### Image Metadata\n- Format: {img.format}\n- Size: {img.size}\n- Mode: {img.mode}\n\n*Note: Image OCR content extraction is not yet implemented.*"
        
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        
        else:
            return {"error": f"Unsupported file extension: {ext}"}

        return {
            "filename": filename,
            "format": ext[1:],
            "markdown_content": content
        }

    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}
