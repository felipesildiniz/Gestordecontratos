"""Leitura simples de variáveis de ambiente a partir de um arquivo .env.

Não depende do Django, para poder ser usada (e testada) isoladamente.
"""
import os
from pathlib import Path


def carregar_env(caminho):
    """Lê linhas CHAVE=valor de um arquivo .env e as coloca em os.environ.

    - Variáveis que já existem no ambiente não são sobrescritas.
    - Linhas vazias e linhas que começam com # são ignoradas.
    - Aspas simples ou duplas ao redor do valor são removidas.
    - Aceita arquivos salvos pelo Bloco de Notas do Windows (com BOM).
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        os.environ.setdefault(chave, valor)


def texto(nome, padrao=""):
    """Devolve o valor da variável como texto."""
    return os.environ.get(nome, padrao)


def booleano(nome, padrao=False):
    """Devolve True para 1, true, sim, yes ou on (sem diferenciar maiúsculas)."""
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "sim", "yes", "on")


def lista(nome, padrao=""):
    """Devolve uma lista a partir de valores separados por vírgula."""
    bruto = os.environ.get(nome, padrao)
    return [item.strip() for item in bruto.split(",") if item.strip()]
