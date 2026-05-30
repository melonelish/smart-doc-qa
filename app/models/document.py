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
    """持久化问答记录 —— 按文档+对话分组，支持历史回看。"""
    __tablename__ = "conversation_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(
        String(36), nullable=False, index=True, comment="关联文档ID"
    )
    conversation_id = Column(
        String(36), nullable=False, index=True, comment="对话会话ID"
    )
    role = Column(
        String(16), nullable=False, comment="角色: user / assistant"
    )
    content = Column(Text, nullable=False, comment="消息内容")
    sources = Column(Text, nullable=True, comment="引用来源 (JSON)")
    created_at = Column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_type = Column(String(20), nullable=False, comment="文件类型扩展名")
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        comment="文档处理状态",
    )
    chunk_count = Column(Integer, default=0, comment="文本分块数量")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
