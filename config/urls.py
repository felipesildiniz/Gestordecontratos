from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Gestor de Contratos — Administração"
admin.site.site_title = "Gestor de Contratos"
admin.site.index_title = "Usuários e perfis"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("backup/", include("manutencao.urls")),
    path("", include("accounts.urls")),
]
