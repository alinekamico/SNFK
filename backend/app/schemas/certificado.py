from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CertificadoCreate(BaseModel):
    empresa_id: str
    nome: str


class CertificadoResponse(BaseModel):
    id: str
    empresa_id: str
    nome: str
    validade: Optional[datetime]
    ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True
