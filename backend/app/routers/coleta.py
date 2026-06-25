from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Empresa
from app.services.coleta_service import coletar_sefaz

router = APIRouter(prefix="/coleta", tags=["coleta"])


@router.post("/sefaz/{empresa_id}")
def disparar_coleta_sefaz(
    empresa_id: str,
    background_tasks: BackgroundTasks,
    ambiente: str = "2",
    db: Session = Depends(get_db),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    def _coleta():
        db2 = SessionLocal()
        try:
            emp = db2.query(Empresa).filter(Empresa.id == empresa_id).first()
            coletar_sefaz(db2, emp, ambiente=ambiente)
        finally:
            db2.close()

    background_tasks.add_task(_coleta)
    return {"ok": True, "message": f"Coleta SEFAZ iniciada para {empresa.razao_social}"}
