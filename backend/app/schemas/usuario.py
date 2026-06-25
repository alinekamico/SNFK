from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    departamento: Optional[str] = None
    senha: str
    perfil: str = "USER"
    empresa_id: Optional[str] = None

    @validator("perfil")
    def valida_perfil(cls, v):
        if v not in ["ADMIN", "USER", "READ_ONLY"]:
            raise ValueError("Perfil inválido")
        return v


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    departamento: Optional[str]
    perfil: str
    empresa_id: Optional[str]
    ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    perfil: str
    nome: str
