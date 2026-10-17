from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .perfis import perfil_do_usuario


@login_required
def home(request):
    return render(request, "home.html", {"perfil": perfil_do_usuario(request.user)})
