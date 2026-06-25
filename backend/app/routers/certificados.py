from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from datetime import datetime
import shutil, os
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.backends import default_backend
from app.database import get_db
from app.models import Certificado, Empresa
from app.schemas.certificado import CertificadoResponse
from app.services.auth_service import cifrar_senha_pfx, decifrar_senha_pfx
from app.config import settings

router = APIRouter(prefix="/certificados", tags=["certificados"])


@router.get("", response_model=List[CertificadoResponse])
def listar_certificados(empresa_id: str = None, db: Session = Depends(get_db)):
    q = db.query(Certificado)
    if empresa_id:
        q = q.filter(Certificado.empresa_id == empresa_id)
    return q.filter(Certificado.ativo == True).order_by(Certificado.nome).all()


@router.post("", response_model=CertificadoResponse)
async def upload_certificado(
    empresa_id: str = Form(...),
    nome: str = Form(...),
    senha: str = Form(...),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    # Validar certificado antes de salvar
    pfx_bytes = await arquivo.read()
    try:
        chave, cert, _ = load_key_and_certificates(pfx_bytes, senha.encode(), default_backend())
        validade = cert.not_valid_after_utc.replace(tzinfo=None)
    except Exception:
        raise HTTPException(status_code=400, detail="Certificado inválido ou senha incorreta")

    # Salvar .pfx fora do webroot
    certs_dir = Path(settings.CERTS_PATH) / empresa.cnpj
    certs_dir.mkdir(parents=True, exist_ok=True)
    pfx_path = certs_dir / arquivo.filename
    pfx_path.write_bytes(pfx_bytes)

    senha_cifrada = cifrar_senha_pfx(senha)

    cert_db = Certificado(
        empresa_id=empresa_id,
        nome=nome,
        pfx_path=str(pfx_path),
        senha_cifrada=senha_cifrada,
        validade=validade,
    )
    db.add(cert_db)
    db.commit()
    db.refresh(cert_db)
    return cert_db


@router.delete("/{cert_id}")
def desativar_certificado(cert_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificado).filter(Certificado.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")
    cert.ativo = False
    db.commit()
    return {"ok": True}
