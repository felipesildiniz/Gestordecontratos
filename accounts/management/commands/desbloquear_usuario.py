"""Desbloqueia o login de um usuário (E4.3, D-030).

O bloqueio é sempre temporário, mas o administrador pode tirá-lo antes.
Uso: python manage.py desbloquear_usuario --usuario NOME   (ou --todos)
"""
from django.core.management.base import BaseCommand, CommandError

from accounts import bloqueio


class Command(BaseCommand):
    help = "Tira o bloqueio de login de um usuário (ou de todos) e zera a reincidência."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default="", help="Nome de login.")
        parser.add_argument("--todos", action="store_true", help="Desbloqueia todos.")

    def handle(self, *args, **opcoes):
        if not opcoes["todos"] and not opcoes["usuario"].strip():
            raise CommandError("Informe --usuario NOME ou --todos.")
        total = bloqueio.desbloquear(opcoes["usuario"], todos=opcoes["todos"])
        if total:
            self.stdout.write(self.style.SUCCESS(f"{total} registro(s) desbloqueado(s)."))
        else:
            self.stdout.write("Nenhum bloqueio encontrado para desbloquear.")
