"""Knowledge Base Service - CRUD + document binding + cross-document indexing."""

import shutil
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import (
    KnowledgeBase, KnowledgeBaseDocument, Document, DocumentStatus
)

settings = get_settings()


class KnowledgeBaseService:

    # ---- CRUD ----

    @staticmethod
    def create(db: Session, name: str, description: str = "") -> KnowledgeBase:
        kb = KnowledgeBase(name=name, description=description)
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def get(db: Session, kb_id: str) -> Optional[KnowledgeBase]:
        return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 50) -> List[KnowledgeBase]:
        return (
            db.query(KnowledgeBase)
            .order_by(KnowledgeBase.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(db: Session, kb_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[KnowledgeBase]:
        kb = KnowledgeBaseService.get(db, kb_id)
        if not kb:
            return None
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        kb.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def delete(db: Session, kb_id: str) -> bool:
        kb = KnowledgeBaseService.get(db, kb_id)
        if not kb:
            return False
        db.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.kb_id == kb_id
        ).delete()
        db.delete(kb)
        db.commit()
        try:
            kb_dir = Path(settings.vector_store_path) / f"kb_{kb_id}"
            if kb_dir.exists():
                shutil.rmtree(kb_dir)
        except Exception:
            pass
        return True

    # ---- Document binding ----

    @staticmethod
    def add_document(db: Session, kb_id: str, doc_id: str) -> bool:
        kb = KnowledgeBaseService.get(db, kb_id)
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not kb or not doc:
            return False
        existing = (
            db.query(KnowledgeBaseDocument)
            .filter(
                KnowledgeBaseDocument.kb_id == kb_id,
                KnowledgeBaseDocument.doc_id == doc_id,
            )
            .first()
        )
        if existing:
            return True

        assoc = KnowledgeBaseDocument(kb_id=kb_id, doc_id=doc_id)
        db.add(assoc)
        db.commit()
        return True

    @staticmethod
    def remove_document(db: Session, kb_id: str, doc_id: str) -> bool:
        db.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.kb_id == kb_id,
            KnowledgeBaseDocument.doc_id == doc_id,
        ).delete()
        db.commit()
        return True

    @staticmethod
    def add_documents_batch(db: Session, kb_id: str, doc_ids: List[str]) -> Dict[str, int]:
        result = {"added": 0, "skipped": 0}
        for doc_id in doc_ids:
            added = KnowledgeBaseService.add_document(db, kb_id, doc_id)
            if added:
                result["added"] += 1
            else:
                result["skipped"] += 1
        return result

    @staticmethod
    def get_documents(db: Session, kb_id: str) -> List[Document]:
        assocs = (
            db.query(KnowledgeBaseDocument)
            .filter(KnowledgeBaseDocument.kb_id == kb_id)
            .order_by(KnowledgeBaseDocument.added_at.asc())
            .all()
        )
        doc_ids = [a.doc_id for a in assocs]
        if not doc_ids:
            return []
        docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {d.id: d for d in docs}
        return [doc_map[did] for did in doc_ids if did in doc_map]

    @staticmethod
    def get_document_ids(db: Session, kb_id: str) -> List[str]:
        assocs = (
            db.query(KnowledgeBaseDocument)
            .filter(KnowledgeBaseDocument.kb_id == kb_id)
            .all()
        )
        return [a.doc_id for a in assocs]

    # ---- Vector store rebuild ----

    @staticmethod
    def rebuild_kb_index(db: Session, kb_id: str) -> str:
        from app.services.qa_service import QAService, load_and_split_document

        doc_ids = KnowledgeBaseService.get_document_ids(db, kb_id)
        if not doc_ids:
            raise ValueError("Knowledge base has no documents")

        all_chunks = []
        for doc_id in doc_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc or doc.status != DocumentStatus.READY:
                continue
            try:
                chunks = load_and_split_document(doc.file_path)
                for chunk in chunks:
                    chunk.metadata["document_id"] = doc_id
                    chunk.metadata["document_name"] = doc.filename
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"[kb] Warning: failed to load doc {doc_id}: {e}")
                continue

        if not all_chunks:
            raise ValueError("No readable documents in this knowledge base")

        kb_store_name = f"kb_{kb_id}"
        qa = QAService()
        store_dir = qa.create_vector_store(all_chunks, kb_store_name)
        meta_path = Path(settings.vector_store_path) / kb_store_name / "doc_ids.txt"
        meta_path.write_text(",".join(doc_ids), encoding="utf-8")
        return store_dir
