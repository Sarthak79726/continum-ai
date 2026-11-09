from typing import List, Dict, Any, Optional

def chunk_document_pages(
    pages: List[Dict[str, Any]], 
    chunk_size: int = 600, 
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Chunks a list of page dicts: [{'page_number': 1, 'text': '...'}]
    into coherent chunks preserving page numbers and chunk index.
    """
    chunks: List[Dict[str, Any]] = []
    chunk_idx = 0

    for page in pages:
        page_num = page.get("page_number", 1)
        page_text = page.get("text", "").strip()
        section = page.get("section_title")
        
        if not page_text:
            continue
            
        # If page text is within chunk_size, keep as a single chunk
        if len(page_text) <= chunk_size:
            chunks.append({
                "chunk_index": chunk_idx,
                "page_number": page_num,
                "section_title": section,
                "text": page_text,
                "token_count": len(page_text.split())
            })
            chunk_idx += 1
            continue

        # Split page into sliding chunks by sentences or paragraphs where possible
        start = 0
        text_len = len(page_text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # If not at the very end, try to break at a period or newline
            if end < text_len:
                break_point = page_text.rfind('. ', start, end)
                if break_point != -1 and break_point > start + (chunk_size // 2):
                    end = break_point + 1
                else:
                    break_nl = page_text.rfind('\n', start, end)
                    if break_nl != -1 and break_nl > start + (chunk_size // 2):
                        end = break_nl + 1

            chunk_text = page_text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "section_title": section,
                    "text": chunk_text,
                    "token_count": len(chunk_text.split())
                })
                chunk_idx += 1

            if end >= text_len:
                break
                
            start = max(start + 1, end - chunk_overlap)

    return chunks

