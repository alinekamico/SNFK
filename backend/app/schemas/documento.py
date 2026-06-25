from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class DocumentoResponse(BaseModel):
    id: str
    empresa_id: str
    chave_acesso: str
    tipo: str
    fonte: str
    cnpj_emitente: Optional[str]
    cnpj_destinatario: Optional[str]
    razao_emitente: Optional[str]
    razao_destinatario: Optional[str]
    numero_nota: Optional[str]
    serie: Optional[str]
    data_emissao: Optional[datetime]
    valor_total: Optional[Decimal]
    status: Optional[str]
    has_xml: bool = False
    has_danfe: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentoFiltro(BaseModel):
    empresa_id: Optional[str]
    tipo: Optional[str]
    fonte: Optional[str]
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    cnpj_emitente: Optional[str]
    cnpj_destinatario: Optional[str]
    numero_nota: Optional[str]
    status: Optional[str]
    page: int = 1
    per_page: int = 50
