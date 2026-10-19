"""Tabelas do app accounts.

Usuários e perfis usam as tabelas padrão do Django (decisão D-010). A única
tabela própria é a do bloqueio de login (E4.3, D-030).
"""
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
