import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
TINY_BASE_URL = "https://api.tiny.com.br/api2"


def listar_nfe_emitidas(token: str, data_inicio: str, data_fim: str, pagina: int = 1) -> Dict:
    """Lista NF-e emitidas no Tiny ERP."""
    try:
        resp = requests.get(
            f"{TINY_BASE_URL}/notas.fiscais.pesquisa.php",
            params={
                "token": token,
                "formato": "json",
                "dataInicial": data_inicio,
                "dataFinal": data_fim,
                "pagina": pagina,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("retorno", {}).get("status") == "OK":
            return data["retorno"]
        return {"notas_fiscais": [], "numero_paginas": 0}
    except Exception as e:
        logger.error(f"Erro Tiny listar NF-e: {e}")
        return {"notas_fiscais": [], "numero_paginas": 0}


def obter_xml_nfe(token: str, id_nota: str) -> Optional[str]:
    """Obtém XML de uma NF-e específica no Tiny."""
    try:
        resp = requests.get(
            f"{TINY_BASE_URL}/nota.fiscal.obter.xml.php",
            params={"token": token, "id": id_nota, "formato": "json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("retorno", {}).get("xml_nfe")
    except Exception as e:
        logger.error(f"Erro Tiny obter XML {id_nota}: {e}")
        return None


def obter_danfe(token: str, id_nota: str) -> Optional[bytes]:
    """Obtém PDF do DANFe de uma NF-e no Tiny."""
    try:
        resp = requests.get(
            f"{TINY_BASE_URL}/nota.fiscal.obter.danfe.php",
            params={"token": token, "id": id_nota},
            timeout=60,
        )
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/pdf"):
            return resp.content
        return None
    except Exception as e:
        logger.error(f"Erro Tiny obter DANFe {id_nota}: {e}")
        return None
