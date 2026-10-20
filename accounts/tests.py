"""Testes da E4: login, perfis Admin/Consulta e criação de usuários.

Rodam com:  python manage.py test
Precisam do PostgreSQL configurado no .env. O usuário do banco precisa da
permissão CREATEDB, porque o Django cria um banco temporário só para os testes.
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.urls import reverse

from config.env import booleano, carregar_env, lista, texto

from . import mfa
from .bloqueio import DURACOES
from .models import BloqueioLogin, CodigoRecuperacao, DispositivoMFA
from .perfis import ADMIN, CONSULTA, perfil_do_usuario

Usuario = get_user_model()
SENHA = "Senha-Forte-123!"


def entrar(cliente, login):
    """Abre a sessão sem passar pela tela de login.

    Os testes usam force_login para não depender da senha em cada teste. A
    senha e o bloqueio são testados à parte, pela própria tela de login.
    """
    cliente.force_login(
        Usuario.objects.get(username=login),
        backend="accounts.backends.ModelBackendComBloqueio",
    )
    # Admin só passa pela verificação em duas etapas, testada à parte (E4.3b).
    sessao = cliente.session
    sessao["mfa_ok"] = True
    sessao.save()


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
            codigos,
            {
                "add_user", "change_user", "delete_user", "view_user",
                "view_bloqueiologin", "change_bloqueiologin",
                "view_dispositivomfa", "change_dispositivomfa",
            },
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
        self.assertRedirects(resposta, reverse("home"), fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_com_senha_errada_nao_autentica(self):
        resposta = self.client.post(
            reverse("login"), {"username": "ana", "password": "errada"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inicio_mostra_o_perfil(self):
        entrar(self.client, "ana")
        resposta = self.client.get(reverse("home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["perfil"], ADMIN)

    def test_sair_encerra_a_sessao(self):
        entrar(self.client, "ana")
        resposta = self.client.post(reverse("logout"))
        self.assertRedirects(resposta, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sair_por_get_nao_e_permitido(self):
        entrar(self.client, "ana")
        resposta = self.client.get(reverse("logout"))
        self.assertEqual(resposta.status_code, 405)


class AreaAdministrativaTests(TestCase):
    def test_admin_acessa_lista_de_usuarios(self):
        criar_usuario("ana", "admin")
        entrar(self.client, "ana")
        resposta = self.client.get("/admin/auth/user/")
        self.assertEqual(resposta.status_code, 200)

    def test_consulta_nao_acessa_area_administrativa(self):
        criar_usuario("beto", "consulta")
        entrar(self.client, "beto")
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


class StaffAcompanhaPerfilAdminTests(TestCase):
    """P-016: entrar no grupo Admin concede is_staff; sair retira."""

    def setUp(self):
        self.admin = Group.objects.get(name=ADMIN)
        self.consulta = Group.objects.get(name=CONSULTA)

    def novo(self, login, **extra):
        return Usuario.objects.create_user(login, password=SENHA, **extra)

    def staff(self, usuario):
        usuario.refresh_from_db()
        return usuario.is_staff

    def test_adicionar_ao_grupo_admin_concede_staff(self):
        u = self.novo("a1")
        self.assertFalse(self.staff(u))
        u.groups.add(self.admin)
        self.assertTrue(self.staff(u))

    def test_set_de_grupos_como_faz_o_formulario_do_admin(self):
        u = self.novo("a2")
        u.groups.set([self.admin])
        self.assertTrue(self.staff(u))

    def test_pelo_lado_do_grupo_tambem(self):
        u = self.novo("a3")
        self.admin.user_set.add(u)
        self.assertTrue(self.staff(u))

    def test_consulta_nao_concede_staff(self):
        u = self.novo("c1")
        u.groups.add(self.consulta)
        self.assertFalse(self.staff(u))

    def test_remover_do_grupo_admin_retira_staff(self):
        u = self.novo("a4")
        u.groups.add(self.admin)
        u.groups.remove(self.admin)
        self.assertFalse(self.staff(u))

    def test_trocar_admin_por_consulta_retira_staff(self):
        u = self.novo("a5")
        u.groups.set([self.admin])
        u.groups.set([self.consulta])
        self.assertFalse(self.staff(u))

    def test_clear_retira_staff(self):
        u = self.novo("a6")
        u.groups.add(self.admin)
        u.groups.clear()
        self.assertFalse(self.staff(u))

    def test_clear_pelo_lado_do_grupo_retira_staff(self):
        u1, u2 = self.novo("a7"), self.novo("a8")
        self.admin.user_set.add(u1, u2)
        self.admin.user_set.clear()
        self.assertFalse(self.staff(u1))
        self.assertFalse(self.staff(u2))

    def test_superusuario_nao_perde_staff(self):
        u = Usuario.objects.create_superuser("root", password=SENHA)
        u.groups.add(self.admin)
        u.groups.remove(self.admin)
        self.assertTrue(self.staff(u))

    def test_continua_admin_se_sair_so_de_outro_grupo(self):
        u = self.novo("a9")
        u.groups.add(self.admin, self.consulta)
        u.groups.remove(self.consulta)
        self.assertTrue(self.staff(u))

    def test_staff_dado_a_mao_a_quem_nao_e_admin_nao_e_mexido(self):
        u = self.novo("s1", is_staff=True)
        u.groups.add(self.consulta)
        u.groups.remove(self.consulta)
        self.assertTrue(self.staff(u))

    def test_novo_admin_acessa_a_area_administrativa(self):
        u = self.novo("novo_admin")
        u.groups.set([self.admin])
        entrar(self.client, "novo_admin")
        self.assertEqual(self.client.get("/admin/auth/user/").status_code, 200)


class BloqueioProgressivoTests(TestCase):
    """E4.3 (D-030): 5 erros bloqueiam por 15 min, depois 1 h, depois 24 h."""

    def setUp(self):
        criar_usuario("ana", "admin")
        criar_usuario("beto", "consulta")
        self.agora = timezone.now()
        relogio = mock.patch("accounts.bloqueio._agora", side_effect=lambda: self.agora)
        relogio.start()
        self.addCleanup(relogio.stop)

    def _errar(self, usuario, vezes, rota=None):
        for _ in range(vezes):
            self.client.post(rota or reverse("login"), {"username": usuario, "password": "errada"})

    def _entrar(self, usuario="ana", senha=SENHA):
        return self.client.post(reverse("login"), {"username": usuario, "password": senha})

    def _registro(self, usuario="ana"):
        return BloqueioLogin.objects.get(usuario=usuario)

    def test_quatro_erros_nao_bloqueiam(self):
        self._errar("ana", 4)
        self.assertRedirects(self._entrar(), reverse("home"), fetch_redirect_response=False)

    def test_cinco_erros_bloqueiam_ate_com_a_senha_certa(self):
        self._errar("ana", 5)
        resposta = self._entrar()
        self.assertEqual(resposta.status_code, 403)
        self.assertContains(resposta, "Acesso bloqueado", status_code=403)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_primeiro_bloqueio_dura_15_minutos(self):
        self._errar("ana", 5)
        registro = self._registro()
        self.assertEqual(registro.bloqueado_ate - self.agora, timedelta(minutes=15))
        self.assertEqual(registro.nivel, 1)

    def test_passado_o_prazo_a_senha_certa_entra(self):
        self._errar("ana", 5)
        self.agora += timedelta(minutes=14)
        self.assertEqual(self._entrar().status_code, 403)
        self.agora += timedelta(minutes=2)
        self.assertRedirects(self._entrar(), reverse("home"), fetch_redirect_response=False)

    def test_reincidencia_sobe_para_1h_depois_24h_e_fica_em_24h(self):
        esperado = [DURACOES[0], DURACOES[1], DURACOES[2], DURACOES[2]]
        for nivel, duracao in enumerate(esperado, start=1):
            self._errar("ana", 5)
            registro = self._registro()
            self.assertEqual(registro.nivel, nivel)
            self.assertEqual(registro.bloqueado_ate - self.agora, duracao)
            self.agora = registro.bloqueado_ate + timedelta(minutes=1)

    def test_nivel_volta_a_zero_depois_de_7_dias(self):
        self._errar("ana", 5)
        self.agora = self._registro().bloqueado_ate + timedelta(days=8)
        self._errar("ana", 5)
        registro = self._registro()
        self.assertEqual(registro.nivel, 1)
        self.assertEqual(registro.bloqueado_ate - self.agora, timedelta(minutes=15))

    def test_tentativas_durante_o_bloqueio_nao_estendem_nem_escalam(self):
        self._errar("ana", 5)
        antes = self._registro()
        self._errar("ana", 3)
        depois = self._registro()
        self.assertEqual(depois.nivel, 1)
        self.assertEqual(depois.bloqueado_ate, antes.bloqueado_ate)

    def test_bloqueio_de_um_usuario_nao_afeta_outro(self):
        self._errar("ana", 5)
        self.assertRedirects(self._entrar("beto"), reverse("home"))

    def test_login_correto_zera_as_senhas_erradas_seguidas(self):
        self._errar("ana", 4)
        self._entrar()
        self.client.post(reverse("logout"))
        self._errar("ana", 4)
        self.assertRedirects(self._entrar(), reverse("home"), fetch_redirect_response=False)

    def test_nome_que_nao_existe_se_comporta_igual(self):
        self._errar("fantasma", 5)
        resposta = self.client.post(reverse("login"), {"username": "fantasma", "password": "x"})
        self.assertContains(resposta, "Acesso bloqueado", status_code=403)

    def test_maiusculas_e_espacos_contam_como_o_mesmo_usuario(self):
        self._errar("ana", 3)
        self._errar(" ANA ", 2)
        self.assertEqual(self._entrar().status_code, 403)

    def test_area_administrativa_tambem_e_protegida(self):
        self._errar("ana", 5, rota="/admin/login/")
        self.client.post("/admin/login/", {"username": "ana", "password": SENHA})
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self._entrar().status_code, 403)

    def test_aviso_na_proxima_entrada_aparece_uma_vez_so(self):
        self._errar("ana", 5)
        self.agora += timedelta(minutes=16)
        resposta = self.client.post(
            reverse("login"), {"username": "ana", "password": SENHA}, follow=True
        )
        self.assertContains(resposta, "foi bloqueada 1 vez")
        self.client.post(reverse("logout"))
        resposta = self.client.post(
            reverse("login"), {"username": "ana", "password": SENHA}, follow=True
        )
        self.assertNotContains(resposta, "foi bloqueada")

    def test_sem_bloqueio_nao_ha_aviso(self):
        resposta = self.client.post(
            reverse("login"), {"username": "ana", "password": SENHA}, follow=True
        )
        self.assertNotContains(resposta, "foi bloqueada")

    def test_desbloqueio_pelo_comando(self):
        self._errar("ana", 5)
        call_command("desbloquear_usuario", usuario="ana")
        self.assertRedirects(self._entrar(), reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self._registro().nivel, 0)

    def test_comando_exige_usuario_ou_todos(self):
        with self.assertRaises(CommandError):
            call_command("desbloquear_usuario")

    def test_desbloqueio_pela_area_administrativa(self):
        criar_usuario("chefe", "admin")
        self._errar("beto", 5)
        entrar(self.client, "chefe")
        registro = self._registro("beto")
        resposta = self.client.post(
            "/admin/accounts/bloqueiologin/",
            {"action": "desbloquear", "index": "0", "_selected_action": [registro.pk]},
        )
        self.assertEqual(resposta.status_code, 302)
        self.client.logout()
        self.assertRedirects(self._entrar("beto"), reverse("home"))

    def test_consulta_nao_ve_os_bloqueios(self):
        entrar(self.client, "beto")
        resposta = self.client.get("/admin/accounts/bloqueiologin/")
        self.assertEqual(resposta.status_code, 302)


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


class ProxyDoServidorTests(TestCase):
    """O waitress precisa confiar no X-Forwarded-Proto do Railway (senão: laço de redirecionamentos)."""

    def test_com_https_o_servidor_confia_no_proxy(self):
        import os
        from unittest import mock

        import serve

        with mock.patch.dict(os.environ, {"DJANGO_USAR_HTTPS": "True"}):
            opcoes = serve.opcoes_de_proxy()
        self.assertEqual(opcoes["trusted_proxy"], "*")
        self.assertIn("x-forwarded-proto", opcoes["trusted_proxy_headers"])

    def test_sem_https_nao_confia_em_proxy(self):
        import os
        from unittest import mock

        import serve

        with mock.patch.dict(os.environ, {"DJANGO_USAR_HTTPS": "False"}):
            self.assertEqual(serve.opcoes_de_proxy(), {})


# --- E4.3b: verificação em duas etapas ---------------------------------------

class TotpTests(SimpleTestCase):
    def test_vetor_oficial_da_rfc_6238(self):
        import base64

        segredo = base64.b32encode(b"12345678901234567890").decode()
        # RFC 6238, tempo 59 s => passo 1; 6 últimos dígitos de 94287082.
        self.assertEqual(mfa.codigo_em(segredo, 1), "287082")
        # tempo 1111111109 s => passo 37037036; 6 últimos dígitos de 07081804.
        self.assertEqual(mfa.codigo_em(segredo, 37037036), "081804")

    def test_segredo_novo_e_base32_de_32_letras(self):
        s = mfa.gerar_segredo()
        self.assertEqual(len(s), 32)
        self.assertNotEqual(s, mfa.gerar_segredo())

    def test_uri_do_aplicativo(self):
        uri = mfa.uri_otpauth("ana", "ABCDEFGH")
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertIn("secret=ABCDEFGH", uri)
        self.assertIn("period=30", uri)


class MfaTestCase(TestCase):
    """Base: relógio controlado para os códigos do aplicativo."""

    def setUp(self):
        self.agora = 1_900_000_000.0
        relogio = mock.patch.object(mfa, "_agora_ts", lambda: self.agora)
        relogio.start()
        self.addCleanup(relogio.stop)
        criar_usuario("ana", "admin")
        self.ana = Usuario.objects.get(username="ana")
        self.cliente = Client()
        self.cliente.force_login(self.ana, backend="accounts.backends.ModelBackendComBloqueio")

    def codigo(self, disp, deslocamento=0):
        return mfa.codigo_em(disp.segredo, int(self.agora // 30) + deslocamento)

    def avancar(self, segundos=30):
        self.agora += segundos

    def ativar(self):
        """Configura e confirma o MFA de 'ana'; devolve (dispositivo, códigos)."""
        self.cliente.get(reverse("mfa_configurar"))
        disp = DispositivoMFA.objects.get(usuario=self.ana)
        r = self.cliente.post(reverse("mfa_configurar"), {"codigo": self.codigo(disp)})
        return DispositivoMFA.objects.get(usuario=self.ana), r.context["codigos"]

    def nova_sessao(self):
        """Simula uma nova entrada com senha (sem MFA ainda)."""
        self.cliente = Client()
        self.cliente.force_login(self.ana, backend="accounts.backends.ModelBackendComBloqueio")


class ExigenciaDeMfaTests(MfaTestCase):
    def test_admin_sem_mfa_vai_para_a_configuracao(self):
        for url in (reverse("home"), reverse("admin:index"), reverse("backup")):
            r = self.cliente.get(url)
            self.assertRedirects(r, reverse("mfa_configurar"), fetch_redirect_response=False)

    def test_admin_com_mfa_pendente_vai_para_a_verificacao(self):
        self.ativar()
        self.nova_sessao()
        r = self.cliente.get(reverse("home"))
        self.assertRedirects(r, reverse("mfa_verificar"), fetch_redirect_response=False)

    def test_consulta_nao_precisa_de_mfa(self):
        criar_usuario("beto", "consulta")
        c = Client()
        c.force_login(Usuario.objects.get(username="beto"),
                      backend="accounts.backends.ModelBackendComBloqueio")
        self.assertEqual(c.get(reverse("home")).status_code, 200)

    def test_consulta_nao_usa_as_telas_de_mfa(self):
        criar_usuario("beto", "consulta")
        c = Client()
        c.force_login(Usuario.objects.get(username="beto"),
                      backend="accounts.backends.ModelBackendComBloqueio")
        self.assertRedirects(c.get(reverse("mfa_configurar")), reverse("home"),
                             fetch_redirect_response=False)
        self.assertRedirects(c.get(reverse("mfa_verificar")), reverse("home"),
                             fetch_redirect_response=False)

    def test_anonimo_vai_para_o_login(self):
        r = Client().get(reverse("mfa_verificar"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith(reverse("login")))

    def test_sair_continua_liberado(self):
        r = self.cliente.post(reverse("logout"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.cliente.get(reverse("home")).status_code, 302)

    def test_nova_entrada_com_senha_pede_o_codigo_de_novo(self):
        self.ativar()
        self.assertEqual(self.cliente.get(reverse("home")).status_code, 200)
        c = Client()
        r = c.post(reverse("login"), {"username": "ana", "password": SENHA})
        self.assertEqual(r.status_code, 302)
        r = c.get(reverse("home"))
        self.assertRedirects(r, reverse("mfa_verificar"), fetch_redirect_response=False)


class ConfigurarMfaTests(MfaTestCase):
    def test_tela_mostra_chave_e_cria_dispositivo_nao_confirmado(self):
        r = self.cliente.get(reverse("mfa_configurar"))
        self.assertEqual(r.status_code, 200)
        disp = DispositivoMFA.objects.get(usuario=self.ana)
        self.assertFalse(disp.confirmado)
        self.assertContains(r, mfa.segredo_legivel(disp.segredo))

    def test_recarregar_mantem_o_mesmo_segredo(self):
        self.cliente.get(reverse("mfa_configurar"))
        antes = DispositivoMFA.objects.get(usuario=self.ana).segredo
        self.cliente.get(reverse("mfa_configurar"))
        self.assertEqual(DispositivoMFA.objects.get(usuario=self.ana).segredo, antes)

    def test_codigo_errado_nao_ativa(self):
        self.cliente.get(reverse("mfa_configurar"))
        r = self.cliente.post(reverse("mfa_configurar"), {"codigo": "000000"})
        self.assertContains(r, "Código incorreto")
        self.assertFalse(DispositivoMFA.objects.get(usuario=self.ana).confirmado)

    def test_codigo_certo_ativa_libera_a_sessao_e_mostra_os_codigos(self):
        disp, codigos = self.ativar()
        self.assertTrue(disp.confirmado)
        self.assertEqual(len(codigos), mfa.QTD_CODIGOS)
        self.assertEqual(CodigoRecuperacao.objects.filter(usuario=self.ana).count(), 8)
        self.assertEqual(self.cliente.get(reverse("home")).status_code, 200)

    def test_codigos_de_recuperacao_so_ficam_como_hash(self):
        _, codigos = self.ativar()
        guardados = set(CodigoRecuperacao.objects.values_list("hash", flat=True))
        for c in codigos:
            self.assertNotIn(c, guardados)
            self.assertNotIn(c.replace("-", ""), guardados)

    def test_depois_de_ativo_a_configuracao_nao_reaparece(self):
        self.ativar()
        r = self.cliente.get(reverse("mfa_configurar"))
        self.assertRedirects(r, reverse("home"), fetch_redirect_response=False)


class VerificarMfaTests(MfaTestCase):
    def setUp(self):
        super().setUp()
        self.disp, self.codigos = self.ativar()
        self.avancar(60)
        self.nova_sessao()

    def test_codigo_certo_libera(self):
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": self.codigo(self.disp)})
        self.assertRedirects(r, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.cliente.get(reverse("home")).status_code, 200)

    def test_codigo_aceita_espacos(self):
        c = self.codigo(self.disp)
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": f"{c[:3]} {c[3:]}"})
        self.assertEqual(r.status_code, 302)

    def test_codigo_errado_nega(self):
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": "000000"})
        self.assertContains(r, "Código incorreto")
        self.assertRedirects(self.cliente.get(reverse("home")), reverse("mfa_verificar"),
                             fetch_redirect_response=False)

    def test_codigo_nao_pode_ser_reusado(self):
        codigo = self.codigo(self.disp)
        self.cliente.post(reverse("mfa_verificar"), {"codigo": codigo})
        self.nova_sessao()
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": codigo})
        self.assertContains(r, "Código incorreto")

    def test_aceita_o_passo_vizinho_mas_nao_o_distante(self):
        self.assertTrue(mfa.conferir_totp(self.disp, self.codigo(self.disp, -1)))
        self.disp.refresh_from_db()
        self.assertFalse(mfa.conferir_totp(self.disp, self.codigo(self.disp, 5)))

    def test_cinco_erros_bloqueiam_por_15_minutos(self):
        for _ in range(mfa.LIMITE_FALHAS):
            self.cliente.post(reverse("mfa_verificar"), {"codigo": "000000"})
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": self.codigo(self.disp)})
        self.assertEqual(r.status_code, 403)
        self.assertRedirects(self.cliente.get(reverse("home")), reverse("mfa_verificar"),
                             fetch_redirect_response=False)

    def test_bloqueio_nao_zera_ao_entrar_de_novo_com_senha(self):
        for _ in range(mfa.LIMITE_FALHAS):
            self.cliente.post(reverse("mfa_verificar"), {"codigo": "000000"})
        self.nova_sessao()
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": self.codigo(self.disp)})
        self.assertEqual(r.status_code, 403)

    def test_depois_dos_15_minutos_volta_a_aceitar(self):
        for _ in range(mfa.LIMITE_FALHAS):
            self.cliente.post(reverse("mfa_verificar"), {"codigo": "000000"})
        self.avancar(0)
        with mock.patch.object(mfa, "_agora", lambda: timezone.now() + timedelta(minutes=16)):
            r = self.cliente.post(reverse("mfa_verificar"), {"codigo": self.codigo(self.disp)})
        self.assertEqual(r.status_code, 302)

    def test_codigo_de_recuperacao_entra_uma_vez_e_avisa(self):
        usado = self.codigos[0]
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": usado.lower()})
        self.assertRedirects(r, reverse("home"), fetch_redirect_response=False)
        pagina = self.cliente.get(reverse("home"))
        self.assertContains(pagina, "código de recuperação")
        self.assertEqual(mfa.codigos_restantes(self.ana), mfa.QTD_CODIGOS - 1)
        self.nova_sessao()
        r = self.cliente.post(reverse("mfa_verificar"), {"codigo": usado})
        self.assertContains(r, "Código incorreto")

    def test_acerto_zera_a_contagem_de_erros(self):
        for _ in range(mfa.LIMITE_FALHAS - 1):
            self.cliente.post(reverse("mfa_verificar"), {"codigo": "000000"})
        self.cliente.post(reverse("mfa_verificar"), {"codigo": self.codigo(self.disp)})
        self.disp.refresh_from_db()
        self.assertEqual(self.disp.falhas, 0)


class RedefinirMfaTests(MfaTestCase):
    def test_comando_apaga_aplicativo_e_codigos(self):
        self.ativar()
        call_command("redefinir_mfa", usuario="ana")
        self.assertFalse(DispositivoMFA.objects.filter(usuario=self.ana).exists())
        self.assertFalse(CodigoRecuperacao.objects.filter(usuario=self.ana).exists())

    def test_comando_com_usuario_inexistente_da_erro(self):
        with self.assertRaises(CommandError):
            call_command("redefinir_mfa", usuario="ninguem")

    def test_depois_de_redefinir_o_admin_configura_de_novo(self):
        self.ativar()
        call_command("redefinir_mfa", usuario="ana")
        self.nova_sessao()
        r = self.cliente.get(reverse("home"))
        self.assertRedirects(r, reverse("mfa_configurar"), fetch_redirect_response=False)

    def test_outro_admin_redefine_pela_area_administrativa(self):
        self.ativar()
        criar_usuario("caio", "admin")
        outro = Client()
        outro.force_login(Usuario.objects.get(username="caio"),
                          backend="accounts.backends.ModelBackendComBloqueio")
        sessao = outro.session
        sessao["mfa_ok"] = True
        sessao.save()
        disp = DispositivoMFA.objects.get(usuario=self.ana)
        r = outro.post(
            reverse("admin:accounts_dispositivomfa_changelist"),
            {"action": "redefinir", "_selected_action": [disp.pk]},
            follow=True,
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(DispositivoMFA.objects.filter(usuario=self.ana).exists())
