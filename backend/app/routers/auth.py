from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, AuditLog
from app.schemas.usuario import LoginRequest, TokenResponse, UsuarioCreate, UsuarioResponse
from app.services.auth_service import (
    hash_senha, verificar_senha, criar_access_token,
    criar_refresh_token, decodificar_token
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == body.email, Usuario.ativo == True).first()
    if not usuario or not verificar_senha(body.senha, usuario.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    access_token = criar_access_token({"sub": usuario.id, "perfil": usuario.perfil})
    refresh_token = criar_refresh_token({"sub": usuario.id})

    db.add(AuditLog(
        user_id=usuario.id, action="login",
        ip=request.client.host if request.client else None,
    ))
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        perfil=usuario.perfil,
        nome=usuario.nome,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    payload = decodificar_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    usuario = db.query(Usuario).filter(Usuario.id == payload["sub"], Usuario.ativo == True).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    access_token = criar_access_token({"sub": usuario.id, "perfil": usuario.perfil})
    new_refresh = criar_refresh_token({"sub": usuario.id})
    return TokenResponse(access_token=access_token, refresh_token=new_refresh, perfil=usuario.perfil, nome=usuario.nome)


@router.post("/usuarios", response_model=UsuarioResponse)
def criar_usuario(body: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == body.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    usuario = Usuario(
        nome=body.nome,
        email=body.email,
        departamento=body.departamento,
        senha_hash=hash_senha(body.senha),
        perfil=body.perfil,
        empresa_id=body.empresa_id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
