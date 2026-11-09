from typing import List, Dict, Any
import docx
from app.services.document_processor.cleaner import clean_text

def extract_docx(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text and table content from a DOCX file using python-docx.
    Organizes paragraphs into sections.
    """
    try:
        doc = docx.Document(file_path)
    except Exception as e:
        raise ValueError(f"Failed to open DOCX file '{file_path}': {str(e)}")

    sections: List[Dict[str, Any]] = []
    current_section = "Document Header"
    current_lines = []
    section_index = 1

    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
            
        # Check if style is heading
        if p.style and p.style.name.startswith("Heading"):
            if current_lines:
                full_text = clean_text("\n".join(current_lines))
                if full_text:
                    sections.append({
                        "page_number": section_index,
                        "text": full_text,
                        "section_title": current_section
                    })
                    section_index += 1
                current_lines = []
            current_section = txt
            current_lines.append(f"## {txt}")
        else:
            current_lines.append(txt)

    # Also extract tables
    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            row_vals = [c.text.strip() for c in row.cells if c.text.strip()]
            if row_vals:
                table_rows.append(" | ".join(row_vals))
        if table_rows:
            current_lines.append("\nTable Data:\n" + "\n".join(table_rows))

    if current_lines:
        full_text = clean_text("\n".join(current_lines))
        if full_text:
            sections.append({
                "page_number": section_index,
                "text": full_text,
                "section_title": current_section
            })

    if not sections:
        raise ValueError("DOCX document contains no readable text.")

    return sections

