from typing import List, Dict, Any
from app.services.document_processor.cleaner import clean_text

def extract_txt(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from TXT or Markdown files with robust encoding fallbacks.
    Splits into pseudo-pages based on double newlines or paragraph volume.
    """
    raw_content = ""
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                raw_content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if not raw_content:
        raise ValueError(f"Unable to read text file '{file_path}' with supported encodings.")

    cleaned = clean_text(raw_content)
    if not cleaned:
        raise ValueError("Text file is empty.")

    # Split into logical sections by paragraphs (e.g., ~1500 chars per page)
    paragraphs = cleaned.split("\n\n")
    pages: List[Dict[str, Any]] = []
    current_page_paras = []
    current_length = 0
    page_number = 1

    for para in paragraphs:
        current_page_paras.append(para)
        current_length += len(para)
        if current_length >= 1200:
            pages.append({
                "page_number": page_number,
                "text": "\n\n".join(current_page_paras),
                "section_title": f"Section {page_number}"
            })
            page_number += 1
            current_page_paras = []
            current_length = 0

    if current_page_paras:
        pages.append({
            "page_number": page_number,
            "text": "\n\n".join(current_page_paras),
            "section_title": f"Section {page_number}"
        })

    return pages

