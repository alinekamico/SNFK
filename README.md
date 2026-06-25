# fiscal-nfe — KAMI CO.

Sistema de gestão de documentos fiscais (NF-e) similar ao Arquivei.
Multi-empresa, multi-certificado, coleta automática SEFAZ + Tiny + UNO.

## Stack

- **Frontend:** React + Next.js 14 + Tailwind CSS
- **Backend:** Python + FastAPI
- **Banco:** MySQL local (dev) / RDS MySQL (produção)
- **Cloud:** EC2 + RDS na AWS (gerenciado pela TI)

## Configuração Local

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Copiar e preencher variáveis
copy .env.example .env

# Gerar FERNET_KEY (executar uma vez)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Criar banco
mysql -u root -p -e "CREATE DATABASE fiscal_nfe CHARACTER SET utf8mb4;"

# Iniciar API
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Acesse: http://localhost:3000

## Fluxo

1. Cadastrar empresa (CNPJ)
2. Upload do certificado .pfx + senha
3. Disparar coleta SEFAZ pelo botão ou aguardar scheduler
4. Visualizar, filtrar e baixar XML/DANFe

## Certificado Digital

O .pfx é armazenado fora do webroot em `certs/<cnpj>/`.
A senha é cifrada com Fernet antes de ir ao banco.
Nunca commitar arquivos .pfx ou .env.

## Deploy AWS (TI)

EC2 + RDS MySQL. Deploy via GitHub conforme governança KAMI CO.
