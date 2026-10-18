"""Faz um backup completo (banco, PDFs e código). Uso: python fazer_backup.py"""
import sys

from manutencao.cli import fazer_backup

if __name__ == "__main__":
    sys.exit(fazer_backup())
