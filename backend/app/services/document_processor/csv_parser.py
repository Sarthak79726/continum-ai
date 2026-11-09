from typing import List, Dict, Any
import pandas as pd
from app.services.document_processor.cleaner import clean_text

def extract_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts structured text from a CSV file using pandas.
    Formats rows as readable records so semantic search and AI understand fields.
    """
    try:
        # Try UTF-8 first, fallback to latin-1
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')
    except Exception as e:
        raise ValueError(f"Failed to read CSV '{file_path}': {str(e)}")

    if df.empty:
        raise ValueError("CSV file is empty.")

    pages: List[Dict[str, Any]] = []
    # Batch rows in groups of 10-15 rows per pseudo-page
    batch_size = 10
    total_rows = len(df)
    page_number = 1

    for start_idx in range(0, total_rows, batch_size):
        end_idx = min(start_idx + batch_size, total_rows)
        batch = df.iloc[start_idx:end_idx]
        
        lines = [f"CSV Records {start_idx + 1} to {end_idx} (Columns: {', '.join(df.columns)}):"]
        for _, row in batch.iterrows():
            record_str = ", ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            lines.append(f"- {record_str}")

        text = clean_text("\n".join(lines))
        pages.append({
            "page_number": page_number,
            "text": text,
            "section_title": f"Records {start_idx + 1}-{end_idx}"
        })
        page_number += 1

    return pages

