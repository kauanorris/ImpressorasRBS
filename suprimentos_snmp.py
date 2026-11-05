import asyncio
import json
import logging
import openpyxl
import os
import re
import sqlite3
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from pysnmp.hlapi.v1arch.asyncio import *

from estoque import registrar_evento_impressora, registrar_nivel_toner


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

BASE_DIR = Path(__file__).parent

ARQUIVO_OFFLINE  = BASE_DIR / "impressoras_offline.json"
ARQUIVO_HISTORICO = BASE_DIR / "historico.json"


# ==========================================================
# CARREGA VARIÁVEIS DO .ENV
# ==========================================================

load_dotenv()

# ==========================================================
# CONFIGURAÇÃO DE LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            BASE_DIR / "monitor.log",
            encoding="utf-8"
        ),
    ]
)

logger = logging.getLogger(__name__)

# ==========================================================
# CONFIGURAÇÕES DE E-MAIL E SNMP
# ==========================================================

EMAIL_SEMED  = os.getenv("EMAIL_SEMED",  "")
EMAIL_OUTROS = os.getenv("EMAIL_OUTROS", "")
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "public")

logger.info("Gmail configurado: %s", os.getenv("GMAIL_REMETENTE"))
logger.info("Senha de app carregada: %s", bool(os.getenv("GMAIL_SENHA_APP")))
logger.info("SNMP Community: %s", SNMP_COMMUNITY)


# ==========================================================
# CONTROLE DE ALERTAS DE TONER
# ==========================================================

def carregar_alertas_enviados():

    try:

        with open(
            "alertas_enviados.json",
            "r",
            encoding="utf-8"
        ) as arquivo:

            return set(json.load(arquivo))

    except:

        return set()


def salvar_alertas_enviados(alertas):
    

    with open(
        "alertas_enviados.json",
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            list(alertas),
            arquivo,
            indent=4
        )


toners_alertados = carregar_alertas_enviados()

# ==========================================================
# HISTÓRICO DE TONERS EM 6%
# ==========================================================

ARQUIVO_TONER_6 = BASE_DIR / "historico_toner_6.json"


def carregar_historico_toner_6():

    try:

        with open(
            ARQUIVO_TONER_6,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except:

        return []


def salvar_historico_toner_6(historico):

    with open(
        ARQUIVO_TONER_6,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            historico,
            arquivo,
            indent=4,
            ensure_ascii=False
        )


historico_toner_6 = carregar_historico_toner_6()

def registrar_toner_6(
    ip,
    nome_impressora,
    toner
):

    agora = datetime.now()

    # Verifica se já existe uma leitura recente
    for evento in reversed(historico_toner_6):

        if (
            evento.get("ip") == ip
            and evento.get("toner") == toner
        ):

            ultima_data = datetime.strptime(
                evento["data"],
                "%d/%m/%Y %H:%M:%S"
            )

            # Não registra novamente no mesmo dia
            if ultima_data.date() == agora.date():
                return

            break

    evento = {

        "data":
            agora.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "ip":
            ip,

        "impressora":
            nome_impressora,

        "toner":
            toner,

        "nivel":
            6
    }

    historico_toner_6.append(evento)

    salvar_historico_toner_6(
        historico_toner_6
    )
# ==========================================================
# VERIFICA TONERS COM LEITURA NÃO CONFIÁVEL
# ==========================================================
# ==========================================================
# VERIFICA TONERS COM 5 DIAS CONSECUTIVOS EM 6%
# ==========================================================

def verificar_toners_nao_confiaveis():

    nao_confiaveis = set()

    registros = {}

    for evento in historico_toner_6:

        ip = evento.get("ip")
        toner = evento.get("toner")
        data = evento.get("data")

        if not ip or not toner or not data:
            continue

        chave = (ip, toner)

        try:

            data_registro = datetime.strptime(
                data,
                "%d/%m/%Y %H:%M:%S"
            ).date()

        except ValueError:

            continue

        if chave not in registros:
            registros[chave] = set()

        registros[chave].add(
            data_registro
        )

    for chave, datas in registros.items():

        datas_ordenadas = sorted(datas)

        dias_consecutivos = 1

        for i in range(1, len(datas_ordenadas)):

            diferenca = (
                datas_ordenadas[i]
                - datas_ordenadas[i - 1]
            ).days

            if diferenca == 1:

                dias_consecutivos += 1

            else:

                dias_consecutivos = 1

            if dias_consecutivos >= 5:

                nao_confiaveis.add(chave)

                break

    return nao_confiaveis
# ==========================================================
# ENVIA E-MAIL DE TONER BAIXO
# ==========================================================

def enviar_email_toner(
    destinatario,
    impressora,
    toner,
    porcentagem
):

    remetente = os.environ.get(
        "GMAIL_REMETENTE"
    )

    senha_app = os.environ.get(
        "GMAIL_SENHA_APP"
    )

    if not remetente or not senha_app:

        logger.error(
            "ERRO: Gmail não configurado."
        )

        return


    mensagem = EmailMessage()

    mensagem["Subject"] = (
        f"⚠️ Toner baixo - {impressora}"
    )

    mensagem["From"] = remetente

    mensagem["To"] = destinatario

    mensagem.set_content(
        f"""Olá,

O sistema de monitoramento identificou toner abaixo de 07%.

Impressora: {impressora}
Toner: {toner}
Nível atual: {porcentagem}

Solicita-se a verificação e substituição do toner.

Este é um aviso automático do Monitor de Impressoras.
"""
    )


    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as servidor:

            servidor.starttls()

            servidor.login(
                remetente,
                senha_app
            )

            servidor.send_message(
                mensagem
            )


        logger.info(f"E-mail enviado para: {destinatario}")


    except Exception as erro:

        logger.error(f"Erro ao enviar e-mail: {erro}")


# ==========================================================
# CARREGA PLANILHA DE IMPRESSORAS
# ==========================================================

def carregar_planilha():

    arquivo = "lista_prefeitura_atualizada.xlsx"

    planilha = openpyxl.load_workbook(
        arquivo,
        data_only=True
    )

    aba = planilha.active

    impressoras_planilha = []


    for linha in aba.iter_rows(
        min_row=1,
        values_only=True
    ):

        descricao = linha[0]

        ip = linha[1]

        patrimonio = linha[2]


        if not ip:

            continue


        ip = str(ip).strip()


        # Remove "(Network)"
        ip = ip.replace(
            "(Network)",
            ""
        ).strip()


        # Se houver texto depois do IP,
        # pega somente o primeiro valor

        ip = ip.split()[0]


        partes = ip.split(".")


        if len(partes) != 4:

            continue


        if not all(
            parte.isdigit()
            for parte in partes
        ):

            continue


        if not all(
            0 <= int(parte) <= 255
            for parte in partes
        ):

            continue


        impressoras_planilha.append({

            "descricao": descricao,

            "ip": ip,

            "patrimonio": patrimonio

        })


    return impressoras_planilha


# ==========================================================
# CARREGA E-MAILS POR IP
# ==========================================================

def carregar_emails():

    arquivo = "lista_impressoras-prefeitura.xlsx"

    planilha = openpyxl.load_workbook(
        arquivo,
        data_only=True
    )

    aba = planilha.active

    emails_por_ip = {}


    for linha in aba.iter_rows(
        min_row=2,
        values_only=True
    ):

        ip = linha[1]

        nome = linha[0]

        email = linha[4]


        if not ip or not email:

            continue


        ip = str(ip).strip()

        email = str(email).strip()


        emails_por_ip[ip] = {

            "email": email,

            "nome": nome

        }


    return emails_por_ip


# ==========================================================
# HISTÓRICO
# ==========================================================

def registrar_evento(
    ip,
    tipo,
    mensagem
):

    try:

        with open(
            ARQUIVO_HISTORICO,
            "r",
            encoding="utf-8"
        ) as arquivo:

            historico = json.load(
                arquivo
            )

    except:

        historico = []


    evento = {

        "data":
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "ip":
            ip,

        "tipo":
            tipo,

        "mensagem":
            mensagem

    }


    historico.append(
        evento
    )


    with open(
        ARQUIVO_HISTORICO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            historico,
            arquivo,
            indent=4,
            ensure_ascii=False
        )


# ==========================================================
# CONTROLE DOS OFFLINES
# ==========================================================

def carregar_offline():

    try:

        with open(
            ARQUIVO_OFFLINE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(
                arquivo
            )

    except:

        return {}


def salvar_offline(dados):

    with open(
        ARQUIVO_OFFLINE,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            indent=4,
            ensure_ascii=False
        )


# ==========================================================
# CONSULTA SNMP
# ==========================================================

async def consultar(
    ip,
    oid_base
):

    resultados = []


    try:

        with SnmpDispatcher() as snmp:

            transporte = await UdpTransportTarget.create(
                (ip, 161),
                timeout=0.3,
                retries=0
            )


            async for (
                erro,
                status,
                indice,
                dados
            ) in walk_cmd(

                snmp,

                CommunityData(
                    SNMP_COMMUNITY
                ),

                transporte,

                (
                    oid_base,
                    None
                )

            ):

                if erro or status:

                    break


                for oid, valor in dados:

                    if not str(
                        oid
                    ).startswith(
                        oid_base
                    ):

                        return resultados


                    resultados.append(
                        valor.prettyPrint()
                    )


    except Exception as erro:

        logger.error(f"Erro SNMP no IP {ip}: {erro}")


    return resultados


# ==========================================================
# CONSULTA MODELO
# ==========================================================

async def consultar_modelo(ip):

    resultados = await consultar(
        ip,
        "1.3.6.1.2.1.1.1"
    )


    if resultados:

        return resultados[0]


    return "Modelo não identificado"


# ==========================================================
# MAIN
# ==========================================================

async def main():

    dados = []

    encontradas = []


    # ------------------------------------------------------
    # CARREGA E-MAILS
    # ------------------------------------------------------

    emails_por_ip = carregar_emails()


    # ------------------------------------------------------
    # CARREGA CONTROLE DE OFFLINE
    # ------------------------------------------------------

    offline = carregar_offline()

    #------------------------------------------------------ 
    # CARREGAR TONERS NÃO CONFIÁVEIS
    #------------------------------------------------------

    toners_nao_confiaveis = verificar_toners_nao_confiaveis()


    # ------------------------------------------------------
    # LISTA DE IMPRESSORAS
    # ------------------------------------------------------

    impressoras = []


    # ------------------------------------------------------
    # IPs ENCONTRADOS ANTERIORMENTE
    # ------------------------------------------------------

    try:

        with open(
            str(BASE_DIR / "impressoras_encontradas.json"),
            "r",
            encoding="utf-8"
        ) as arquivo:

            ips_existentes = json.load(
                arquivo
            )

    except:

        ips_existentes = []


    # ------------------------------------------------------
    # IPs DA PLANILHA
    # ------------------------------------------------------

    dados_planilha = carregar_planilha()


    planilha_por_ip = {

        item["ip"]: item

        for item in dados_planilha

    }


    ips_planilha = [

        item["ip"]

        for item in dados_planilha

    ]


    # ------------------------------------------------------
    # JUNTA OS IPS
    # ------------------------------------------------------

    ips_para_testar = list(
        set(
            ips_existentes
            +
            ips_planilha
        )
    )


    for ip in ips_para_testar:

        impressoras.append({

            "nome":
                f"Impressora {ip}",

            "ip":
                ip

        })


    logger.info(f"TOTAL DE IPs PARA TESTAR: {len(impressoras)}")


    # ======================================================
    # TESTA CADA IMPRESSORA
    # ======================================================

    for impressora in impressoras:

        ip = impressora["ip"]


        logger.info(f"Testando impressora: {ip}")


        # --------------------------------------------------
        # DADOS DA PLANILHA
        # --------------------------------------------------

        dados_cadastro = planilha_por_ip.get(
            ip,
            {}
        )


        descricao_planilha = (
            dados_cadastro.get(
                "descricao",
                "Não cadastrado"
            )
        )


        patrimonio = (
            dados_cadastro.get(
                "patrimonio",
                "Não cadastrado"
            )
        )


        nome_impressora = (
            descricao_planilha
        )

        modelo_planilha = extrair_modelo_planilha(descricao_planilha
        )


        # --------------------------------------------------
        # DEFINE E-MAIL
        # --------------------------------------------------

        if str(
            nome_impressora
        ).upper().startswith(
            "SEMED"
        ):

            email = EMAIL_SEMED

        else:

            email = EMAIL_OUTROS


        logger.info(f"IP: {ip}")

        logger.info(f"Modelo/Descrição: {descricao_planilha}")

        logger.info(f"Modelo planilha: {modelo_planilha}")

        logger.info(f"Patrimônio: {patrimonio}")


        # ==================================================
        # CONSULTA OS SUPRIMENTOS
        # ==================================================

        descricoes = await consultar(

            ip,

            "1.3.6.1.2.1.43.11.1.1.6"

        )


        # ==================================================
        # IMPRESSORA NÃO RESPONDEU
        # ==================================================

        if not descricoes:

            logger.info(f"IMPRESSORA OFFLINE: {ip}")


            agora = datetime.now()


            # --------------------------------------------------
            # SE É A PRIMEIRA VEZ QUE ESTÁ OFFLINE,
            # COMEÇA A CONTAR O TEMPO
            # --------------------------------------------------

            if ip not in offline:

                offline[ip] = {

                    "inicio":
                        agora.strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),

                    "registrado":
                        False

                }


                salvar_offline(
                    offline
                )


            # --------------------------------------------------
            # PEGA O REGISTRO DESTE IP
            # --------------------------------------------------
# --------------------------------------------------
            # VERIFICA SE A IMPRESSORA ESTÁ OFFLINE
            # --------------------------------------------------

            dados_offline = offline[ip]


            inicio = datetime.strptime(

                dados_offline["inicio"],

                "%d/%m/%Y %H:%M:%S"

            )


            # --------------------------------------------------
            # CALCULA O TEMPO OFFLINE
            # --------------------------------------------------

            tempo_offline = (

                agora - inicio

            ).total_seconds()


            # --------------------------------------------------
            # REGISTRA NO HISTÓRICO SOMENTE APÓS 24 HORAS
            # --------------------------------------------------

            if (

                tempo_offline >= 86400

                and

                not dados_offline["registrado"]

            ):

                minutos = int(

                    tempo_offline / 60

                )


                registrar_evento_impressora(

                    ip_impressora=ip,

                    patrimonio=patrimonio,

                    modelo=descricao_planilha,

                    evento="OFFLINE",

                    inicio_offline=inicio.strftime(
                        "%d/%m/%Y %H:%M:%S"
                    ),

                    duracao_minutos=minutos

                )


                # Marca somente esta impressora
                # como já registrada

                dados_offline["registrado"] = True


                salvar_offline(

                    offline

                )


                logger.info(

                    "EVENTO OFFLINE REGISTRADO:",

                    ip

                )


            # --------------------------------------------------
            # CONTINUA APARECENDO COMO OFFLINE NA TELA
            # --------------------------------------------------

            dados.append({

                "nome":
                    impressora["nome"],

                "ip":
                    ip,

                "modelo":
                    descricao_planilha,

                "patrimonio":
                    patrimonio,

                "email":
                    email,

                "ciano":
                    "-",

                "magenta":
                    "-",

                "amarelo":
                    "-",

                "preto":
                    "-",

                "status":
                    "Offline"

            })


            continue


        # ==================================================
        # IMPRESSORA RESPONDEU
        # ==================================================

        logger.info(f"IMPRESSORA ENCONTRADA: {ip}")


        # --------------------------------------------------
        # VERIFICA SE ELA ESTAVA OFFLINE
        # --------------------------------------------------

        if ip in offline:

            dados_retorno = offline[ip]


            # --------------------------------------------------
            # SE O OFFLINE JÁ TINHA SIDO REGISTRADO,
            # REGISTRA O RETORNO ONLINE
            # --------------------------------------------------

            if dados_retorno.get(
                "registrado",
                False
            ):

                inicio = datetime.strptime(

                    dados_retorno["inicio"],

                    "%d/%m/%Y %H:%M:%S"

                )


                agora = datetime.now()


                segundos_offline = (

                    agora - inicio

                ).total_seconds()


                minutos = int(
                    segundos_offline / 60
                )


                registrar_evento(

                    ip,

                    "ONLINE",

                    (
                        "Impressora voltou a "
                        "responder ao SNMP após "
                        f"{minutos} minutos offline."
                    )

                )


                logger.info(f"EVENTO ONLINE REGISTRADO: {ip}")


            # --------------------------------------------------
            # REMOVE O CONTROLE DO OFFLINE
            # --------------------------------------------------

            del offline[ip]


            salvar_offline(offline)


        # --------------------------------------------------
        # GUARDA COMO ENCONTRADA
        # --------------------------------------------------

        encontradas.append(
            ip
        )

# ==================================================
        # CONSULTA MODELO
        # ==================================================

        modelo = await consultar_modelo(
            ip
        )

        logger.info(f"MODELO: {modelo}")


        # ==================================================
        # CAPACIDADE DOS TONERS
        # ==================================================

        capacidades = await consultar(
            ip,
            "1.3.6.1.2.1.43.11.1.1.8"
        )


        # ==================================================
        # NÍVEL ATUAL DOS TONERS
        # ==================================================

        niveis = await consultar(
            ip,
            "1.3.6.1.2.1.43.11.1.1.9"
        )


        logger.info(f"IP: {ip}")

        logger.info(f"DESCRICOES: {descricoes}")

        logger.info(f"CAPACIDADES: {capacidades}")

        logger.info(f"NIVEIS: {niveis}")


        # ==================================================
        # VALORES INICIAIS
        # ==================================================

        ciano = "-"
        magenta = "-"
        amarelo = "-"
        preto = "-"

        # ==================================================
        # MODELO DA PLANILHA
        # ==================================================

        modelo_estoque = modelo_planilha

        # Lista de cores encontradas nesta impressora
        cores_estoque = []

        # ==================================================
        # PROCESSA SUPRIMENTOS
        # ==================================================

        suprimentos_validos = []


        for i in range(
            len(descricoes)
        ):

            if (
                i >= len(capacidades)
                or
                i >= len(niveis)
            ):
                continue


            try:

                capacidade = int(
                    capacidades[i]
                )

                nivel = int(
                    niveis[i]
                )

            except (
                ValueError,
                TypeError
            ):

                continue


            # --------------------------------------------------
            # IGNORA VALORES INVÁLIDOS
            # --------------------------------------------------

            if (
                capacidade <= 0
                or
                nivel < 0
            ):

                continue


            porcentagem_numero = (
                nivel /
                capacidade
            ) * 100


            porcentagem_numero = max(
                0,
                min(
                    100,
                    porcentagem_numero
                )
            )


            porcentagem = (
                f"{porcentagem_numero:.0f}%"
            )


            descricao = str(
                descricoes[i]
            ).upper()


            suprimentos_validos.append({

                "descricao":
                    descricao,

                "porcentagem":
                    porcentagem

            })


        # ==================================================
        # IDENTIFICA CORES
        # ==================================================

        for suprimento in (
            suprimentos_validos
        ):

            descricao = (
                suprimento["descricao"]
            )

            porcentagem = (
                suprimento["porcentagem"]
            )


            if (
                descricao.endswith("C")
                or
                " CYAN" in descricao
            ):

                ciano = porcentagem
                cores_estoque.append(
                    "Ciano"
                )


            elif (
                descricao.endswith("M")
                or
                " MAGENTA" in descricao
            ):

                magenta = porcentagem
                cores_estoque.append(
                    "Magenta"
                )


            elif (
                descricao.endswith("Y")
                or
                " YELLOW" in descricao
            ):

                amarelo = porcentagem
                cores_estoque.append(
                    "Amarelo"
                )


            elif (
                descricao.endswith("K")
                or
                " BLACK" in descricao
            ):

                preto = porcentagem
                cores_estoque.append(
                    "Preto"
                )


        # ==================================================
        # SE POSSUI APENAS UM TONER,
        # CONSIDERA COMO PRETO
        # ==================================================

        if len(
            suprimentos_validos
        ) == 1:

            preto = (
                suprimentos_validos[0]
                ["porcentagem"]
            )
            if "Preto" not in cores_estoque:
              cores_estoque.append("Preto")

        # ==================================================
        # VERIFICA TONER ABAIXO DE 10%
        # ==================================================

        toners = {

            "Ciano":
                ciano,

            "Magenta":
                magenta,

            "Amarelo":
                amarelo,

            "Preto":
                preto

        }


        for (
            nome_toner,
            nivel
        ) in toners.items():


            if (
                not nivel
                or
                nivel == "-"
            ):

                continue


            try:

                porcentagem = int(
                    str(nivel)
                    .replace("%", "")
                    .strip()
                )

            except ValueError:

                continue

            try:
                baixa_automatica = registrar_nivel_toner(
                    ip,
                    modelo_planilha,
                    nome_toner,
                    porcentagem,
                    patrimonio
                )
            except sqlite3.Error:
                logger.exception(
                    "Erro ao registrar nível do toner %s da impressora %s.",
                    nome_toner,
                    ip
                )
                baixa_automatica = None

            if baixa_automatica and baixa_automatica["status"] == "registrada":
                logger.info(
                    "TROCA DE TONER REGISTRADA AUTOMATICAMENTE: "
                    "%s %s (%s) na impressora %s; estoque agora %s.",
                    baixa_automatica["marca"],
                    baixa_automatica["codigo"],
                    baixa_automatica["cor"],
                    ip,
                    baixa_automatica["novo_estoque"]
                )
            elif baixa_automatica:
                logger.warning(
                    "Troca de toner detectada na impressora %s (%s), "
                    "mas a baixa não foi registrada: %s. Verifique o "
                    "modelo compatível cadastrado para o toner %s.",
                    ip,
                    modelo_planilha,
                    baixa_automatica["status"],
                    nome_toner
                )


            # --------------------------------------------------
            # TONER VOLTOU AO NORMAL
            # --------------------------------------------------

            if porcentagem >= 7:

                chave_alerta = (
                    f"{ip}-{nome_toner}"
                )


                if (
                    chave_alerta
                    in
                    toners_alertados
                ):

                    toners_alertados.remove(
                        chave_alerta
                    )

                    salvar_alertas_enviados(
                        toners_alertados
                    )

                continue


            # --------------------------------------------------
            # REGISTRA SOMENTE TONER EXATAMENTE EM 6%
            # --------------------------------------------------

            if porcentagem == 6:

                registrar_toner_6(
                    ip,
                    nome_impressora,
                    nome_toner
                )


            # --------------------------------------------------
            # TONER ABAIXO DE 7%
            # --------------------------------------------------

            chave_alerta = (
                f"{ip}-{nome_toner}"
            )


            if (
                porcentagem < 7
                and
                (ip, nome_toner)
                not in
                toners_nao_confiaveis
                and
                chave_alerta
                not in
                toners_alertados
            ):

                logger.info(

                    "ALERTA DE TONER:",

                    ip,

                    nome_impressora,

                    nome_toner,

                    porcentagem,

                    "%",

                    "DESTINATÁRIO:",

                    email

                )


                enviar_email_toner(

                    email,

                    nome_impressora,

                    nome_toner,

                    f"{porcentagem}%"

                )


                toners_alertados.add(
                    chave_alerta
                )


                salvar_alertas_enviados(
                    toners_alertados
                )


        # ==================================================
        # ADICIONA IMPRESSORA ONLINE
        # ==================================================

        dados.append({

            "nome":
                impressora["nome"],

            "ip":
                ip,

            "modelo":
                descricao_planilha,

            "patrimonio":
                patrimonio,

            "email":
                email,

            "ciano":
                ciano,

            "magenta":
                magenta,

            "amarelo":
                amarelo,

            "preto":
                preto,

            "status":
                "Online"

        })


    # ======================================================
    # MOSTRA IMPRESSORAS ENCONTRADAS
    # ======================================================

    logger.info(
        "IMPRESSORAS ENCONTRADAS:"
    )

    logger.info(f"Encontradas: {encontradas}")



    # ======================================================
    # SALVA IPS ENCONTRADOS
    # ======================================================

    with open(
        str(BASE_DIR / "impressoras_encontradas.json"),
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            encontradas,
            arquivo,
            indent=4
        )


    return dados

# ==========================================================
# EXTRAI O MODELO DA IMPRESSORA DA DESCRIÇÃO DA PLANILHA
# ==========================================================

def extrair_modelo_planilha(descricao):

    descricao = str(
        descricao or ""
    ).strip()

    modelo_kyocera = re.search(
        r"\bM\d{3,5}[A-Z0-9-]*",
        descricao,
        re.IGNORECASE
    )
    if modelo_kyocera:
        return modelo_kyocera.group(0)

    # Procura o texto dentro dos parênteses
    if "(" in descricao and ")" in descricao:

        modelo_completo = descricao.rsplit(
            "(",
            1
        )[1].split(
            ")",
            1
        )[0].strip()

        # Exemplo:
        # Kyocera ECOSYS M2040dn
        # retorna somente:
        # M2040dn

        partes = modelo_completo.split()

        if partes:
            return partes[-1].strip()

    return "Modelo não identificado"

# ==========================================================
# FUNÇÃO USADA PELO FLASK
# ==========================================================

async def obter_impressoras():

    return await main()


# ==========================================================
# EXECUÇÃO DIRETA
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )