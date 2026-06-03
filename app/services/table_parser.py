"""
SmartDocQA — Table Extraction Module
======================================
Extracts structured tables from PDF documents using `pdfplumber`.
Lightweight and purpose-built for PDF table extraction.

Output format (List[Dict]):
    {
        "page": int | None,
        "text": str,                  # raw table text (pipe-separated)
        "headers": [str],             # parsed column headers
        "rows": [[str]],              # parsed data rows
        "description": str,           # table summary for keyword matching
    }
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_tables_from_pdf(file_path: str) -> List[Dict]:
    """
    Extract all tables from a PDF file using pdfplumber.

    pdfplumber extracts tables by detecting cell boundaries on each page.
    Returns a list of table dicts with headers and rows.

    Safe to call on non-PDF files — will raise FileNotFoundError or
    pdfplumber.pdfminer.pdfparser.PDFSyntaxError which callers can catch.
    """
    import pdfplumber

    tables: List[Dict] = []
    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            for raw_table in page_tables:
                if not raw_table or not any(any(cell.strip() if cell else False for cell in row) for row in raw_table):
                    continue

                # Convert to text, stripping whitespace and None
                cleaned = [
                    [ (cell or "").strip() for cell in row ]
                    for row in raw_table
                ]

                # First non-empty row is headers
                headers: List[str] = []
                rows: List[List[str]] = []

                for i, row in enumerate(cleaned):
                    if not any(row):
                        continue
                    if not headers:
                        headers = row
                    else:
                        rows.append(row)

                table_text = " | ".join(headers) + "\n" + "\n".join(
                    " | ".join(r) for r in rows
                )

                table = {
                    "page": page_number,
                    "text": table_text,
                    "headers": headers,
                    "rows": rows,
                    "description": _summarise_table(headers, rows),
                }
                tables.append(table)

    logger.info(
        f"[table_parser] Extracted {len(tables)} table(s) "
        f"from {Path(file_path).name}"
    )
    return tables


def _summarise_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Build a short description of the table content for keyword matching.
    Combines headers and key values into a plain-text summary.
    """
    parts: List[str] = list(headers)
    for row in rows[:3]:  # first 3 rows only
        parts.extend(row)
    return " | ".join(parts)