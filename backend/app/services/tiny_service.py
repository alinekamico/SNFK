import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

TINY_BASE_URL = "https://api.tiny.com.br/public-api/v3"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def listar_nfe_emitidas(
    token: str,
    situacao: Optional[str] = None,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    pagina: int = 1,
    limite: int = 100,
) -> Dict:
    """
    Lista NF-e emitidas no Tiny v3.
    situacao: A=Autorizada, C=Cancelada, E=Em digitação, etc.
    data_inicial/data_final: dd/MM/yyyy
    """
    try:
        params = {"pagina": pagina, "limite": limite}
        if situacao:
            params["situacao"] = situacao
        if data_inicial:
            params["dataInicial"] = data_inicial
        if data_final:
            params["dataFinal"] = data_final

        resp = requests.get(
            f"{TINY_BASE_URL}/nota-fiscal",
            headers=_headers(token),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro Tiny v3 listar NF-e: {e}")
        return {"itens": [], "paginacao": {}}


def obter_nfe(token: str, id_nota: str) -> Optional[Dict]:
    """Obtém dados de uma NF-e específica no Tiny v3."""
    try:
        resp = requests.get(
            f"{TINY_BASE_URL}/nota-fiscal/{id_nota}",
            headers=_headers(token),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro Tiny v3 obter NF-e {id_nota}: {e}")
        return None


def obter_xml_nfe(token: str, id_nota: str) -> Optional[str]:
    """Obtém XML de uma NF-e no Tiny v3."""
    try:
        resp = requests.get(
            f"{TINY_BASE_URL}/nota-fiscal/{id_nota}/xml",
            headers=_headers(token),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("xml") or data.get("xmlNfe")
    except Exception as e:
        logger.error(f"Erro Tiny v3 obter XML {id_nota}: {e}")
        return None


def obter_danfe(token: str, id_nota: str) -> Optional[bytes]:
    """Obtém PDF do DANFe no Tiny v3."""
    try:
        resp = requests.get(
            f"{TINY_BASE_URL}/nota-fiscal/{id_nota}/danfe",
            headers=_headers(token),
            timeout=60,
        )
        resp.raise_for_status()
        if "pdf" in resp.headers.get("content-type", ""):
            return resp.content
        # Tiny v3 pode retornar JSON com URL
        data = resp.json()
        if data.get("linkDanfe"):
            r2 = requests.get(data["linkDanfe"], timeout=60)
            return r2.content
        return None
    except Exception as e:
        logger.error(f"Erro Tiny v3 obter DANFe {id_nota}: {e}")
        return None
