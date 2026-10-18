"""Linha de comando do backup e da restauração (E4.1).

Lê as configurações do arquivo .env, como o resto do sistema, e usa
manutencao/nucleo.py. Não depende do Django.
Uso: python fazer_backup.py   |   python restaurar_backup.py PASTA_DO_BACKUP
"""
import argparse
import sys
from pathlib import Path

from config.env import carregar_env, texto

from . import nucleo

BASE_DIR = Path(__file__).resolve().parent.parent


def configuracao():
    """Devolve as configurações lidas do .env (ou do ambiente)."""
    carregar_env(BASE_DIR / ".env")
    return {
        "banco": {
            "nome": texto("DB_NOME", "gestor_contratos"),
            "usuario": texto("DB_USUARIO", "gestor"),
            "senha": texto("DB_SENHA"),
            "host": texto("DB_HOST", "localhost"),
            "porta": texto("DB_PORTA", "5432"),
        },
        "pasta_projeto": BASE_DIR,
        "pasta_arquivos": Path(texto("ARQUIVOS_PASTA") or BASE_DIR / "media"),
        "pasta_backup": Path(texto("BACKUP_PASTA") or BASE_DIR / "backups"),
        "pasta_copia": texto("BACKUP_PASTA_COPIA") or None,
        "manter": int(texto("BACKUP_MANTER", "30") or "30"),
        "pg_bin": texto("PG_BIN") or None,
    }


def fazer_backup(argumentos=None):
    cfg = configuracao()
    try:
        r = nucleo.fazer_backup(
            cfg["banco"], cfg["pasta_projeto"], cfg["pasta_arquivos"], cfg["pasta_backup"],
            pasta_copia=cfg["pasta_copia"], manter=cfg["manter"], pg_bin=cfg["pg_bin"],
        )
    except nucleo.ErroBackup as erro:
        print(f"ERRO NO BACKUP: {erro}")
        return 1
    q = r["manifesto"]["quantidade"]
    print(f"Backup concluído: {r['pasta']}")
    print(f"  PDFs: {q['pdfs']} | arquivos do projeto: {q['arquivos_do_projeto']}")
    if r["copia"]:
        print(f"  Cópia em outro lugar: {r['copia']}")
    if r["apagados"]:
        print(f"  Backups antigos apagados: {', '.join(r['apagados'])}")
    for aviso in r["avisos"]:
        print(f"ATENÇÃO: {aviso}")
    # Código 2 = backup local feito, mas com aviso (por exemplo, cópia falhou).
    return 2 if r["avisos"] else 0


def restaurar_backup(argumentos=None):
    p = argparse.ArgumentParser(description="Restaura um backup (por padrão, em um banco novo).")
    p.add_argument("pasta", help="Pasta do backup, por exemplo backups\\2026-10-17_020000")
    p.add_argument("--banco", help="Banco de destino (padrão: <banco>_restaurado).")
    p.add_argument("--pdfs", help="Pasta dos PDFs restaurados (padrão: restauracao\\<backup>\\arquivos).")
    p.add_argument("--projeto", help="Pasta do código restaurado (padrão: restauracao\\<backup>\\projeto).")
    p.add_argument("--so-banco", action="store_true", help="Restaura apenas o banco.")
    p.add_argument("--sobrescrever", action="store_true",
                   help="Permite restaurar por cima de um banco existente (PERIGOSO).")
    a = p.parse_args(argumentos)
    cfg = configuracao()
    destino = a.banco or f"{cfg['banco']['nome']}_restaurado"
    if not a.so_banco:
        base = BASE_DIR / "restauracao" / Path(a.pasta).resolve().name
        a.pdfs = a.pdfs or str(base / "arquivos")
        a.projeto = a.projeto or str(base / "projeto")
    if a.sobrescrever:
        print(f"Isto vai APAGAR e substituir o conteúdo do banco '{destino}'.")
        if input(f"Para continuar, digite o nome do banco ({destino}): ").strip() != destino:
            print("Cancelado.")
            return 1
    try:
        r = nucleo.restaurar_backup(
            a.pasta, cfg["banco"], destino, pasta_arquivos_destino=a.pdfs,
            pasta_projeto_destino=a.projeto, sobrescrever=a.sobrescrever, pg_bin=cfg["pg_bin"],
        )
    except nucleo.ErroBackup as erro:
        print(f"ERRO NA RESTAURAÇÃO: {erro}")
        return 1
    print(f"Restauração concluída no banco '{r['banco']}'. PDFs: {r['pdfs']} | projeto: {r['projeto']}")
    return 0


if __name__ == "__main__":
    sys.exit(fazer_backup())
