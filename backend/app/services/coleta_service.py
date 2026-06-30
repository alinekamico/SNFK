import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Empresa, Certificado, Documento, ColetaCursor, AuditLog
from app.models.documento import TipoDocumento, FonteDocumento
from app.services import sefaz_service, danfe_service

logger = logging.getLogger(__name__)


def executar_coleta_todas_empresas(session_factory):
    from app.routers.coleta import _coletar_tiny, _coletar_uno
    from datetime import date

    db: Session = session_factory()
    try:
        empresas = db.query(Empresa).filter(Empresa.ativa == True).all()
        dt_ini = "01/01/2019"
        dt_fim = date.today().strftime("%d/%m/%Y")

        for empresa in empresas:
            # SEFAZ
            try:
                coletar_sefaz(db, empresa)
            except Exception as e:
                logger.error(f"Erro coleta SEFAZ empresa {empresa.cnpj}: {e}")

            # Tiny
            if empresa.tiny_token:
                try:
                    _coletar_tiny(db, empresa, dt_ini, dt_fim)
                except Exception as e:
                    logger.error(f"Erro coleta Tiny empresa {empresa.cnpj}: {e}")

        # UNO (global)
        try:
            _coletar_uno(db, dt_ini, dt_fim)
        except Exception as e:
            logger.error(f"Erro coleta UNO: {e}")
    finally:
        db.close()


def coletar_sefaz(db: Session, empresa: Empresa, ambiente: str = "1"):
    cert = db.query(Certificado).filter(
        Certificado.empresa_id == empresa.id,
        Certificado.ativo == True,
    ).first()
    if not cert:
        logger.warning(f"Empresa {empresa.cnpj} sem certificado ativo — pulando coleta SEFAZ")
        return

    cursor = db.query(ColetaCursor).filter(
        ColetaCursor.empresa_id == empresa.id,
        ColetaCursor.fonte == "sefaz",
    ).first()
    if not cursor:
        cursor = ColetaCursor(empresa_id=empresa.id, fonte="sefaz", ultimo_nsu="0")
        db.add(cursor)
        db.commit()

    tem_mais = True
    total_novos = 0

    while tem_mais:
        resultado = sefaz_service.consultar_nfe_distribuicao(
            cnpj=empresa.cnpj,
            pfx_path=cert.pfx_path,
            senha_cifrada=cert.senha_cifrada,
            ultimo_nsu=cursor.ultimo_nsu,
            ambiente=ambiente,
        )

        if resultado["status"] not in ("138", "137"):
            logger.warning(f"SEFAZ retornou status {resultado['status']}: {resultado.get('motivo')}")
            break

        for doc in resultado["documentos"]:
            if "procNFe" not in doc.get("schema", "") and "resNFe" not in doc.get("schema", ""):
                continue
            xml_str = sefaz_service.descompactar_xml(doc["xml_gz_b64"])
            if not xml_str:
                continue
            meta = sefaz_service.extrair_metadados_nfe(xml_str)
            if not meta.get("chave_acesso"):
                continue

            # Deduplicação por empresa + chave de acesso
            existente = db.query(Documento).filter(
                Documento.empresa_id == empresa.id,
                Documento.chave_acesso == meta["chave_acesso"],
            ).first()
            if existente:
                continue

            # Salvar XML
            xml_dir = Path(settings.STORAGE_PATH) / "xml" / empresa.cnpj
            xml_dir.mkdir(parents=True, exist_ok=True)
            xml_path = xml_dir / f"{meta['chave_acesso']}.xml"
            xml_path.write_text(xml_str, encoding="utf-8")

            # Gerar DANFe
            danfe_dir = Path(settings.STORAGE_PATH) / "danfe" / empresa.cnpj
            danfe_dir.mkdir(parents=True, exist_ok=True)
            danfe_path = danfe_dir / f"{meta['chave_acesso']}.pdf"
            danfe_gerado = danfe_service.gerar_danfe_from_xml(xml_str, str(danfe_path))

            doc_db = Documento(
                empresa_id=empresa.id,
                chave_acesso=meta["chave_acesso"],
                tipo=TipoDocumento.recebida,
                fonte=FonteDocumento.sefaz,
                cnpj_emitente=meta.get("cnpj_emitente"),
                razao_emitente=meta.get("razao_emitente"),
                cnpj_destinatario=meta.get("cnpj_destinatario"),
                razao_destinatario=meta.get("razao_destinatario"),
                numero_nota=meta.get("numero_nota"),
                serie=meta.get("serie"),
                data_emissao=_parse_datetime(meta.get("data_emissao")),
                valor_total=float(meta.get("valor_total") or 0),
                xml_path=str(xml_path),
                danfe_path=str(danfe_path) if danfe_gerado else None,
                nsu=doc["nsu"],
            )
            db.add(doc_db)
            total_novos += 1

        cursor.ultimo_nsu = resultado["ultimo_nsu"]
        cursor.ultima_coleta = datetime.utcnow()
        cursor.total_coletados += total_novos
        db.commit()

        tem_mais = resultado.get("tem_mais", False)

    log = AuditLog(
        action="coleta_sefaz",
        entity="empresa",
        entity_id=empresa.id,
        details=f"CNPJ {empresa.cnpj} — {total_novos} novos documentos coletados",
    )
    db.add(log)
    db.commit()
    logger.info(f"Coleta SEFAZ empresa {empresa.cnpj}: {total_novos} novos documentos")


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt[:len(s[:19])])
        except ValueError:
            continue
    return None
