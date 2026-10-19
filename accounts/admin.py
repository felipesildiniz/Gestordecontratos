from django.contrib import admin
from django.utils import timezone

from . import bloqueio
from .models import BloqueioLogin


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
