"""Restaura um backup. Uso: python restaurar_backup.py PASTA_DO_BACKUP [--banco NOME]"""
import sys

from manutencao.cli import restaurar_backup

if __name__ == "__main__":
    sys.exit(restaurar_backup())
