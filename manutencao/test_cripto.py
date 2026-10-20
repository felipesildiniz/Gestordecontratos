"""Testes da criptografia dos backups (E4.4). Não precisam de banco."""
import base64
import os
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization

from . import cripto

SENHA = "senha-de-teste-123"


class CriptoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.privada, cls.publica = cripto.gerar_par_de_chaves(SENHA, bits=2048)
        cls.outra_privada, cls.outra_publica = cripto.gerar_par_de_chaves(SENHA, bits=2048)

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.pasta = Path(self.dir.name)

    def _cifrar(self, conteudo, bloco=cripto.BLOCO, publica=None):
        origem = self.pasta / "o.zip"
        origem.write_bytes(conteudo)
        destino = self.pasta / "o.zip.enc"
        cripto.criptografar_arquivo(
            origem, destino, cripto.publica_do_texto((publica or self.publica).decode()), bloco
        )
        return destino

    def _abrir(self, enc, privada=None, senha=SENHA):
        saida = self.pasta / "saida.zip"
        cripto.descriptografar_arquivo(enc, saida, privada or self.privada, senha)
        return saida.read_bytes()

    def test_ida_e_volta_em_varios_blocos(self):
        conteudo = os.urandom(1000)
        enc = self._cifrar(conteudo, bloco=64)
        self.assertEqual(self._abrir(enc), conteudo)

    def test_arquivo_vazio_e_tamanho_exato_de_bloco(self):
        for conteudo in (b"", b"x" * 64, b"x" * 128):
            enc = self._cifrar(conteudo, bloco=64)
            self.assertEqual(self._abrir(enc), conteudo)

    def test_conteudo_nao_aparece_no_arquivo_cifrado(self):
        enc = self._cifrar(b"CONTRATO-SECRETO" * 50)
        self.assertNotIn(b"CONTRATO-SECRETO", enc.read_bytes())

    def test_dois_envios_do_mesmo_arquivo_ficam_diferentes(self):
        a = self._cifrar(b"igual").read_bytes()
        b = self._cifrar(b"igual").read_bytes()
        self.assertNotEqual(a, b)

    def test_senha_errada_nao_abre(self):
        enc = self._cifrar(b"dados")
        with self.assertRaises(cripto.ErroCripto):
            self._abrir(enc, senha="errada")

    def test_outra_chave_privada_nao_abre(self):
        enc = self._cifrar(b"dados")
        with self.assertRaises(cripto.ErroCripto):
            self._abrir(enc, privada=self.outra_privada)

    def test_adulteracao_e_detectada_e_nao_deixa_saida(self):
        enc = self._cifrar(b"dados" * 100, bloco=64)
        bruto = bytearray(enc.read_bytes())
        bruto[-5] ^= 0x01
        enc.write_bytes(bytes(bruto))
        with self.assertRaises(cripto.ErroCripto):
            self._abrir(enc)
        self.assertFalse((self.pasta / "saida.zip").exists())

    def test_arquivo_cortado_e_detectado(self):
        enc = self._cifrar(b"dados" * 100, bloco=64)
        bruto = enc.read_bytes()
        # Corta exatamente depois do 1º bloco: sem o bloco final marcado.
        enc.write_bytes(bruto[: len(bruto) // 2])
        with self.assertRaises(cripto.ErroCripto):
            self._abrir(enc)

    def test_dados_sobrando_no_fim_sao_detectados(self):
        enc = self._cifrar(b"dados")
        enc.write_bytes(enc.read_bytes() + b"lixo")
        with self.assertRaises(cripto.ErroCripto):
            self._abrir(enc)

    def test_arquivo_que_nao_e_backup(self):
        (self.pasta / "x.enc").write_bytes(b"qualquer coisa")
        with self.assertRaises(cripto.ErroCripto):
            self._abrir(self.pasta / "x.enc")

    def test_chave_publica_aceita_pem_ou_base64(self):
        pem = self.publica.decode()
        cripto.publica_do_texto(pem)
        cripto.publica_do_texto(base64.b64encode(pem.encode()).decode())
        cripto.publica_do_texto(pem.replace("\n", "\\n"))

    def test_chave_publica_invalida_ou_vazia(self):
        for ruim in ("", "   ", "lixo", "-----BEGIN PUBLIC KEY-----\nabc\n-----END PUBLIC KEY-----"):
            with self.assertRaises(cripto.ErroCripto):
                cripto.publica_do_texto(ruim)

    def test_chave_privada_gerada_e_protegida_por_senha(self):
        with self.assertRaises(TypeError):
            serialization.load_pem_private_key(self.privada, None)
        with self.assertRaises(cripto.ErroCripto):
            cripto.gerar_par_de_chaves("")


if __name__ == "__main__":
    unittest.main()
