from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base


class ResetToken(Base):
    __tablename__ = "reset_tokens"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    usado = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
