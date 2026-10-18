"""Testes da tela de backup (E4.2 item 4, D-027).

Precisam do Django e do PostgreSQL (rodam com: python manage.py test). O teste
que gera o .zip de verdade é pulado se o pg_dump não estiver instalado.
"""
import io
import tempfile
import zipfile
from pathlib import Path
from unittest import mock, skipUnless

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from config.env import texto

from . import nucleo, web

SENHA = "Senha-Forte-123!"
Usuario = get_user_model()


def _pg_disponivel():
    try:
        for ferramenta in ("pg_dump", "pg_restore", "psql"):
            nucleo.localizar_ferramenta(ferramenta, texto("PG_BIN") or None)
        return True
    except nucleo.ErroBackup:
        return False


class TelaDeBackupAcessoTests(TestCase):
    def setUp(self):
        call_command("criar_usuario", usuario="ana", perfil="admin", senha=SENHA)
        call_command("criar_usuario", usuario="beto", perfil="consulta", senha=SENHA)

    def test_anonimo_vai_para_o_login(self):
        r = self.client.get(reverse("backup"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith(reverse("login")))

    def test_anonimo_nao_gera_backup_por_post(self):
        r = self.client.post(reverse("backup"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith(reverse("login")))

    def test_consulta_recebe_403_no_get_e_no_post(self):
        self.client.force_login(Usuario.objects.get(username="beto"))
        self.assertEqual(self.client.get(reverse("backup")).status_code, 403)
        with mock.patch.object(nucleo, "fazer_backup") as fazer:
            self.assertEqual(self.client.post(reverse("backup")).status_code, 403)
            fazer.assert_not_called()

    def test_admin_ve_a_pagina_sem_gerar_nada(self):
        self.client.force_login(Usuario.objects.get(username="ana"))
        with mock.patch.object(nucleo, "fazer_backup") as fazer:
            r = self.client.get(reverse("backup"))
            fazer.assert_not_called()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Gerar e baixar backup")

    def test_link_do_backup_aparece_so_para_admin(self):
        self.client.force_login(Usuario.objects.get(username="ana"))
        self.assertContains(self.client.get(reverse("home")), reverse("backup"))
        self.client.force_login(Usuario.objects.get(username="beto"))
        self.assertNotContains(self.client.get(reverse("home")), reverse("backup"))


class TelaDeBackupGeracaoTests(TestCase):
    def setUp(self):
        call_command("criar_usuario", usuario="ana", perfil="admin", senha=SENHA)
        self.client.force_login(Usuario.objects.get(username="ana"))

    def test_falha_do_backup_mostra_o_erro_e_nao_deixa_lixo(self):
        pastas_antes = set(Path(tempfile.gettempdir()).glob("backup-gestor-*"))
        with mock.patch.object(nucleo, "fazer_backup",
                               side_effect=nucleo.ErroBackup("pg_dump quebrou")):
            r = self.client.post(reverse("backup"))
        self.assertEqual(r.status_code, 500)
        self.assertContains(r, "pg_dump quebrou", status_code=500)
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("backup-gestor-*")), pastas_antes)

    def test_backup_simultaneo_e_recusado(self):
        self.assertTrue(web._em_andamento.acquire(blocking=False))
        try:
            with mock.patch.object(nucleo, "fazer_backup") as fazer:
                r = self.client.post(reverse("backup"))
                fazer.assert_not_called()
            self.assertEqual(r.status_code, 409)
            self.assertContains(r, "Já existe um backup", status_code=409)
        finally:
            web._em_andamento.release()

    @skipUnless(_pg_disponivel(), "pg_dump/pg_restore/psql não instalados")
    def test_gera_zip_com_banco_pdfs_e_manifesto_sem_env(self):
        with tempfile.TemporaryDirectory() as midia:
            (Path(midia) / "2026").mkdir()
            (Path(midia) / "2026" / "contrato.pdf").write_bytes(b"%PDF-1.4 teste")
            pastas_antes = set(Path(tempfile.gettempdir()).glob("backup-gestor-*"))
            with override_settings(MEDIA_ROOT=Path(midia)):
                r = self.client.post(reverse("backup"))
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r["Content-Type"], "application/zip")
                self.assertIn("attachment; filename=\"backup-gestor-", r["Content-Disposition"])
                corpo = b"".join(r.streaming_content)
                r.close()
        with zipfile.ZipFile(io.BytesIO(corpo)) as z:
            nomes = z.namelist()
            self.assertEqual(len(nomes), 3, nomes)
            self.assertTrue(any(n.endswith("/banco.dump") for n in nomes))
            self.assertTrue(any(n.endswith("/arquivos.zip") for n in nomes))
            self.assertTrue(any(n.endswith("/manifest.json") for n in nomes))
            self.assertFalse(any("projeto" in n or ".env" in n for n in nomes))
            with tempfile.TemporaryDirectory() as destino:
                z.extractall(destino)
                pasta = next(Path(destino).iterdir())
                self.assertEqual(nucleo.verificar_backup(pasta), [])
                with zipfile.ZipFile(pasta / "arquivos.zip") as pdfs:
                    self.assertEqual(pdfs.namelist(), ["2026/contrato.pdf"])
        # A pasta temporária some depois do envio.
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("backup-gestor-*")), pastas_antes)
