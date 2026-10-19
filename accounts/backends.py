from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from .bloqueio import esta_bloqueado


class ModelBackendComBloqueio(ModelBackend):
    """Autenticação padrão, mas recusa o usuário enquanto o login está bloqueado (D-030).

    Vale para qualquer porta de entrada (tela de entrada e /admin/login/).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("username")
        if username and esta_bloqueado(username):
            raise PermissionDenied("Login bloqueado temporariamente.")
        return super().authenticate(request, username=username, password=password, **kwargs)
