import os
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict
from lxml import etree
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from app.config import settings
from app.services.auth_service import decifrar_senha_pfx

logger = logging.getLogger(__name__)

SEFAZ_URL_PROD = "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
SEFAZ_URL_HOM = "https://hom.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"

# URLs NFeConsultaProtocolo4 por cUF (primeiros 2 dígitos da chave de acesso)
_SVRS = "https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx"
CONSULTA_URLS_PROD = {
    "11": "https://nfe.sefin.ro.gov.br/nfe/NFeConsulta4",
    "13": "https://nfe.sefaz.am.gov.br/services/NfeConsulta4",
    "15": "https://nfe.sefa.pa.gov.br/nfe/NFeConsulta4",
    "21": "https://nfe.sefaz.ma.gov.br/nfe/NFeConsulta4",
    "31": "https://nfe.fazenda.mg.gov.br/nfe2/services/NFeConsulta4",
    "35": "https://nfe.fazenda.sp.gov.br/ws/nfeconsulta4.asmx",
    "41": "https://nfe.fazenda.pr.gov.br/nfe/NFeConsulta4",
    "51": "https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeConsulta4",
}
CONSULTA_URLS_HOM = {
    "35": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsulta4.asmx",
    "31": "https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeConsulta4",
}

SOAP_CONSULTA = """<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Header>
    <nfeCabecMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
      <cUF>{cuf}</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap12:Header>
  <soap12:Body>
    <nfeConsultaNF xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
      <nfeDadosMsg>
        <consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
          <tpAmb>{ambiente}</tpAmb>
          <xServ>CONSULTAR</xServ>
          <chNFe>{chave}</chNFe>
        </consSitNFe>
      </nfeDadosMsg>
    </nfeConsultaNF>
  </soap12:Body>
</soap12:Envelope>"""

SOAP_ENVELOPE = """<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
      <nfeDadosMsg>
        <distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">
          <tpAmb>{ambiente}</tpAmb>
          <cUFAutor>35</cUFAutor>
          <CNPJ>{cnpj}</CNPJ>
          <distNSU>
            <ultNSU>{ultimo_nsu}</ultNSU>
          </distNSU>
        </distDFeInt>
      </nfeDadosMsg>
    </nfeDistDFeInteresse>
  </soap12:Body>
</soap12:Envelope>"""


def carregar_certificado(pfx_path: str, senha_cifrada: str):
    """Carrega certificado .pfx e retorna (cert_pem, key_pem)."""
    senha = decifrar_senha_pfx(senha_cifrada)
    with open(pfx_path, "rb") as f:
        pfx_data = f.read()
    chave, cert, extras = load_key_and_certificates(
        pfx_data, senha.encode(), default_backend()
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = chave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def consultar_nfe_distribuicao(
    cnpj: str,
    pfx_path: str,
    senha_cifrada: str,
    ultimo_nsu: str = "0",
    ambiente: str = "1",  # 1=produção, 2=homologação
    max_tentativas: int = 3,
) -> Dict:
    """
    Consulta NFeDistribuicaoDFe e retorna documentos recebidos.
    Implementa retry com backoff exponencial (timeouts SEFAZ são comuns).
    """
    import requests
    import tempfile

    cert_pem, key_pem = carregar_certificado(pfx_path, senha_cifrada)
    url = SEFAZ_URL_HOM if ambiente == "2" else SEFAZ_URL_PROD

    soap_body = SOAP_ENVELOPE.format(
        ambiente=ambiente,
        cnpj=re.sub(r"\D", "", cnpj),
        ultimo_nsu=ultimo_nsu.zfill(15),
    )

    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "SOAPAction": "",
    }

    # Escrita temporária dos arquivos de certificado para requests
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as cert_file:
        cert_file.write(cert_pem)
        cert_tmp = cert_file.name

    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as key_file:
        key_file.write(key_pem)
        key_tmp = key_file.name

    try:
        for tentativa in range(1, max_tentativas + 1):
            try:
                import certifi, ssl, os
                # Usa bundle do sistema que inclui ICP-Brasil após update-ca-certificates
                ca_bundle = "/etc/ssl/certs/ca-certificates.crt"
                if not os.path.exists(ca_bundle):
                    ca_bundle = certifi.where()
                resp = requests.post(
                    url,
                    data=soap_body.encode("utf-8"),
                    headers=headers,
                    cert=(cert_tmp, key_tmp),
                    timeout=60,
                    verify=ca_bundle,
                )
                resp.raise_for_status()
                return _parsear_resposta(resp.text)
            except requests.Timeout:
                wait = 2 ** tentativa
                logger.warning(f"Timeout SEFAZ tentativa {tentativa}/{max_tentativas}. Aguardando {wait}s.")
                if tentativa < max_tentativas:
                    time.sleep(wait)
                else:
                    raise
    finally:
        os.unlink(cert_tmp)
        os.unlink(key_tmp)


def _parsear_resposta(xml_str: str) -> Dict:
    """Parseia resposta SOAP da SEFAZ e extrai lista de documentos."""
    root = etree.fromstring(xml_str.encode("utf-8"))
    ns = {
        "soap": "http://www.w3.org/2003/05/soap-envelope",
        "nfe": "http://www.portalfiscal.inf.br/nfe",
    }

    ret_dist = root.find(".//nfe:retDistDFeInt", ns)
    if ret_dist is None:
        return {"status": "erro", "documentos": [], "ultimo_nsu": "0"}

    c_stat = ret_dist.findtext("nfe:cStat", namespaces=ns)
    x_motivo = ret_dist.findtext("nfe:xMotivo", namespaces=ns)
    ultimo_nsu = ret_dist.findtext("nfe:ultNSU", namespaces=ns) or "0"
    max_nsu = ret_dist.findtext("nfe:maxNSU", namespaces=ns) or "0"

    documentos = []
    for doc_zip in ret_dist.findall(".//nfe:docZip", ns):
        nsu = doc_zip.get("NSU", "")
        schema = doc_zip.get("schema", "")
        documentos.append({
            "nsu": nsu,
            "schema": schema,
            "xml_gz_b64": doc_zip.text,
        })

    return {
        "status": c_stat,
        "motivo": x_motivo,
        "ultimo_nsu": ultimo_nsu,
        "max_nsu": max_nsu,
        "documentos": documentos,
        "tem_mais": int(max_nsu or 0) > int(ultimo_nsu or 0),
    }


def descompactar_xml(xml_gz_b64: str) -> Optional[str]:
    """Descompacta XML retornado pela SEFAZ (gzip + base64)."""
    import gzip
    import base64
    try:
        compressed = base64.b64decode(xml_gz_b64)
        return gzip.decompress(compressed).decode("utf-8")
    except Exception as e:
        logger.error(f"Erro ao descompactar XML SEFAZ: {e}")
        return None


def extrair_metadados_nfe(xml_str: str) -> Dict:
    """Extrai metadados principais de um XML de NF-e."""
    try:
        root = etree.fromstring(xml_str.encode("utf-8"))
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        ide = root.find(".//nfe:ide", ns)
        emit = root.find(".//nfe:emit", ns)
        dest = root.find(".//nfe:dest", ns)
        total = root.find(".//nfe:ICMSTot", ns)
        inf_nfe = root.find(".//nfe:infNFe", ns)

        return {
            "chave_acesso": inf_nfe.get("Id", "").replace("NFe", "") if inf_nfe is not None else "",
            "numero_nota": ide.findtext("nfe:nNF", namespaces=ns) if ide is not None else "",
            "serie": ide.findtext("nfe:serie", namespaces=ns) if ide is not None else "",
            "data_emissao": ide.findtext("nfe:dhEmi", namespaces=ns) if ide is not None else "",
            "cnpj_emitente": emit.findtext("nfe:CNPJ", namespaces=ns) if emit is not None else "",
            "razao_emitente": emit.findtext("nfe:xNome", namespaces=ns) if emit is not None else "",
            "cnpj_destinatario": (dest.findtext("nfe:CNPJ", namespaces=ns) or dest.findtext("nfe:CPF", namespaces=ns)) if dest is not None else "",
            "razao_destinatario": dest.findtext("nfe:xNome", namespaces=ns) if dest is not None else "",
            "valor_total": total.findtext("nfe:vNF", namespaces=ns) if total is not None else "0",
        }
    except Exception as e:
        logger.error(f"Erro ao extrair metadados NF-e: {e}")
        return {}


def buscar_nfe_por_chave(chave: str, pfx_path: str, senha_cifrada: str, ambiente: str = "1") -> Optional[str]:
    """
    Consulta NFeConsultaProtocolo4 pelo chave de acesso e retorna o XML completo da NF-e.
    Usado para notas UNO que não têm XML armazenado localmente.
    """
    import requests, tempfile

    cuf = chave[:2]
    urls = CONSULTA_URLS_HOM if ambiente == "2" else CONSULTA_URLS_PROD
    url = urls.get(cuf, _SVRS)

    cert_pem, key_pem = carregar_certificado(pfx_path, senha_cifrada)
    soap_body = SOAP_CONSULTA.format(cuf=cuf, ambiente=ambiente, chave=chave)
    headers = {"Content-Type": "application/soap+xml; charset=utf-8", "SOAPAction": ""}

    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as cf:
        cf.write(cert_pem); cert_tmp = cf.name
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as kf:
        kf.write(key_pem); key_tmp = kf.name

    try:
        ca_bundle = "/etc/ssl/certs/ca-certificates.crt"
        if not os.path.exists(ca_bundle):
            import certifi; ca_bundle = certifi.where()
        resp = requests.post(url, data=soap_body.encode("utf-8"), headers=headers,
                             cert=(cert_tmp, key_tmp), timeout=60, verify=ca_bundle)
        resp.raise_for_status()
        root = etree.fromstring(resp.content)
        proc = root.find(".//{http://www.portalfiscal.inf.br/nfe}procNFe")
        if proc is not None:
            return etree.tostring(proc, encoding="unicode")
        nfe_el = root.find(".//{http://www.portalfiscal.inf.br/nfe}NFe")
        if nfe_el is not None:
            return etree.tostring(nfe_el, encoding="unicode")
        logger.warning(f"NFeConsultaProtocolo: sem XML para chave {chave}. Body: {resp.text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Erro NFeConsultaProtocolo chave {chave}: {e}")
        return None
    finally:
        os.unlink(cert_tmp)
        os.unlink(key_tmp)


import re
