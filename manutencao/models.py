"""Tabelas do app manutencao: histórico do backup externo (E4.4)."""
from django.db import models


class ExecucaoBackup(models.Model):
    """Uma tentativa de backup criptografado para o Google Drive."""

    inicio = models.DateTimeField("início")
    fim = models.DateTimeField(null=True, blank=True)
    origem = models.CharField(max_length=10)  # "agendado" ou "manual"
    sucesso = models.BooleanField(null=True)  # None = em andamento
    mensagem = models.TextField(blank=True)
    arquivo = models.CharField(max_length=120, blank=True)
    bytes = models.BigIntegerField(null=True, blank=True)
    apagados = models.PositiveSmallIntegerField("antigos apagados", default=0)

    class Meta:
        verbose_name = "execução do backup externo"
        verbose_name_plural = "execuções do backup externo"
        ordering = ["-inicio"]
