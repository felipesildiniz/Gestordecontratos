from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExecucaoBackup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("inicio", models.DateTimeField(verbose_name="início")),
                ("fim", models.DateTimeField(blank=True, null=True)),
                ("origem", models.CharField(max_length=10)),
                ("sucesso", models.BooleanField(null=True)),
                ("mensagem", models.TextField(blank=True)),
                ("arquivo", models.CharField(blank=True, max_length=120)),
                ("bytes", models.BigIntegerField(blank=True, null=True)),
                ("apagados", models.PositiveSmallIntegerField(default=0, verbose_name="antigos apagados")),
            ],
            options={
                "verbose_name": "execução do backup externo",
                "verbose_name_plural": "execuções do backup externo",
                "ordering": ["-inicio"],
            },
        ),
    ]
