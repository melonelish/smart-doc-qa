import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.db.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True, comment="Owner user ID"
    )
    name = Column(String(100), nullable=False, comment="User-given name e.g. 'My DeepSeek'")
    provider = Column(
        String(50), nullable=False,
        comment="Provider: deepseek / openai / qwen / doubao / mimo / custom"
    )
    base_url = Column(String(500), nullable=False, comment="API base URL")
    api_key_encrypted = Column(String(500), nullable=False, comment="Fernet-encrypted API key")
    model_name = Column(String(100), nullable=False, comment="Model name e.g. deepseek-chat")
    is_active = Column(Boolean, default=False, comment="Currently selected model")
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), comment="Creation time"
    )
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="Last update time"
    )
