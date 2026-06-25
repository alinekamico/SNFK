import requests
import logging
from typing import Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.UNO_TOKEN}"}


def _base() -> str:
    return settings.UNO_BASE_URL.rstrip("/")


def listar_nfe_emitidas(
    dt_inicio: str,
    dt_fim: str,
    cnpj: Optional[str] = None,
    page: int = 0,
    size: int = 100,
) -> List[Dict]:
    """Lista NF-e de venda no UNO. dt_inicio/dt_fim: dd/MM/yyyy"""
    try:
        params = {
            "dtEmissaoInicial": dt_inicio,
            "dtEmissaoFinal": dt_fim,
            "page": page,
            "size": size,
        }
        if cnpj:
            params["cnpj"] = cnpj

        resp = requests.get(
            f"{_base()}/nota-fiscal-venda",
            headers=_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json() if resp.text else []
    except Exception as e:
        logger.error(f"Erro UNO listar NF-e: {e}")
        return []


def obter_nfe(cod_nota: int) -> Optional[Dict]:
    """Obtém detalhes de uma NF-e específica incluindo URLs de XML e PDF."""
    try:
        resp = requests.get(
            f"{_base()}/nota-fiscal-venda/{cod_nota}",
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro UNO obter NF-e {cod_nota}: {e}")
        return None


def baixar_xml(url_xml: str) -> Optional[str]:
    """Baixa o XML da NF-e a partir da URL retornada pelo UNO."""
    try:
        resp = requests.get(url_xml, headers=_headers(), timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"Erro UNO baixar XML {url_xml}: {e}")
        return None


def baixar_pdf(url_pdf: str) -> Optional[bytes]:
    """Baixa o PDF do DANFe a partir da URL retornada pelo UNO."""
    try:
        resp = requests.get(url_pdf, headers=_headers(), timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"Erro UNO baixar PDF {url_pdf}: {e}")
        return None
