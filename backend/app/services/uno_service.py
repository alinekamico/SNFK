import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def listar_nfe_emitidas(base_url: str, token: str, data_inicio: str, data_fim: str) -> Dict:
    """Lista NF-e emitidas no UNO ERP."""
    try:
        resp = requests.get(
            f"{base_url}/api/nfe",
            headers={"Authorization": f"Bearer {token}"},
            params={"data_inicio": data_inicio, "data_fim": data_fim},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro UNO listar NF-e: {e}")
        return {"data": []}


def obter_xml_nfe(base_url: str, token: str, id_nota: str) -> Optional[str]:
    """Obtém XML de NF-e no UNO ERP."""
    try:
        resp = requests.get(
            f"{base_url}/api/nfe/{id_nota}/xml",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"Erro UNO obter XML {id_nota}: {e}")
        return None


def obter_danfe(base_url: str, token: str, id_nota: str) -> Optional[bytes]:
    """Obtém DANFe PDF no UNO ERP."""
    try:
        resp = requests.get(
            f"{base_url}/api/nfe/{id_nota}/danfe",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"Erro UNO obter DANFe {id_nota}: {e}")
        return None
