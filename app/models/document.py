import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum
from app.db.database import Base
import enum


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ConversationRecord(Base):
    """Persistence QA conversation records."""
    __tablename__ = "conversation_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(
        String(36), nullable=False, index=True, comment="Associated document ID"
    )
    conversation_id = Column(
        String(36), nullable=False, index=True, comment="Conversation session ID"
    )
    role = Column(
        String(16), nullable=False, comment="Role: user / assistant"
    )
    content = Column(Text, nullable=False, comment="Message content")
    sources = Column(Text, nullable=True, comment="Source references (JSON)")
    created_at = Column(
        DateTime, default=datetime.utcnow, comment="Creation time"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False, comment="Original filename")
    file_path = Column(String(500), nullable=False, comment="File storage path")
    file_type = Column(String(20), nullable=False, comment="File extension")
    file_size = Column(Integer, nullable=False, comment="File size in bytes")
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        comment="Document processing status",
    )
    chunk_count = Column(Integer, default=0, comment="Number of text chunks")
    error_message = Column(Text, nullable=True, comment="Error message")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Creation time")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update time"
    )


class KnowledgeBase(Base):
    """A knowledge base groups multiple documents for cross-document QA."""
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, comment="Knowledge base name")
    description = Column(Text, nullable=True, comment="Knowledge base description")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Creation time")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update time"
    )


class KnowledgeBaseDocument(Base):
    """Many-to-many association between knowledge bases and documents."""
    __tablename__ = "knowledge_base_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kb_id = Column(String(36), nullable=False, index=True, comment="Knowledge base ID")
    doc_id = Column(String(36), nullable=False, index=True, comment="Document ID")
    added_at = Column(DateTime, default=datetime.utcnow, comment="When document was added")
