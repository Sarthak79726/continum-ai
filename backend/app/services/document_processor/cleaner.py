import re

def clean_text(text: str) -> str:
    """
    Cleans extracted document text by:
    - Normalizing whitespace and multiple empty lines
    - Stripping trailing whitespaces
    - Preserving semantic paragraph breaks
    - Handling common unicode artifacts
    """
    if not text:
        return ""
    
    # Replace non-breaking spaces and zero-width spaces
    text = text.replace('\u00a0', ' ').replace('\ufeff', '').replace('\r\n', '\n')
    
    # Replace multiple spaces with a single space (excluding newlines)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Normalize excessive newlines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

