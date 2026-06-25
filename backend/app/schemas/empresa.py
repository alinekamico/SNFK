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
    tiny_token: Optional[str] = None


class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    email: Optional[str] = None
    ativa: Optional[bool] = None
    tiny_token: Optional[str] = None


class EmpresaResponse(EmpresaBase):
    id: str
    ativa: bool
    tiny_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
