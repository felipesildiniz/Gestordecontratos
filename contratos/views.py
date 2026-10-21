from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ContratoForm
from .models import Contrato
from .validadores import so_digitos


class ListaContratos(PermissionRequiredMixin, ListView):
    permission_required = "contratos.view_contrato"
    model = Contrato
    template_name = "contratos/lista.html"
    paginate_by = 25

    def get_queryset(self):
        qs = Contrato.objects.select_related("contratado", "modalidade")
        q = self.request.GET.get("q", "").strip()
        if q:
            filtro = (
                Q(numero_formatado__icontains=q)
                | Q(objeto__icontains=q)
                | Q(contratado__razao_social__icontains=q)
            )
            digitos = so_digitos(q)
            if digitos:
                filtro |= Q(contratado__documento__contains=digitos)
            qs = qs.filter(filtro)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "").strip()
        return contexto


class DetalheContrato(PermissionRequiredMixin, DetailView):
    permission_required = "contratos.view_contrato"
    model = Contrato
    template_name = "contratos/detalhe.html"

    def get_queryset(self):
        return Contrato.objects.select_related("contratado", "modalidade")


class NovoContrato(PermissionRequiredMixin, CreateView):
    permission_required = "contratos.add_contrato"
    model = Contrato
    form_class = ContratoForm
    template_name = "contratos/form.html"

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        form.instance.atualizado_por = self.request.user
        resposta = super().form_valid(form)
        messages.success(self.request, f"Contrato {self.object.numero_formatado} cadastrado.")
        return resposta

    def get_success_url(self):
        return reverse("contratos:detalhe", args=[self.object.pk])


class EditarContrato(PermissionRequiredMixin, UpdateView):
    permission_required = "contratos.change_contrato"
    model = Contrato
    form_class = ContratoForm
    template_name = "contratos/form.html"

    def form_valid(self, form):
        form.instance.atualizado_por = self.request.user
        resposta = super().form_valid(form)
        messages.success(self.request, f"Contrato {self.object.numero_formatado} atualizado.")
        return resposta

    def get_success_url(self):
        return reverse("contratos:detalhe", args=[self.object.pk])


class ExcluirContrato(PermissionRequiredMixin, DeleteView):
    permission_required = "contratos.delete_contrato"
    model = Contrato
    template_name = "contratos/excluir.html"
    success_url = reverse_lazy("contratos:lista")

    def form_valid(self, form):
        numero = self.object.numero_formatado
        resposta = super().form_valid(form)
        messages.success(self.request, f"Contrato {numero} excluído.")
        return resposta
