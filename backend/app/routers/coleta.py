from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Empresa, Documento
from app.services.coleta_service import coletar_sefaz
from app.services import tiny_service, uno_service
from app.config import settings
from datetime import datetime, date
from typing import Optional
import logging
import os

router = APIRouter(prefix="/coleta", tags=["coleta"])
logger = logging.getLogger(__name__)


def _salvar_arquivo(conteudo: bytes | str, pasta: str, nome: str) -> str:
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    modo = "wb" if isinstance(conteudo, bytes) else "w"
    with open(caminho, modo, encoding=None if isinstance(conteudo, bytes) else "utf-8") as f:
        f.write(conteudo)
    return caminho


@router.post("/sefaz/{empresa_id}")
def disparar_coleta_sefaz(
    empresa_id: str,
    background_tasks: BackgroundTasks,
    ambiente: str = "1",
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


@router.post("/tiny/{empresa_id}")
def disparar_coleta_tiny(
    empresa_id: str,
    background_tasks: BackgroundTasks,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    db: Session = Depends(get_db),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    if not empresa.tiny_token:
        raise HTTPException(status_code=400, detail="Token Tiny não configurado para esta empresa")

    dt_ini = data_inicial or date.today().replace(day=1).strftime("%d/%m/%Y")
    dt_fim = data_final or date.today().strftime("%d/%m/%Y")

    def _coleta():
        db2 = SessionLocal()
        try:
            emp = db2.query(Empresa).filter(Empresa.id == empresa_id).first()
            _coletar_tiny(db2, emp, dt_ini, dt_fim)
        finally:
            db2.close()

    background_tasks.add_task(_coleta)
    return {"ok": True, "message": f"Coleta Tiny iniciada para {empresa.razao_social}"}


@router.post("/uno")
def disparar_coleta_uno(
    background_tasks: BackgroundTasks,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not settings.UNO_TOKEN:
        raise HTTPException(status_code=400, detail="Token UNO não configurado no servidor")

    dt_ini = data_inicial or date.today().replace(day=1).strftime("%d/%m/%Y")
    dt_fim = data_final or date.today().strftime("%d/%m/%Y")

    def _coleta():
        db2 = SessionLocal()
        try:
            _coletar_uno(db2, dt_ini, dt_fim)
        finally:
            db2.close()

    background_tasks.add_task(_coleta)
    return {"ok": True, "message": "Coleta UNO iniciada"}


def _coletar_tiny(db: Session, empresa: Empresa, dt_ini: str, dt_fim: str):
    logger.info(f"Iniciando coleta Tiny para {empresa.razao_social} ({dt_ini} a {dt_fim})")
    pagina = 1
    novos = 0
    while True:
        resultado = tiny_service.listar_nfe_emitidas(
            token=empresa.tiny_token,
            situacao="A",
            data_inicial=dt_ini,
            data_final=dt_fim,
            pagina=pagina,
        )
        itens = resultado.get("itens", [])
        if not itens:
            break

        for item in itens:
            id_nota = str(item.get("id") or "")
            chave = str(item.get("chave_acesso") or "")
            if not chave or len(chave) != 44:
                continue
            if db.query(Documento).filter(Documento.chave_acesso == chave).first():
                continue

            xml = tiny_service.obter_xml_nfe(empresa.tiny_token, id_nota)
            xml_path = None
            if xml:
                pasta = os.path.join(settings.STORAGE_PATH, "xml", empresa.cnpj)
                xml_path = _salvar_arquivo(xml, pasta, f"{chave}.xml")

            danfe = tiny_service.obter_danfe(empresa.tiny_token, id_nota)
            danfe_path = None
            if danfe:
                pasta = os.path.join(settings.STORAGE_PATH, "danfe", empresa.cnpj)
                danfe_path = _salvar_arquivo(danfe, pasta, f"{chave}.pdf")

            dt_emissao = None
            try:
                dt_str = item.get("data_emissao") or ""
                if dt_str:
                    dt_emissao = datetime.strptime(dt_str, "%d/%m/%Y")
            except Exception:
                pass

            cliente = item.get("cliente") or {}
            doc = Documento(
                empresa_id=empresa.id,
                chave_acesso=chave,
                tipo="emitida",
                fonte="tiny",
                cnpj_emitente=empresa.cnpj,
                razao_emitente=empresa.razao_social,
                cnpj_destinatario=str(cliente.get("cpf_cnpj") or "").replace(".", "").replace("/", "").replace("-", ""),
                razao_destinatario=str(cliente.get("nome") or item.get("nome") or ""),
                numero_nota=str(item.get("numero") or ""),
                serie=str(item.get("serie") or ""),
                data_emissao=dt_emissao,
                valor_total=float(item.get("valor_total") or 0),
                xml_path=xml_path,
                danfe_path=danfe_path,
                status="Autorizada",
            )
            db.add(doc)
            novos += 1

        paginas = resultado.get("paginas", 1)
        if pagina >= paginas:
            break
        pagina += 1

    db.commit()
    logger.info(f"Coleta Tiny {empresa.razao_social}: {novos} novas NF-e")


def _coletar_uno(db: Session, dt_ini: str, dt_fim: str):
    logger.info(f"Iniciando coleta UNO ({dt_ini} a {dt_fim})")
    empresas = db.query(Empresa).filter(Empresa.ativa == True).all()
    notas = uno_service.listar_nfe_emitidas(dt_inicio=dt_ini, dt_fim=dt_fim)
    novos = 0

    for item in notas:
        chave = str(item.get("chaveNfe") or "")
        if not chave or len(chave) != 44:
            continue
        if db.query(Documento).filter(Documento.chave_acesso == chave).first():
            continue

        cnpj_emit = chave[6:20]
        empresa = next((e for e in empresas if e.cnpj == cnpj_emit), None)
        if not empresa:
            continue

        xml_url = item.get("xml") or ""
        xml_path = None
        if xml_url:
            xml = uno_service.baixar_xml(xml_url)
            if xml:
                pasta = os.path.join(settings.STORAGE_PATH, "xml", empresa.cnpj)
                xml_path = _salvar_arquivo(xml, pasta, f"{chave}.xml")

        pdf_url = item.get("pdf") or ""
        danfe_path = None
        if pdf_url:
            pdf = uno_service.baixar_pdf(pdf_url)
            if pdf:
                pasta = os.path.join(settings.STORAGE_PATH, "danfe", empresa.cnpj)
                danfe_path = _salvar_arquivo(pdf, pasta, f"{chave}.pdf")

        dt_emissao = None
        try:
            dt_str = str(item.get("dtEmissao") or "")
            if dt_str:
                dt_emissao = datetime.strptime(dt_str, "%d/%m/%Y")
        except Exception:
            pass

        doc = Documento(
            empresa_id=empresa.id,
            chave_acesso=chave,
            tipo="emitida",
            fonte="uno",
            cnpj_emitente=cnpj_emit,
            razao_emitente=empresa.razao_social,
            numero_nota=str(item.get("nrNotaFiscal") or item.get("codNotaFiscal") or ""),
            serie=str(item.get("serie") or ""),
            data_emissao=dt_emissao,
            valor_total=float(item.get("vlTotalNotaFiscal") or 0),
            xml_path=xml_path,
            danfe_path=danfe_path,
            status="Autorizada",
        )
        db.add(doc)
        novos += 1

    db.commit()
    logger.info(f"Coleta UNO: {novos} novas NF-e")
