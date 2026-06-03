"""
SmartDocQA — Structured Data Store
====================================
Persists and retrieves structured table data alongside FAISS vector indexes.

File layout in vector store directory:
    index.faiss       — FAISS binary index
    chunks.pkl        — serialised LangChain Document chunks
    tables.json       — extracted table data (this module)
    version.txt       — embedding model version marker
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def save_tables(tables: List[Dict], store_dir: str) -> str:
    """Persist extracted tables as ``tables.json`` in the FAISS store directory."""
    path = Path(store_dir) / "tables.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tables, f, ensure_ascii=False, indent=2)
    logger.info(f"[structured_store] Saved {len(tables)} table(s) to {path}")
    return str(path)


def load_tables(store_dir: str) -> List[Dict]:
    """Load ``tables.json`` from the FAISS store directory. Returns [] if absent."""
    path = Path(store_dir) / "tables.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_tables(tables: List[Dict], query: str) -> List[Dict]:
    """
    Rank tables by keyword relevance to the user query.

    Scoring:
        +1  per query-term match in description / headers / text
        +3  per column-header substring match in query
    """
    query_lower = query.lower()
    query_terms = [t for t in query_lower.split() if len(t) > 1]

    scored: List[tuple] = []
    for table in tables:
        score = 0
        haystack = (
            table.get("description", "")
            + " "
            + " ".join(table.get("headers", []))
            + " "
            + table.get("text", "")
        ).lower()

        for term in query_terms:
            if term in haystack:
                score += 1

        for header in table.get("headers", []):
            if header.lower() in query_lower:
                score += 3

        if score > 0:
            scored.append((table, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in scored]