"""Testes do cadastro de contratos (E5a): modelo, validações, telas e permissões."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.tests import SENHA, entrar
from .forms import proximo_sequencial
from .models import Contratado, Contrato, Modalidade
from .validadores import cnpj_valido, cpf_valido, documento_valido, formatar_documento

Usuario = get_user_model()
CPF = "529.982.247-25"
CNPJ = "11.222.333/0001-81"


class ValidadoresTests(SimpleTestCase):
    def test_cpf(self):
        self.assertTrue(cpf_valido(CPF))
        self.assertTrue(cpf_valido("52998224725"))
        for ruim in ("529.982.247-24", "111.111.111-11", "123", "", None):
            self.assertFalse(cpf_valido(ruim), ruim)

    def test_cnpj(self):
        self.assertTrue(cnpj_valido(CNPJ))
        for ruim in ("11.222.333/0001-80", "00.000.000/0000-00", "123", ""):
            self.assertFalse(cnpj_valido(ruim), ruim)

    def test_documento_identifica_o_tipo(self):
        self.assertEqual(documento_valido(CPF), "PF")
        self.assertEqual(documento_valido(CNPJ), "PJ")
        self.assertIsNone(documento_valido("12345678900"))

    def test_formatacao(self):
        self.assertEqual(formatar_documento("52998224725"), CPF)
        self.assertEqual(formatar_documento("11222333000181"), CNPJ)


class Base(TestCase):
    def setUp(self):
        call_command("criar_usuario", usuario="ana", perfil="admin", senha=SENHA)
        call_command("criar_usuario", usuario="beto", perfil="consulta", senha=SENHA)
        self.pe = Modalidade.objects.get(sigla="PE")

    def dados(self, **extra):
        d = {
            "sequencial": 1, "modalidade": self.pe.pk, "numero_modalidade": 15, "ano": 2026,
            "data_assinatura": "2026-03-10", "data_publicacao": "",
            "data_inicio_vigencia": "2026-03-11", "data_fim_vigencia": "2027-03-10",
            "objeto": "Fornecimento de material de expediente", "valor": "12345.67",
            "documento_contratado": CNPJ, "razao_social_contratado": "Papelaria Exemplo Ltda",
            "informacoes_complementares": "",
        }
        d.update(extra)
        return d

    def criar(self, **extra):
        contratado, _ = Contratado.objects.get_or_create(
            documento="11222333000181", defaults={"tipo_pessoa": "PJ", "razao_social": "Papelaria"})
        campos = dict(
            sequencial=1, modalidade=self.pe, numero_modalidade=15, ano=2026,
            data_assinatura=date(2026, 3, 10), data_inicio_vigencia=date(2026, 3, 11),
            data_fim_vigencia=date(2027, 3, 10), objeto="Objeto", valor=Decimal("100.00"),
            contratado=contratado,
        )
        campos.update(extra)
        return Contrato.objects.create(**campos)


class ModeloTests(Base):
    def test_modalidades_iniciais(self):
        self.assertEqual(
            set(Modalidade.objects.values_list("sigla", flat=True)),
            {"AD", "CE", "CH", "PE", "INEX"},
        )
        self.assertEqual(Modalidade.objects.get(sigla="AD").nome, "Adesão de Ata")

    def test_numero_formatado_e_vigencia_original(self):
        c = self.criar()
        self.assertEqual(c.numero_formatado, "1.PE.15/2026")
        self.assertEqual(c.data_fim_vigencia_original, date(2027, 3, 10))
        c.data_fim_vigencia = date(2028, 3, 10)
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.data_fim_vigencia_original, date(2027, 3, 10))

    def test_sequencial_unico_por_ano_mas_reinicia_no_outro(self):
        self.criar()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.criar(numero_modalidade=16)
        self.criar(ano=2027)  # outro ano: pode repetir o N° 1

    def test_valor_negativo_e_datas_invertidas_sao_barrados_no_banco(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.criar(valor=Decimal("-1"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.criar(sequencial=2, data_fim_vigencia=date(2026, 3, 1))

    def test_proximo_sequencial_do_ano(self):
        self.assertEqual(proximo_sequencial(2026), 1)
        self.criar(sequencial=7)
        self.assertEqual(proximo_sequencial(2026), 8)
        self.assertEqual(proximo_sequencial(2027), 1)

    def test_nao_ha_migracao_pendente(self):
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)


class PermissoesTests(Base):
    def test_anonimo_vai_para_o_login(self):
        for nome, args in (("lista", []), ("novo", []), ("detalhe", [1]),
                           ("editar", [1]), ("excluir", [1])):
            r = self.client.get(reverse(f"contratos:{nome}", args=args))
            self.assertEqual(r.status_code, 302, nome)
            self.assertTrue(r.url.startswith(reverse("login")))

    def test_consulta_so_visualiza(self):
        c = self.criar()
        entrar(self.client, "beto")
        self.assertEqual(self.client.get(reverse("contratos:lista")).status_code, 200)
        self.assertEqual(self.client.get(reverse("contratos:detalhe", args=[c.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("contratos:novo")).status_code, 403)
        self.assertEqual(self.client.post(reverse("contratos:novo"), self.dados()).status_code, 403)
        self.assertEqual(self.client.get(reverse("contratos:editar", args=[c.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("contratos:excluir", args=[c.pk])).status_code, 403)
        self.assertTrue(Contrato.objects.filter(pk=c.pk).exists())

    def test_consulta_nao_ve_botoes_de_edicao(self):
        c = self.criar()
        entrar(self.client, "beto")
        r = self.client.get(reverse("contratos:detalhe", args=[c.pk]))
        self.assertNotContains(r, reverse("contratos:editar", args=[c.pk]))
        self.assertNotContains(r, reverse("contratos:excluir", args=[c.pk]))
        self.assertNotContains(self.client.get(reverse("contratos:lista")), reverse("contratos:novo"))

    def test_usuario_sem_perfil_recebe_403(self):
        Usuario.objects.create_user("sem", password=SENHA)
        self.client.force_login(Usuario.objects.get(username="sem"),
                                backend="accounts.backends.ModelBackendComBloqueio")
        self.assertEqual(self.client.get(reverse("contratos:lista")).status_code, 403)

    def test_home_mostra_link_para_quem_pode_ver(self):
        entrar(self.client, "beto")
        self.assertContains(self.client.get(reverse("home")), reverse("contratos:lista"))


class CadastroTests(Base):
    def setUp(self):
        super().setUp()
        entrar(self.client, "ana")

    def test_tela_de_novo_sugere_ano_e_sequencial(self):
        self.criar(sequencial=4, ano=date.today().year, numero_modalidade=3)
        r = self.client.get(reverse("contratos:novo"))
        self.assertEqual(r.context["form"].initial["sequencial"], 5)
        self.assertEqual(r.context["form"].initial["ano"], date.today().year)

    def test_cadastra_contrato_completo(self):
        r = self.client.post(reverse("contratos:novo"), self.dados())
        c = Contrato.objects.get()
        self.assertRedirects(r, reverse("contratos:detalhe", args=[c.pk]))
        self.assertEqual(c.numero_formatado, "1.PE.15/2026")
        self.assertEqual(c.valor, Decimal("12345.67"))
        self.assertEqual(c.contratado.documento, "11222333000181")
        self.assertEqual(c.contratado.tipo_pessoa, "PJ")
        self.assertEqual(c.criado_por.username, "ana")
        self.assertIsNone(c.data_publicacao)

    def test_cpf_vira_pessoa_fisica(self):
        self.client.post(reverse("contratos:novo"),
                         self.dados(documento_contratado=CPF, razao_social_contratado="João"))
        self.assertEqual(Contrato.objects.get().contratado.tipo_pessoa, "PF")

    def test_campos_obrigatorios(self):
        for campo in ("sequencial", "modalidade", "numero_modalidade", "ano", "data_assinatura",
                      "data_inicio_vigencia", "data_fim_vigencia", "objeto", "valor",
                      "documento_contratado", "razao_social_contratado"):
            r = self.client.post(reverse("contratos:novo"), self.dados(**{campo: ""}))
            self.assertEqual(r.status_code, 200, campo)
            self.assertIn(campo, r.context["form"].errors, campo)
        self.assertEqual(Contrato.objects.count(), 0)

    def test_documento_invalido(self):
        r = self.client.post(reverse("contratos:novo"), self.dados(documento_contratado="123"))
        self.assertIn("documento_contratado", r.context["form"].errors)

    def test_numero_da_modalidade_fora_de_1_a_100(self):
        for n in ("0", "101"):
            r = self.client.post(reverse("contratos:novo"), self.dados(numero_modalidade=n))
            self.assertIn("numero_modalidade", r.context["form"].errors, n)

    def test_valor_negativo(self):
        r = self.client.post(reverse("contratos:novo"), self.dados(valor="-5"))
        self.assertIn("valor", r.context["form"].errors)

    def test_vigencia_final_antes_do_inicio(self):
        r = self.client.post(reverse("contratos:novo"), self.dados(data_fim_vigencia="2026-03-01"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Contrato.objects.count(), 0)
        self.assertContains(r, "vigência final não pode ser anterior")

    def test_sequencial_repetido_no_mesmo_ano(self):
        self.client.post(reverse("contratos:novo"), self.dados())
        r = self.client.post(reverse("contratos:novo"), self.dados(numero_modalidade=20))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Já existe um contrato com este N°")
        self.assertEqual(Contrato.objects.count(), 1)

    def test_contratado_existente_e_reaproveitado(self):
        self.client.post(reverse("contratos:novo"), self.dados())
        self.client.post(reverse("contratos:novo"), self.dados(sequencial=2, documento_contratado="11222333000181"))
        self.assertEqual(Contratado.objects.count(), 1)
        self.assertEqual(Contrato.objects.count(), 2)

    def test_razao_social_nova_atualiza_o_contratado(self):
        self.client.post(reverse("contratos:novo"), self.dados())
        self.client.post(reverse("contratos:novo"), self.dados(
            sequencial=2, razao_social_contratado="Papelaria Exemplo S/A"))
        self.assertEqual(Contratado.objects.get().razao_social, "Papelaria Exemplo S/A")

    def test_publicacao_e_complementares_opcionais(self):
        self.client.post(reverse("contratos:novo"), self.dados(
            data_publicacao="2026-03-12", informacoes_complementares="Obs", envolve_saude="on"))
        c = Contrato.objects.get()
        self.assertEqual(c.data_publicacao, date(2026, 3, 12))
        self.assertTrue(c.envolve_saude)
        self.assertFalse(c.envolve_educacao)

    def test_modalidade_inativa_nao_aparece_no_cadastro(self):
        Modalidade.objects.filter(sigla="CH").update(ativo=False)
        r = self.client.get(reverse("contratos:novo"))
        siglas = [m.sigla for m in r.context["form"].fields["modalidade"].queryset]
        self.assertNotIn("CH", siglas)


class EdicaoEExclusaoTests(Base):
    def setUp(self):
        super().setUp()
        entrar(self.client, "ana")
        self.c = self.criar()

    def test_tela_de_edicao_traz_os_dados(self):
        r = self.client.get(reverse("contratos:editar", args=[self.c.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["form"].initial["documento_contratado"], "11.222.333/0001-81")
        self.assertContains(r, 'value="2026-03-10"')

    def test_edita_remonta_numero_e_preserva_a_vigencia_original(self):
        r = self.client.post(reverse("contratos:editar", args=[self.c.pk]), self.dados(
            numero_modalidade=22, data_fim_vigencia="2028-03-10", valor="999.00"))
        self.assertRedirects(r, reverse("contratos:detalhe", args=[self.c.pk]))
        self.c.refresh_from_db()
        self.assertEqual(self.c.numero_formatado, "1.PE.22/2026")
        self.assertEqual(self.c.data_fim_vigencia, date(2028, 3, 10))
        self.assertEqual(self.c.data_fim_vigencia_original, date(2027, 3, 10))
        self.assertEqual(self.c.atualizado_por.username, "ana")
        r = self.client.get(reverse("contratos:detalhe", args=[self.c.pk]))
        self.assertContains(r, "original: 10/03/2027")

    def test_editar_sem_mudar_o_sequencial_nao_acusa_duplicidade(self):
        r = self.client.post(reverse("contratos:editar", args=[self.c.pk]), self.dados(objeto="Novo objeto"))
        self.assertEqual(r.status_code, 302)

    def test_exclusao_pede_confirmacao_e_apaga_de_vez(self):
        r = self.client.get(reverse("contratos:excluir", args=[self.c.pk]))
        self.assertContains(r, "definitiva")
        self.assertTrue(Contrato.objects.filter(pk=self.c.pk).exists())
        r = self.client.post(reverse("contratos:excluir", args=[self.c.pk]))
        self.assertRedirects(r, reverse("contratos:lista"))
        self.assertFalse(Contrato.objects.filter(pk=self.c.pk).exists())

    def test_contrato_inexistente_da_404(self):
        self.assertEqual(self.client.get(reverse("contratos:detalhe", args=[99999])).status_code, 404)


class ListaTests(Base):
    def setUp(self):
        super().setUp()
        entrar(self.client, "ana")
        self.criar(objeto="Merenda escolar")
        outro = Contratado.objects.create(tipo_pessoa="PF", documento="52998224725", razao_social="Maria Silva")
        self.criar(sequencial=2, numero_modalidade=2, objeto="Reforma da escola", contratado=outro)

    def numeros(self, **params):
        r = self.client.get(reverse("contratos:lista"), params)
        return [c.numero_formatado for c in r.context["object_list"]]

    def test_lista_tudo_do_mais_novo_para_o_mais_antigo(self):
        self.assertEqual(self.numeros(), ["2.PE.2/2026", "1.PE.15/2026"])

    def test_busca_por_objeto_numero_contratado_e_documento(self):
        self.assertEqual(self.numeros(q="merenda"), ["1.PE.15/2026"])
        self.assertEqual(self.numeros(q="1.PE.15"), ["1.PE.15/2026"])
        self.assertEqual(self.numeros(q="maria"), ["2.PE.2/2026"])
        self.assertEqual(self.numeros(q="529.982.247-25"), ["2.PE.2/2026"])
        self.assertEqual(self.numeros(q="11.222.333/0001-81"), ["1.PE.15/2026"])
        self.assertEqual(self.numeros(q="nada"), [])

    def test_mensagem_quando_nao_ha_resultado(self):
        r = self.client.get(reverse("contratos:lista"), {"q": "nada"})
        self.assertContains(r, "Nenhum contrato encontrado")

    def test_paginacao(self):
        for i in range(3, 30):
            self.criar(sequencial=i, numero_modalidade=(i % 100) or 1)
        r = self.client.get(reverse("contratos:lista"))
        self.assertTrue(r.context["is_paginated"])
        self.assertEqual(len(r.context["object_list"]), 25)
