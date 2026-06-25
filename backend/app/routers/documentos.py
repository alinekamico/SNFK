from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import zipfile, io, os
from app.database import get_db
from app.models import Documento
from app.schemas.documento import DocumentoResponse

router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.get("", response_model=List[DocumentoResponse])
def listar_documentos(
    empresa_id: Optional[str] = None,
    tipo: Optional[str] = None,
    fonte: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    cnpj_emitente: Optional[str] = None,
    numero_nota: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Documento)
    if empresa_id:
        q = q.filter(Documento.empresa_id == empresa_id)
    if tipo:
        q = q.filter(Documento.tipo == tipo)
    if fonte:
        q = q.filter(Documento.fonte == fonte)
    if data_inicio:
        q = q.filter(Documento.data_emissao >= data_inicio)
    if data_fim:
        q = q.filter(Documento.data_emissao <= data_fim)
    if cnpj_emitente:
        q = q.filter(Documento.cnpj_emitente == cnpj_emitente)
    if numero_nota:
        q = q.filter(Documento.numero_nota == numero_nota)
    if status:
        q = q.filter(Documento.status == status)

    total = q.count()
    docs = q.order_by(Documento.data_emissao.desc()).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for d in docs:
        dr = DocumentoResponse.from_orm(d)
        dr.has_xml = bool(d.xml_path and Path(d.xml_path).exists())
        dr.has_danfe = bool(d.danfe_path and Path(d.danfe_path).exists())
        result.append(dr)
    return result


@router.get("/{doc_id}/xml")
def download_xml(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc or not doc.xml_path:
        raise HTTPException(status_code=404, detail="XML não encontrado")
    if not Path(doc.xml_path).exists():
        raise HTTPException(status_code=404, detail="Arquivo XML não encontrado no servidor")
    return FileResponse(doc.xml_path, filename=f"{doc.chave_acesso}.xml", media_type="application/xml")


@router.get("/{doc_id}/danfe")
def download_danfe(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc or not doc.danfe_path:
        raise HTTPException(status_code=404, detail="DANFe não encontrado")
    if not Path(doc.danfe_path).exists():
        raise HTTPException(status_code=404, detail="Arquivo DANFe não encontrado no servidor")
    return FileResponse(doc.danfe_path, filename=f"DANFE_{doc.numero_nota}.pdf", media_type="application/pdf")


@router.post("/download-lote")
def download_lote(ids: List[str], db: Session = Depends(get_db)):
    """Download em lote de XMLs e DANFes em ZIP."""
    docs = db.query(Documento).filter(Documento.id.in_(ids)).all()
    if not docs:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            if doc.xml_path and Path(doc.xml_path).exists():
                zf.write(doc.xml_path, f"xml/{doc.chave_acesso}.xml")
            if doc.danfe_path and Path(doc.danfe_path).exists():
                zf.write(doc.danfe_path, f"danfe/DANFE_{doc.numero_nota}.pdf")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=documentos_fiscais.zip"},
    )
