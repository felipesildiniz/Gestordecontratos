"""Testes da E4: login, perfis Admin/Consulta e criação de usuários.

Rodam com:  python manage.py test
Precisam do PostgreSQL configurado no .env. O usuário do banco precisa da
permissão CREATEDB, porque o Django cria um banco temporário só para os testes.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from config.env import booleano, carregar_env, lista, texto

from .perfis import ADMIN, CONSULTA, perfil_do_usuario

Usuario = get_user_model()
SENHA = "Senha-Forte-123!"


def criar_usuario(login, perfil):
    call_command("criar_usuario", usuario=login, perfil=perfil, senha=SENHA)
    return Usuario.objects.get(username=login)


class PerfisExistemTests(TestCase):
    def test_grupos_admin_e_consulta_existem_apos_migrate(self):
        nomes = set(Group.objects.values_list("name", flat=True))
        self.assertIn(ADMIN, nomes)
        self.assertIn(CONSULTA, nomes)

    def test_admin_gerencia_usuarios_e_consulta_nao_tem_permissoes(self):
        # Garante os perfis mesmo que o sinal de migração não tenha rodado.
        from .perfis import garantir_perfis

        garantir_perfis()
        admin = Group.objects.get(name=ADMIN)
        consulta = Group.objects.get(name=CONSULTA)
        codigos = set(admin.permissions.values_list("codename", flat=True))
        self.assertEqual(
            codigos, {"add_user", "change_user", "delete_user", "view_user"}
        )
        self.assertEqual(consulta.permissions.count(), 0)

    def test_garantir_perfis_pode_rodar_varias_vezes(self):
        from .perfis import garantir_perfis

        garantir_perfis()
        garantir_perfis()
        self.assertEqual(Group.objects.filter(name=ADMIN).count(), 1)
        self.assertEqual(Group.objects.filter(name=CONSULTA).count(), 1)


class PerfilDoUsuarioTests(TestCase):
    def test_admin(self):
        self.assertEqual(perfil_do_usuario(criar_usuario("ana", "admin")), ADMIN)

    def test_consulta(self):
        self.assertEqual(
            perfil_do_usuario(criar_usuario("beto", "consulta")), CONSULTA
        )

    def test_usuario_sem_perfil(self):
        usuario = Usuario.objects.create_user("sem.perfil", password=SENHA)
        self.assertIsNone(perfil_do_usuario(usuario))

    def test_superusuario_conta_como_admin(self):
        usuario = Usuario.objects.create_superuser("root", password=SENHA)
        self.assertEqual(perfil_do_usuario(usuario), ADMIN)


class LoginTests(TestCase):
    def setUp(self):
        criar_usuario("ana", "admin")

    def test_pagina_de_login_abre(self):
        resposta = self.client.get(reverse("login"))
        self.assertEqual(resposta.status_code, 200)

    def test_inicio_exige_login(self):
        resposta = self.client.get(reverse("home"))
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("login")))

    def test_login_correto_leva_ao_inicio(self):
        resposta = self.client.post(
            reverse("login"), {"username": "ana", "password": SENHA}
        )
        self.assertRedirects(resposta, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_com_senha_errada_nao_autentica(self):
        resposta = self.client.post(
            reverse("login"), {"username": "ana", "password": "errada"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inicio_mostra_o_perfil(self):
        self.client.login(username="ana", password=SENHA)
        resposta = self.client.get(reverse("home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["perfil"], ADMIN)

    def test_sair_encerra_a_sessao(self):
        self.client.login(username="ana", password=SENHA)
        resposta = self.client.post(reverse("logout"))
        self.assertRedirects(resposta, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sair_por_get_nao_e_permitido(self):
        self.client.login(username="ana", password=SENHA)
        resposta = self.client.get(reverse("logout"))
        self.assertEqual(resposta.status_code, 405)


class AreaAdministrativaTests(TestCase):
    def test_admin_acessa_lista_de_usuarios(self):
        criar_usuario("ana", "admin")
        self.client.login(username="ana", password=SENHA)
        resposta = self.client.get("/admin/auth/user/")
        self.assertEqual(resposta.status_code, 200)

    def test_consulta_nao_acessa_area_administrativa(self):
        criar_usuario("beto", "consulta")
        self.client.login(username="beto", password=SENHA)
        resposta = self.client.get("/admin/auth/user/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/login/", resposta.url)


class CriarUsuarioComandoTests(TestCase):
    def test_admin_recebe_grupo_e_acesso_staff(self):
        usuario = criar_usuario("ana", "admin")
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.groups.filter(name=ADMIN).exists())

    def test_consulta_recebe_grupo_e_nao_e_staff(self):
        usuario = criar_usuario("beto", "consulta")
        self.assertFalse(usuario.is_staff)
        self.assertTrue(usuario.groups.filter(name=CONSULTA).exists())

    def test_usuario_repetido_e_recusado(self):
        criar_usuario("ana", "admin")
        with self.assertRaises(CommandError):
            call_command("criar_usuario", usuario="ana", perfil="admin", senha=SENHA)

    def test_senha_fraca_e_recusada_e_nada_e_criado(self):
        with self.assertRaises(CommandError):
            call_command("criar_usuario", usuario="caio", perfil="consulta", senha="12345")
        self.assertFalse(Usuario.objects.filter(username="caio").exists())


class LimiteDeTentativasTests(TestCase):
    """E4.2: depois de 5 senhas erradas o usuário fica bloqueado (django-axes)."""

    def setUp(self):
        criar_usuario("ana", "admin")
        criar_usuario("beto", "consulta")

    def _errar(self, usuario, vezes):
        for _ in range(vezes):
            self.client.post(reverse("login"), {"username": usuario, "password": "errada"})

    def test_quatro_erros_nao_bloqueiam(self):
        self._errar("ana", 4)
        resposta = self.client.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertRedirects(resposta, reverse("home"))

    def test_cinco_erros_bloqueiam_ate_com_a_senha_certa(self):
        self._errar("ana", 5)
        resposta = self.client.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertEqual(resposta.status_code, 403)
        self.assertContains(resposta, "Acesso bloqueado", status_code=403)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_bloqueio_de_um_usuario_nao_afeta_outro(self):
        self._errar("ana", 5)
        resposta = self.client.post(reverse("login"), {"username": "beto", "password": SENHA})
        self.assertRedirects(resposta, reverse("home"))

    def test_login_correto_zera_a_contagem(self):
        self._errar("ana", 4)
        self.client.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.client.post(reverse("logout"))
        self._errar("ana", 4)
        resposta = self.client.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertRedirects(resposta, reverse("home"))

    def test_area_administrativa_tambem_e_protegida(self):
        for _ in range(5):
            self.client.post("/admin/login/", {"username": "ana", "password": "errada"})
        resposta = self.client.post("/admin/login/", {"username": "ana", "password": SENHA})
        self.assertEqual(resposta.status_code, 403)

    def test_desbloqueio_pelo_comando_do_axes(self):
        self._errar("ana", 5)
        call_command("axes_reset")
        resposta = self.client.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertRedirects(resposta, reverse("home"))


class HttpsTests(TestCase):
    """E4.2: com HTTPS ativo, o HTTP é redirecionado e há cabeçalho HSTS."""

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_e_redirecionado_para_https(self):
        resposta = Client().get(reverse("login"))
        self.assertEqual(resposta.status_code, 301)
        self.assertTrue(resposta.url.startswith("https://"))

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=3600)
    def test_https_funciona_e_envia_hsts(self):
        resposta = Client().get(reverse("login"), secure=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("max-age=3600", resposta["Strict-Transport-Security"])

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_cookies_sao_marcados_como_seguros(self):
        criar_usuario("ana", "admin")
        cliente = Client()
        resposta = cliente.post(
            reverse("login"), {"username": "ana", "password": SENHA}, secure=True
        )
        self.assertTrue(resposta.cookies["sessionid"]["secure"])
        self.assertTrue(resposta.cookies["sessionid"]["httponly"])

    def test_pagina_nao_pode_ser_colocada_em_moldura(self):
        resposta = self.client.get(reverse("login"))
        self.assertEqual(resposta["X-Frame-Options"], "DENY")


class VerificarArmazenamentoTests(SimpleTestCase):
    def test_cria_marca_e_depois_reconhece(self):
        import tempfile
        from io import StringIO
        from pathlib import Path

        with tempfile.TemporaryDirectory() as pasta:
            with override_settings(MEDIA_ROOT=Path(pasta) / "arquivos"):
                primeira = StringIO()
                call_command("verificar_armazenamento", stdout=primeira)
                self.assertIn("criada agora", primeira.getvalue())
                segunda = StringIO()
                call_command("verificar_armazenamento", stdout=segunda)
                self.assertIn("persistente", segunda.getvalue())

    def test_pasta_sem_permissao_gera_erro(self):
        from pathlib import Path

        with override_settings(MEDIA_ROOT=Path("/proc/nao-pode-gravar")):
            with self.assertRaises(CommandError):
                call_command("verificar_armazenamento")


class LeituraDoEnvTests(SimpleTestCase):
    """Testa config/env.py sem depender do banco."""

    def test_le_arquivo_env(self):
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / ".env"
            arquivo.write_text(
                "﻿# comentário\n\nX_TESTE_A=um\nX_TESTE_B = 'dois com espaço'\n"
                "X_TESTE_C=a=b\nX_TESTE_LISTA=a, b ,c\nX_TESTE_BOOL=Sim\n",
                encoding="utf-8",
            )
            try:
                carregar_env(arquivo)
                self.assertEqual(texto("X_TESTE_A"), "um")
                self.assertEqual(texto("X_TESTE_B"), "dois com espaço")
                self.assertEqual(texto("X_TESTE_C"), "a=b")
                self.assertEqual(lista("X_TESTE_LISTA"), ["a", "b", "c"])
                self.assertTrue(booleano("X_TESTE_BOOL"))
                self.assertFalse(booleano("X_TESTE_NAO_EXISTE"))
            finally:
                for chave in list(os.environ):
                    if chave.startswith("X_TESTE_"):
                        del os.environ[chave]

    def test_arquivo_inexistente_e_ignorado(self):
        carregar_env("/caminho/que/nao/existe/.env")
