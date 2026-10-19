from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render

from .bloqueio import bloqueio_ativo
from .perfis import perfil_do_usuario


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
