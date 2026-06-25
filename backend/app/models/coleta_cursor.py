from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base


class ColetaCursor(Base):
    __tablename__ = "coleta_cursors"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(CHAR(36), ForeignKey("empresas.id"), nullable=False)
    fonte = Column(String(50), nullable=False)  # sefaz | tiny | uno
    ultimo_nsu = Column(String(20), default="0")
    ultima_coleta = Column(DateTime)
    total_coletados = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="coleta_cursors")
