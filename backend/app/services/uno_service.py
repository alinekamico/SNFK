import requests
import logging
from typing import Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

SITUACAO_AUTORIZADA = 80


def _supabase_headers() -> dict:
    return {
        "apikey": settings.UNO_SUPABASE_KEY,
        "Authorization": f"Bearer {settings.UNO_SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def listar_nfe_emitidas(
    dt_inicio: str,
    dt_fim: str,
    cnpj: Optional[str] = None,
    page: int = 0,
    size: int = 1000,
) -> List[Dict]:
    """Lista NF-e autorizadas do UNO via Supabase REST. dt_inicio/dt_fim: dd/MM/yyyy"""
    try:
        from datetime import datetime
        dt_ini_iso = datetime.strptime(dt_inicio, "%d/%m/%Y").strftime("%Y-%m-%d")
        dt_fim_iso = datetime.strptime(dt_fim, "%d/%m/%Y").strftime("%Y-%m-%d")

        url = (
            f"{settings.UNO_SUPABASE_URL}/rest/v1/vd_nota_fiscal_snfk"
            f"?select=cod_empresa,nr_nota_fiscal,serie,situacao,dt_emissao,cnpj,razao_social,vl_total_nota_fiscal,chave_nfe"
            f"&situacao=eq.{SITUACAO_AUTORIZADA}"
            f"&dt_emissao=gte.{dt_ini_iso}"
            f"&dt_emissao=lte.{dt_fim_iso}"
            f"&limit={size}&offset={page * size}"
        )
        resp = requests.get(url, headers=_supabase_headers(), timeout=60)
        resp.raise_for_status()
        return resp.json() if resp.text else []
    except Exception as e:
        logger.error(f"Erro UNO Supabase listar NF-e: {e}")
        return []


def listar_nfe_todas_paginas(dt_inicio: str, dt_fim: str, size: int = 1000) -> List[Dict]:
    """Busca todas as páginas de NF-e no período."""
    todas = []
    page = 0
    while True:
        pagina = listar_nfe_emitidas(dt_inicio, dt_fim, page=page, size=size)
        if not pagina:
            break
        todas.extend(pagina)
        logger.info(f"UNO paginação: página {page + 1}, {len(pagina)} registros, total {len(todas)}")
        if len(pagina) < size:
            break
        page += 1
    return todas


def baixar_xml(url_xml: str) -> Optional[str]:
    try:
        resp = requests.get(url_xml, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"Erro UNO baixar XML {url_xml}: {e}")
        return None


def baixar_pdf(url_pdf: str) -> Optional[bytes]:
    try:
        resp = requests.get(url_pdf, timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"Erro UNO baixar PDF {url_pdf}: {e}")
        return None
