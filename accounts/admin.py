from django.contrib import admin
from django.utils import timezone

from . import bloqueio, mfa
from .models import BloqueioLogin, DispositivoMFA


@admin.register(BloqueioLogin)
class BloqueioLoginAdmin(admin.ModelAdmin):
    """Lista de bloqueios de login, com a ação de desbloquear (D-030)."""

    list_display = ("usuario", "situacao", "falhas", "nivel", "bloqueado_ate", "ultima_falha")
    search_fields = ("usuario",)
    actions = ["desbloquear"]

    def get_readonly_fields(self, request, obj=None):
        return [campo.name for campo in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="situação")
    def situacao(self, obj):
        bloqueado = obj.bloqueado_ate and obj.bloqueado_ate > timezone.now()
        return "Bloqueado" if bloqueado else "Livre"

    @admin.action(description="Desbloquear os usuários selecionados", permissions=["change"])
    def desbloquear(self, request, queryset):
        total = 0
        for registro in queryset:
            total += bloqueio.desbloquear(registro.usuario)
        self.message_user(request, f"{total} usuário(s) desbloqueado(s).")


@admin.register(DispositivoMFA)
class DispositivoMFAAdmin(admin.ModelAdmin):
    """Quem ativou a verificação em duas etapas, com a ação de redefinir (E4.3b).

    Redefinir apaga o aplicativo e os códigos de recuperação do usuário; na
    próxima entrada ele (se for Admin) precisa configurar tudo de novo. Use
    quando alguém perdeu o celular e os códigos.
    """

    list_display = ("usuario", "confirmado", "confirmado_em", "codigos_sobrando")
    search_fields = ("usuario__username",)
    actions = ["redefinir"]
    fields = ("usuario", "confirmado", "confirmado_em", "falhas", "bloqueado_ate", "criado_em")

    def get_readonly_fields(self, request, obj=None):
        return list(self.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="códigos de recuperação sobrando")
    def codigos_sobrando(self, obj):
        return mfa.codigos_restantes(obj.usuario)

    @admin.action(description="Redefinir a verificação em duas etapas dos selecionados",
                  permissions=["change"])
    def redefinir(self, request, queryset):
        total = 0
        for dispositivo in list(queryset):
            mfa.redefinir(dispositivo.usuario)
            total += 1
        self.message_user(request, f"{total} verificação(ões) redefinida(s).")
