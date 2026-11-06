import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REMETENTE = os.getenv("GMAIL_REMETENTE")
SENHA_APP = os.getenv("GMAIL_SENHA_APP")
DESTINATARIO = os.getenv("EMAIL_SEMED", REMETENTE)

if not REMETENTE or not SENHA_APP or not DESTINATARIO:
    raise RuntimeError(
        "Configure GMAIL_REMETENTE, GMAIL_SENHA_APP e EMAIL_SEMED no arquivo .env."
    )


mensagem = EmailMessage()

mensagem["Subject"] = "Teste - Monitor de Impressoras"
mensagem["From"] = REMETENTE
mensagem["To"] = DESTINATARIO

mensagem.set_content(
    "Este é um teste do sistema de monitoramento de impressoras."
)


with smtplib.SMTP("smtp.gmail.com", 587) as servidor:

    servidor.starttls()

    servidor.login(
        REMETENTE,
        SENHA_APP
    )

    servidor.send_message(mensagem)


print("E-mail enviado com sucesso!")