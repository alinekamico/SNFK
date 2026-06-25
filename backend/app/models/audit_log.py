from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("usuarios.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100))
    entity_id = Column(String(36))
    ip = Column(String(45))
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
