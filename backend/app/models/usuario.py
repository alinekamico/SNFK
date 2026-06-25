from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base
import enum


class PerfilUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    READ_ONLY = "READ_ONLY"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    departamento = Column(String(100))
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilUsuario), default=PerfilUsuario.USER)
    empresa_id = Column(CHAR(36), ForeignKey("empresas.id"), nullable=True)  # null = acesso a todas
    empresa = relationship("Empresa", back_populates="usuarios")
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
