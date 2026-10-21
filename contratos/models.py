"""Tabelas do cadastro de contratos (E5, DATABASE.md)."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Modalidade(models.Model):
    sigla = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=80)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["sigla"]
        verbose_name_plural = "modalidades"

    def __str__(self):
        return f"{self.sigla} — {self.nome}"


class Contratado(models.Model):
    tipo_pessoa = models.CharField(
        max_length=2, choices=[("PF", "Pessoa física"), ("PJ", "Pessoa jurídica")]
    )
    documento = models.CharField(max_length=14, unique=True)
    razao_social = models.CharField(max_length=200)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["razao_social"]
        verbose_name_plural = "contratados"

    def __str__(self):
        return self.razao_social


class Contrato(models.Model):
    sequencial = models.PositiveIntegerField()
    modalidade = models.ForeignKey(Modalidade, on_delete=models.PROTECT)
    numero_modalidade = models.PositiveSmallIntegerField()
    ano = models.PositiveSmallIntegerField()
    numero_formatado = models.CharField(max_length=30, unique=True, editable=False)
    data_assinatura = models.DateField()
    data_publicacao = models.DateField(null=True, blank=True)
    data_inicio_vigencia = models.DateField()
    data_fim_vigencia = models.DateField()
    data_fim_vigencia_original = models.DateField(editable=False)
    objeto = models.TextField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    contratado = models.ForeignKey(Contratado, on_delete=models.PROTECT)
    informacoes_complementares = models.TextField(blank=True)
    envolve_saude = models.BooleanField(default=False)
    envolve_educacao = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        ordering = ["-ano", "-sequencial"]
        verbose_name_plural = "contratos"
        constraints = [
            models.UniqueConstraint(
                fields=["ano", "sequencial"],
                name="contrato_ano_sequencial_unico",
                violation_error_message="Já existe um contrato com este N° (sequencial) neste ano.",
            ),
            models.CheckConstraint(
                condition=Q(valor__gte=0),
                name="contrato_valor_nao_negativo",
                violation_error_message="O valor não pode ser negativo.",
            ),
            models.CheckConstraint(
                condition=Q(data_fim_vigencia__gte=F("data_inicio_vigencia")),
                name="contrato_fim_apos_inicio",
                violation_error_message="A vigência final não pode ser anterior ao início da vigência.",
            ),
            models.CheckConstraint(
                condition=Q(data_fim_vigencia__gte=F("data_assinatura")),
                name="contrato_fim_apos_assinatura",
                violation_error_message="A vigência final não pode ser anterior à data de assinatura.",
            ),
        ]

    def __str__(self):
        return self.numero_formatado

    def montar_numero(self):
        return f"{self.sequencial}.{self.modalidade.sigla}.{self.numero_modalidade}/{self.ano}"

    def save(self, *args, **kwargs):
        self.numero_formatado = self.montar_numero()
        if not self.data_fim_vigencia_original:
            # Cópia da vigência na assinatura; nunca muda depois (prorrogações mudam só a vigente).
            self.data_fim_vigencia_original = self.data_fim_vigencia
        super().save(*args, **kwargs)
