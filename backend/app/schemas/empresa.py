from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re


class EmpresaBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str]
    cnpj: str
    email: Optional[str]

    @validator("cnpj")
    def valida_cnpj(cls, v):
        cnpj = re.sub(r"\D", "", v)
        if len(cnpj) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")
        return cnpj


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razao_social: Optional[str]
    nome_fantasia: Optional[str]
    email: Optional[str]
    ativa: Optional[bool]


class EmpresaResponse(EmpresaBase):
    id: str
    ativa: bool
    created_at: datetime

    class Config:
        from_attributes = True
