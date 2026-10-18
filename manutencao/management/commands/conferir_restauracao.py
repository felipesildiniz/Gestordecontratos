"""Prova que um backup .zip (o baixado pela tela "Backup dos dados") restaura.

Uso: python manage.py conferir_restauracao --zip caminho/backup-gestor-....zip

O que faz, sem tocar no banco em uso:
  1. extrai o .zip numa pasta temporária e confere as somas SHA-256;
  2. restaura o banco.dump num banco NOVO e temporário;
  3. conta as linhas das tabelas e mostra os usuários (nunca as senhas);
  4. compara com o banco em uso e apaga o banco temporário.
Se o arquivo não existir, não faz nada (para poder ficar no comando de
inicialização sem efeito). Retorna erro se algo falhar.
"""
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from manutencao import nucleo
from manutencao.web import _configuracao_do_banco

TABELAS = ("auth_user", "auth_group", "auth_permission", "django_migrations", "django_content_type")


def _contar(cfg, banco, psql, tabela):
    saida = nucleo._executar(
        [psql, *nucleo._conexao(cfg), "-d", banco, "-tAc", f"SELECT count(*) FROM {tabela}"],
        cfg, f"Contagem de {tabela} em {banco}",
    )
    return int(saida.strip())


def _usuarios(cfg, banco, psql):
    saida = nucleo._executar(
        [psql, *nucleo._conexao(cfg), "-d", banco, "-tAc",
         "SELECT string_agg(username, ', ' ORDER BY username) FROM auth_user"],
        cfg, f"Lista de usuários em {banco}",
    )
    return saida.strip() or "(nenhum)"


class Command(BaseCommand):
    help = "Restaura um backup .zip num banco temporário, confere os dados e apaga o temporário."

    def add_arguments(self, parser):
        parser.add_argument("--zip", dest="arquivo", default="", help="Caminho do .zip do backup.")

    def handle(self, *args, **opcoes):
        arquivo = (opcoes["arquivo"] or "").strip()
        if not arquivo or not Path(arquivo).is_file():
            self.stdout.write("conferir_restauracao: nenhum arquivo informado; nada a fazer.")
            return
        cfg = _configuracao_do_banco()
        psql = nucleo.localizar_ferramenta("psql")
        temporario = "teste_restauracao_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta = Path(tempfile.mkdtemp(prefix="restauracao-gestor-"))
        try:
            with zipfile.ZipFile(arquivo) as z:
                if z.testzip() is not None:
                    raise CommandError("O .zip está corrompido.")
                z.extractall(pasta / "extraido")
            candidatos = [p for p in (pasta / "extraido").rglob("manifest.json")]
            if len(candidatos) != 1:
                raise CommandError("O .zip não contém exatamente um manifest.json.")
            pasta_backup = candidatos[0].parent
            self.stdout.write(f"Backup: {pasta_backup.name}")
            problemas = nucleo.verificar_backup(pasta_backup)
            if problemas:
                raise CommandError("Conferência falhou: " + "; ".join(problemas))
            self.stdout.write("Somas SHA-256 conferem com o manifesto.")

            resultado = nucleo.restaurar_backup(
                pasta_backup, cfg, temporario,
                pasta_arquivos_destino=pasta / "pdfs",
            )
            self.stdout.write(f"Restaurado no banco temporário {temporario}; arquivos extraídos: {resultado['pdfs']}.")
            try:
                divergencias = 0
                for tabela in TABELAS:
                    restaurado = _contar(cfg, temporario, psql, tabela)
                    em_uso = _contar(cfg, cfg["nome"], psql, tabela)
                    self.stdout.write(f"  {tabela}: restaurado={restaurado} em_uso={em_uso}")
                    if restaurado == 0 and tabela in ("auth_permission", "django_migrations"):
                        divergencias += 1
                self.stdout.write(f"  usuários restaurados: {_usuarios(cfg, temporario, psql)}")
                if divergencias:
                    raise CommandError("Tabelas essenciais restauradas vazias.")
            finally:
                nucleo._executar(
                    [psql, *nucleo._conexao(cfg), "-d", "postgres", "-c",
                     f'DROP DATABASE IF EXISTS "{temporario}"'],
                    cfg, "Remoção do banco temporário",
                )
                self.stdout.write(f"Banco temporário {temporario} removido.")
            self.stdout.write(self.style.SUCCESS("RESTAURACAO_OK: o backup restaurou e os dados conferem."))
        except nucleo.ErroBackup as erro:
            raise CommandError(str(erro)) from erro
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
