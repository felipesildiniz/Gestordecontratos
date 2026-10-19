from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "entrar/",
        views.EntrarView.as_view(),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
]
