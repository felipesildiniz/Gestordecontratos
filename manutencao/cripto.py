"""Criptografia dos backups enviados para fora do Railway (E4.4, D-029).

Usa o programa `age` (https://age-encryption.org). O servidor só tem a chave
PÚBLICA (começa com "age1"): consegue criptografar, mas NÃO consegue abrir o
arquivo. A chave privada fica só com o responsável. Para abrir um backup no
computador dele:  age -d -i chave-privada.txt -o backup.zip backup.zip.age
"""
import re
import shutil
import subprocess
from pathlib import Path

# Alfabeto bech32 (sem 1, b, i, o) e 58 caracteres depois de "age1".
PADRAO_CHAVE_PUBLICA = re.compile(r"^age1[023456789acdefghjklmnpqrstuvwxyz]{58}$")


class ErroCripto(Exception):
    """Falha ao criptografar (mensagem em português, sem segredos)."""


def chave_publica_valida(chave):
    return bool(PADRAO_CHAVE_PUBLICA.match((chave or "").strip()))


def criptografar(origem, destino, chave_publica):
    """Criptografa `origem` para `destino` (.age) com a chave pública dada."""
    chave = (chave_publica or "").strip()
    if not chave_publica_valida(chave):
        raise ErroCripto(
            "A chave pública do backup (BACKUP_CHAVE_PUBLICA) está ausente ou inválida; "
            "ela deve começar com 'age1'."
        )
    programa = shutil.which("age")
    if not programa:
        raise ErroCripto("O programa 'age' não está instalado no servidor.")
    destino = Path(destino)
    try:
        r = subprocess.run(
            [programa, "-r", chave, "-o", str(destino), str(origem)],
            capture_output=True, text=True, timeout=3600,
        )
    except (OSError, subprocess.SubprocessError) as erro:
        raise ErroCripto(f"Não foi possível rodar o age ({type(erro).__name__}).") from erro
    if r.returncode != 0 or not destino.is_file() or destino.stat().st_size == 0:
        raise ErroCripto(f"A criptografia falhou: {r.stderr.strip()[:200]}")
    return destino
