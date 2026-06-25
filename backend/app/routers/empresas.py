from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("", response_model=List[EmpresaResponse])
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(Empresa).filter(Empresa.ativa == True).order_by(Empresa.razao_social).all()


@router.post("", response_model=EmpresaResponse)
def criar_empresa(body: EmpresaCreate, db: Session = Depends(get_db)):
    if db.query(Empresa).filter(Empresa.cnpj == body.cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    empresa = Empresa(**body.dict())
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return empresa


@router.get("/{empresa_id}", response_model=EmpresaResponse)
def obter_empresa(empresa_id: str, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa


@router.patch("/{empresa_id}", response_model=EmpresaResponse)
def atualizar_empresa(empresa_id: str, body: EmpresaUpdate, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    for k, v in body.dict(exclude_none=True).items():
        setattr(empresa, k, v)
    db.commit()
    db.refresh(empresa)
    return empresa
