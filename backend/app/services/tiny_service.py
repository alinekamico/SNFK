import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

TINY_BASE_URL = "https://api.tiny.com.br/api2"


def listar_nfe_emitidas(
    token: str,
    situacao: Optional[str] = None,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    pagina: int = 1,
    limite: int = 100,
) -> Dict:
    """Lista NF-e no Tiny API v2. situacao: A=Autorizada, C=Cancelada"""
    try:
        params = {"token": token, "formato": "JSON", "pagina": pagina}
        if situacao:
            params["situacao"] = situacao
        if data_inicial:
            params["dataInicial"] = data_inicial
        if data_final:
            params["dataFinal"] = data_final

        resp = requests.get(
            f"{TINY_BASE_URL}/notas.fiscais.pesquisa.php",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        retorno = data.get("retorno", {})
        if retorno.get("status") != "OK":
            logger.warning(f"Tiny v2 status não OK: {retorno.get('erros')}")
            return {"itens": [], "paginas": 1}

        notas = retorno.get("notas_fiscais", [])
        itens = [n["nota_fiscal"] for n in notas if "nota_fiscal" in n]
        return {"itens": itens, "paginas": int(retorno.get("numero_paginas", 1))}
    except Exception as e:
        logger.error(f"Erro Tiny v2 listar NF-e: {e}")
        return {"itens": [], "paginas": 1}


def obter_xml_nfe(token: str, id_nota: str) -> Optional[str]:
    """Obtém XML de uma NF-e no Tiny v2."""
    try:
        params = {"token": token, "id": id_nota}
        resp = requests.get(
            f"{TINY_BASE_URL}/nota.fiscal.obter.xml.php",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        # Tiny v2 retorna XML direto ou JSON com xml embutido
        content = resp.text.strip()
        if content.startswith("<?xml") or content.startswith("<"):
            return content
        # Tenta JSON
        try:
            data = resp.json()
            retorno = data.get("retorno", {})
            return retorno.get("xml_nfe") or retorno.get("xml")
        except Exception:
            return None
    except Exception as e:
        logger.error(f"Erro Tiny v2 obter XML {id_nota}: {e}")
        return None


def obter_danfe(token: str, id_nota: str) -> Optional[bytes]:
    """Obtém PDF do DANFe no Tiny v2."""
    try:
        # Tiny v2: primeiro obtém a nota para pegar o link do DANFe
        params = {"token": token, "id": id_nota, "formato": "JSON"}
        resp = requests.get(
            f"{TINY_BASE_URL}/nota.fiscal.obter.php",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        retorno = data.get("retorno", {})
        nota = retorno.get("nota_fiscal", {})
        link = nota.get("link_danfe") or nota.get("linkDanfe") or nota.get("url_danfe")
        if not link:
            return None
        r2 = requests.get(link, timeout=60)
        r2.raise_for_status()
        if b"%PDF" in r2.content[:10]:
            return r2.content
        return None
    except Exception as e:
        logger.error(f"Erro Tiny v2 obter DANFe {id_nota}: {e}")
        return None
