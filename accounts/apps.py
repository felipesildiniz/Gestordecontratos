from django.apps import AppConfig
from django.db.models.signals import m2m_changed, post_migrate


def _criar_perfis_apos_migracao(sender, using="default", **kwargs):
    from .perfis import garantir_perfis

    garantir_perfis(using=using)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Contas e perfis"

    def ready(self):
        # Depois de cada "migrate", garante que os perfis existam.
        post_migrate.connect(
            _criar_perfis_apos_migracao,
            sender=self,
            dispatch_uid="accounts.criar_perfis",
        )
        # Bloqueio de login progressivo e aviso na próxima entrada (E4.3).
        from . import sinais  # noqa: F401

        # Quem entra no grupo Admin ganha acesso à área administrativa (P-016).
        from django.contrib.auth import get_user_model

        from .perfis import sincronizar_staff

        m2m_changed.connect(
            sincronizar_staff,
            sender=get_user_model().groups.through,
            dispatch_uid="accounts.sincronizar_staff",
        )
