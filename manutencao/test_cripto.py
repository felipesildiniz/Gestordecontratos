"""Testes da criptografia do backup externo (E4.4). O teste de ida e volta usa o
programa `age` de verdade e é pulado se ele não estiver instalado."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import cripto

TEM_AGE = bool(shutil.which("age") and shutil.which("age-keygen"))
CHAVE_VALIDA = "age1" + "q" * 58


class ChavePublicaTests(unittest.TestCase):
    def test_chaves_validas_e_invalidas(self):
        self.assertTrue(cripto.chave_publica_valida(CHAVE_VALIDA))
        self.assertTrue(cripto.chave_publica_valida("  " + CHAVE_VALIDA + "\n"))
        for ruim in ("", None, "age1curta", "AGE1" + "q" * 58, "age-secret-key-1" + "q" * 58,
                     "age1" + "b" * 58, "ssh-ed25519 AAAA"):
            self.assertFalse(cripto.chave_publica_valida(ruim), ruim)

    def test_chave_invalida_nao_roda_nada(self):
        with mock.patch.object(cripto.subprocess, "run") as rodar:
            with self.assertRaises(cripto.ErroCripto):
                cripto.criptografar("a", "b", "lixo")
            rodar.assert_not_called()

    def test_sem_o_programa_age_da_erro_claro(self):
        with mock.patch.object(cripto.shutil, "which", return_value=None):
            with self.assertRaises(cripto.ErroCripto) as e:
                cripto.criptografar("a", "b", CHAVE_VALIDA)
        self.assertIn("age", str(e.exception))

    def test_falha_do_age_vira_erro_sem_arquivo_vazio(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "x.age"
            falha = subprocess.CompletedProcess([], 1, "", "boom")
            with mock.patch.object(cripto.shutil, "which", return_value="/usr/bin/age"), \
                 mock.patch.object(cripto.subprocess, "run", return_value=falha):
                with self.assertRaises(cripto.ErroCripto) as e:
                    cripto.criptografar("a", destino, CHAVE_VALIDA)
        self.assertIn("boom", str(e.exception))


@unittest.skipUnless(TEM_AGE, "age/age-keygen não instalados")
class IdaEVoltaTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.pasta = Path(self.dir.name)
        chaves = subprocess.run(["age-keygen"], capture_output=True, text=True, check=True)
        self.privada = self.pasta / "chave.txt"
        self.privada.write_text(chaves.stdout)
        self.publica = re.search(r"age1[a-z0-9]{58}", chaves.stdout + chaves.stderr).group(0)

    def test_criptografa_e_so_a_chave_privada_abre(self):
        original = self.pasta / "backup.zip"
        original.write_bytes(b"dados do backup " * 1000)
        cifrado = self.pasta / "backup.zip.age"
        cripto.criptografar(original, cifrado, self.publica)
        self.assertNotIn(b"dados do backup", cifrado.read_bytes())
        aberto = self.pasta / "aberto.zip"
        subprocess.run(["age", "-d", "-i", str(self.privada), "-o", str(aberto), str(cifrado)],
                       check=True)
        self.assertEqual(aberto.read_bytes(), original.read_bytes())

    def test_outra_chave_nao_abre(self):
        original = self.pasta / "b.zip"
        original.write_bytes(b"segredo")
        cifrado = self.pasta / "b.zip.age"
        cripto.criptografar(original, cifrado, self.publica)
        outra = subprocess.run(["age-keygen"], capture_output=True, text=True, check=True)
        arq = self.pasta / "outra.txt"
        arq.write_text(outra.stdout)
        r = subprocess.run(["age", "-d", "-i", str(arq), str(cifrado)], capture_output=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
