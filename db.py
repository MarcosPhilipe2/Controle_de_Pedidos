"""Camada de banco de dados: conexão SQLite, esquema e migração dos dados antigos.

Este módulo substitui o armazenamento anterior baseado em ``pedidos.json``.
O SQLite passa a cuidar das operações de leitura e escrita de forma transacional,
sem a necessidade de regravar o arquivo inteiro a cada alteração.

Nesta versão, o banco é propositalmente local. Quando o programa é executado
como script, ``pedidos.db`` fica na pasta do projeto; quando é empacotado como
executável pelo PyInstaller, o banco fica ao lado do arquivo .exe.

Para um cenário futuro com vários computadores acessando os mesmos dados ao
mesmo tempo, a evolução recomendada é usar um banco servidor (por exemplo,
PostgreSQL) ou uma API centralizada, em vez de compartilhar o arquivo SQLite
diretamente por uma pasta de rede.
"""

import json
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def pasta_aplicacao():
    """Retorna a pasta persistente usada pelo aplicativo.

    No modo de desenvolvimento, usa a pasta dos arquivos Python. No executável
    gerado pelo PyInstaller, usa a pasta onde o .exe foi colocado.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PASTA_PROJETO = pasta_aplicacao()
ARQUIVO_PEDIDOS_JSON_ANTIGO = PASTA_PROJETO / "pedidos.json"


def caminho_banco_dados():
    """Retorna o caminho do banco SQLite local do aplicativo."""
    return PASTA_PROJETO / "pedidos.db"


ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_usuario TEXT NOT NULL UNIQUE,
    nome_completo TEXT NOT NULL,
    hash_senha TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('admin', 'operador')),
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    cidade_destino TEXT NOT NULL,
    peso_kg REAL NOT NULL CHECK (peso_kg > 0),
    status TEXT NOT NULL CHECK (status IN ('Pendente', 'Em transporte', 'Entregue')),
    criado_em TEXT NOT NULL,
    criado_por TEXT,
    atualizado_em TEXT,
    atualizado_por TEXT
);
"""


@contextmanager
def conexao():
    """Abre uma conexão de curta duração, já configurada, e garante o fechamento.

    WAL (Write-Ahead Logging) melhora a concorrência entre leituras e escritas
    dentro do uso local do aplicativo. ``busy_timeout`` faz uma operação de
    escrita aguardar um pouco antes de falhar caso o banco esteja ocupado.
    """
    caminho = caminho_banco_dados()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho, timeout=30)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar_banco():
    """Cria as tabelas (se necessário) e importa pedidos.json antigo uma única vez."""
    with conexao() as conn:
        conn.executescript(ESQUEMA_SQL)

    _migrar_pedidos_json_se_necessario()


def _migrar_pedidos_json_se_necessario():
    """Importa os pedidos do antigo pedidos.json para o banco, uma única vez.

    Só faz algo se: o arquivo antigo existe, tem pedidos, e a tabela pedidos no
    banco novo ainda está vazia (evita duplicar dados em execuções futuras).
    """
    if not ARQUIVO_PEDIDOS_JSON_ANTIGO.exists():
        return

    with conexao() as conn:
        (quantidade_atual,) = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()
        if quantidade_atual > 0:
            return

        try:
            with ARQUIVO_PEDIDOS_JSON_ANTIGO.open("r", encoding="utf-8-sig") as arquivo:
                pedidos_antigos = json.load(arquivo)
        except (OSError, json.JSONDecodeError):
            return

        if not pedidos_antigos:
            return

        for pedido in pedidos_antigos:
            conn.execute(
                """
                INSERT INTO pedidos
                    (id, cliente, cidade_destino, peso_kg, status, criado_em, criado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido.get("id"),
                    pedido.get("cliente"),
                    pedido.get("cidade_destino"),
                    pedido.get("peso_kg"),
                    pedido.get("status"),
                    pedido.get("criado_em") or datetime.now().astimezone().isoformat(timespec="seconds"),
                    "migracao_dados_antigos",
                ),
            )


def banco_tem_usuarios():
    with conexao() as conn:
        (quantidade,) = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()
    return quantidade > 0
