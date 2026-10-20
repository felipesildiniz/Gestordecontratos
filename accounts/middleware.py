"""Exige a verificação em duas etapas de todo Admin (E4.3b, D-030).

Enquanto o Admin não confirmar o código na sessão atual, qualquer página fora
da própria verificação, da saída e dos arquivos estáticos leva para ela. Quem
ainda não configurou o aplicativo é levado à configuração.
"""
from django.shortcuts import redirect

from . import mfa
from .perfis import eh_admin

LIBERADOS = ("/mfa/", "/sair/", "/static/")


class ExigirMFAParaAdmin:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = request.user
        if (
            usuario.is_authenticated
            and eh_admin(usuario)
            and not request.session.get(mfa.CHAVE_SESSAO)
            and not request.path.startswith(LIBERADOS)
        ):
            destino = "mfa_verificar" if mfa.dispositivo_confirmado(usuario) else "mfa_configurar"
            return redirect(destino)
        return self.get_response(request)
