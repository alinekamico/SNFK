from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base


class Certificado(Base):
    __tablename__ = "certificados"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(CHAR(36), ForeignKey("empresas.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    pfx_path = Column(Text, nullable=False)   # caminho no servidor, fora do webroot
    senha_cifrada = Column(Text, nullable=False)  # Fernet encrypted
    validade = Column(DateTime)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="certificados")

    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
