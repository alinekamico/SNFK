from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db, SessionLocal
from app.models import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _coleta_inicial(empresa_id: str):
    """Roda coleta completa (SEFAZ + Tiny + UNO) para empresa recém-cadastrada."""
    from app.routers.coleta import _coletar_tiny, _coletar_uno
    from app.services.coleta_service import coletar_sefaz
    from datetime import date
    import logging
    logger = logging.getLogger(__name__)

    dt_ini = "01/01/2019"
    dt_fim = date.today().strftime("%d/%m/%Y")

    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            return

        logger.info(f"Coleta inicial automática para {empresa.razao_social}")

        # SEFAZ
        try:
            coletar_sefaz(db, empresa)
        except Exception as e:
            logger.error(f"Erro coleta SEFAZ inicial {empresa.cnpj}: {e}")

        # Tiny
        if empresa.tiny_token:
            try:
                _coletar_tiny(db, empresa, dt_ini, dt_fim)
            except Exception as e:
                logger.error(f"Erro coleta Tiny inicial {empresa.cnpj}: {e}")

        # UNO (global — já filtra por CNPJ das empresas cadastradas)
        try:
            _coletar_uno(db, dt_ini, dt_fim)
        except Exception as e:
            logger.error(f"Erro coleta UNO inicial: {e}")

        logger.info(f"Coleta inicial concluída para {empresa.razao_social}")
    finally:
        db.close()


@router.get("", response_model=List[EmpresaResponse])
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(Empresa).filter(Empresa.ativa == True).order_by(Empresa.razao_social).all()


@router.post("", response_model=EmpresaResponse)
def criar_empresa(body: EmpresaCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if db.query(Empresa).filter(Empresa.cnpj == body.cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    empresa = Empresa(**body.dict())
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    background_tasks.add_task(_coleta_inicial, str(empresa.id))
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
