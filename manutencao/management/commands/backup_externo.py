"""Faz agora um backup criptografado e o envia ao Google Drive (E4.4).

Uso: python manage.py backup_externo
Precisa das variáveis GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
e BACKUP_CHAVE_PUBLICA (veja INSTALACAO_NUVEM.md).
"""
from django.core.management.base import BaseCommand, CommandError

from manutencao import externo


class Command(BaseCommand):
    help = "Gera o backup, criptografa e envia ao Google Drive, aplicando a retenção."

    def handle(self, *args, **opcoes):
        try:
            r = externo.executar("manual")
        except externo.ErroExterno as erro:
            raise CommandError(str(erro))
        if not r.sucesso:
            raise CommandError(r.mensagem)
        self.stdout.write(self.style.SUCCESS(
            f"Enviado: {r.arquivo} ({r.bytes} bytes); antigos apagados: {r.apagados}."))
