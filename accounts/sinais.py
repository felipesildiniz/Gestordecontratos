"""Liga o bloqueio de login aos sinais de entrada do Django (E4.3)."""
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from django.utils import timezone

from .bloqueio import pegar_avisos, registrar_falha, registrar_sucesso


@receiver(user_login_failed, dispatch_uid="accounts.bloqueio.falha")
def ao_falhar(sender, credentials=None, **kwargs):
    registrar_falha((credentials or {}).get("username"))


@receiver(user_logged_in, dispatch_uid="accounts.bloqueio.sucesso")
def ao_entrar(sender, request=None, user=None, **kwargs):
    if user is None:
        return
    nome = user.get_username()
    registrar_sucesso(nome)
    # O aviso só é dado (e descontado) quando há onde mostrá-lo.
    if request is None or not hasattr(request, "_messages"):
        return
    quantos, quando = pegar_avisos(nome)
    if quantos:
        vezes = "1 vez" if quantos == 1 else f"{quantos} vezes"
        momento = timezone.localtime(quando).strftime("%d/%m/%Y %H:%M") if quando else ""
        messages.warning(
            request,
            f"Atenção: desde a sua última entrada, esta conta foi bloqueada {vezes} por "
            f"tentativas de senha erradas (última em {momento}). Se não foi você, troque "
            "a sua senha e avise o administrador do sistema.",
        )
