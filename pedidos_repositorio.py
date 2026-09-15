"""Repositório de pedidos: todas as operações de leitura/escrita no banco SQLite.

Cada função abre sua própria transação curta (via db.conexao()), evitando o
modelo antigo de carregar e regravar todo o arquivo ``pedidos.json`` a cada
alteração. As operações ficam centralizadas e persistidas no SQLite local.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from db import caminho_banco_dados, conexao
from regras_pedidos import (
    STATUS_DISPONIVEIS,
    interpretar_data_cadastro,
    normalizar_texto_busca,
    validar_peso,
)


def pasta_backups():
    """Mantém os backups em uma pasta ao lado do banco de dados local."""
    return caminho_banco_dados().parent / "backups"


def pasta_exportacoes():
    return caminho_banco_dados().parent / "exportacoes"


class PedidoNaoEncontrado(ValueError):
    """Levantado quando um id de pedido não existe."""


def _linha_para_dict(linha):
    return dict(linha)


def criar_pedido(cliente, cidade_destino, peso_kg, usuario=None):
    if not isinstance(cliente, str) or not cliente.strip():
        raise ValueError("O nome do cliente não pode ficar vazio.")
    if not isinstance(cidade_destino, str) or not cidade_destino.strip():
        raise ValueError("A cidade de destino não pode ficar vazia.")
    validar_peso(peso_kg)

    agora = datetime.now().astimezone().isoformat(timespec="seconds")
    with conexao() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pedidos
                (cliente, cidade_destino, peso_kg, status, criado_em, criado_por)
            VALUES (?, ?, ?, 'Pendente', ?, ?)
            """,
            (cliente.strip(), cidade_destino.strip(), peso_kg, agora, usuario),
        )
        novo_id = cursor.lastrowid

    return obter_pedido_por_id(novo_id)


def obter_pedido_por_id(identificador):
    if type(identificador) is not int:
        raise ValueError("O id precisa ser um número inteiro.")

    with conexao() as conn:
        linha = conn.execute(
            "SELECT * FROM pedidos WHERE id = ?", (identificador,)
        ).fetchone()

    return _linha_para_dict(linha) if linha is not None else None


def listar_pedidos():
    with conexao() as conn:
        linhas = conn.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
    return [_linha_para_dict(linha) for linha in linhas]


def editar_pedido(identificador, cliente, cidade_destino, peso_kg, usuario=None):
    if not isinstance(cliente, str) or not cliente.strip():
        raise ValueError("O nome do cliente não pode ficar vazio.")
    if not isinstance(cidade_destino, str) or not cidade_destino.strip():
        raise ValueError("A cidade de destino não pode ficar vazia.")
    validar_peso(peso_kg)

    agora = datetime.now().astimezone().isoformat(timespec="seconds")
    with conexao() as conn:
        cursor = conn.execute(
            """
            UPDATE pedidos
               SET cliente = ?, cidade_destino = ?, peso_kg = ?,
                   atualizado_em = ?, atualizado_por = ?
             WHERE id = ?
            """,
            (cliente.strip(), cidade_destino.strip(), peso_kg, agora, usuario, identificador),
        )
        if cursor.rowcount == 0:
            raise PedidoNaoEncontrado("Pedido não encontrado.")

    return obter_pedido_por_id(identificador)


def alterar_status(identificador, novo_status, usuario=None):
    if novo_status not in STATUS_DISPONIVEIS:
        raise ValueError("Status inválido. Use Pendente, Em transporte ou Entregue.")

    agora = datetime.now().astimezone().isoformat(timespec="seconds")
    with conexao() as conn:
        cursor = conn.execute(
            """
            UPDATE pedidos
               SET status = ?, atualizado_em = ?, atualizado_por = ?
             WHERE id = ?
            """,
            (novo_status, agora, usuario, identificador),
        )
        if cursor.rowcount == 0:
            raise PedidoNaoEncontrado("Pedido não encontrado.")

    return obter_pedido_por_id(identificador)


def excluir_pedido(identificador):
    with conexao() as conn:
        cursor = conn.execute("DELETE FROM pedidos WHERE id = ?", (identificador,))
        if cursor.rowcount == 0:
            raise PedidoNaoEncontrado("Pedido não encontrado.")


def buscar_por_texto(texto):
    termo_busca = normalizar_texto_busca(texto)
    if not termo_busca:
        raise ValueError("Digite um texto válido para pesquisar.")

    return [
        pedido
        for pedido in listar_pedidos()
        if termo_busca in normalizar_texto_busca(pedido["cliente"])
        or termo_busca in normalizar_texto_busca(pedido["cidade_destino"])
    ]


def filtrar_por_status(status):
    if status not in STATUS_DISPONIVEIS:
        raise ValueError("Status inválido. Use Pendente, Em transporte ou Entregue.")

    with conexao() as conn:
        linhas = conn.execute(
            "SELECT * FROM pedidos WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
    return [_linha_para_dict(linha) for linha in linhas]


def consultar_por_periodo(data_inicial, data_final):
    if data_final < data_inicial:
        raise ValueError("A data final não pode ser anterior à data inicial.")

    encontrados = []
    for pedido in listar_pedidos():
        momento = interpretar_data_cadastro(pedido.get("criado_em"))
        if momento is not None and data_inicial <= momento.date() <= data_final:
            encontrados.append(pedido)
    return encontrados


def contar_pedidos_sem_data():
    return sum(pedido.get("criado_em") is None for pedido in listar_pedidos())


def gerar_resumo():
    pedidos = listar_pedidos()
    quantidade_por_status = {
        status: sum(pedido["status"] == status for pedido in pedidos)
        for status in STATUS_DISPONIVEIS
    }

    try:
        peso_total = sum(pedido["peso_kg"] for pedido in pedidos)
    except OverflowError:
        peso_total = None

    return {
        "total_pedidos": len(pedidos),
        "quantidade_por_status": quantidade_por_status,
        "peso_total_kg": peso_total,
    }


def _preparar_texto_csv(texto):
    inicio_de_formula = texto.lstrip().startswith(("=", "+", "-", "@"))
    inicio_de_controle = texto.startswith(("\t", "\r", "\n"))
    if inicio_de_formula or inicio_de_controle:
        return "'" + texto
    return texto


def exportar_csv():
    pedidos = listar_pedidos()
    if not pedidos:
        raise ValueError("Não há pedidos para exportar.")

    pasta = pasta_exportacoes()
    pasta.mkdir(exist_ok=True)
    nome_arquivo = datetime.now().strftime("pedidos_%Y%m%d_%H%M%S_%f.csv")
    caminho_csv = pasta / nome_arquivo
    arquivo_criado = False

    try:
        with caminho_csv.open("x", encoding="utf-8-sig", newline="") as arquivo:
            arquivo_criado = True
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow([
                "ID", "Cliente", "Cidade de destino", "Peso (kg)", "Status",
                "Data de cadastro (ISO 8601)", "Criado por", "Atualizado por",
            ])

            for pedido in pedidos:
                escritor.writerow([
                    pedido["id"],
                    _preparar_texto_csv(pedido["cliente"]),
                    _preparar_texto_csv(pedido["cidade_destino"]),
                    str(pedido["peso_kg"]).replace(".", ","),
                    pedido["status"],
                    pedido.get("criado_em") or "",
                    pedido.get("criado_por") or "",
                    pedido.get("atualizado_por") or "",
                ])
    except (OSError, ValueError, csv.Error) as erro:
        if arquivo_criado:
            try:
                caminho_csv.unlink()
            except OSError:
                pass
        if isinstance(erro, csv.Error):
            raise ValueError("Não foi possível formatar os dados em CSV.") from erro
        raise

    return caminho_csv


def fazer_backup(usuario=None):
    """Salva uma cópia (JSON) de todos os pedidos atuais, com data e hora no nome."""
    pasta = pasta_backups()
    pasta.mkdir(exist_ok=True)
    nome_arquivo = datetime.now().strftime("pedidos_backup_%Y%m%d_%H%M%S.json")
    caminho_backup = pasta / nome_arquivo

    pedidos = listar_pedidos()
    conteudo = {
        "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "gerado_por": usuario,
        "pedidos": pedidos,
    }

    arquivo_temporario = caminho_backup.with_suffix(".tmp")
    with arquivo_temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    arquivo_temporario.replace(caminho_backup)

    return caminho_backup


def listar_backups():
    """Devolve os arquivos de backup existentes, do mais recente para o mais antigo."""
    pasta = pasta_backups()
    if not pasta.exists():
        return []
    return sorted(pasta.glob("pedidos_backup_*.json"), reverse=True)


def ler_backup(caminho_backup):
    with Path(caminho_backup).open("r", encoding="utf-8") as arquivo:
        conteudo = json.load(arquivo)
    return conteudo.get("pedidos", [])


def restaurar_backup(caminho_backup):
    """Substitui todos os pedidos atuais pelos do arquivo de backup informado.

    Faz isso dentro de uma única transação: se algo falhar no meio, nada é
    alterado (o banco fica exatamente como estava antes da tentativa).
    """
    pedidos_backup = ler_backup(caminho_backup)

    with conexao() as conn:
        conn.execute("DELETE FROM pedidos")
        for pedido in pedidos_backup:
            conn.execute(
                """
                INSERT INTO pedidos
                    (id, cliente, cidade_destino, peso_kg, status,
                     criado_em, criado_por, atualizado_em, atualizado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido.get("id"),
                    pedido.get("cliente"),
                    pedido.get("cidade_destino"),
                    pedido.get("peso_kg"),
                    pedido.get("status"),
                    pedido.get("criado_em"),
                    pedido.get("criado_por"),
                    pedido.get("atualizado_em"),
                    pedido.get("atualizado_por"),
                ),
            )

    return len(pedidos_backup)
