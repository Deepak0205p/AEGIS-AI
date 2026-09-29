"""
OCR Cleaning & Normalization Pipeline for Air-Gapped Local AI.
Cleans raw OCR output before embedding or vector indexing, removing scan artifacts,
broken hyphenated words, noise symbols, corrupted punctuation, and stamp artifacts.
"""

import re
from typing import Dict, Any, List, Optional


def clean_ocr_text_for_embedding(raw_text: str) -> str:
    """
    Cleans OCR output before ingestion into vector index or embeddings:
    1. Removes non-printable / control characters while preserving standard punctuation and newlines.
    2. Reassembles words broken across lines by hyphens (e.g. 'tem- \nperature' -> 'temperature').
    3. Normalizes repeated noise characters (e.g. '____', '.....', '~~~~', '****', '|||||').
    4. Strips isolated single-character noise tokens resulting from speckles or paper folds.
    5. Normalizes consecutive whitespaces and excessive line breaks.
    6. Preserves critical engineering notations (temperatures, standards, equipment tags).
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Unify line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Reassemble hyphenated words broken across line breaks: 'proce-\n dure' -> 'procedure'
    text = re.sub(r"([A-Za-z0-9])[-–—]\s*\n\s*([A-Za-z0-9])", r"\1\2", text)

    # 3. Remove non-printable / control characters (keep \n and \t)
    text = "".join(ch for ch in text if ch in ("\n", "\t") or (ord(ch) >= 32 and ord(ch) <= 126) or ord(ch) >= 160)

    # 4. Remove scan lines / separator artifacts (repeated symbols >= 3)
    text = re.sub(r"[_=\-\~\|\*]{3,}", " ", text)
    text = re.sub(r"\.{4,}", "... ", text)

    # 5. Fix common OCR character confusion in technical text
    # e.g., orphan punctuation at start of lines: ', 101' -> '101'
    text = re.sub(r"^\s*[,;:`~]+\s*", "", text, flags=re.MULTILINE)

    # 6. Remove isolated speckle characters on their own line (e.g. solitary '.' or '`' or '|')
    text = re.sub(r"^\s*[^a-zA-Z0-9\s]\s*$", "", text, flags=re.MULTILINE)

    # 7. Collapse excessive spaces and blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_ocr_document_metadata(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans all text fields of an OCR document before adding to the knowledge base.
    """
    cleaned = dict(doc_dict)
    if "content" in cleaned and isinstance(cleaned["content"], str):
        cleaned["content"] = clean_ocr_text_for_embedding(cleaned["content"])
    if "title" in cleaned and isinstance(cleaned["title"], str):
        cleaned["title"] = clean_ocr_text_for_embedding(cleaned["title"])
    return cleaned
