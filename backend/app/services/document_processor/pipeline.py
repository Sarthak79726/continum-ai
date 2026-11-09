import os
from typing import List, Dict, Any
from app.services.document_processor.pdf_parser import extract_pdf
from app.services.document_processor.docx_parser import extract_docx
from app.services.document_processor.csv_parser import extract_csv
from app.services.document_processor.txt_parser import extract_txt
from app.services.document_processor.chunker import chunk_document_pages

def process_document_file(file_path: str, file_type: str) -> List[Dict[str, Any]]:
    """
    Main extraction pipeline:
    1. Selects the appropriate extractor based on extension/type
    2. Extracts raw content by pages/sections
    3. Normalizes and cleans the text
    4. Divides text into indexed chunks with preserved page metadata
    """
    ext = file_type.lower().strip().replace(".", "")
    
    if ext == "pdf":
        pages = extract_pdf(file_path)
    elif ext in ["docx", "doc"]:
        pages = extract_docx(file_path)
    elif ext == "csv":
        pages = extract_csv(file_path)
    elif ext in ["txt", "md", "log"]:
        pages = extract_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: '.{ext}'. Supported formats: PDF, DOCX, TXT, CSV.")

    # Divide extracted pages into semantic chunks
    chunks = chunk_document_pages(pages, chunk_size=600, chunk_overlap=120)
    
    if not chunks:
        raise ValueError("Document processing produced 0 usable text chunks.")

    return chunks

