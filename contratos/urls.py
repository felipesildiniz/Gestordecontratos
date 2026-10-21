from django.urls import path

from . import views

app_name = "contratos"

urlpatterns = [
    path("", views.ListaContratos.as_view(), name="lista"),
    path("novo/", views.NovoContrato.as_view(), name="novo"),
    path("<int:pk>/", views.DetalheContrato.as_view(), name="detalhe"),
    path("<int:pk>/editar/", views.EditarContrato.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.ExcluirContrato.as_view(), name="excluir"),
]
