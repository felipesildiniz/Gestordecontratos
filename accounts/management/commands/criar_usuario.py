import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.perfis import ADMIN, CONSULTA, garantir_perfis


class Command(BaseCommand):
    help = "Cria um usuário com o perfil Admin ou Consulta."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", required=True, help="Nome de login.")
        parser.add_argument("--perfil", required=True, choices=["admin", "consulta"])
        parser.add_argument("--nome", default="", help="Nome completo (opcional).")
        parser.add_argument("--email", default="", help="E-mail (opcional).")
        parser.add_argument(
            "--senha",
            default=None,
            help="Evite usar: a senha ficaria registrada no histórico do terminal. "
            "Se omitida, ela é pedida de forma segura.",
        )

    def handle(self, *args, **opcoes):
        Usuario = get_user_model()
        login = opcoes["usuario"].strip()
        if not login:
            raise CommandError("O nome de usuário não pode ficar vazio.")
        if Usuario.objects.filter(username=login).exists():
            raise CommandError(f"O usuário '{login}' já existe.")

        senha = opcoes["senha"]
        if senha is None:
            senha = getpass.getpass("Senha: ")
            if senha != getpass.getpass("Repita a senha: "):
                raise CommandError("As senhas não conferem.")

        usuario = Usuario(
            username=login, first_name=opcoes["nome"], email=opcoes["email"]
        )
        try:
            validate_password(senha, usuario)
        except ValidationError as erro:
            raise CommandError("Senha recusada: " + " ".join(erro.messages)) from erro

        perfil = ADMIN if opcoes["perfil"] == "admin" else CONSULTA
        grupos = garantir_perfis()
        # Admin precisa de acesso à área /admin/ para gerenciar usuários.
        usuario.is_staff = perfil == ADMIN
        usuario.set_password(senha)
        usuario.save()
        usuario.groups.add(grupos[perfil])
        self.stdout.write(
            self.style.SUCCESS(f"Usuário '{login}' criado com o perfil {perfil}.")
        )
