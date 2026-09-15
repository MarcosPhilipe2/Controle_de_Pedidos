"""Autenticação e gestão de usuários: login, papéis (admin/operador) e senhas.

Só usa a biblioteca padrão do Python (hashlib + secrets), sem depender de pacotes
externos como bcrypt, para manter a instalação simples nos computadores da
empresa. O algoritmo é PBKDF2-HMAC-SHA256, recomendado pelo NIST para este uso.
"""

import hashlib
import secrets
from datetime import datetime

from db import conexao


PAPEIS_DISPONIVEIS = ("admin", "operador")
ITERACOES_PBKDF2 = 200_000
TAMANHO_SAL = 16


class ErroAutenticacao(Exception):
    """Erro esperado de login/gestão de usuários (mensagem própria para exibir)."""


def _gerar_hash_senha(senha, sal=None):
    if sal is None:
        sal = secrets.token_bytes(TAMANHO_SAL)
    derivado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERACOES_PBKDF2)
    return f"pbkdf2_sha256${ITERACOES_PBKDF2}${sal.hex()}${derivado.hex()}"


def _verificar_senha(senha, hash_armazenado):
    try:
        algoritmo, iteracoes_texto, sal_hex, hash_hex = hash_armazenado.split("$")
    except ValueError:
        return False
    if algoritmo != "pbkdf2_sha256":
        return False

    sal = bytes.fromhex(sal_hex)
    derivado_esperado = hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), sal, int(iteracoes_texto)
    )
    return secrets.compare_digest(derivado_esperado.hex(), hash_hex)


def validar_senha_forte(senha):
    if not isinstance(senha, str) or len(senha) < 8:
        raise ErroAutenticacao("A senha precisa ter pelo menos 8 caracteres.")


def validar_nome_usuario(nome_usuario):
    if not isinstance(nome_usuario, str) or not nome_usuario.strip():
        raise ErroAutenticacao("O nome de usuário não pode ficar vazio.")
    if " " in nome_usuario.strip():
        raise ErroAutenticacao("O nome de usuário não pode conter espaços.")


def criar_usuario(nome_usuario, nome_completo, senha, papel, criado_por=None):
    """Cria um usuário novo. Levanta ErroAutenticacao com mensagem amigável se algo for inválido."""
    validar_nome_usuario(nome_usuario)
    nome_usuario = nome_usuario.strip()

    if not isinstance(nome_completo, str) or not nome_completo.strip():
        raise ErroAutenticacao("Informe o nome completo do usuário.")

    if papel not in PAPEIS_DISPONIVEIS:
        raise ErroAutenticacao("Papel inválido. Use 'admin' ou 'operador'.")

    validar_senha_forte(senha)
    hash_senha = _gerar_hash_senha(senha)

    with conexao() as conn:
        existente = conn.execute(
            "SELECT id FROM usuarios WHERE nome_usuario = ?", (nome_usuario,)
        ).fetchone()
        if existente is not None:
            raise ErroAutenticacao(f"Já existe um usuário com o nome '{nome_usuario}'.")

        conn.execute(
            """
            INSERT INTO usuarios (nome_usuario, nome_completo, hash_senha, papel, ativo, criado_em)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (
                nome_usuario,
                nome_completo.strip(),
                hash_senha,
                papel,
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )


def autenticar(nome_usuario, senha):
    """Confere usuário/senha e devolve o registro do usuário (sem o hash) se estiver correto.

    Levanta ErroAutenticacao com uma mensagem genérica em caso de falha, sem
    revelar se o problema foi o usuário ou a senha (prática recomendada).
    """
    if not isinstance(nome_usuario, str) or not isinstance(senha, str):
        raise ErroAutenticacao("Usuário ou senha inválidos.")

    with conexao() as conn:
        linha = conn.execute(
            "SELECT * FROM usuarios WHERE nome_usuario = ?", (nome_usuario.strip(),)
        ).fetchone()

    mensagem_erro = "Usuário ou senha inválidos."
    if linha is None:
        raise ErroAutenticacao(mensagem_erro)
    if not linha["ativo"]:
        raise ErroAutenticacao("Este usuário está desativado. Fale com um administrador.")
    if not _verificar_senha(senha, linha["hash_senha"]):
        raise ErroAutenticacao(mensagem_erro)

    return {
        "id": linha["id"],
        "nome_usuario": linha["nome_usuario"],
        "nome_completo": linha["nome_completo"],
        "papel": linha["papel"],
    }


def listar_usuarios():
    with conexao() as conn:
        linhas = conn.execute(
            "SELECT id, nome_usuario, nome_completo, papel, ativo, criado_em "
            "FROM usuarios ORDER BY nome_completo"
        ).fetchall()
    return [dict(linha) for linha in linhas]


def definir_ativo(id_usuario, ativo):
    with conexao() as conn:
        cursor = conn.execute(
            "UPDATE usuarios SET ativo = ? WHERE id = ?", (1 if ativo else 0, id_usuario)
        )
        if cursor.rowcount == 0:
            raise ErroAutenticacao("Usuário não encontrado.")


def redefinir_senha(id_usuario, nova_senha):
    validar_senha_forte(nova_senha)
    hash_senha = _gerar_hash_senha(nova_senha)
    with conexao() as conn:
        cursor = conn.execute(
            "UPDATE usuarios SET hash_senha = ? WHERE id = ?", (hash_senha, id_usuario)
        )
        if cursor.rowcount == 0:
            raise ErroAutenticacao("Usuário não encontrado.")


def contar_admins_ativos():
    with conexao() as conn:
        (quantidade,) = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE papel = 'admin' AND ativo = 1"
        ).fetchone()
    return quantidade
