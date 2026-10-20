"""Testes do cliente do Google Drive (E4.4) com um Google de mentira. Sem banco."""
import json
import tempfile
import unittest
from pathlib import Path

from . import drive


class GoogleFalso:
    """Registra as chamadas e responde de acordo com um roteiro simples."""

    def __init__(self):
        self.chamadas = []
        self.pasta_existente = False
        self.arquivos = []
        self.falhas_no_bloco = 0
        self.tamanho_guardado = None
        self.recebido = 0
        self.token_status = 200

    def __call__(self, metodo, endereco, cabecalhos=None, corpo=b"", timeout=300):
        self.chamadas.append((metodo, endereco, cabecalhos or {}, corpo))
        if endereco.startswith(drive.ENDERECO_TOKEN):
            if self.token_status != 200:
                return self.token_status, {}, json.dumps({"error": "invalid_grant"}).encode()
            return 200, {}, json.dumps({"access_token": "TOKEN"}).encode()
        if endereco.startswith(drive.ENDERECO_ENVIO):
            return 200, {"location": "https://sessao.exemplo/abc"}, b"{}"
        if endereco.startswith("https://sessao.exemplo/"):
            if self.falhas_no_bloco:
                self.falhas_no_bloco -= 1
                return 503, {}, b""
            inicio, resto = cabecalhos["Content-Range"].split(" ")[1].split("-")
            fim, total = resto.split("/")
            self.recebido += len(corpo)
            if int(fim) + 1 == int(total):
                tam = self.tamanho_guardado if self.tamanho_guardado is not None else int(total)
                return 200, {}, json.dumps({"id": "F1", "name": "x", "size": str(tam)}).encode()
            return 308, {}, b""
        if metodo == "GET" and "files?" in endereco:
            if "mimeType" in endereco:
                achados = [{"id": "PASTA", "name": "p"}] if self.pasta_existente else []
                return 200, {}, json.dumps({"files": achados}).encode()
            return 200, {}, json.dumps({"files": self.arquivos}).encode()
        if metodo == "POST" and endereco.startswith(drive.ENDERECO_API):
            return 200, {}, json.dumps({"id": "PASTA_NOVA"}).encode()
        if metodo == "DELETE":
            return 204, {}, b""
        return 500, {}, b""


class DriveTests(unittest.TestCase):
    def setUp(self):
        self.google = GoogleFalso()
        self.cliente = drive.ClienteDrive("id", "segredo", "refresh", http=self.google,
                                          dormir=lambda s: None)
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def arquivo(self, tamanho):
        caminho = Path(self.dir.name) / "a.enc"
        caminho.write_bytes(b"x" * tamanho)
        return caminho

    def test_token_e_pedido_uma_vez_so(self):
        self.cliente.token()
        self.cliente.token()
        pedidos = [c for c in self.google.chamadas if c[1].startswith(drive.ENDERECO_TOKEN)]
        self.assertEqual(len(pedidos), 1)

    def test_autorizacao_recusada_da_erro_claro_sem_segredos(self):
        self.google.token_status = 400
        with self.assertRaises(drive.ErroDrive) as e:
            self.cliente.token()
        self.assertIn("recusou a autoriza", str(e.exception))
        self.assertNotIn("segredo", str(e.exception))
        self.assertNotIn("refresh", str(e.exception))

    def test_pasta_existente_e_reaproveitada(self):
        self.google.pasta_existente = True
        self.assertEqual(self.cliente.achar_ou_criar_pasta("Backups"), "PASTA")

    def test_pasta_inexistente_e_criada(self):
        self.assertEqual(self.cliente.achar_ou_criar_pasta("Backups"), "PASTA_NOVA")

    def test_nome_de_pasta_com_aspas_e_escapado(self):
        self.cliente.achar_ou_criar_pasta("O'Brien")
        consulta = [c for c in self.google.chamadas if "mimeType" in c[1]][0][1]
        self.assertIn("O%5C%27Brien", consulta)

    def test_envio_em_varios_blocos_confere_tamanho(self):
        original = drive.BLOCO_ENVIO
        drive.BLOCO_ENVIO = 100
        self.addCleanup(setattr, drive, "BLOCO_ENVIO", original)
        resultado = self.cliente.enviar(self.arquivo(250), "gestor.zip.enc", "PASTA")
        self.assertEqual(resultado["id"], "F1")
        self.assertEqual(self.google.recebido, 250)

    def test_envio_pequeno_em_um_bloco(self):
        self.assertEqual(self.cliente.enviar(self.arquivo(10), "n", "P")["id"], "F1")

    def test_tamanho_diferente_no_drive_e_erro(self):
        self.google.tamanho_guardado = 5
        with self.assertRaises(drive.ErroDrive):
            self.cliente.enviar(self.arquivo(10), "n", "P")

    def test_falha_temporaria_do_bloco_e_repetida(self):
        self.google.falhas_no_bloco = 2
        self.assertEqual(self.cliente.enviar(self.arquivo(10), "n", "P")["id"], "F1")

    def test_falha_permanente_do_bloco_da_erro(self):
        self.google.falhas_no_bloco = 10
        with self.assertRaises(drive.ErroDrive):
            self.cliente.enviar(self.arquivo(10), "n", "P")

    def test_arquivo_vazio_nao_e_enviado(self):
        with self.assertRaises(drive.ErroDrive):
            self.cliente.enviar(self.arquivo(0), "n", "P")

    def test_listar_e_apagar(self):
        self.google.arquivos = [{"id": "1", "name": "a"}]
        self.assertEqual(self.cliente.listar("P"), [{"id": "1", "name": "a"}])
        self.cliente.apagar("1")
        self.assertEqual(self.google.chamadas[-1][0], "DELETE")


if __name__ == "__main__":
    unittest.main()
