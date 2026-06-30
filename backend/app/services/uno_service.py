import requests
import logging
from typing import Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Mapeamento cod_empresa UNO -> CNPJ emitente
UNO_EMPRESA_CNPJ = {
    2:  "30917874000179",  # NEXXA
    4:  "39362018000179",  # ENERGY
    5:  "39696052000180",  # HAIRPRO
    10: "36016032000122",  # 3MKO
}

SITUACAO_AUTORIZADA = 80


def _supabase_headers() -> dict:
    return {
        "apikey": settings.UNO_SUPABASE_KEY,
        "Authorization": f"Bearer {settings.UNO_SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept-Profile": "unia",
    }


def _supabase_url(table: str) -> str:
    return f"{settings.UNO_SUPABASE_URL}/rest/v1/{table}"


def listar_nfe_emitidas(
    dt_inicio: str,
    dt_fim: str,
    cnpj: Optional[str] = None,
    page: int = 0,
    size: int = 1000,
) -> List[Dict]:
    """Lista NF-e autorizadas do UNO via Supabase REST. dt_inicio/dt_fim: dd/MM/yyyy"""
    try:
        # Converte dd/MM/yyyy para yyyy-MM-dd
        from datetime import datetime
        dt_ini_iso = datetime.strptime(dt_inicio, "%d/%m/%Y").strftime("%Y-%m-%d")
        dt_fim_iso = datetime.strptime(dt_fim, "%d/%m/%Y").strftime("%Y-%m-%d")

        params = {
            "select": "cod_empresa,cod_nota_fiscal,nr_nota_fiscal,serie,situacao,dt_emissao,cnpj,razao_social,vl_total_nota_fiscal,chave_nfe",
            "situacao": f"eq.{SITUACAO_AUTORIZADA}",
            "dt_emissao": f"gte.{dt_ini_iso}",
            "dt_emissao": f"lte.{dt_fim_iso}",
            "chave_nfe": "not.is.null",
            "order": "dt_emissao.asc",
            "offset": page * size,
            "limit": size,
        }

        # Supabase não aceita dois params com mesmo nome — usa range header
        headers = _supabase_headers()
        headers["Range"] = f"{page * size}-{page * size + size - 1}"

        resp = requests.get(
            f"{settings.UNO_SUPABASE_URL}/rest/v1/vd_nota_fiscal",
            headers=headers,
            params={
                "select": "cod_empresa,cod_nota_fiscal,nr_nota_fiscal,serie,situacao,dt_emissao,cnpj,razao_social,vl_total_nota_fiscal,chave_nfe",
                "situacao": f"eq.{SITUACAO_AUTORIZADA}",
                "dt_emissao": f"gte.{dt_ini_iso}",
                "chave_nfe": "not.is.null",
                "order": "dt_emissao.asc",
                "limit": size,
                "offset": page * size,
            },
            timeout=30,
        )
        resp.raise_for_status()
        notas = resp.json() if resp.text else []

        # Filtra até dt_fim
        from datetime import date
        dt_fim_date = datetime.strptime(dt_fim, "%d/%m/%Y").date()
        resultado = []
        for n in notas:
            dt = n.get("dt_emissao", "")
            if dt and dt > dt_fim_iso:
                continue
            resultado.append(n)
        return resultado
    except Exception as e:
        logger.error(f"Erro UNO Supabase listar NF-e: {e}")
        return []


def baixar_xml(url_xml: str) -> Optional[str]:
    """Baixa XML via URL (mantido por compatibilidade)."""
    try:
        resp = requests.get(url_xml, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"Erro UNO baixar XML {url_xml}: {e}")
        return None


def baixar_pdf(url_pdf: str) -> Optional[bytes]:
    """Baixa PDF via URL (mantido por compatibilidade)."""
    try:
        resp = requests.get(url_pdf, timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"Erro UNO baixar PDF {url_pdf}: {e}")
        return None
