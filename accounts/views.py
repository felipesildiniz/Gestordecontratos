from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe

from . import mfa
from .bloqueio import bloqueio_ativo
from .models import DispositivoMFA
from .perfis import eh_admin, perfil_do_usuario


class EntrarView(LoginView):
    """Tela de entrada que mostra o aviso de bloqueio temporário (D-030)."""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        registro = bloqueio_ativo(form.data.get("username", ""))
        if registro:
            return render(
                self.request, "bloqueado.html", {"ate": registro.bloqueado_ate}, status=403
            )
        return super().form_invalid(form)


@login_required
def home(request):
    return render(request, "home.html", {"perfil": perfil_do_usuario(request.user)})


# --- Verificação em duas etapas (E4.3b) -------------------------------------

def _so_admin(request):
    return eh_admin(request.user)


@login_required
def mfa_configurar(request):
    """Primeiro uso: mostra o QR, confere o 1º código e entrega os códigos de recuperação."""
    if not _so_admin(request):
        return redirect("home")
    usuario = request.user
    if mfa.dispositivo_confirmado(usuario):
        return redirect("home")
    disp, _ = DispositivoMFA.objects.get_or_create(
        usuario=usuario, defaults={"segredo": mfa.gerar_segredo()}
    )
    erro = False
    if request.method == "POST":
        if mfa.conferir_totp(disp, request.POST.get("codigo", "")):
            disp.confirmado = True
            disp.confirmado_em = timezone.now()
            disp.save(update_fields=["confirmado", "confirmado_em"])
            codigos = mfa.gerar_codigos(usuario)
            request.session[mfa.CHAVE_SESSAO] = True
            return render(request, "mfa_codigos.html", {"codigos": codigos})
        erro = True
    uri = mfa.uri_otpauth(usuario.get_username(), disp.segredo)
    contexto = {
        "erro": erro,
        "segredo": mfa.segredo_legivel(disp.segredo),
        "qr": mark_safe(mfa.svg_qr(uri)),
    }
    return render(request, "mfa_configurar.html", contexto, status=200)


@login_required
def mfa_verificar(request):
    """Pede o código do aplicativo (ou um código de recuperação) a cada entrada."""
    if not _so_admin(request):
        return redirect("home")
    usuario = request.user
    disp = mfa.dispositivo_confirmado(usuario)
    if disp is None:
        return redirect("mfa_configurar")
    if request.session.get(mfa.CHAVE_SESSAO):
        return redirect("home")
    erro = False
    ate = mfa.bloqueado_ate(disp)
    if request.method == "POST" and not ate:
        resultado = mfa.verificar_segundo_fator(usuario, request.POST.get("codigo", ""))
        if resultado in ("ok", "recuperacao"):
            request.session[mfa.CHAVE_SESSAO] = True
            if resultado == "recuperacao":
                restantes = mfa.codigos_restantes(usuario)
                messages.warning(
                    request,
                    f"Você entrou com um código de recuperação (restam {restantes}). "
                    "Cada código vale uma única vez; se estiver acabando, peça ao "
                    "administrador para redefinir a sua verificação e gerar novos.",
                )
            return redirect("home")
        ate = mfa.bloqueado_ate(mfa.dispositivo_confirmado(usuario))
        erro = True
    return render(
        request, "mfa_verificar.html", {"erro": erro, "bloqueado_ate": ate},
        status=403 if ate else 200,
    )
