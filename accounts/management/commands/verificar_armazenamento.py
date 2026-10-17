"""Confere se a pasta dos PDFs (MEDIA_ROOT) sobrevive a novas implantações.

No Railway o disco do contêiner é apagado a cada deploy; só um volume
persiste. Este comando grava um arquivo-marca na pasta dos PDFs na primeira vez
e, nas execuções seguintes, informa desde quando ele existe. Se a marca
sumir depois de um deploy, a pasta NÃO é persistente.
"""
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

NOME_MARCA = ".marca-armazenamento"


class Command(BaseCommand):
    help = "Verifica se a pasta dos PDFs é gravável e persistente."

    def handle(self, *args, **opcoes):
        pasta = settings.MEDIA_ROOT
        try:
            pasta.mkdir(parents=True, exist_ok=True)
            marca = pasta / NOME_MARCA
            if marca.exists():
                criada = marca.read_text(encoding="utf-8").strip()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Armazenamento OK em {pasta}: marca criada em {criada} "
                        "e ainda presente (persistente)."
                    )
                )
            else:
                agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
                marca.write_text(agora, encoding="utf-8")
                self.stdout.write(
                    self.style.WARNING(
                        f"Armazenamento em {pasta}: marca criada agora ({agora}). "
                        "Se no próximo deploy ela aparecer de novo como 'criada agora', "
                        "a pasta não é persistente."
                    )
                )
        except OSError as erro:
            raise CommandError(f"Não foi possível gravar em {pasta}: {erro}") from erro
