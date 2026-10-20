from django.urls import path

from . import web

urlpatterns = [
    path("", web.backup, name="backup"),
    path("externo/", web.backup_externo, name="backup_externo"),
]
