import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = destinatario
        msg.attach(MIMEText(corpo_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.EMAIL_FROM, destinatario, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {destinatario}: {e}")
        return False


def enviar_reset_senha(destinatario: str, nome: str, token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/redefinir-senha?token={token}"
    corpo = f"""
    <div style="font-family: Poppins, sans-serif; max-width: 520px; margin: auto;">
      <div style="background:#463E3F; padding: 32px; text-align:center;">
        <h1 style="color:#EFEEE8; font-size:28px; letter-spacing:4px; margin:0;">
          KAMI CO<span style="color:#E2042A;">.</span>
        </h1>
        <p style="color:#EFEEE8; opacity:.6; font-size:11px; margin:4px 0 0; text-transform:uppercase; letter-spacing:2px;">
          Sistema de Notas Fiscais
        </p>
      </div>
      <div style="background:#EFEEE8; padding: 32px;">
        <h2 style="color:#463E3F; margin-top:0;">Olá, {nome}!</h2>
        <p style="color:#463E3F;">Recebemos uma solicitação para redefinir sua senha no SNFK.</p>
        <p style="color:#463E3F;">Clique no botão abaixo para criar uma nova senha. Este link expira em <strong>30 minutos</strong>.</p>
        <div style="text-align:center; margin: 32px 0;">
          <a href="{link}"
             style="background:#E2042A; color:#fff; text-decoration:none; padding:14px 32px;
                    border-radius:8px; font-weight:bold; font-size:14px; letter-spacing:1px; text-transform:uppercase;">
            Redefinir Senha
          </a>
        </div>
        <p style="color:#463E3F; font-size:12px; opacity:.7;">
          Se você não solicitou a redefinição de senha, ignore este e-mail. Sua senha permanece a mesma.
        </p>
      </div>
      <div style="background:#463E3F; padding:16px; text-align:center;">
        <p style="color:#EFEEE8; opacity:.4; font-size:10px; margin:0;">Smart Beauty Made by People</p>
      </div>
    </div>
    """
    return enviar_email(destinatario, "Redefinição de senha — SNFK KAMI CO.", corpo)
