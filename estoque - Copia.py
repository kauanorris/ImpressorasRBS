import sqlite3
import os
import re
from datetime import datetime


# ==========================================================
# CAMINHO DO BANCO DE DADOS
# ==========================================================

BANCO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "estoque.db"
)


def conectar():
    return sqlite3.connect(BANCO)


# ==========================================================
# CRIA AS TABELAS DO BANCO (SE NÃO EXISTIREM)
# ==========================================================

def criar_banco():

    conexao = conectar()
    cursor = conexao.cursor()

    # ==========================================
    # TONERS
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS toners (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            marca TEXT NOT NULL,

            codigo TEXT NOT NULL,

            cor TEXT NOT NULL,

            modelos_compativeis TEXT NOT NULL DEFAULT '',

            estoque INTEGER NOT NULL DEFAULT 0,

            estoque_minimo INTEGER NOT NULL DEFAULT 1,

            ativo INTEGER NOT NULL DEFAULT 1,

            UNIQUE(marca, codigo, cor)
        )
    """)

    colunas_toners = {
        coluna[1]
        for coluna in cursor.execute(
            "PRAGMA table_info(toners)"
        ).fetchall()
    }

    if "modelos_compativeis" not in colunas_toners:
        cursor.execute("""
            ALTER TABLE toners
            ADD COLUMN modelos_compativeis TEXT NOT NULL DEFAULT ''
        """)


    # ==========================================
    # MOVIMENTAÇÕES DO ESTOQUE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            toner_id INTEGER NOT NULL,

            tipo TEXT NOT NULL,

            quantidade INTEGER NOT NULL,

            data TEXT NOT NULL,

            nota TEXT,

            ip_impressora TEXT,

            patrimonio TEXT,

            responsavel TEXT,

            local_impressora TEXT,

            observacao TEXT,

            FOREIGN KEY (toner_id)
                REFERENCES toners(id)
        )
    """)

    colunas_movimentacoes = {
        coluna[1]
        for coluna in cursor.execute(
            "PRAGMA table_info(movimentacoes)"
        ).fetchall()
    }

    if "local_impressora" not in colunas_movimentacoes:
        cursor.execute("""
            ALTER TABLE movimentacoes
            ADD COLUMN local_impressora TEXT
        """)


    # ==========================================
    # TROCAS DE TONER
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trocas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            toner_id INTEGER NOT NULL,

            ip_impressora TEXT NOT NULL,

            patrimonio TEXT,

            quantidade INTEGER NOT NULL DEFAULT 1,

            responsavel TEXT NOT NULL,

            data TEXT NOT NULL,

            observacao TEXT,

            FOREIGN KEY (toner_id)
                REFERENCES toners(id)
        )
    """)

    # ==========================================
    # EVENTOS DE IMPRESSORAS OFFLINE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_impressoras (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ip_impressora TEXT NOT NULL,

            patrimonio TEXT,

            modelo TEXT,

            evento TEXT NOT NULL,

            inicio_offline TEXT NOT NULL,

            data_registro TEXT NOT NULL,

            duracao_minutos INTEGER NOT NULL

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS niveis_toner (
            ip_impressora TEXT NOT NULL,
            cor TEXT NOT NULL,
            percentual INTEGER NOT NULL,
            atualizado_em TEXT NOT NULL,
            PRIMARY KEY (ip_impressora, cor)
        )
    """)

    conexao.commit()
    conexao.close()


# ==========================================================
# CADASTRA UM NOVO TONER
# ==========================================================

def cadastrar_toner(
    marca,
    codigo,
    cor,
    estoque=0,
    estoque_minimo=1,
    modelos_compativeis=""
):

    conexao = conectar()
    cursor = conexao.cursor()

    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    marca = marca.strip()
    codigo = codigo.strip()
    cor = cor.strip()

    try:

        # Verifica se o toner já está cadastrado
        cursor.execute("""
            SELECT id, estoque
            FROM toners
            WHERE LOWER(TRIM(marca)) = LOWER(?)
              AND LOWER(TRIM(codigo)) = LOWER(?)
              AND LOWER(TRIM(cor)) = LOWER(?)
            LIMIT 1
        """, (marca, codigo, cor))

        existente = cursor.fetchone()

        if existente:

            toner_id, saldo_atual = existente

            quantidade = int(estoque)

            novo_saldo = int(saldo_atual) + quantidade

            # Atualiza o estoque do toner existente
            cursor.execute("""
                UPDATE toners
                SET estoque = ?, estoque_minimo = ?,
                    modelos_compativeis = CASE
                        WHEN TRIM(?) = '' THEN modelos_compativeis
                        ELSE ?
                    END
                WHERE id = ?
            """, (
                novo_saldo,
                int(estoque_minimo),
                modelos_compativeis,
                modelos_compativeis.strip(),
                toner_id
            ))

            # Registra a entrada no histórico
            if quantidade > 0:

                cursor.execute("""
                    INSERT INTO movimentacoes
                    (toner_id, tipo, quantidade, data, observacao)
                    VALUES (?, 'ENTRADA', ?, ?, ?)
                """, (
                    toner_id,
                    quantidade,
                    data_atual,
                    "Reposição de estoque pelo cadastro"
                ))

            conexao.commit()

            return toner_id

        # Se não existir, cadastra um novo toner
        cursor.execute("""
            INSERT INTO toners
            (marca, codigo, cor, modelos_compativeis, estoque, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            marca,
            codigo,
            cor,
            modelos_compativeis.strip(),
            int(estoque),
            int(estoque_minimo)
        ))

        toner_id = cursor.lastrowid

        # Registra o estoque inicial
        if int(estoque) > 0:

            cursor.execute("""
                INSERT INTO movimentacoes
                (toner_id, tipo, quantidade, data, observacao)
                VALUES (?, 'ENTRADA', ?, ?, ?)
            """, (
                toner_id,
                int(estoque),
                data_atual,
                "Estoque inicial do cadastro"
            ))

        conexao.commit()

        return toner_id

    finally:

        conexao.close()

# ==========================================================
# LISTA TONERS ATIVOS
# ==========================================================

def listar_toners(incluir_inativos=False):

    conexao = conectar()
    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
            marca,
            codigo,
            cor,
            modelos_compativeis,
            estoque,
            estoque_minimo,
            ativo
        FROM toners
        WHERE ativo = 1 OR ? = 1
        ORDER BY marca, codigo, cor
    """, (int(incluir_inativos),))

    toners = cursor.fetchall()

    conexao.close()

    return [dict(toner) for toner in toners]


# ==========================================================
# DESATIVA (REMOVE) UM TONER
# ==========================================================

def remover_toner(toner_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            UPDATE toners
            SET ativo = 0
            WHERE id = ?
        """, (toner_id,))

        if cursor.rowcount == 0:
            raise ValueError("Toner não encontrado.")

        conexao.commit()

        return True

    except Exception:

        conexao.rollback()

        raise

    finally:

        conexao.close()


def reativar_toner(toner_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE toners
            SET ativo = 1
            WHERE id = ?
        """, (toner_id,))

        if cursor.rowcount == 0:
            raise ValueError("Toner não encontrado.")

        conexao.commit()
        return True

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def atualizar_modelos_compativeis(toner_id, modelos_compativeis):
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE toners
            SET modelos_compativeis = ?
            WHERE id = ?
        """, (modelos_compativeis.strip(), toner_id))

        if cursor.rowcount == 0:
            raise ValueError("Toner não encontrado.")

        conexao.commit()
        return True

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


# ==========================================================
# BUSCA UM TONER POR ID
# ==========================================================

def buscar_toner(toner_id):

    conexao = conectar()
    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM toners
        WHERE id = ?
    """, (toner_id,))

    toner = cursor.fetchone()

    conexao.close()

    if toner:
        return dict(toner)

    return None


# ==========================================================
def registrar_saida_toner(
    toner_id,
    quantidade,
    ip_impressora=None,
    patrimonio=None,
    responsavel=None,
    observacao=None
):

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        novo_estoque = _registrar_saida_no_cursor(
            cursor,
            toner_id,
            quantidade,
            ip_impressora,
            patrimonio,
            responsavel,
            observacao
        )

        conexao.commit()

        return novo_estoque


    except Exception:

        conexao.rollback()

        raise


    finally:

        conexao.close()


def _registrar_saida_no_cursor(
    cursor,
    toner_id,
    quantidade,
    ip_impressora,
    patrimonio,
    responsavel,
    observacao,
    local_impressora=None
):
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    cursor.execute("""
        SELECT estoque
        FROM toners
        WHERE id = ?
          AND ativo = 1
    """, (toner_id,))
    resultado = cursor.fetchone()

    if not resultado:
        raise ValueError("Toner não encontrado ou está inativo.")

    novo_estoque = resultado[0] - quantidade
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    cursor.execute("""
        UPDATE toners
        SET estoque = ?
        WHERE id = ?
    """, (novo_estoque, toner_id))

    cursor.execute("""
        INSERT INTO movimentacoes (
            toner_id, tipo, quantidade, data, ip_impressora,
            patrimonio, responsavel, local_impressora, observacao
        )
        VALUES (?, 'SAIDA', ?, ?, ?, ?, ?, ?, ?)
    """, (
        toner_id,
        quantidade,
        data_atual,
        ip_impressora,
        patrimonio,
        responsavel,
        local_impressora,
        observacao
    ))

    cursor.execute("""
        INSERT INTO trocas (
            toner_id, ip_impressora, patrimonio, quantidade,
            responsavel, data, observacao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        toner_id,
        ip_impressora or "",
        patrimonio,
        quantidade,
        responsavel or "",
        data_atual,
        observacao
    ))

    return novo_estoque


def _modelos_da_descricao(descricao):
    modelos = set()
    for modelo in re.findall(
        r"(?<![A-Z0-9])(?:[A-Z]{1,3}\d{3,5}[A-Z0-9]*|\d{3,5}[A-Z]{1,3}[A-Z0-9]*)(?![A-Z0-9])",
        descricao.upper()
    ):
        modelos.add(modelo)
        familia = re.match(r"([A-Z]{1,3}\d{3,5})", modelo)
        if familia:
            modelos.add(familia.group(1))

    return modelos


def registrar_nivel_toner(
    ip_impressora,
    modelo_impressora,
    cor,
    percentual,
    patrimonio=None,
    local_impressora=None
):
    if not ip_impressora or not cor:
        raise ValueError("IP e cor do toner são obrigatórios.")

    if not isinstance(percentual, int) or not 0 <= percentual <= 100:
        raise ValueError("O nível do toner deve estar entre 0 e 100.")

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("""
            SELECT percentual
            FROM niveis_toner
            WHERE ip_impressora = ? AND cor = ?
        """, (ip_impressora, cor))
        leitura_anterior = cursor.fetchone()

        if (
            not leitura_anterior
            or leitura_anterior[0] > 10
            or percentual < 90
        ):
            _salvar_nivel_toner(
                cursor,
                ip_impressora,
                cor,
                percentual
            )
            conexao.commit()
            return None

        modelos = _modelos_da_descricao(modelo_impressora or "")
        if not modelos:
            conexao.commit()
            return {"status": "modelo_nao_identificado"}

        cursor.execute("""
            SELECT id, marca, codigo, cor, modelos_compativeis
            FROM toners
            WHERE ativo = 1 AND lower(cor) = lower(?)
        """, (cor,))

        correspondencias = []
        for toner in cursor.fetchall():
            modelos_compativeis = _modelos_da_descricao(
                toner[4] or ""
            )
            if modelos.intersection(modelos_compativeis):
                correspondencias.append(toner)

        if not correspondencias:
            conexao.commit()
            return {
                "status": "sem_toner_compativel",
                "modelos": sorted(modelos)
            }

        if len(correspondencias) > 1:
            conexao.commit()
            return {
                "status": "varios_toners_compativeis",
                "modelos": sorted(modelos)
            }

        toner_id, marca, codigo, cor_toner, _ = correspondencias[0]
        observacao = (
            "Baixa automática por troca detectada: "
            f"{leitura_anterior[0]}% para {percentual}% "
            f"(modelo {', '.join(sorted(modelos))})."
        )
        novo_estoque = _registrar_saida_no_cursor(
            cursor,
            toner_id,
            1,
            ip_impressora,
            patrimonio,
            "Monitoramento automático",
            observacao,
            local_impressora
        )
        _salvar_nivel_toner(
            cursor,
            ip_impressora,
            cor,
            percentual
        )
        conexao.commit()

        return {
            "status": "registrada",
            "marca": marca,
            "codigo": codigo,
            "cor": cor_toner,
            "novo_estoque": novo_estoque,
            "nivel_anterior": leitura_anterior[0],
            "nivel_atual": percentual
        }

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def _salvar_nivel_toner(cursor, ip_impressora, cor, percentual):
    cursor.execute("""
        INSERT INTO niveis_toner (
            ip_impressora, cor, percentual, atualizado_em
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ip_impressora, cor) DO UPDATE SET
            percentual = excluded.percentual,
            atualizado_em = excluded.atualizado_em
    """, (
        ip_impressora,
        cor,
        percentual,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ))

def ajustar_estoque_manual(toner_id, acao):
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT estoque
            FROM toners
            WHERE id = ? AND ativo = 1
        """, (toner_id,))

        resultado = cursor.fetchone()

        if not resultado:
            raise ValueError("Toner não encontrado.")

        estoque_atual = int(resultado[0])

        if acao == "entrada":
            novo_estoque = estoque_atual + 1
            tipo = "ENTRADA"

        elif acao == "saida":
            if estoque_atual <= 0:
                raise ValueError("Não há estoque disponível para retirada.")

            novo_estoque = estoque_atual - 1
            tipo = "SAIDA"

        else:
            raise ValueError("Operação inválida.")

        cursor.execute("""
            UPDATE toners
            SET estoque = ?
            WHERE id = ?
        """, (novo_estoque, toner_id))

        data_atual = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO movimentacoes (
                toner_id,
                tipo,
                quantidade,
                data,
                observacao
            )
            VALUES (?, ?, 1, ?, ?)
        """, (
            toner_id,
            tipo,
            data_atual,
            "Ajuste rápido de estoque pela tela"
        ))

        conexao.commit()

        return novo_estoque

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
# ==========================================================
# REGISTRA EVENTO DE IMPRESSORA (OFFLINE/ONLINE)
# ==========================================================

def registrar_evento_impressora(
    ip_impressora,
    patrimonio,
    modelo,
    evento,
    inicio_offline,
    duracao_minutos
):

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        data_registro = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        if evento == "OFFLINE":
            cursor.execute("""
                SELECT 1
                FROM eventos_impressoras
                WHERE ip_impressora = ?
                  AND evento = 'OFFLINE'
                  AND substr(data_registro, 1, 10) = ?
                LIMIT 1
            """, (
                ip_impressora,
                data_registro[:10]
            ))
            if cursor.fetchone():
                conexao.commit()
                return False

        cursor.execute("""
            INSERT INTO eventos_impressoras (
                ip_impressora,
                patrimonio,
                modelo,
                evento,
                inicio_offline,
                data_registro,
                duracao_minutos
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ip_impressora,
            patrimonio,
            modelo,
            evento,
            inicio_offline,
            data_registro,
            duracao_minutos
        ))

        conexao.commit()
        return True

    except Exception:

        conexao.rollback()

        raise

    finally:

        conexao.close()


if __name__ == "__main__":

    criar_banco()

    print(
        "Banco de estoque criado com sucesso."
    )
