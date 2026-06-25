from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255))
    cnpj = Column(String(14), unique=True, nullable=False, index=True)
    email = Column(String(255))
    ativa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tiny_token = Column(String(255))   # token API Tiny v3 por empresa
    usuarios = relationship("Usuario", back_populates="empresa")

    certificados = relationship("Certificado", back_populates="empresa", cascade="all, delete-orphan")
    documentos = relationship("Documento", back_populates="empresa", cascade="all, delete-orphan")
    coleta_cursors = relationship("ColetaCursor", back_populates="empresa", cascade="all, delete-orphan")

    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
