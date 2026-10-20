"""Apaga a verificação em duas etapas de um usuário (E4.3b, D-030).

Para quando um Admin perdeu o celular e os códigos de recuperação e não há
outro Admin para redefinir em /admin/. Na próxima entrada, o usuário configura
o aplicativo de novo.
Uso: python manage.py redefinir_mfa --usuario NOME
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts import mfa


class Command(BaseCommand):
    help = "Redefine a verificação em duas etapas (aplicativo e códigos) de um usuário."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", required=True, help="Nome de login.")

    def handle(self, *args, **opcoes):
        try:
            usuario = get_user_model().objects.get(username=opcoes["usuario"].strip())
        except get_user_model().DoesNotExist:
            raise CommandError(f"O usuário '{opcoes['usuario']}' não existe.")
        total = mfa.redefinir(usuario)
        if total:
            self.stdout.write(self.style.SUCCESS(f"Verificação de '{usuario.username}' redefinida."))
        else:
            self.stdout.write("Esse usuário não tinha verificação em duas etapas.")
