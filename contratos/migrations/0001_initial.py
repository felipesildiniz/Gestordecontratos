import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def carga_inicial_modalidades(apps, schema_editor):
    Modalidade = apps.get_model("contratos", "Modalidade")
    for sigla, nome in [
        ("AD", "Adesão de Ata"),
        ("CE", "Concorrência Eletrônica"),
        ("CH", "Chamada Pública"),
        ("PE", "Pregão Eletrônico"),
        ("INEX", "Inexigibilidade"),
    ]:
        Modalidade.objects.get_or_create(sigla=sigla, defaults={"nome": nome, "ativo": True})


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Modalidade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sigla", models.CharField(max_length=10, unique=True)),
                ("nome", models.CharField(max_length=80)),
                ("ativo", models.BooleanField(default=True)),
            ],
            options={"verbose_name_plural": "modalidades", "ordering": ["sigla"]},
        ),
        migrations.CreateModel(
            name="Contratado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo_pessoa", models.CharField(choices=[("PF", "Pessoa física"), ("PJ", "Pessoa jurídica")], max_length=2)),
                ("documento", models.CharField(max_length=14, unique=True)),
                ("razao_social", models.CharField(max_length=200)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name_plural": "contratados", "ordering": ["razao_social"]},
        ),
        migrations.CreateModel(
            name="Contrato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequencial", models.PositiveIntegerField()),
                ("numero_modalidade", models.PositiveSmallIntegerField()),
                ("ano", models.PositiveSmallIntegerField()),
                ("numero_formatado", models.CharField(editable=False, max_length=30, unique=True)),
                ("data_assinatura", models.DateField()),
                ("data_publicacao", models.DateField(blank=True, null=True)),
                ("data_inicio_vigencia", models.DateField()),
                ("data_fim_vigencia", models.DateField()),
                ("data_fim_vigencia_original", models.DateField(editable=False)),
                ("objeto", models.TextField()),
                ("valor", models.DecimalField(decimal_places=2, max_digits=15)),
                ("informacoes_complementares", models.TextField(blank=True)),
                ("envolve_saude", models.BooleanField(default=False)),
                ("envolve_educacao", models.BooleanField(default=False)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "atualizado_por",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "contratado",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="contratos.contratado"),
                ),
                (
                    "criado_por",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modalidade",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="contratos.modalidade"),
                ),
            ],
            options={
                "verbose_name_plural": "contratos",
                "ordering": ["-ano", "-sequencial"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("ano", "sequencial"),
                        name="contrato_ano_sequencial_unico",
                        violation_error_message="Já existe um contrato com este N° (sequencial) neste ano.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("valor__gte", 0)),
                        name="contrato_valor_nao_negativo",
                        violation_error_message="O valor não pode ser negativo.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("data_fim_vigencia__gte", models.F("data_inicio_vigencia"))),
                        name="contrato_fim_apos_inicio",
                        violation_error_message="A vigência final não pode ser anterior ao início da vigência.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("data_fim_vigencia__gte", models.F("data_assinatura"))),
                        name="contrato_fim_apos_assinatura",
                        violation_error_message="A vigência final não pode ser anterior à data de assinatura.",
                    ),
                ],
            },
        ),
        migrations.RunPython(carga_inicial_modalidades, migrations.RunPython.noop),
    ]
