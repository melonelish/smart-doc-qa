import csv
import os
import pickle
import re
import shutil
from pathlib import Path
from typing import List

from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from app.core.config import get_settings

settings = get_settings()


class LocalEmbeddings(Embeddings):
    """基于 TF-IDF 的本地嵌入，不依赖云端 API 或 Sentence Transformers。"""

    def __init__(self, model_name: str, vectorizer_path: str = ""):
        self._model_name = model_name
        self._vectorizer = None
        self._vectorizer_path = vectorizer_path
        if vectorizer_path and os.path.exists(vectorizer_path):
            with open(vectorizer_path, "rb") as f:
                self._vectorizer = pickle.load(f)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._vectorizer = TfidfVectorizer(max_features=1536)
        vectors = self._vectorizer.fit_transform(texts)
        if self._vectorizer_path:
            os.makedirs(os.path.dirname(self._vectorizer_path), exist_ok=True)
            with open(self._vectorizer_path, "wb") as f:
                pickle.dump(self._vectorizer, f)
        return vectors.toarray().tolist()

    def embed_query(self, text: str) -> List[float]:
        if self._vectorizer is None:
            if self._vectorizer_path and os.path.exists(self._vectorizer_path):
                with open(self._vectorizer_path, "rb") as f:
                    self._vectorizer = pickle.load(f)
            else:
                raise RuntimeError(
                    f"TF-IDF vectorizer not fitted. Path={self._vectorizer_path}. "
                    f"Please re-process the document."
                )
        return self._vectorizer.transform([text]).toarray().tolist()[0]


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
        text = "\n".join(para.text for para in docx_doc.paragraphs if para.text.strip())
        return [Document(page_content=text, metadata={"source": path.name})]

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _split_text(text: str) -> List[str]:
    chunks = []
    parts = re.split(r"(\n\n|\n|。|！|？|\. |! |\? )", text)

    current = ""
    for part in parts:
        if len(current) + len(part) <= settings.chunk_size:
            current += part
        else:
            if current.strip():
                chunks.append(current.strip())
            current = part
    if current.strip():
        chunks.append(current.strip())

    merged = []
    for chunk in chunks:
        if len(chunk) < 100:
            if merged and len(merged[-1]) + len(chunk) < settings.chunk_size:
                merged[-1] += chunk
            else:
                merged.append(chunk)
        else:
            merged.append(chunk)

    return merged if merged else chunks


def load_and_split_document(file_path: str) -> List[Document]:
    raw_docs = _load_document(file_path)
    result = []
    for doc in raw_docs:
        texts = _split_text(doc.page_content)
        for i, t in enumerate(texts):
            meta = dict(doc.metadata)
            meta["chunk"] = i
            result.append(Document(page_content=t, metadata=meta))
    return result


SYSTEM_PROMPT = """You are a professional document Q&A assistant. Answer questions based only on the provided document excerpts.

Rules:
1. Only answer based on the provided excerpts, do not fabricate information
2. If the excerpts are insufficient, clearly state so
3. Keep answers concise and professional, use Chinese
4. Cite specific data when mentioned in excerpts"""


class QAService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=settings.openai_timeout,
                max_retries=1,
            )
        return self._client

    def _get_embeddings(self, vector_store_name: str = ""):
        if settings.openai_embedding_model == "local":
            vp = ""
            if vector_store_name:
                vp = os.path.join(settings.vector_store_path, vector_store_name, "vectorizer.pkl")
            return LocalEmbeddings(settings.local_embedding_model, vp)
        else:
            from langchain_openai import OpenAIEmbeddings
            kwargs = {
                "model": settings.openai_embedding_model,
                "openai_api_key": settings.openai_api_key,
                "openai_api_base": settings.openai_base_url,
                "request_timeout": settings.openai_timeout,
            }
            if settings.openai_proxy:
                kwargs["openai_proxy"] = settings.openai_proxy
            return OpenAIEmbeddings(**kwargs)

    def llm_chat(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content

    def create_vector_store(self, chunks: List[Document], vector_store_name: str) -> str:
        vector_store_dir = Path(settings.vector_store_path) / vector_store_name
        # 先清空旧数据（避免上次失败残留）
        if vector_store_dir.exists():
            shutil.rmtree(vector_store_dir)
        vector_store_dir.mkdir(parents=True, exist_ok=True)

        embeddings = self._get_embeddings(vector_store_name)
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(str(vector_store_dir))

        # 验证保存成功
        idx_path = vector_store_dir / "index.faiss"
        if not idx_path.exists():
            raise RuntimeError(
                f"FAISS index not saved to {idx_path}. "
                f"Directory contents: {os.listdir(str(vector_store_dir))}"
            )
        return str(vector_store_dir)

    def load_vector_store(self, vector_store_name: str):
        vector_store_dir = Path(settings.vector_store_path) / vector_store_name
        idx_path = vector_store_dir / "index.faiss"
        if not idx_path.exists():
            return None
        embeddings = self._get_embeddings(vector_store_name)
        return FAISS.load_local(
            str(vector_store_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    def delete_vector_store(self, vector_store_name: str):
        vector_store_dir = Path(settings.vector_store_path) / vector_store_name
        if vector_store_dir.exists():
            shutil.rmtree(vector_store_dir)

    def ask_question(self, vector_store_name: str, question: str, top_k: int = 4) -> dict:
        vector_store = self.load_vector_store(vector_store_name)
        if vector_store is None:
            raise ValueError(f"Vector store not found: {vector_store_name}")

        docs = vector_store.similarity_search(question, k=top_k)

        context = "\n\n".join(doc.page_content for doc in docs)

        user_message = f"Document excerpts:\n{context}\n\nQuestion: {question}"
        answer = self.llm_chat(SYSTEM_PROMPT, user_message)

        sources = []
        seen = set()
        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            if source not in seen:
                sources.append(source)
                seen.add(source)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "source_count": len(docs),
        }
