import io
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class ConferirRestauracaoTests(SimpleTestCase):
    def test_sem_arquivo_nao_faz_nada(self):
        saida = io.StringIO()
        call_command("conferir_restauracao", "--zip", "", stdout=saida)
        self.assertIn("nada a fazer", saida.getvalue())

    def test_arquivo_inexistente_nao_faz_nada(self):
        saida = io.StringIO()
        call_command("conferir_restauracao", "--zip", "/nao/existe.zip", stdout=saida)
        self.assertIn("nada a fazer", saida.getvalue())

    def test_zip_sem_manifesto_e_recusado(self):
        import zipfile

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "ruim.zip"
            with zipfile.ZipFile(caminho, "w") as z:
                z.writestr("qualquer.txt", "x")
            with self.assertRaises(CommandError):
                call_command("conferir_restauracao", "--zip", str(caminho), stdout=io.StringIO())
