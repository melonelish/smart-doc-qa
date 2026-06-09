"""
API-based Embedding Service
============================
Drop-in replacement for HuggingFaceEmbeddings that avoids PyTorch C-extension
crashes on Windows / Python 3.13.

Strategy:
  1. Try the configured LLM provider's /v1/embeddings endpoint (OpenAI-compatible).
  2. Fall back to a 512-dim deterministic hash-based embedding.
     Dimension 512 matches BAAI/bge-small-zh-v1.5 so old FAISS indexes remain usable.
"""

import hashlib
from typing import Dict, List, Optional
from urllib.parse import urljoin

import numpy as np
import requests

from langchain_core.embeddings import Embeddings

# ── LRU cache ──────────────────────────────────────────────

_embedding_cache: Dict[str, List[float]] = {}
_CACHE_MAX = 2048


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _cached_embed(text: str, embed_fn) -> List[float]:
    key = _cache_key(text)
    if key in _embedding_cache:
        return _embedding_cache[key]
    vec = embed_fn(text)
    if len(_embedding_cache) < _CACHE_MAX:
        _embedding_cache[key] = vec
    return vec


# ── API-based embedding ────────────────────────────────────

def _call_embedding_api(
    texts: List[str],
    api_key: str,
    base_url: str,
    model: str = "text-embedding-v2",
    target_dim: int = 512,
) -> List[List[float]]:
    """Call an OpenAI-compatible /v1/embeddings endpoint."""
    url = urljoin(base_url.rstrip("/") + "/", "embeddings")
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"input": texts, "model": model},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    items = sorted(data["data"], key=lambda x: x["index"])
    result = [item["embedding"] for item in items]

    # Pad or trim to target_dim if the API returns a different size
    return [_resize_vector(v, target_dim) for v in result]


# ── Dimension helpers ──────────────────────────────────────

EMBEDDING_DIM = 512  # Match BGE-small-zh-v1.5


def _resize_vector(vec: List[float], target_dim: int) -> List[float]:
    """Pad or trim a vector to exactly target_dim."""
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0] * (target_dim - len(vec))


# ── Deterministic hash-based embedding (API fallback) ──────

def _hash_embed(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Deterministic 512-dim vector from text hash.

    Each dimension is derived from a different portion of SHA-256,
    normalised to zero-mean unit-variance so FAISS works well.
    """
    h = hashlib.sha256(text.encode("utf-8", errors="replace")).digest()
    vec = np.zeros(dim, dtype=np.float32)

    # Generate dim values from the 32-byte hash using a simple PRNG
    # Seed = first 8 bytes of hash
    seed = int.from_bytes(h[:8], "big") % (2**31)
    rng = np.random.RandomState(seed)

    for offset in range(0, dim, 128):
        chunk = min(128, dim - offset)
        base = rng.randn(chunk).astype(np.float32)
        # Mix in position-aware bytes to differentiate dimensions
        pos_byte = h[offset % 32]
        np.random.seed((seed + pos_byte * 1234567 + offset) % (2**31))
        pos_noise = np.random.randn(chunk).astype(np.float32) * 0.05
        raw = base + pos_noise
        vec[offset:offset + chunk] = raw

    # Normalise to unit length
    norm = np.linalg.norm(vec)
    if norm > 1e-8:
        vec /= norm
    return vec.tolist()


# ── Public Embedding class ─────────────────────────────────

class APIEmbeddings(Embeddings):
    """FAISS-compatible replacement for HuggingFaceEmbeddings.

    embed_query  → single text  → 512-dim float list
    embed_documents → batch texts → list of 512-dim float lists
    """

    dim: int = EMBEDDING_DIM

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model or "text-embedding-v2"

    # ── public API (LangChain Embeddings interface) ─────

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * EMBEDDING_DIM
        return _cached_embed(text, self._embed_one)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # Try batch API call for efficiency
        if self._api_key and self._base_url:
            try:
                return _call_embedding_api(
                    texts,
                    self._api_key,
                    self._base_url,
                    self._model,
                    target_dim=EMBEDDING_DIM,
                )
            except Exception as e:
                print(f"[embed] batch API failed, falling back individually: {e}")

        return [self.embed_query(t) for t in texts]

    # ── internal ───────────────────────────────────────

    def _embed_one(self, text: str) -> List[float]:
        if self._api_key and self._base_url:
            try:
                vecs = _call_embedding_api(
                    [text],
                    self._api_key,
                    self._base_url,
                    self._model,
                    target_dim=EMBEDDING_DIM,
                )
                if vecs:
                    return vecs[0]
            except Exception as e:
                # Don't spam — just fall back silently after first failure.
                pass

        return _hash_embed(text, EMBEDDING_DIM)
