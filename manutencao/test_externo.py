"""Testes do backup externo: retenção, execução, agendador e tela (E4.4)."""
import os
from datetime import datetime, timedelta, timezone as fuso
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import agendador, cripto, drive, externo, nucleo
from .models import ExecucaoBackup

CHAVE = "age1" + "q" * 58
ENV = {
    "GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "segredo",
    "GOOGLE_REFRESH_TOKEN": "refresh", "BACKUP_CHAVE_PUBLICA": CHAVE,
}


def nome(dia, hora="030000", mes="10", ano="2026"):
    return f"gestor-{ano}-{mes}-{dia:02d}_{hora}.zip.age"


class RetencaoTests(SimpleTestCase):
    def test_guarda_os_dois_mais_recentes_de_cada_mes(self):
        nomes = [nome(4), nome(11), nome(18), nome(25), nome(5, mes="11"), nome(12, mes="11")]
        self.assertEqual(externo.escolher_apagar(nomes), [nome(4), nome(11)])

    def test_mes_com_ate_dois_nao_apaga_nada(self):
        self.assertEqual(externo.escolher_apagar([nome(4), nome(11)]), [])
        self.assertEqual(externo.escolher_apagar([]), [])

    def test_meses_e_anos_diferentes_sao_independentes(self):
        nomes = [nome(28, mes="12", ano="2025"), nome(29, mes="12", ano="2025"),
                 nome(30, mes="12", ano="2025"), nome(2, mes="01", ano="2026")]
        self.assertEqual(externo.escolher_apagar(nomes), [nome(28, mes="12", ano="2025")])

    def test_arquivos_estranhos_nunca_sao_apagados(self):
        nomes = ["foto.jpg", "gestor-manual.zip", nome(4), nome(11), nome(18)]
        self.assertEqual(externo.escolher_apagar(nomes), [nome(4)])

    def test_mesmo_dia_usa_a_hora_para_desempatar(self):
        nomes = [nome(4, "010000"), nome(4, "020000"), nome(4, "030000")]
        self.assertEqual(externo.escolher_apagar(nomes), [nome(4, "010000")])


class ClienteFalso:
    def __init__(self, existentes=()):
        self.existentes = {n: f"id-{n}" for n in existentes}
        self.apagados = []
        self.enviados = []

    def achar_ou_criar_pasta(self, nome_pasta):
        self.pasta = nome_pasta
        return "PASTA"

    def enviar(self, caminho, nome_arquivo, pasta_id):
        self.enviados.append(nome_arquivo)
        self.existentes[nome_arquivo] = "novo"
        return {"id": "novo", "name": nome_arquivo, "size": str(os.path.getsize(caminho))}

    def listar(self, pasta_id):
        return [{"id": i, "name": n} for n, i in self.existentes.items()]

    def apagar(self, arquivo_id):
        self.apagados.append(arquivo_id)


def _fazer_backup_falso(cfg, **kw):
    pasta = Path(kw["pasta_backup"]) / "2026-10-20_030000"
    pasta.mkdir(parents=True)
    (pasta / "banco.dump").write_bytes(b"banco")
    (pasta / "arquivos.zip").write_bytes(b"pdfs")
    return {"pasta": str(pasta)}


def _cripto_falso(origem, destino, chave):
    Path(destino).write_bytes(b"cifrado" * 10)
    return destino


class ExecutarTests(TestCase):
    def rodar(self, cliente, env=ENV, **extra):
        with mock.patch.dict(os.environ, env, clear=False), \
             mock.patch.object(nucleo, "fazer_backup", side_effect=_fazer_backup_falso), \
             mock.patch.object(cripto, "criptografar", side_effect=_cripto_falso):
            return externo.executar("manual", cliente=cliente)

    def test_sucesso_envia_registra_e_aplica_a_retencao(self):
        antigos = [nome(4, mes="10", ano="2026"), nome(11, mes="10", ano="2026"),
                   nome(18, mes="10", ano="2026")]
        cliente = ClienteFalso(antigos)
        r = self.rodar(cliente)
        self.assertTrue(r.sucesso, r.mensagem)
        self.assertEqual(r.arquivo, "gestor-2026-10-20_030000.zip.age")
        self.assertEqual(cliente.enviados, [r.arquivo])
        self.assertEqual(r.apagados, 2)
        self.assertEqual(sorted(cliente.apagados), sorted([f"id-{antigos[0]}", f"id-{antigos[1]}"]))
        self.assertIsNotNone(r.fim)

    def test_nada_e_apagado_se_o_envio_falha(self):
        cliente = ClienteFalso([nome(4), nome(11), nome(18)])
        cliente.enviar = mock.Mock(side_effect=drive.ErroDrive("sem rede"))
        r = self.rodar(cliente)
        self.assertFalse(r.sucesso)
        self.assertIn("sem rede", r.mensagem)
        self.assertEqual(cliente.apagados, [])

    def test_configuracao_faltando_registra_falha_clara(self):
        vazio = {k: "" for k in ENV}
        r = self.rodar(ClienteFalso(), env=vazio)
        self.assertFalse(r.sucesso)
        self.assertIn("GOOGLE_CLIENT_ID", r.mensagem)

    def test_chave_publica_invalida_e_recusada(self):
        r = self.rodar(ClienteFalso(), env={**ENV, "BACKUP_CHAVE_PUBLICA": "lixo"})
        self.assertFalse(r.sucesso)
        self.assertIn("age1", r.mensagem)

    def test_erro_inesperado_nao_vaza_detalhes_e_nao_derruba(self):
        cliente = ClienteFalso()
        cliente.achar_ou_criar_pasta = mock.Mock(side_effect=RuntimeError("segredo123"))
        r = self.rodar(cliente)
        self.assertFalse(r.sucesso)
        self.assertNotIn("segredo123", r.mensagem)

    def test_nao_roda_dois_ao_mesmo_tempo(self):
        ExecucaoBackup.objects.create(inicio=externo.timezone.now(), origem="manual")
        with self.assertRaises(externo.ErroExterno):
            self.rodar(ClienteFalso())

    def test_execucao_antiga_travada_nao_bloqueia(self):
        ExecucaoBackup.objects.create(
            inicio=externo.timezone.now() - timedelta(hours=5), origem="manual")
        self.assertTrue(self.rodar(ClienteFalso()).sucesso)

    def test_interrompidas_viram_falha(self):
        ExecucaoBackup.objects.create(inicio=externo.timezone.now(), origem="manual")
        self.assertEqual(externo.marcar_interrompidas(), 1)
        self.assertFalse(ExecucaoBackup.objects.get().sucesso)

    def test_comando_falha_com_mensagem_quando_o_backup_falha(self):
        from django.core.management.base import CommandError

        with mock.patch.dict(os.environ, {k: "" for k in ENV}):
            with self.assertRaises(CommandError):
                call_command("backup_externo")


def utc(*a):
    return datetime(*a, tzinfo=fuso.utc)


class AgendadorTests(TestCase):
    # America/Belem = UTC-3: 05:00 UTC são 02:00 locais (dentro da janela).
    NOITE = utc(2026, 10, 20, 5, 0)

    def registrar(self, quando, sucesso):
        return ExecucaoBackup.objects.create(
            inicio=quando, fim=quando, origem="agendado", sucesso=sucesso)

    def test_primeira_vez_roda_de_madrugada(self):
        self.assertTrue(agendador.devido(self.NOITE))

    def test_fora_da_janela_nao_roda(self):
        self.assertFalse(agendador.devido(utc(2026, 10, 20, 18, 0)))  # 15h local

    def test_sucesso_recente_nao_repete(self):
        self.registrar(self.NOITE - timedelta(days=3), True)
        self.assertFalse(agendador.devido(self.NOITE))

    def test_depois_de_uma_semana_roda(self):
        self.registrar(self.NOITE - timedelta(days=7), True)
        self.assertTrue(agendador.devido(self.NOITE))

    def test_falha_recente_espera_seis_horas(self):
        self.registrar(self.NOITE - timedelta(hours=1), False)
        self.assertFalse(agendador.devido(self.NOITE))

    def test_falha_antiga_tenta_de_novo(self):
        self.registrar(self.NOITE - timedelta(hours=7), False)
        self.assertTrue(agendador.devido(self.NOITE))

    def test_passo_executa_quando_devido(self):
        with mock.patch.object(agendador, "devido", return_value=True), \
             mock.patch.object(agendador.externo, "executar", return_value="r") as ex, \
             mock.patch.object(agendador, "close_old_connections"):
            self.assertEqual(agendador.passo(), "r")
            ex.assert_called_once_with("agendado")

    def test_passo_nao_derruba_com_erro_inesperado(self):
        with mock.patch.object(agendador, "devido", side_effect=RuntimeError("x")), \
             mock.patch.object(agendador, "close_old_connections"):
            self.assertIsNone(agendador.passo())


class TelaExternoTests(TestCase):
    def setUp(self):
        call_command("criar_usuario", usuario="ana", perfil="admin", senha="Senha-Forte-123!")
        call_command("criar_usuario", usuario="beto", perfil="consulta", senha="Senha-Forte-123!")

    def entrar(self, nome_usuario):
        from django.contrib.auth import get_user_model

        self.client.force_login(get_user_model().objects.get(username=nome_usuario))
        sessao = self.client.session
        sessao["mfa_ok"] = True
        sessao.save()

    def test_consulta_nao_dispara(self):
        self.entrar("beto")
        with mock.patch("manutencao.web.threading.Thread") as t:
            self.assertEqual(self.client.post(reverse("backup_externo")).status_code, 403)
            t.assert_not_called()

    def test_admin_dispara_em_segundo_plano_e_volta_para_a_tela(self):
        self.entrar("ana")
        with mock.patch("manutencao.web.threading.Thread") as t:
            r = self.client.post(reverse("backup_externo"))
            t.return_value.start.assert_called_once()
        self.assertRedirects(r, reverse("backup"))

    def test_get_do_botao_so_redireciona(self):
        self.entrar("ana")
        r = self.client.get(reverse("backup_externo"))
        self.assertRedirects(r, reverse("backup"))

    def test_tela_lista_as_execucoes_e_o_aviso(self):
        self.entrar("ana")
        ExecucaoBackup.objects.create(
            inicio=externo.timezone.now(), fim=externo.timezone.now(), origem="agendado",
            sucesso=False, mensagem="O Google recusou a autorização")
        with mock.patch.dict(os.environ, {"BACKUP_EXTERNO_ATIVO": "False"}):
            r = self.client.get(reverse("backup"))
        self.assertContains(r, "Cópia semanal no Google Drive")
        self.assertContains(r, "O Google recusou a autorização")
        self.assertContains(r, "desligado")
