from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import engine, SessionLocal
from app.models import *  # noqa: F401,F403 — importa todos os models para o Base
from app.database import Base
from app.routers import auth, empresas, certificados, documentos, coleta
from app.services.scheduler import iniciar_scheduler, parar_scheduler
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Criar tabelas
Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="SNFK — Sistema de Notas Fiscais KAMI CO.",
    description="Sistema de gestão de documentos fiscais (NF-e) — KAMI CO.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = [o.strip() for o in (
    __import__("os").getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(certificados.router)
app.include_router(documentos.router)
app.include_router(coleta.router)


@app.on_event("startup")
def startup():
    iniciar_scheduler(SessionLocal)


@app.on_event("shutdown")
def shutdown():
    parar_scheduler()


@app.get("/health")
def health():
    return {"status": "ok", "service": "snfk"}
