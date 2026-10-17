from django.apps import AppConfig
from django.db.models.signals import post_migrate


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
