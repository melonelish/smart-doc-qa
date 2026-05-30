"""
SmartDocQA - Question Answering Service
========================================
Retrieval pipeline:

    User question
        │
        ▼
  ┌──────────────────────┐
  │  FAISS  Vector Search│  ← BGE semantic embeddings
  │  + BM25  Keyword Sz  │  ← jieba tokenization
  └──────────┬───────────┘
             │  RRF Fusion (Reciprocal Rank Fusion)
             ▼
  ┌──────────────────────┐
  │  Cross-Encoder Rank  │  ← BGE reranker re-sorts
  └──────────┬───────────┘
             │  Top-K chunks
             ▼
  ┌──────────────────────┐
  │  LLM Generation      │  ← context + history → answer + sources
  └──────────────────────┘
"""

import csv
import os
import pickle
import shutil
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings

settings = get_settings()

# HuggingFace mirror for China — set in .env as HF_ENDPOINT=https://hf-mirror.com
if settings.hf_endpoint:
    os.environ["HF_ENDPOINT"] = settings.hf_endpoint

# ═══════════════════════════════════════════════════════════
#  SYSTEM PROMPT  — improved with source-citation rules
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是 SmartDocQA，一个专业的文档智能问答助手。你必须严格基于下面提供的文档片段回答问题，不得虚构任何信息。

## 核心原则

1. 基于文档：回答中所有事实、数据和结论，必须能在提供的文档片段中找到明确依据。
2. 诚实作答：如果文档片段不足以回答问题，必须明确说明「根据提供的文档内容，无法回答此问题」，并告知缺少什么信息。
3. 精确引用：回答中的重要事实请在后面标注引用来源，格式为 [来源: 文档名]。
4. 数据准确：数字、日期、人名必须原样引用，不得改写或约算。
5. 简洁清晰：用中文回答，先给结论再展开细节。

## 回答格式（严格遵守）

你的回答必须按以下结构组织，每个部分之间空一行：

结论：一句话给出明确答案。

依据：逐条列出文档中的关键证据，每条单独一行。

引用：[来源: xxx] 跟在每条依据后或统一列出。

——

特殊情况（分析型问题）：
先给出分析推导，再列依据，最后说明哪些是原文、哪些是推断。

——

重要排版规则：
- 各部分之间必须用空行分隔，不要把所有内容挤在一段
- 不要使用 Markdown 加粗符号（如 ** 或 __）
- 不要使用标题符号（如 ## 或 ###）
- 纯文本自然分段即可

## 多轮对话

上方可能包含对话历史。如果当前问题与历史对话相关，请结合上下文理解意图；如果无关，忽略历史直接聚焦当前问题。无论是否有历史，你的事实依据必须来自本次提供的文档片段。"""

# ═══════════════════════════════════════════════════════════
#  SINGLETON EMBEDDINGS
# ═══════════════════════════════════════════════════════════

_embeddings_instance: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Lazy singleton — load once, reuse across all queries."""
    global _embeddings_instance
    if _embeddings_instance is None:
        print(f"[embed] Loading {settings.local_embedding_model} ... (first time, may download)")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.local_embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 8,
            },
        )
        print("[embed] Model loaded OK")
    return _embeddings_instance


# ═══════════════════════════════════════════════════════════
#  SINGLETON RERANKER
# ═══════════════════════════════════════════════════════════

_reranker_instance = None  # type: Optional[object]


def get_reranker():
    """Lazy singleton cross-encoder reranker."""
    global _reranker_instance
    if _reranker_instance is None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is required for reranking. "
                "Run: pip install sentence-transformers"
            )
        print(f"[rerank] Loading {settings.reranker_model} ... (first time, may download)")
        _reranker_instance = CrossEncoder(
            settings.reranker_model,
            max_length=512,
            device="cpu",
        )
        print("[rerank] Model loaded OK")
    return _reranker_instance


# ═══════════════════════════════════════════════════════════
#  BM25 KEYWORD RETRIEVER  (for hybrid search)
# ═══════════════════════════════════════════════════════════


def _tokenize(text: str) -> List[str]:
    """Chinese-aware tokenizer: uses jieba for CJK, space split for ASCII."""
    try:
        import jieba
    except ImportError:
        raise RuntimeError("jieba is required for BM25. Run: pip install jieba")
    tokens: List[str] = []
    for token in jieba.cut(text):
        token = token.strip()
        if token:
            tokens.append(token)
    return tokens


class BM25Retriever:
    """BM25 keyword retriever built over document chunks."""

    def __init__(self, documents: List[Document]):
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise RuntimeError("rank-bm25 is required. Run: pip install rank-bm25")
        self._documents = documents
        self._corpus = [_tokenize(doc.page_content) for doc in documents]
        self._bm25 = BM25Okapi(self._corpus)

    def search(
        self, query: str, k: int = 10
    ) -> List[Tuple[Document, float]]:
        tokenized = _tokenize(query)
        scores = self._bm25.get_scores(tokenized)
        # Normalise to [0, 1]
        max_s = max(scores) if max(scores) > 0 else 1.0
        normalised = [s / max_s for s in scores]
        results = list(zip(self._documents, normalised))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


# ═══════════════════════════════════════════════════════════
#  RRF FUSION  (Reciprocal Rank Fusion)
# ═══════════════════════════════════════════════════════════


def _rrf_fusion(
    faiss_results: List[Tuple[Document, float]],
    bm25_results: List[Tuple[Document, float]],
    k: int = 60,
) -> List[Tuple[Document, float]]:
    """
    Merge FAISS (semantic) and BM25 (keyword) retrieval results.

    RRF formula: score(d) = Σ 1/(k + rank_i(d))

    Deduplication key: (page_content[:80], metadata["source"])
    """
    _id_of = {}  # doc -> compact id
    _doc_of = {}  # compact id -> doc
    scores: Dict[str, float] = {}

    for rank, (doc, _) in enumerate(faiss_results):
        key = _make_key(doc)
        if key not in _id_of:
            _id_of[key] = key
            _doc_of[key] = doc
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)

    for rank, (doc, _) in enumerate(bm25_results):
        key = _make_key(doc)
        if key not in _id_of:
            _id_of[key] = key
            _doc_of[key] = doc
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(_doc_of[key], score) for key, score in ranked]


def _make_key(doc: Document) -> str:
    """Compact identity key for deduplication."""
    return f"{doc.page_content[:80]}|{doc.metadata.get('source','')}|{doc.metadata.get('page','')}|{doc.metadata.get('chunk','')}"


# ═══════════════════════════════════════════════════════════
#  CROSS-ENCODER RERANK
# ═══════════════════════════════════════════════════════════


def _rerank(
    query: str,
    documents: List[Tuple[Document, float]],
    top_k: int = 4,
) -> List[Document]:
    """Re-sort candidates with a cross-encoder for precision."""
    if not documents:
        return []
    docs = [doc for doc, _ in documents]
    pairs = [[query, doc.page_content] for doc in docs]
    reranker = get_reranker()
    scores = reranker.predict(
        pairs,
        show_progress_bar=False,
        batch_size=min(8, len(docs)),
    )
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked[:top_k]]


# ═══════════════════════════════════════════════════════════
#  CONVERSATION MEMORY  (multi-turn)
# ═══════════════════════════════════════════════════════════


@dataclass
class ConversationTurn:
    role: str          # "user" | "assistant"
    content: str
    sources: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class ConversationMemory:
    """In-memory multi-turn conversation store with TTL eviction."""

    def __init__(self, ttl_seconds: int = 3600):
        self._store: Dict[str, List[ConversationTurn]] = {}
        self._ttl = ttl_seconds

    def _evict(self, conv_id: str) -> None:
        now = time.time()
        if conv_id in self._store:
            self._store[conv_id] = [
                t for t in self._store[conv_id]
                if now - t.timestamp < self._ttl
            ]

    def get_history(
        self, conversation_id: str, max_turns: int = 6
    ) -> List[ConversationTurn]:
        self._evict(conversation_id)
        return self._store.get(conversation_id, [])[-max_turns:]

    def add_turn(self, conversation_id: str, turn: ConversationTurn) -> None:
        if conversation_id not in self._store:
            self._store[conversation_id] = []
        self._store[conversation_id].append(turn)
        self._evict(conversation_id)

    def clear(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)


conversation_memory = ConversationMemory(
    ttl_seconds=settings.conversation_ttl_seconds
)


# ═══════════════════════════════════════════════════════════
#  DOCUMENT LOADER
# ═══════════════════════════════════════════════════════════


def _load_document(file_path: str) -> List[Document]:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        docs = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"source": path.name, "page": i + 1},
                ))
        return docs

    elif ext == ".csv":
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            raise ValueError("CSV file is empty")
        docs = []
        for i, row in enumerate(rows):
            text = " | ".join(f"{k}: {v}" for k, v in row.items())
            docs.append(Document(
                page_content=text,
                metadata={"source": path.name, "row": i + 1},
            ))
        return docs

    elif ext in (".txt", ".md"):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        return [Document(page_content=text, metadata={"source": path.name})]

    elif ext == ".docx":
        from docx import Document as DocxDocument
        docx_doc = DocxDocument(str(path))
        text = "\n".join(
            para.text for para in docx_doc.paragraphs if para.text.strip()
        )
        return [Document(page_content=text, metadata={"source": path.name})]

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ═══════════════════════════════════════════════════════════
#  DOCUMENT SPLITTER
# ═══════════════════════════════════════════════════════════


def _split_document(documents: List[Document]) -> List[Document]:
    """Split pages into semantic chunks using RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", " "],
        keep_separator=True,
    )
    chunks = text_splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk"] = i
    return chunks


def load_and_split_document(file_path: str) -> List[Document]:
    """Public API — load + split a document file."""
    raw_docs = _load_document(file_path)
    return _split_document(raw_docs)


# ═══════════════════════════════════════════════════════════
#  QA SERVICE  (main class)
# ═══════════════════════════════════════════════════════════


class QAService:
    """
    Smart document Q&A service.

    Pipeline:  FAISS + BM25 → RRF fusion → Cross-encoder rerank → LLM
    Supports:  multi-turn conversation, source citation with chunk details.
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None

    # ------- LLM client (lazy) ----------------------------------

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=settings.openai_timeout,
                max_retries=1,
            )
        return self._client

    # ------- Vector store CRUD -----------------------------------

    @staticmethod
    def create_vector_store(
        chunks: List[Document], vector_store_name: str
    ) -> str:
        """Create FAISS index and persist chunks for BM25 reconstruction."""
        vector_store_dir = Path(settings.vector_store_path) / vector_store_name
        if vector_store_dir.exists():
            shutil.rmtree(vector_store_dir)
        vector_store_dir.mkdir(parents=True, exist_ok=True)

        embeddings = get_embeddings()
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(str(vector_store_dir))

        # Verify
        idx_path = vector_store_dir / "index.faiss"
        if not idx_path.exists():
            raise RuntimeError(
                f"FAISS index not saved to {idx_path}. "
                f"Directory: {os.listdir(str(vector_store_dir))}"
            )

        # Persist chunks for BM25 rebuild
        chunks_path = vector_store_dir / "chunks.pkl"
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)

        # Persist version marker
        version_path = vector_store_dir / "version.txt"
        version_path.write_text(
            f"model={settings.local_embedding_model}\n", encoding="utf-8"
        )

        print(f"[vector] Created '{vector_store_name}' ({len(chunks)} chunks)")
        return str(vector_store_dir)

    @staticmethod
    def load_vector_store(vector_store_name: str):
        """Load FAISS index. Returns None if missing."""
        vector_store_dir = Path(settings.vector_store_path) / vector_store_name
        idx_path = vector_store_dir / "index.faiss"
        if not idx_path.exists():
            return None
        embeddings = get_embeddings()
        try:
            return FAISS.load_local(
                str(vector_store_dir),
                embeddings,
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            # Dimension mismatch → old vector store, needs reprocessing
            raise RuntimeError(
                f"无法加载向量库 '{vector_store_name}'，可能是旧版本创建的。"
                f"请重新处理文档。错误: {e}"
            )

    @classmethod
    def _load_chunks(cls, vector_store_name: str) -> List[Document]:
        chunks_path = (
            Path(settings.vector_store_path) / vector_store_name / "chunks.pkl"
        )
        if not chunks_path.exists():
            return []
        with open(chunks_path, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def delete_vector_store(vector_store_name: str) -> None:
        vector_store_dir = Path(settings.vector_store_path) / vector_store_name
        if vector_store_dir.exists():
            shutil.rmtree(vector_store_dir)

    # ------- LLM chat wrapper ------------------------------------

    def llm_chat(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,  # slight variation, but still factual
        )
        return resp.choices[0].message.content

    def _format_answer(self, text: str) -> str:
        """Post-process LLM answer: strip markdown, normalize readability.

        Produces plain-text structured with blank lines between sections
        and each list item on its own line.
        """
        import re

        # 1 ▸ Remove markdown formatting markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold** → bold
        text = re.sub(r'__(.+?)__', r'\1', text)        # __underline__
        text = re.sub(r'^#{1,6}\s', '', text, flags=re.MULTILINE)  # strip headers

        # 2 ▸ Ensure ordered-list items each start their own line
        #    e.g. "1.xxx，2.yyy" or "1.xxx, 2.yyy" → "1.xxx\n2.yyy"
        text = re.sub(
            r'(\d{1,2}[\.\)、]\s*\S.*?)\s*[，,]+\s*(?=\d{1,2}[\.\)、]\s)',
            r'\1\n',
            text
        )

        # 3 ▸ Ensure dash/bullet items each start their own line
        #    e.g. "- xxx，- yyy" or "- xxx, - yyy" → "- xxx\n- yyy"
        text = re.sub(
            r'([\-·•]\s*\S.*?)\s*[，,]+\s*(?=[\-·•]\s)',
            r'\1\n',
            text
        )

        # 4 ▸ Insert blank line before section labels (结论/依据/引用/分析/注意)
        for label in ['结论', '依据', '引用', '分析', '注意', '补充', '说明', '总结', '拓展', '备注']:
            text = re.sub(
                rf'(?<!\n)(?<!^)({label}[：:]\s*)',
                r'\n\n\1',
                text
            )

        # 5 ▸ Normalize excessive blank lines (3+ → 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 6 ▸ Trim leading/trailing whitespace
        text = text.strip()

        return text

    # ------- Core Q&A --------------------------------------------

    def ask_question(
        self,
        vector_store_name: str,
        question: str,
        conversation_id: str = "",
        top_k: int = 4,
        use_hybrid: bool = True,
        use_rerank: bool = True,
    ) -> dict:
        """
        Full retrieval-augmented Q&A pipeline.

        Parameters
        ----------
        vector_store_name : str   — document ID used as vector store key
        question          : str   — user's question
        conversation_id   : str   — empty = new conversation; non-empty = continue
        top_k             : int   — number of chunks to feed the LLM
        use_hybrid        : bool  — enable BM25 + FAISS hybrid retrieval
        use_rerank        : bool  — enable cross-encoder re-ranking
        """
        # 1 ▸ Load vector store
        vector_store = self.load_vector_store(vector_store_name)
        if vector_store is None:
            raise ValueError(f"Vector store not found: {vector_store_name}")

        # 2 ▸ Retrieve — FAISS (always) + BM25 (optional)
        candidates: List[Tuple[Document, float]]
        if use_hybrid:
            all_chunks = self._load_chunks(vector_store_name)
            if all_chunks:
                bm25 = BM25Retriever(all_chunks)
                bm25_results = bm25.search(question, k=top_k * 5)
            else:
                bm25_results = []
            faiss_results = vector_store.similarity_search_with_score(
                question, k=top_k * 5
            )
            candidates = _rrf_fusion(faiss_results, bm25_results, k=60)
        else:
            candidates = vector_store.similarity_search_with_score(
                question, k=top_k * 5
            )

        if not candidates:
            raise ValueError("No relevant document passages found")

        # 3 ▸ Rerank  (optional, adds precision)
        if use_rerank and len(candidates) > top_k:
            pool = candidates[: min(top_k * 3, len(candidates))]
            final_docs = _rerank(question, pool, top_k=top_k)
        else:
            final_docs = [doc for doc, _ in candidates[:top_k]]

        # 4 ▸ Build context & source details
        context_parts: List[str] = []
        source_details: OrderedDict[str, list] = OrderedDict()

        for i, doc in enumerate(final_docs):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "")
            chunk_idx = doc.metadata.get("chunk", i)

            label = f"[片段 {i + 1}]"
            if page:
                label += f"  来源: {source} · 第 {page} 页"
            else:
                label += f"  来源: {source}"
            context_parts.append(f"{label}\n{doc.page_content}")

            if source not in source_details:
                source_details[source] = []
            source_details[source].append({
                "chunk_index": i + 1,
                "page": page,
                "snippet": (
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                ),
            })

        context = "\n\n" + "─" * 60 + "\n\n".join(context_parts) + "\n\n" + "─" * 60

        # 5 ▸ Build user message (history + context + question)
        history_text = ""
        if conversation_id:
            history = conversation_memory.get_history(conversation_id, max_turns=6)
            if history:
                history_parts = []
                for turn in history:
                    role_label = "👤 用户" if turn.role == "user" else "🤖 助手"
                    history_parts.append(f"{role_label}: {turn.content}")
                history_text = (
                    "## 历史对话\n\n"
                    + "\n\n".join(history_parts)
                    + "\n\n" + "─" * 60 + "\n\n"
                )

        user_message = (
            f"{history_text}"
            f"## 文档片段 (共 {len(final_docs)} 段)\n"
            f"{context}\n\n"
            f"## 当前问题\n\n"
            f"{question}"
        )

        # 6 ▸ LLM generation
        answer = self.llm_chat(SYSTEM_PROMPT, user_message)

        # 6b ▸ Post-process answer: strip markdown, normalize formatting
        answer = self._format_answer(answer)

        # 7 ▸ Persist conversation
        convo_id = conversation_id or str(uuid.uuid4())
        conversation_memory.add_turn(
            convo_id,
            ConversationTurn(role="user", content=question),
        )
        conversation_memory.add_turn(
            convo_id,
            ConversationTurn(
                role="assistant",
                content=answer,
                sources=[s for s in source_details],
            ),
        )

        # 8 ▸ Build response
        retrieve_method = (
            "hybrid + rerank" if use_hybrid and use_rerank
            else "hybrid" if use_hybrid
            else "vector + rerank" if use_rerank
            else "vector"
        )

        return {
            "question": question,
            "conversation_id": convo_id,
            "answer": answer,
            "sources": list(source_details.keys()),
            "source_details": [
                {"source": s, "chunks": d}
                for s, d in source_details.items()
            ],
            "source_count": len(final_docs),
            "retrieval_method": retrieve_method,
        }
