from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/fiscal_nfe"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FERNET_KEY: str = ""  # gerado com Fernet.generate_key() - para cifrar senha do .pfx
    STORAGE_PATH: str = "./storage"
    CERTS_PATH: str = "./certs"
    COLLECTION_INTERVAL_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "noreply@kamico.com.br"
    FRONTEND_URL: str = "http://54.173.44.220:8080"
    UNO_BASE_URL: str = "https://kami.omegasoft.net.br/Kami-api/predict/v1"
    UNO_TOKEN: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
