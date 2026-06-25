from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import CHAR
import uuid
from datetime import datetime
from app.database import Base
import enum


class TipoDocumento(str, enum.Enum):
    emitida = "emitida"
    recebida = "recebida"


class FonteDocumento(str, enum.Enum):
    sefaz = "sefaz"
    tiny = "tiny"
    uno = "uno"


class Documento(Base):
    __tablename__ = "documentos_fiscais"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(CHAR(36), ForeignKey("empresas.id"), nullable=False)
    chave_acesso = Column(String(44), nullable=False, index=True)
    tipo = Column(Enum(TipoDocumento), nullable=False)
    fonte = Column(Enum(FonteDocumento), nullable=False)
    cnpj_emitente = Column(String(14), index=True)
    cnpj_destinatario = Column(String(14), index=True)
    razao_emitente = Column(String(255))
    razao_destinatario = Column(String(255))
    numero_nota = Column(String(20))
    serie = Column(String(3))
    data_emissao = Column(DateTime)
    valor_total = Column(Numeric(15, 2))
    xml_path = Column(Text)
    danfe_path = Column(Text)
    status = Column(String(50), default="Autorizada")
    nsu = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="documentos")

    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
