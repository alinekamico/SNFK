import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def gerar_danfe_from_xml(xml_str: str, output_path: str) -> bool:
    """
    Gera PDF do DANFe a partir do XML da NF-e.
    Usa nfelib + reportlab ou, se disponível, brazilfiscalreport.
    """
    try:
        from brazilfiscalreport.danfe import Danfe
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w", encoding="utf-8") as f:
            f.write(xml_str)
            tmp_xml = f.name
        try:
            danfe = Danfe(xml=tmp_xml)
            danfe.output(output_path)
            return True
        finally:
            os.unlink(tmp_xml)
    except ImportError:
        logger.warning("brazilfiscalreport não instalado — DANFe não gerado automaticamente")
        return False
    except Exception as e:
        logger.error(f"Erro ao gerar DANFe: {e}")
        return False
