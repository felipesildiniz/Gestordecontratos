import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DispositivoMFA",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("segredo", models.CharField(max_length=64)),
                ("confirmado", models.BooleanField(default=False)),
                ("confirmado_em", models.DateTimeField(blank=True, null=True)),
                ("ultimo_passo", models.BigIntegerField(default=0, verbose_name="último passo usado")),
                ("falhas", models.PositiveSmallIntegerField(default=0, verbose_name="códigos errados seguidos")),
                ("bloqueado_ate", models.DateTimeField(blank=True, null=True, verbose_name="bloqueado até")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dispositivo_mfa",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "verificação em duas etapas",
                "verbose_name_plural": "verificações em duas etapas",
            },
        ),
        migrations.CreateModel(
            name="CodigoRecuperacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hash", models.CharField(max_length=64)),
                ("usado_em", models.DateTimeField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="codigos_recuperacao",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "código de recuperação",
                "verbose_name_plural": "códigos de recuperação",
            },
        ),
    ]
