from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import zipfile, io, os
from app.database import get_db
from app.models import Documento, Certificado
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
        dr.has_danfe = bool(d.danfe_path and Path(d.danfe_path).exists()) or bool(d.xml_path and Path(d.xml_path).exists())
        result.append(dr)
    return result


@router.get("/stats")
def stats_documentos(db: Session = Depends(get_db)):
    total = db.query(Documento).count()
    recebidas = db.query(Documento).filter(Documento.tipo == "recebida").count()
    emitidas = db.query(Documento).filter(Documento.tipo == "emitida").count()
    return {"total": total, "recebidas": recebidas, "emitidas": emitidas}


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
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    # Se já tem DANFe salvo, retorna direto
    if doc.danfe_path and Path(doc.danfe_path).exists():
        return FileResponse(doc.danfe_path, filename=f"DANFE_{doc.numero_nota}.pdf", media_type="application/pdf")

    # Gera DANFe on-demand a partir do XML
    if doc.xml_path and Path(doc.xml_path).exists():
        from app.services.tiny_service import gerar_danfe_do_xml
        xml_content = Path(doc.xml_path).read_text(encoding="utf-8")
        pdf = gerar_danfe_do_xml(xml_content)
        if pdf:
            return StreamingResponse(
                io.BytesIO(pdf),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=DANFE_{doc.numero_nota}.pdf"}
            )

    raise HTTPException(status_code=404, detail="DANFe não disponível para este documento")


@router.post("/buscar-xml/{doc_id}")
def buscar_xml_sefaz(doc_id: str, db: Session = Depends(get_db)):
    """Busca XML no SEFAZ via NFeConsultaProtocolo4 para notas sem XML local (ex: UNO)."""
    from app.services import sefaz_service, danfe_service
    from app.config import settings

    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    if doc.xml_path and Path(doc.xml_path).exists():
        # Já tem XML — retorna direto
        return FileResponse(doc.xml_path, filename=f"{doc.chave_acesso}.xml", media_type="application/xml")

    cert = db.query(Certificado).filter(
        Certificado.empresa_id == doc.empresa_id,
        Certificado.ativo == True,
    ).first()
    if not cert:
        raise HTTPException(status_code=400, detail="Empresa sem certificado ativo para consultar SEFAZ")

    xml_str = sefaz_service.buscar_nfe_por_chave(
        chave=doc.chave_acesso,
        pfx_path=cert.pfx_path,
        senha_cifrada=cert.senha_cifrada,
        ambiente="1",
    )
    if not xml_str:
        raise HTTPException(status_code=502, detail="SEFAZ não retornou XML para esta chave de acesso")

    # Salva XML
    xml_dir = Path(settings.STORAGE_PATH) / "xml" / doc.cnpj_emitente
    xml_dir.mkdir(parents=True, exist_ok=True)
    xml_path = xml_dir / f"{doc.chave_acesso}.xml"
    xml_path.write_text(xml_str, encoding="utf-8")

    # Gera DANFe
    danfe_dir = Path(settings.STORAGE_PATH) / "danfe" / doc.cnpj_emitente
    danfe_dir.mkdir(parents=True, exist_ok=True)
    danfe_path = danfe_dir / f"{doc.chave_acesso}.pdf"
    danfe_service.gerar_danfe_from_xml(xml_str, str(danfe_path))

    # Atualiza registro
    doc.xml_path = str(xml_path)
    doc.danfe_path = str(danfe_path) if danfe_path.exists() else None
    db.commit()

    return FileResponse(str(xml_path), filename=f"{doc.chave_acesso}.xml", media_type="application/xml")


@router.post("/buscar-danfe/{doc_id}")
def buscar_danfe_sefaz(doc_id: str, db: Session = Depends(get_db)):
    """Busca XML no SEFAZ e gera DANFe para notas sem arquivo local."""
    from app.services import sefaz_service, danfe_service
    from app.config import settings

    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    # Se já tem DANFe ou XML local, usa o fluxo normal
    if doc.danfe_path and Path(doc.danfe_path).exists():
        return FileResponse(doc.danfe_path, filename=f"DANFE_{doc.numero_nota}.pdf", media_type="application/pdf")
    if doc.xml_path and Path(doc.xml_path).exists():
        from app.services.tiny_service import gerar_danfe_do_xml
        xml_content = Path(doc.xml_path).read_text(encoding="utf-8")
        pdf = gerar_danfe_do_xml(xml_content)
        if pdf:
            return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=DANFE_{doc.numero_nota}.pdf"})

    cert = db.query(Certificado).filter(
        Certificado.empresa_id == doc.empresa_id, Certificado.ativo == True,
    ).first()
    if not cert:
        raise HTTPException(status_code=400, detail="Empresa sem certificado ativo")

    xml_str = sefaz_service.buscar_nfe_por_chave(doc.chave_acesso, cert.pfx_path, cert.senha_cifrada, "1")
    if not xml_str:
        raise HTTPException(status_code=502, detail="SEFAZ não retornou XML")

    xml_dir = Path(settings.STORAGE_PATH) / "xml" / doc.cnpj_emitente
    xml_dir.mkdir(parents=True, exist_ok=True)
    xml_path = xml_dir / f"{doc.chave_acesso}.xml"
    xml_path.write_text(xml_str, encoding="utf-8")
    doc.xml_path = str(xml_path)

    danfe_dir = Path(settings.STORAGE_PATH) / "danfe" / doc.cnpj_emitente
    danfe_dir.mkdir(parents=True, exist_ok=True)
    danfe_path_obj = danfe_dir / f"{doc.chave_acesso}.pdf"
    danfe_service.gerar_danfe_from_xml(xml_str, str(danfe_path_obj))

    if danfe_path_obj.exists():
        doc.danfe_path = str(danfe_path_obj)
        db.commit()
        return FileResponse(str(danfe_path_obj), filename=f"DANFE_{doc.numero_nota}.pdf", media_type="application/pdf")

    db.commit()
    raise HTTPException(status_code=500, detail="Erro ao gerar DANFe")


@router.post("/download-lote")
def download_lote(ids: List[str], db: Session = Depends(get_db)):
    """Download em lote de XMLs e DANFes em ZIP."""
    from app.services.tiny_service import gerar_danfe_do_xml
    docs = db.query(Documento).filter(Documento.id.in_(ids)).all()
    if not docs:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            xml_ok = doc.xml_path and Path(doc.xml_path).exists()
            if xml_ok:
                zf.write(doc.xml_path, f"xml/{doc.chave_acesso}.xml")
                # Gera DANFe on-demand se não tiver salvo
                if not (doc.danfe_path and Path(doc.danfe_path).exists()):
                    xml_content = Path(doc.xml_path).read_text(encoding="utf-8")
                    pdf = gerar_danfe_do_xml(xml_content)
                    if pdf:
                        zf.writestr(f"danfe/DANFE_{doc.numero_nota}.pdf", pdf)
                else:
                    zf.write(doc.danfe_path, f"danfe/DANFE_{doc.numero_nota}.pdf")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=documentos_fiscais.zip"},
    )
