"""Regras de negócio puras: validações e conversões, sem nenhum acesso a dados.

Estas funções não sabem se os pedidos estão num banco de dados, numa lista em
memória ou em um arquivo — só validam e convertem valores. São reaproveitadas
tanto por pedidos_repositorio.py (antes de gravar no banco) quanto pela própria
interface gráfica (para validar o que a pessoa digitou antes de enviar).
"""

import math
import re
import unicodedata
from datetime import datetime


STATUS_DISPONIVEIS = ("Pendente", "Em transporte", "Entregue")


def validar_peso(peso):
    try:
        peso_valido = type(peso) in (int, float) and peso > 0 and math.isfinite(peso)
    except OverflowError:
        peso_valido = False

    if not peso_valido:
        raise ValueError("O peso precisa ser um número finito maior que zero.")


def interpretar_data_cadastro(valor):
    """Lê a data salva; registros antigos podem não ter esse campo."""
    if valor is None:
        return None

    if not isinstance(valor, str):
        raise ValueError("A data de cadastro precisa ser um texto no formato ISO.")

    try:
        momento = datetime.fromisoformat(valor)
    except ValueError as erro:
        raise ValueError("A data de cadastro está inválida.") from erro

    if momento.tzinfo is None or momento.utcoffset() is None:
        raise ValueError("A data de cadastro precisa incluir o fuso horário.")

    return momento


def normalizar_texto_busca(texto):
    """Prepara uma cópia do texto para comparar sem acentos ou maiúsculas."""
    if not isinstance(texto, str):
        raise ValueError("Digite um texto válido para pesquisar.")

    texto_separado = unicodedata.normalize("NFD", texto.casefold())
    texto_sem_acentos = "".join(
        caractere
        for caractere in texto_separado
        if not unicodedata.combining(caractere)
    )
    return " ".join(texto_sem_acentos.split())


def converter_data_consulta(texto):
    """Converte DD/MM/AAAA em uma data e rejeita dias que não existem."""
    if not isinstance(texto, str):
        raise ValueError("Informe uma data no formato DD/MM/AAAA.")

    texto = texto.strip()
    if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", texto):
        raise ValueError("Use o formato DD/MM/AAAA, por exemplo 11/09/2026.")

    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError as erro:
        raise ValueError("Essa data não existe. Confira o dia, o mês e o ano.") from erro
