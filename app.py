import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import openpyxl
from flask import Flask, jsonify, render_template, request

from estoque import (
    cadastrar_toner,
    conectar,
    criar_banco,
    atualizar_modelos_compativeis,
    listar_toners,
    reativar_toner,
    registrar_saida_toner,
    remover_toner,
    ajustar_estoque_manual,
)
from suprimentos_snmp import (
    historico_toner_6,
    obter_impressoras,
    verificar_toners_nao_confiaveis,
)


# ==========================================================
# LOGGING
# ==========================================================

BASE_DIR = Path(__file__).parent

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
# APP FLASK
# ==========================================================

app = Flask(__name__)
criar_banco()


# ==========================================================
# CARREGA A LISTA DE IMPRESSORAS E IDENTIFICA OS GRUPOS
# ==========================================================

def carregar_lista_impressoras():

    arquivo = BASE_DIR / "lista_prefeitura_atualizada.xlsx"

    planilha = openpyxl.load_workbook(
        arquivo,
        data_only=True
    )

    aba = planilha.active

    lista = []

    for linha in aba.iter_rows(min_row=2, values_only=True):

        # COLUNA B = IP
        ip = linha[1]

        # COLUNA A = NOME DA IMPRESSORA / LOCAL
        nome = linha[0]

        if not ip or not nome:
            continue

        ip = str(ip).strip()
        nome = str(nome).strip()

        # --------------------------------------------------
        # O GRUPO É O TEXTO ANTES DO PRIMEIRO "-"
        #
        # Exemplo:
        # SEMAD - Almoxarifado
        #
        # vira:
        # SEMAD
        # --------------------------------------------------
        #Pega somente o código antes do primeiro "-"
        if "-" in nome:

            grupo = nome.split("-", 1)[0].strip().upper()

        else:

            grupo = nome.strip().upper()


        lista.append({

            "ip": ip,

            "nome": nome,

            "grupo": grupo

        })


    return lista


# ==========================================================
# ORGANIZA OS DADOS DO SNMP COM OS GRUPOS DA PLANILHA
# ==========================================================
def adicionar_grupos(impressoras):

    lista_planilha = carregar_lista_impressoras()

    # Cria um índice pelo IP
    por_ip = {
        item["ip"]: item
        for item in lista_planilha
    }

   

    for impressora in impressoras:

        ip = str(
            impressora.get("ip", "")
        ).strip()

        # ==================================================
        # 1 - ENCONTRA PELO IP
        # ==================================================

        cadastro = por_ip.get(ip)

        if cadastro:

            # Usa exatamente o grupo vindo da planilha
            impressora["grupo"] = cadastro["grupo"]

            # Mantém o nome/local exatamente como está na planilha
            impressora["nome_planilha"] = cadastro["nome"]

            continue

        # ==================================================
        # 2 - NÃO ENCONTROU PELO IP
        #    TENTA PELO MODELO/NOME
        # ==================================================

        nome = str(
            impressora.get("modelo", "")
        ).strip()

        if "-" in nome:

            impressora ["grupo"] = nome.split(
                "-",
                1)[0].strip().upper()
        elif nome:
            impressora["grupo"]=(
                nome.split()
                [0].strip().upper()
            )

        else:

            impressora["grupo"]= "OUTROS"
            impressora["nome_planilha"] = nome

    return impressoras

       


    


# ==========================================================
# PÁGINA PRINCIPAL
# ==========================================================

@app.route("/")
def index():

    impressoras = asyncio.run(
        obter_impressoras()
    )


    # Adiciona os grupos da nova planilha
    impressoras = adicionar_grupos(
        impressoras
    )


    horario = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )


    # Descobre automaticamente os grupos existentes
    grupos = sorted(
        set(
            impressora.get("grupo","OUTROS")
            for impressora in impressoras
        )
    )


    return render_template(

        "index.html",

        impressoras=impressoras,

        grupos=grupos,

        horario=horario

    )


# ==========================================================
# DADOS PARA ATUALIZAÇÃO DA TELA
# ==========================================================

@app.route("/dados")
def dados():

    impressoras = asyncio.run(
        obter_impressoras()
    )


    impressoras = adicionar_grupos(
        impressoras
    )
    logger.info(f"TOTAL DE IMPRESSORAS ENVIADAS AO PAINEL: {len(impressoras)}")




    return jsonify(
        impressoras
    )

# ==========================================================
# ESTOQUE DE TONERS
# ==========================================================

@app.route("/estoque")
def estoque():

    incluir_inativos = request.args.get(
        "incluir_inativos",
        ""
    ).strip().lower() in ("1", "true", "sim")
    toners = listar_toners(incluir_inativos)

    return jsonify(toners)


@app.route("/cadastrar-toner", methods=["POST"])
def cadastrar_toner_rota():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "Dados inválidos."}), 400

    marca = dados.get("marca")
    codigo = dados.get("codigo")
    cor = dados.get("cor")
    modelos_compativeis = dados.get("modelos_compativeis", "")

    if not all(
        isinstance(valor, str) and valor.strip()
        for valor in (marca, codigo, cor)
    ):
        return jsonify({
            "erro": "Preencha marca, código e cor."
        }), 400

    if not isinstance(modelos_compativeis, str):
        return jsonify({
            "erro": "Os modelos compatíveis devem ser informados como texto."
        }), 400

    try:
        estoque_inicial = dados.get("estoque")
        estoque_minimo = dados.get("estoque_minimo")

        if isinstance(estoque_inicial, bool) or isinstance(estoque_minimo, bool):
            raise ValueError

        if (
            isinstance(estoque_inicial, float)
            and not estoque_inicial.is_integer()
        ) or (
            isinstance(estoque_minimo, float)
            and not estoque_minimo.is_integer()
        ):
            raise ValueError

        estoque_inicial = int(estoque_inicial)
        estoque_minimo = int(estoque_minimo)

        if estoque_inicial < 0 or estoque_minimo < 0:
            raise ValueError

    except (TypeError, ValueError, OverflowError):
        return jsonify({
            "erro": "Estoque e estoque mínimo devem ser números inteiros não negativos."
        }), 400

    try:
        toner_id = cadastrar_toner(
            marca.strip(),
            codigo.strip(),
            cor.strip(),
            estoque_inicial,
            estoque_minimo,
            modelos_compativeis,
        )
    except sqlite3.Error:
        logger.exception("Erro ao cadastrar toner.")
        return jsonify({
            "erro": "Não foi possível cadastrar o toner."
        }), 500

    if toner_id is None:
        return jsonify({
            "erro": "Já existe um toner cadastrado com essa marca, código e cor."
        }), 409

    return jsonify({
        "sucesso": True,
        "toner_id": toner_id,
        "mensagem": "Toner cadastrado com sucesso."
    }), 201

@app.route("/ajustar-estoque/<int:toner_id>", methods=["POST"])
def ajustar_estoque_rota(toner_id):

    try:
        dados = request.get_json()
        acao = dados.get("acao")

        novo_estoque = ajustar_estoque_manual(
            toner_id,
            acao
        )

        return jsonify({
            "sucesso": True,
            "novo_estoque": novo_estoque
        })

    except Exception as erro:
        return jsonify({
            "sucesso": False,
            "erro": str(erro)
        }), 400


@app.route("/remover-toner/<int:toner_id>", methods=["DELETE"])
def remover_toner_rota(toner_id):

    try:

        remover_toner(toner_id)

        return jsonify({
            "sucesso": True,
            "mensagem": "Toner removido com sucesso."
        })

    except Exception as erro:

        return jsonify({
            "sucesso": False,
            "erro": str(erro)
        }), 400


@app.route("/reativar-toner/<int:toner_id>", methods=["POST"])
def reativar_toner_rota(toner_id):

    try:
        reativar_toner(toner_id)
        return jsonify({
            "sucesso": True,
            "mensagem": "Toner reativado com sucesso."
        })
    
    except ValueError as erro:
        return jsonify({"sucesso": False, "erro": str(erro)}), 404
    except sqlite3.Error:
        logger.exception("Erro ao reativar toner %s.", toner_id)
        return jsonify({
            "sucesso": False,
            "erro": "Não foi possível reativar o toner."
        }), 500


@app.route(
    "/toner/<int:toner_id>/modelos-compativeis",
    methods=["PUT"]
)
def atualizar_modelos_compativeis_rota(toner_id):

    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Dados inválidos."}), 400

    modelos_compativeis = dados.get("modelos_compativeis")
    if not isinstance(modelos_compativeis, str):
        return jsonify({
            "erro": "Informe os modelos compatíveis como texto."
        }), 400

    try:
        atualizar_modelos_compativeis(
            toner_id,
            modelos_compativeis
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 404
    except sqlite3.Error:
        logger.exception(
            "Erro ao atualizar modelos compatíveis do toner %s.",
            toner_id
        )
        return jsonify({
            "erro": "Não foi possível atualizar os modelos compatíveis."
        }), 500

    return jsonify({
        "sucesso": True,
        "mensagem": "Modelos compatíveis atualizados."
    })
    
@app.route("/historico")
def historico():

    # --------------------------------------------------
    # PAGINACAO: /historico?pagina=1&limite=50
    # --------------------------------------------------

    try:
        pagina = int(request.args.get("pagina", 1))
        limite = int(request.args.get("limite", 50))
    except (ValueError, TypeError):
        pagina = 1
        limite = 50

    pagina = max(1, pagina)
    limite = max(1, min(200, limite))
    offset = (pagina - 1) * limite

    entradas = []
    saidas = []
    saidas_automaticas = []
    offline = []


    # ==================================================
    # 1 - ENTRADAS E SAÍDAS DE TONER
    # ==================================================

    conexao = conectar()

    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            m.id,
            m.data,
            m.tipo,
            m.quantidade,
            m.ip_impressora,
            m.patrimonio,
            m.responsavel,
            m.observacao,

            t.marca,
            t.codigo,
            t.cor

        FROM movimentacoes m

        INNER JOIN toners t
            ON t.id = m.toner_id

        WHERE m.tipo IN ('ENTRADA', 'SAIDA')

        ORDER BY m.id DESC

        LIMIT ? OFFSET ?
    """, (limite, offset))

    registros = cursor.fetchall()

    # Total para paginacao
    cursor.execute("""
        SELECT COUNT(*)
        FROM movimentacoes
        WHERE tipo IN ('ENTRADA', 'SAIDA')
    """)
    total_movimentacoes = cursor.fetchone()[0]


    for registro in registros:

        item = {

            "id":
                registro["id"],

            "data":
                registro["data"],

            "tipo":
                registro["tipo"],

            "toner":
                (
                    registro["marca"]
                    + " - "
                    + registro["codigo"]
                    + " - "
                    + registro["cor"]
                ),

            "quantidade":
                registro["quantidade"],

            "ip_impressora":
                registro["ip_impressora"] or "-",

            "patrimonio":
                registro["patrimonio"] or "-",

            "responsavel":
                registro["responsavel"] or "-",

            "observacao":
                registro["observacao"] or "-"

        }


        if registro["tipo"] == "ENTRADA":

            entradas.append(item)

        elif registro["tipo"] == "SAIDA":

            saidas.append(item)

    cursor.execute("""
        SELECT
            m.id,
            m.data,
            m.tipo,
            m.quantidade,
            m.ip_impressora,
            m.patrimonio,
            m.responsavel,
            m.observacao,
            t.marca,
            t.codigo,
            t.cor
        FROM movimentacoes m
        INNER JOIN toners t
            ON t.id = m.toner_id
        WHERE m.tipo = 'SAIDA'
          AND m.observacao LIKE 'Baixa automática por troca detectada:%'
        ORDER BY m.id DESC
    """)

    for registro in cursor.fetchall():
        saidas_automaticas.append({
            "id": registro["id"],
            "data": registro["data"],
            "tipo": registro["tipo"],
            "toner": (
                registro["marca"]
                + " - "
                + registro["codigo"]
                + " - "
                + registro["cor"]
            ),
            "quantidade": registro["quantidade"],
            "ip_impressora": registro["ip_impressora"] or "-",
            "patrimonio": registro["patrimonio"] or "-",
            "responsavel": registro["responsavel"] or "-",
            "observacao": registro["observacao"] or "-"
    })


    # ==================================================
    # 2 - IMPRESSORAS OFFLINE DE HOJE, SEM DUPLICAR POR IP
    # ==================================================

    cursor.execute("""
        SELECT
            id,
            ip_impressora,
            patrimonio,
            modelo,
            evento,
            inicio_offline,
            data_registro,
            duracao_minutos

        FROM eventos_impressoras

        WHERE evento = 'OFFLINE'

        AND substr(data_registro, 7, 4) =
            strftime('%Y', 'now', 'localtime')

        AND substr(data_registro, 4, 2) =
            strftime('%m', 'now', 'localtime')

        AND substr(data_registro, 1, 2) =
            strftime('%d', 'now', 'localtime')

        AND id IN (
            SELECT MAX(id)
            FROM eventos_impressoras
            WHERE evento = 'OFFLINE'
              AND substr(data_registro, 7, 4) =
                  strftime('%Y', 'now', 'localtime')
              AND substr(data_registro, 4, 2) =
                  strftime('%m', 'now', 'localtime')
              AND substr(data_registro, 1, 2) =
                  strftime('%d', 'now', 'localtime')
            GROUP BY ip_impressora, substr(data_registro, 1, 10)
        )

        ORDER BY id DESC
    """)

    eventos = cursor.fetchall()


    for evento in eventos:

        horas = evento["duracao_minutos"] // 60


        if horas == 1:

           duracao= "1 hora"

        else:

          duracao = f"{horas} horas"


        offline.append({

            "id":
                evento["id"],

            "data":
                evento["data_registro"],

            "tipo":
                "OFFLINE",

            "toner":
                "-",

            "quantidade":
                "-",

            "ip_impressora":
                evento["ip_impressora"] or "-",

            "patrimonio":
                evento["patrimonio"] or "-",

            "responsavel":
                "-",

            "modelo":
                evento["modelo"] or "-",
                "duracao":
                   duracao,

            "observacao":
                (
                    f"Modelo / Local: "
                    f"{evento['modelo'] or '-'} | "
                    f"Offline por {duracao}."
                )

        })


    # ==================================================
    # RETORNA OS HISTÓRICOS SEPARADOS
    # ==================================================

    conexao.close()

    logger.info(
        "Historico consultado: pagina=%s limite=%s",
        pagina, limite
    )

    return jsonify({

        "entradas":
            entradas,

        "saidas":
            saidas,

        "saidas_automaticas":
            saidas_automaticas,

        "offline":
            offline,

        "paginacao": {
            "pagina":  pagina,
            "limite":  limite,
            "total":   total_movimentacoes,
            "paginas": (
                (total_movimentacoes + limite - 1) // limite
                if total_movimentacoes else 1
            ),
        },

    })
# ==================================================
# TONERS NÃO CONFIÁVEIS
# ==================================================
@app.route("/toners-nao-confiaveis")
def toners_nao_confiaveis():

    nao_confiaveis = verificar_toners_nao_confiaveis()

    resultado = []

    for ip, toner in nao_confiaveis:

        # Procura os dados históricos para descobrir
        # o nome da impressora
        impressora_nome = "-"

        for evento in historico_toner_6:

            if (
                evento.get("ip") == ip
                and evento.get("toner") == toner
            ):
                impressora_nome = evento.get(
                    "impressora",
                    "-"
                )

                break

        resultado.append({
            "ip": ip,
            "impressora": impressora_nome,
            "toner": toner,
            "status": "Toner não confiável"
        })

    return jsonify(resultado)

# ==========================================================
# INICIA O SERVIDOR
# ==========================================================
@app.route("/registrar-saida-toner", methods=["POST"])
def registrar_saida_toner_rota():

    try:

        dados = request.get_json()

        toner_id = dados.get("toner_id")
        quantidade = dados.get("quantidade")
        ip_impressora = dados.get("ip_impressora")
        patrimonio = dados.get("patrimonio")
        responsavel = dados.get("responsavel")
        observacao = dados.get("observacao")


        if not toner_id:

            return jsonify({
                "erro": "Selecione o toner."
            }), 400


        if not quantidade:

            return jsonify({
                "erro": "Informe a quantidade."
            }), 400


        novo_estoque = registrar_saida_toner(

            toner_id=int(toner_id),

            quantidade=int(quantidade),

            ip_impressora=ip_impressora,

            patrimonio=patrimonio,

            responsavel=responsavel,

            observacao=observacao

        )


        return jsonify({

            "sucesso": True,

            "novo_estoque": novo_estoque,

            "mensagem":
                "Saída registrada com sucesso."

        })


    except Exception as erro:

        return jsonify({

            "sucesso": False,

            "erro": str(erro)

        }), 400
    
if __name__ == "__main__":

   app.run(host="0.0.0.0", port=5000, debug=False)
    