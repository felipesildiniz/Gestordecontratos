"""Tabelas do app accounts.

Usuários e perfis usam as tabelas padrão do Django (decisão D-010). A única
tabela própria é a do bloqueio de login (E4.3, D-030).
"""
from django.conf import settings
from django.db import models


class BloqueioLogin(models.Model):
    """Controle do bloqueio temporário e progressivo de um nome de usuário.

    Guarda as senhas erradas seguidas, o nível de reincidência e até quando o
    login está bloqueado. Existe também para nomes que não são de nenhum
    usuário, para que a tela se comporte igual e não revele quem existe.
    """

    usuario = models.CharField("usuário", max_length=150, unique=True)
    falhas = models.PositiveIntegerField("falhas seguidas", default=0)
    nivel = models.PositiveSmallIntegerField("nível de reincidência", default=0)
    bloqueado_ate = models.DateTimeField("bloqueado até", null=True, blank=True)
    ultima_falha = models.DateTimeField("última falha", null=True, blank=True)
    ultimo_bloqueio_em = models.DateTimeField("último bloqueio em", null=True, blank=True)
    avisos_pendentes = models.PositiveIntegerField("bloqueios ainda não avisados", default=0)

    class Meta:
        verbose_name = "bloqueio de login"
        verbose_name_plural = "bloqueios de login"

    def __str__(self):
        return self.usuario


class DispositivoMFA(models.Model):
    """Aplicativo autenticador de um usuário (E4.3b). Só vale depois de confirmado."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dispositivo_mfa"
    )
    segredo = models.CharField(max_length=64)
    confirmado = models.BooleanField(default=False)
    confirmado_em = models.DateTimeField(null=True, blank=True)
    ultimo_passo = models.BigIntegerField("último passo usado", default=0)
    falhas = models.PositiveSmallIntegerField("códigos errados seguidos", default=0)
    bloqueado_ate = models.DateTimeField("bloqueado até", null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "verificação em duas etapas"
        verbose_name_plural = "verificações em duas etapas"

    def __str__(self):
        return f"MFA de {self.usuario}"


class CodigoRecuperacao(models.Model):
    """Código de recuperação de uso único (guarda só o hash)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="codigos_recuperacao"
    )
    hash = models.CharField(max_length=64)
    usado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "código de recuperação"
        verbose_name_plural = "códigos de recuperação"
