from datetime import date
from decimal import Decimal

from django import forms
from django.db import transaction
from django.db.models import Max, Q

from .models import Contratado, Contrato, Modalidade
from .validadores import documento_valido, formatar_documento, so_digitos


def proximo_sequencial(ano):
    """Próximo N° do ano (o sequencial reinicia a cada ano)."""
    atual = Contrato.objects.filter(ano=ano).aggregate(m=Max("sequencial"))["m"]
    return (atual or 0) + 1


def _data():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class ContratoForm(forms.ModelForm):
    documento_contratado = forms.CharField(label="CPF ou CNPJ do contratado", max_length=20)
    razao_social_contratado = forms.CharField(
        label="Contratado (razão social ou nome)", max_length=200
    )

    class Meta:
        model = Contrato
        fields = [
            "sequencial", "modalidade", "numero_modalidade", "ano",
            "data_assinatura", "data_publicacao", "data_inicio_vigencia", "data_fim_vigencia",
            "objeto", "valor", "informacoes_complementares", "envolve_saude", "envolve_educacao",
        ]
        labels = {
            "sequencial": "N° (sequencial do ano)",
            "modalidade": "Modalidade",
            "numero_modalidade": "Número da modalidade (1 a 100)",
            "ano": "Ano",
            "data_assinatura": "Data de assinatura",
            "data_publicacao": "Data de publicação (opcional)",
            "data_inicio_vigencia": "Início da vigência",
            "data_fim_vigencia": "Vigência final",
            "objeto": "Objeto",
            "valor": "Valor (R$)",
            "informacoes_complementares": "Informações complementares (opcional)",
            "envolve_saude": "Envolve saúde",
            "envolve_educacao": "Envolve educação",
        }
        widgets = {
            "data_assinatura": _data(),
            "data_publicacao": _data(),
            "data_inicio_vigencia": _data(),
            "data_fim_vigencia": _data(),
            "objeto": forms.Textarea(attrs={"rows": 3}),
            "informacoes_complementares": forms.Textarea(attrs={"rows": 3}),
        }

    field_order = [
        "sequencial", "modalidade", "numero_modalidade", "ano",
        "data_assinatura", "data_publicacao", "data_inicio_vigencia", "data_fim_vigencia",
        "objeto", "valor", "documento_contratado", "razao_social_contratado",
        "informacoes_complementares", "envolve_saude", "envolve_educacao",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filtro = Q(ativo=True)
        if self.instance.pk:
            filtro |= Q(pk=self.instance.modalidade_id)
            self.initial.setdefault(
                "documento_contratado", formatar_documento(self.instance.contratado.documento)
            )
            self.initial.setdefault("razao_social_contratado", self.instance.contratado.razao_social)
        else:
            ano = date.today().year
            self.initial.setdefault("ano", ano)
            self.initial.setdefault("sequencial", proximo_sequencial(ano))
        self.fields["modalidade"].queryset = Modalidade.objects.filter(filtro)
        self.fields["modalidade"].empty_label = "Selecione"
        self.fields["numero_modalidade"].min_value = 1

    def clean_numero_modalidade(self):
        n = self.cleaned_data["numero_modalidade"]
        if not 1 <= n <= 100:
            raise forms.ValidationError("Informe um número de 1 a 100.")
        return n

    def clean_sequencial(self):
        n = self.cleaned_data["sequencial"]
        if n < 1:
            raise forms.ValidationError("O N° deve ser 1 ou maior.")
        return n

    def clean_ano(self):
        ano = self.cleaned_data["ano"]
        if not 1990 <= ano <= 2100:
            raise forms.ValidationError("Informe um ano entre 1990 e 2100.")
        return ano

    def clean_valor(self):
        valor = self.cleaned_data["valor"]
        if valor < Decimal("0"):
            raise forms.ValidationError("O valor não pode ser negativo.")
        return valor

    def clean_documento_contratado(self):
        bruto = self.cleaned_data["documento_contratado"]
        if not documento_valido(bruto):
            raise forms.ValidationError("CPF ou CNPJ inválido. Confira os números.")
        return so_digitos(bruto)

    def clean_razao_social_contratado(self):
        nome = self.cleaned_data["razao_social_contratado"].strip()
        if not nome:
            raise forms.ValidationError("Informe o contratado.")
        return nome

    @transaction.atomic
    def save(self, commit=True):
        documento = self.cleaned_data["documento_contratado"]
        nome = self.cleaned_data["razao_social_contratado"]
        contratado, criado = Contratado.objects.get_or_create(
            documento=documento,
            defaults={"tipo_pessoa": documento_valido(documento), "razao_social": nome},
        )
        if not criado and contratado.razao_social != nome:
            contratado.razao_social = nome
            contratado.save()
        self.instance.contratado = contratado
        return super().save(commit=commit)
