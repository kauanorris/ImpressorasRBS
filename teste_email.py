import smtplib
from email.message import EmailMessage


REMETENTE = "elisdaianecoutinho@gmail.com"
SENHA_APP = "fmqa znuw ukvj tosm"

DESTINATARIO = "elisdaianecoutinho@gmail.com"


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