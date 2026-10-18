from django.urls import path

from . import web

urlpatterns = [
    path("", web.backup, name="backup"),
]
