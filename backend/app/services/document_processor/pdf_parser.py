from typing import List, Dict, Any
import pymupdf
from app.services.document_processor.cleaner import clean_text

def extract_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page from a PDF file using PyMuPDF.
    Attempts OCR on scanned/image-only pages where Tesseract is installed.
    Returns: List[Dict[str, Any]] containing 'page_number' and 'text'.
    """
    pages: List[Dict[str, Any]] = []
    try:
        doc = pymupdf.open(file_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            raw_text = page.get_text("text")
            
            # If standard text extraction yields nothing, attempt OCR
            if not raw_text.strip():
                try:
                    textpage = page.get_textpage_ocr(flags=0, language="eng", dpi=150)
                    raw_text = page.get_text("text", textpage=textpage)
                except Exception:
                    pass

            cleaned = clean_text(raw_text)
            if cleaned:
                pages.append({
                    "page_number": page_idx + 1,
                    "text": cleaned,
                    "section_title": f"Page {page_idx + 1}"
                })
        doc.close()
    except Exception as e:
        raise ValueError(f"Failed to process PDF '{file_path}': {str(e)}")
        
    if not pages:
        raise ValueError("PDF document contains no extractable text. Scanned image OCR is unavailable or document is empty.")
        
    return pages
