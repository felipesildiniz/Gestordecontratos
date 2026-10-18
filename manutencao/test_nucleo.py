"""Testes do backup e da restauração (E4.1).

Rodam com:  python manage.py test   (ou: python -m unittest manutencao.test_nucleo)
Os testes marcados "com PostgreSQL" criam e apagam bancos temporários próprios
(nomes teste_bkp_*), usando o usuário do .env (precisa de CREATEDB). Se o
PostgreSQL ou suas ferramentas (pg_dump, pg_restore, psql) não estiverem
disponíveis, esses testes são pulados.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from config.env import carregar_env, texto

from . import nucleo
from .nucleo import ErroBackup

BASE_DIR = Path(__file__).resolve().parent.parent
carregar_env(BASE_DIR / ".env")


def _cfg(nome="postgres"):
    return {
        "nome": nome,
        "usuario": texto("DB_USUARIO", "gestor"),
        "senha": texto("DB_SENHA"),
        "host": texto("DB_HOST", "localhost"),
        "porta": texto("DB_PORTA", "5432"),
    }


def _postgres_disponivel():
    try:
        psql = nucleo.localizar_ferramenta("psql", texto("PG_BIN") or None)
        nucleo.localizar_ferramenta("pg_dump", texto("PG_BIN") or None)
        nucleo.localizar_ferramenta("pg_restore", texto("PG_BIN") or None)
        nucleo._executar([psql, *nucleo._conexao(_cfg()), "-d", "postgres", "-tAc", "SELECT 1"],
                         _cfg(), "teste de conexão")
        return True
    except ErroBackup:
        return False


COM_POSTGRES = _postgres_disponivel()


def _sql(banco, comando):
    """Executa um comando SQL e devolve o texto da resposta."""
    psql = nucleo.localizar_ferramenta("psql", texto("PG_BIN") or None)
    return nucleo._executar(
        [psql, *nucleo._conexao(_cfg()), "-d", banco, "-tAc", comando], _cfg(), "SQL de teste"
    ).strip()


class ProjetoTemporario(unittest.TestCase):
    """Cria uma pasta de 'projeto' com código, PDFs e backups de mentira."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bkp_teste_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.projeto = self.tmp / "projeto"
        self.pdfs = self.projeto / "media"
        self.backups = self.projeto / "backups"
        (self.projeto / "config").mkdir(parents=True)
        (self.projeto / ".venv" / "lib").mkdir(parents=True)
        (self.projeto / "staticfiles").mkdir()
        (self.projeto / "config" / "settings.py").write_text("X = 1\n", encoding="utf-8")
        (self.projeto / "config" / "x.pyc").write_bytes(b"lixo")
        (self.projeto / ".env").write_text("DJANGO_SECRET_KEY=abc\n", encoding="utf-8")
        (self.projeto / ".venv" / "lib" / "pesado.py").write_text("nao entra\n")
        (self.projeto / "staticfiles" / "a.css").write_text("nao entra\n")
        (self.pdfs / "2026").mkdir(parents=True)
        (self.pdfs / "2026" / "contrato-1.pdf").write_bytes(b"%PDF-1.4 conteudo um")
        (self.pdfs / "2026" / "contrato-2.pdf").write_bytes(b"%PDF-1.4 conteudo dois")


class CompactacaoTests(ProjetoTemporario):
    def test_projeto_ignora_venv_estaticos_pdfs_e_backups(self):
        self.backups.mkdir()
        (self.backups / "antigo.txt").write_text("nao entra")
        destino = self.tmp / "p.zip"
        total = nucleo._compactar_pasta(self.projeto, destino, ignorar_pastas=[self.pdfs])
        with zipfile.ZipFile(destino) as z:
            nomes = set(z.namelist())
        self.assertEqual(nomes, {".env", "config/settings.py"})
        self.assertEqual(total, 2)

    def test_pasta_de_pdfs_inexistente_gera_zip_vazio(self):
        destino = self.tmp / "vazio.zip"
        self.assertEqual(nucleo._compactar_pasta(self.tmp / "nao-existe", destino), 0)
        with zipfile.ZipFile(destino) as z:
            self.assertEqual(z.namelist(), [])

    def test_extrair_recusa_caminho_fora_da_pasta(self):
        mal = self.tmp / "mal.zip"
        with zipfile.ZipFile(mal, "w") as z:
            z.writestr("../fora.txt", "x")
        with self.assertRaises(ErroBackup):
            nucleo._extrair_zip(mal, self.tmp / "destino")
        self.assertFalse((self.tmp / "fora.txt").exists())


class RetencaoTests(ProjetoTemporario):
    def _criar(self, nome, completo=True):
        pasta = self.backups / nome
        pasta.mkdir(parents=True)
        if completo:
            (pasta / "manifest.json").write_text("{}")
        return pasta

    def test_mantem_apenas_os_mais_recentes(self):
        for dia in range(1, 6):
            self._criar(f"2026-10-0{dia}_020000")
        apagados = nucleo.aplicar_retencao(self.backups, 2)
        self.assertEqual(apagados, ["2026-10-01_020000", "2026-10-02_020000", "2026-10-03_020000"])
        self.assertEqual([p.name for p in nucleo.listar_backups(self.backups)],
                         ["2026-10-04_020000", "2026-10-05_020000"])

    def test_nunca_apaga_o_ultimo_nem_pastas_alheias(self):
        self._criar("2026-10-01_020000")
        parcial = self._criar("2026-10-02_020000.parcial", completo=False)
        outra = self.backups / "minhas-fotos"
        outra.mkdir()
        nucleo.aplicar_retencao(self.backups, 0)
        self.assertEqual(len(nucleo.listar_backups(self.backups)), 1)
        self.assertTrue(parcial.exists())
        self.assertTrue(outra.exists())


class VerificacaoTests(ProjetoTemporario):
    def _backup_falso(self):
        pasta = self.tmp / "2026-10-17_020000"
        pasta.mkdir()
        manifesto = {"arquivos": {}}
        for nome in nucleo.ARQUIVOS_DO_BACKUP:
            (pasta / nome).write_bytes(nome.encode() * 10)
            manifesto["arquivos"][nome] = {
                "bytes": (pasta / nome).stat().st_size,
                "sha256": nucleo.soma_sha256(pasta / nome),
            }
        (pasta / "manifest.json").write_text(json.dumps(manifesto))
        return pasta

    def test_backup_integro_nao_tem_problemas(self):
        self.assertEqual(nucleo.verificar_backup(self._backup_falso()), [])

    def test_detecta_arquivo_alterado(self):
        pasta = self._backup_falso()
        original = (pasta / "arquivos.zip").read_bytes()
        (pasta / "arquivos.zip").write_bytes(original[:-1] + b"X")  # mesmo tamanho
        problemas = nucleo.verificar_backup(pasta)
        self.assertEqual(len(problemas), 1)
        self.assertIn("corrompido", problemas[0])

    def test_detecta_arquivo_ausente_truncado_e_sem_manifesto(self):
        pasta = self._backup_falso()
        (pasta / "banco.dump").unlink()
        (pasta / "projeto.zip").write_bytes(b"curto")
        textos = " ".join(nucleo.verificar_backup(pasta))
        self.assertIn("banco.dump não existe", textos)
        self.assertIn("projeto.zip tem tamanho diferente", textos)
        (pasta / "manifest.json").unlink()
        self.assertIn("manifest.json", nucleo.verificar_backup(pasta)[0])


class FerramentasTests(unittest.TestCase):
    def test_programa_inexistente_da_mensagem_clara(self):
        with self.assertRaises(ErroBackup) as ctx:
            nucleo.localizar_ferramenta("programa_que_nao_existe_xyz")
        self.assertIn("PG_BIN", str(ctx.exception))


@unittest.skipUnless(COM_POSTGRES, "PostgreSQL ou suas ferramentas indisponíveis")
class ComPostgresTests(ProjetoTemporario):
    """Backup e restauração de verdade, em bancos temporários."""

    def setUp(self):
        super().setUp()
        sufixo = str(os.getpid())
        self.origem = f"teste_bkp_origem_{sufixo}"
        self.destino = f"teste_bkp_destino_{sufixo}"
        for banco in (self.origem, self.destino):
            _sql("postgres", f'DROP DATABASE IF EXISTS "{banco}"')
        _sql("postgres", f'CREATE DATABASE "{self.origem}"')
        self.addCleanup(self._limpar)
        _sql(self.origem, "CREATE TABLE contrato (id serial PRIMARY KEY, numero text)")
        _sql(self.origem, "INSERT INTO contrato (numero) VALUES ('1.PE.1/2026'),('2.CE.7/2026')")

    def _limpar(self):
        for banco in (self.origem, self.destino):
            _sql("postgres", f'DROP DATABASE IF EXISTS "{banco}"')

    def _fazer(self, **extra):
        return nucleo.fazer_backup(
            _cfg(self.origem), self.projeto, self.pdfs, self.backups,
            pg_bin=texto("PG_BIN") or None, **extra,
        )

    def test_backup_e_restauracao_devolvem_os_mesmos_dados(self):
        r = self._fazer(pasta_copia=self.tmp / "disco-externo")
        pasta = Path(r["pasta"])
        self.assertEqual(r["avisos"], [])
        self.assertEqual(nucleo.verificar_backup(pasta), [])
        self.assertTrue((self.tmp / "disco-externo" / pasta.name / "manifest.json").is_file())
        self.assertEqual(r["manifesto"]["quantidade"]["pdfs"], 2)

        # Muda o banco depois do backup: a restauração deve trazer o estado antigo.
        _sql(self.origem, "DELETE FROM contrato")
        res = nucleo.restaurar_backup(
            pasta, _cfg(), self.destino,
            pasta_arquivos_destino=self.tmp / "pdfs-restaurados",
            pasta_projeto_destino=self.tmp / "projeto-restaurado",
            pg_bin=texto("PG_BIN") or None,
        )
        self.assertEqual(res["pdfs"], 2)
        self.assertEqual(
            _sql(self.destino, "SELECT string_agg(numero, ',' ORDER BY id) FROM contrato"),
            "1.PE.1/2026,2.CE.7/2026",
        )
        self.assertEqual(
            (self.tmp / "pdfs-restaurados" / "2026" / "contrato-2.pdf").read_bytes(),
            b"%PDF-1.4 conteudo dois",
        )
        self.assertEqual(
            (self.tmp / "projeto-restaurado" / ".env").read_text(encoding="utf-8"),
            "DJANGO_SECRET_KEY=abc\n",
        )
        # A restauração não tocou no banco original.
        self.assertEqual(_sql(self.origem, "SELECT count(*) FROM contrato"), "0")

    def test_restauracao_nao_sobrescreve_banco_existente_sem_pedir(self):
        pasta = Path(self._fazer()["pasta"])
        with self.assertRaises(ErroBackup) as ctx:
            nucleo.restaurar_backup(pasta, _cfg(), self.origem, pg_bin=texto("PG_BIN") or None)
        self.assertIn("já existe", str(ctx.exception))
        self.assertEqual(_sql(self.origem, "SELECT count(*) FROM contrato"), "2")

    def test_restauracao_sobrescrevendo_quando_confirmado(self):
        pasta = Path(self._fazer()["pasta"])
        _sql(self.origem, "DELETE FROM contrato WHERE numero LIKE '1.%'")
        nucleo.restaurar_backup(pasta, _cfg(), self.origem, sobrescrever=True,
                                pg_bin=texto("PG_BIN") or None)
        self.assertEqual(_sql(self.origem, "SELECT count(*) FROM contrato"), "2")

    def test_restauracao_recusa_backup_corrompido(self):
        pasta = Path(self._fazer()["pasta"])
        dump = pasta / "banco.dump"
        dados = bytearray(dump.read_bytes())
        dados[len(dados) // 2] ^= 0xFF
        dump.write_bytes(bytes(dados))
        with self.assertRaises(ErroBackup) as ctx:
            nucleo.restaurar_backup(pasta, _cfg(), self.destino, pg_bin=texto("PG_BIN") or None)
        self.assertIn("corrompido", str(ctx.exception))
        self.assertEqual(_sql("postgres", f"SELECT count(*) FROM pg_database WHERE datname='{self.destino}'"), "0")

    def test_nome_de_banco_invalido_e_recusado(self):
        pasta = Path(self._fazer()["pasta"])
        with self.assertRaises(ErroBackup):
            nucleo.restaurar_backup(pasta, _cfg(), 'x"; DROP DATABASE postgres; --',
                                    pg_bin=texto("PG_BIN") or None)

    def test_pasta_de_pdfs_de_destino_precisa_estar_vazia(self):
        pasta = Path(self._fazer()["pasta"])
        ocupada = self.tmp / "ocupada"
        ocupada.mkdir()
        (ocupada / "x.txt").write_text("x")
        with self.assertRaises(ErroBackup):
            nucleo.restaurar_backup(pasta, _cfg(), self.destino, pasta_arquivos_destino=ocupada,
                                    pg_bin=texto("PG_BIN") or None)

    def test_falha_na_copia_gera_aviso_mas_mantem_o_backup_local(self):
        bloqueio = self.tmp / "arquivo-comum"
        bloqueio.write_text("isto não é uma pasta")
        r = self._fazer(pasta_copia=bloqueio / "dentro")
        self.assertTrue(Path(r["pasta"]).is_dir())
        self.assertEqual(nucleo.verificar_backup(r["pasta"]), [])
        self.assertTrue(any("falhou" in a for a in r["avisos"]))

    def test_sem_copia_configurada_gera_aviso(self):
        r = self._fazer()
        self.assertTrue(any("BACKUP_PASTA_COPIA" in a for a in r["avisos"]))

    def test_retencao_apos_varios_backups(self):
        inicio = datetime(2026, 10, 1, 2, 0, 0)
        for dia in range(4):
            nucleo.fazer_backup(_cfg(self.origem), self.projeto, self.pdfs, self.backups,
                                manter=2, agora=inicio + timedelta(days=dia),
                                pg_bin=texto("PG_BIN") or None)
        self.assertEqual([p.name for p in nucleo.listar_backups(self.backups)],
                         ["2026-10-03_020000", "2026-10-04_020000"])
        self.assertEqual([p for p in self.backups.iterdir() if p.name.endswith(".parcial")], [])

    def test_banco_inexistente_falha_e_nao_deixa_lixo(self):
        with self.assertRaises(ErroBackup):
            nucleo.fazer_backup(_cfg("banco_que_nao_existe_xyz"), self.projeto, self.pdfs,
                                self.backups, pg_bin=texto("PG_BIN") or None)
        self.assertEqual(list(self.backups.iterdir()), [])

    def test_mesmo_segundo_nao_sobrescreve_backup_existente(self):
        momento = datetime(2026, 10, 1, 2, 0, 0)
        kw = dict(pg_bin=texto("PG_BIN") or None, agora=momento)
        nucleo.fazer_backup(_cfg(self.origem), self.projeto, self.pdfs, self.backups, **kw)
        with self.assertRaises(ErroBackup):
            nucleo.fazer_backup(_cfg(self.origem), self.projeto, self.pdfs, self.backups, **kw)


if __name__ == "__main__":
    unittest.main()
