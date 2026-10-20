from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BloqueioLogin",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("usuario", models.CharField(max_length=150, unique=True, verbose_name="usuário")),
                ("falhas", models.PositiveIntegerField(default=0, verbose_name="falhas seguidas")),
                (
                    "nivel",
                    models.PositiveSmallIntegerField(default=0, verbose_name="nível de reincidência"),
                ),
                (
                    "bloqueado_ate",
                    models.DateTimeField(blank=True, null=True, verbose_name="bloqueado até"),
                ),
                (
                    "ultima_falha",
                    models.DateTimeField(blank=True, null=True, verbose_name="última falha"),
                ),
                (
                    "ultimo_bloqueio_em",
                    models.DateTimeField(blank=True, null=True, verbose_name="último bloqueio em"),
                ),
                (
                    "avisos_pendentes",
                    models.PositiveIntegerField(
                        default=0, verbose_name="bloqueios ainda não avisados"
                    ),
                ),
            ],
            options={
                "verbose_name": "bloqueio de login",
                "verbose_name_plural": "bloqueios de login",
            },
        ),
    ]
