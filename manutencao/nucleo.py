"""Núcleo do backup e da restauração (etapa E4.1, decisões D-012, D-022, D-023).

Usa só a biblioteca padrão do Python e as ferramentas do PostgreSQL
(pg_dump, pg_restore, psql). Não depende do Django, para poder ser testado
isoladamente e para funcionar mesmo que o sistema esteja com problema.

Um backup é uma pasta com nome AAAA-MM-DD_HHMMSS contendo:
  banco.dump      cópia do banco (pg_dump, formato custom)
  arquivos.zip    os PDFs enviados ao sistema
  projeto.zip     o código do sistema e o arquivo .env (guarda as senhas!);
                  opcional: o backup feito pela tela do sistema na nuvem não o inclui
  manifest.json   tamanhos e somas SHA-256, usados para conferir o backup
"""
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

FORMATO_PASTA = "%Y-%m-%d_%H%M%S"
PADRAO_PASTA = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{6}$")
PADRAO_NOME_BANCO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
ARQUIVOS_DO_BACKUP = ("banco.dump", "arquivos.zip", "projeto.zip")
# Sempre presentes; o projeto.zip só é conferido se o manifesto o declarar.
ARQUIVOS_OBRIGATORIOS = ("banco.dump", "arquivos.zip")
# Pastas que não entram no projeto.zip (são recriáveis ou são os próprios backups).
PASTAS_IGNORADAS = {
    ".venv", "venv", "__pycache__", "staticfiles", "backups", "restauracao",
    "node_modules", ".mypy_cache", ".ruff_cache", ".pytest_cache",
}


class ErroBackup(Exception):
    """Falha ao fazer, conferir ou restaurar um backup."""


# --------------------------------------------------------------------------
# Ferramentas do PostgreSQL
# --------------------------------------------------------------------------
def localizar_ferramenta(nome, pg_bin=None):
    """Acha pg_dump, pg_restore ou psql. Devolve o caminho ou levanta ErroBackup."""
    sufixo = ".exe" if os.name == "nt" else ""
    if pg_bin:
        candidato = Path(pg_bin) / (nome + sufixo)
        if candidato.is_file():
            return str(candidato)
    achado = shutil.which(nome)
    if achado:
        return achado
    if os.name == "nt":
        padrao = rf"C:\Program Files\PostgreSQL\*\bin\{nome}.exe"
        versoes = sorted(
            glob.glob(padrao),
            key=lambda c: [int(p) for p in re.findall(r"\d+", c.split("PostgreSQL")[1])],
            reverse=True,
        )
        if versoes:
            return versoes[0]
    raise ErroBackup(
        f"Não encontrei o programa '{nome}' do PostgreSQL. Instale o PostgreSQL no "
        "servidor ou informe a pasta 'bin' dele na variável PG_BIN do arquivo .env "
        r"(exemplo: PG_BIN=C:\Program Files\PostgreSQL\17\bin)."
    )


def _ambiente(cfg):
    env = dict(os.environ)
    env["PGPASSWORD"] = cfg.get("senha", "") or ""
    env["PGCONNECT_TIMEOUT"] = "15"
    return env


def _conexao(cfg):
    return ["-h", cfg["host"], "-p", str(cfg["porta"]), "-U", cfg["usuario"]]


def _executar(comando, cfg, descricao):
    try:
        r = subprocess.run(
            comando, env=_ambiente(cfg), capture_output=True, text=True, timeout=3600
        )
    except (OSError, subprocess.TimeoutExpired) as erro:
        raise ErroBackup(f"{descricao}: {erro}") from erro
    if r.returncode != 0:
        raise ErroBackup(f"{descricao} falhou:\n{(r.stderr or r.stdout).strip()}")
    return r.stdout


# --------------------------------------------------------------------------
# Utilitários de arquivo
# --------------------------------------------------------------------------
def soma_sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def _dentro_de(caminho, pasta):
    try:
        Path(caminho).resolve().relative_to(Path(pasta).resolve())
        return True
    except ValueError:
        return False


def _compactar_pasta(origem, destino_zip, ignorar_pastas=(), ignorar_nomes=PASTAS_IGNORADAS):
    """Compacta 'origem' em 'destino_zip'. Devolve a quantidade de arquivos."""
    origem = Path(origem)
    ignorar_pastas = [Path(p).resolve() for p in ignorar_pastas if p]
    total = 0
    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        if origem.is_dir():
            for raiz, pastas, arquivos in os.walk(origem):
                atual = Path(raiz).resolve()
                pastas[:] = [
                    p for p in pastas
                    if p not in ignorar_nomes and (atual / p).resolve() not in ignorar_pastas
                ]
                for nome in arquivos:
                    if nome.endswith(".pyc"):
                        continue
                    caminho = Path(raiz) / nome
                    if caminho.is_symlink() or not caminho.is_file():
                        continue
                    z.write(caminho, caminho.relative_to(origem).as_posix())
                    total += 1
    return total


def _extrair_zip(arquivo_zip, destino):
    """Extrai com proteção contra caminhos fora da pasta de destino."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    base = destino.resolve()
    with zipfile.ZipFile(arquivo_zip) as z:
        for item in z.infolist():
            alvo = (destino / item.filename).resolve()
            if base != alvo and base not in alvo.parents:
                raise ErroBackup(f"Arquivo suspeito dentro do backup: {item.filename}")
        z.extractall(destino)
        return len(z.infolist())


# --------------------------------------------------------------------------
# Backup
# --------------------------------------------------------------------------
def listar_backups(pasta):
    """Pastas de backup completas (com manifest.json), da mais antiga à mais nova."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        return []
    return sorted(
        p for p in pasta.iterdir()
        if p.is_dir() and PADRAO_PASTA.match(p.name) and (p / "manifest.json").is_file()
    )


def aplicar_retencao(pasta, manter):
    """Apaga os backups mais antigos, mantendo os 'manter' mais recentes (mínimo 1)."""
    manter = max(1, int(manter))
    antigos = listar_backups(pasta)[:-manter]
    for p in antigos:
        shutil.rmtree(p)
    return [p.name for p in antigos]


def verificar_backup(pasta):
    """Confere um backup. Devolve a lista de problemas (vazia = tudo certo)."""
    pasta = Path(pasta)
    problemas = []
    manifesto = pasta / "manifest.json"
    if not manifesto.is_file():
        return [f"Não há manifest.json em {pasta}."]
    try:
        dados = json.loads(manifesto.read_text(encoding="utf-8"))
    except ValueError as erro:
        return [f"manifest.json ilegível: {erro}"]
    declarados = dados.get("arquivos", {})
    for nome in ARQUIVOS_DO_BACKUP:
        info = declarados.get(nome)
        caminho = pasta / nome
        if info is None and nome not in ARQUIVOS_OBRIGATORIOS:
            if caminho.is_file():
                problemas.append(f"{nome} existe na pasta mas não consta no manifesto.")
            continue
        if info is None:
            problemas.append(f"{nome} não consta no manifesto.")
        elif not caminho.is_file():
            problemas.append(f"{nome} não existe na pasta do backup.")
        elif caminho.stat().st_size != info["bytes"]:
            problemas.append(f"{nome} tem tamanho diferente do registrado.")
        elif soma_sha256(caminho) != info["sha256"]:
            problemas.append(f"{nome} está corrompido (soma SHA-256 diferente).")
    return problemas


def fazer_backup(cfg, pasta_projeto, pasta_arquivos, pasta_backup,
                 pasta_copia=None, manter=30, pg_bin=None, agora=None,
                 incluir_projeto=True):
    """Faz um backup completo. Devolve um dicionário com o resultado.

    cfg: {"nome", "usuario", "senha", "host", "porta"} do banco a copiar.
    pasta_copia: segundo destino (disco externo ou pasta de rede), opcional.
    incluir_projeto: False para não gravar o projeto.zip (código e .env); é o
    caso do backup baixado pela tela do sistema na nuvem (D-027).
    Se a cópia secundária falhar, o backup local continua valendo e o problema
    vem em resultado["avisos"].
    """
    agora = agora or datetime.now()
    pg_dump = localizar_ferramenta("pg_dump", pg_bin)
    pg_restore = localizar_ferramenta("pg_restore", pg_bin)
    pasta_backup = Path(pasta_backup)
    pasta_backup.mkdir(parents=True, exist_ok=True)

    nome = agora.strftime(FORMATO_PASTA)
    final = pasta_backup / nome
    parcial = pasta_backup / (nome + ".parcial")
    if final.exists() or parcial.exists():
        raise ErroBackup(f"Já existe um backup feito neste mesmo segundo: {nome}.")
    parcial.mkdir()
    try:
        # 1) Banco
        dump = parcial / "banco.dump"
        _executar(
            [pg_dump, "-Fc", "--no-owner", "--no-privileges", *_conexao(cfg),
             "-f", str(dump), cfg["nome"]],
            cfg, "Cópia do banco (pg_dump)",
        )
        listagem = _executar([pg_restore, "--list", str(dump)], cfg,
                             "Conferência da cópia do banco (pg_restore --list)")
        if "TABLE" not in listagem:
            raise ErroBackup("A cópia do banco foi gerada, mas não contém tabelas.")

        # 2) PDFs enviados ao sistema
        total_pdfs = _compactar_pasta(pasta_arquivos, parcial / "arquivos.zip")

        # 3) Código do sistema (inclui .env), sem PDFs nem backups
        total_projeto = 0
        if incluir_projeto:
            total_projeto = _compactar_pasta(
                pasta_projeto, parcial / "projeto.zip",
                ignorar_pastas=[pasta_arquivos, pasta_backup, pasta_copia],
            )

        # 4) Manifesto
        versao = _executar([pg_dump, "--version"], cfg, "Versão do pg_dump").strip()
        manifesto = {
            "versao": 1,
            "criado_em": agora.isoformat(timespec="seconds"),
            "banco": {"nome": cfg["nome"], "host": cfg["host"], "porta": str(cfg["porta"]),
                      "pg_dump": versao},
            "quantidade": {"pdfs": total_pdfs, "arquivos_do_projeto": total_projeto},
            "arquivos": {
                n: {"bytes": (parcial / n).stat().st_size, "sha256": soma_sha256(parcial / n)}
                for n in ARQUIVOS_DO_BACKUP
                if (parcial / n).is_file()
            },
        }
        (parcial / "manifest.json").write_text(
            json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(parcial, final)
    except BaseException:
        shutil.rmtree(parcial, ignore_errors=True)
        raise

    problemas = verificar_backup(final)
    if problemas:
        raise ErroBackup("O backup foi gerado mas não passou na conferência:\n" + "\n".join(problemas))

    resultado = {"pasta": str(final), "copia": None, "avisos": [],
                 "apagados": aplicar_retencao(pasta_backup, manter),
                 "manifesto": manifesto}

    # 5) Cópia em outro lugar (protege contra falha do disco do servidor)
    if pasta_copia:
        try:
            pasta_copia = Path(pasta_copia)
            pasta_copia.mkdir(parents=True, exist_ok=True)
            temporaria = pasta_copia / (nome + ".parcial")
            if temporaria.exists():
                shutil.rmtree(temporaria)
            shutil.copytree(final, temporaria)
            erros = verificar_backup(temporaria)
            if erros:
                shutil.rmtree(temporaria, ignore_errors=True)
                raise ErroBackup("A cópia não confere com o original: " + "; ".join(erros))
            os.replace(temporaria, pasta_copia / nome)
            resultado["copia"] = str(pasta_copia / nome)
            aplicar_retencao(pasta_copia, manter)
        except (OSError, ErroBackup) as erro:
            resultado["avisos"].append(
                f"O backup local está pronto, mas a cópia para '{pasta_copia}' falhou: {erro}"
            )
    else:
        resultado["avisos"].append(
            "Nenhuma cópia em outro lugar está configurada (BACKUP_PASTA_COPIA). "
            "Se o disco do servidor falhar, os backups se perdem junto."
        )
    return resultado


# --------------------------------------------------------------------------
# Restauração
# --------------------------------------------------------------------------
def _banco_existe(cfg, nome, psql):
    saida = _executar(
        [psql, *_conexao(cfg), "-d", "postgres", "-tAc",
         f"SELECT 1 FROM pg_database WHERE datname = '{nome}'"],
        cfg, "Consulta aos bancos existentes",
    )
    return saida.strip() == "1"


def restaurar_backup(pasta, cfg, banco_destino, pasta_arquivos_destino=None,
                     pasta_projeto_destino=None, sobrescrever=False, pg_bin=None):
    """Restaura um backup.

    Por segurança, o padrão é restaurar em um banco NOVO (banco_destino) e em
    pastas vazias, sem tocar no sistema em uso. Para restaurar por cima de um
    banco que já existe, é preciso passar sobrescrever=True.
    """
    pasta = Path(pasta)
    problemas = verificar_backup(pasta)
    if problemas:
        raise ErroBackup("Backup recusado, não passou na conferência:\n" + "\n".join(problemas))
    if not PADRAO_NOME_BANCO.match(banco_destino):
        raise ErroBackup("Nome de banco inválido: use letras, números e sublinhado.")

    pg_restore = localizar_ferramenta("pg_restore", pg_bin)
    psql = localizar_ferramenta("psql", pg_bin)

    existe = _banco_existe(cfg, banco_destino, psql)
    if existe and not sobrescrever:
        raise ErroBackup(
            f"O banco '{banco_destino}' já existe. Escolha outro nome ou confirme que "
            "quer sobrescrevê-lo."
        )
    for rotulo, destino in (("dos PDFs", pasta_arquivos_destino),
                            ("do projeto", pasta_projeto_destino)):
        if destino and Path(destino).exists() and any(Path(destino).iterdir()) and not sobrescrever:
            raise ErroBackup(f"A pasta {rotulo} de destino não está vazia: {destino}")

    if not existe:
        _executar([psql, *_conexao(cfg), "-d", "postgres", "-c",
                   f'CREATE DATABASE "{banco_destino}"'], cfg, "Criação do banco de destino")
    comando = [pg_restore, "--no-owner", "--no-privileges", "--exit-on-error",
               *_conexao(cfg), "-d", banco_destino]
    if existe:
        comando += ["--clean", "--if-exists"]
    comando.append(str(pasta / "banco.dump"))
    _executar(comando, cfg, "Restauração do banco (pg_restore)")

    resultado = {"banco": banco_destino, "pdfs": 0, "projeto": 0}
    if pasta_arquivos_destino:
        resultado["pdfs"] = _extrair_zip(pasta / "arquivos.zip", pasta_arquivos_destino)
    if pasta_projeto_destino and (pasta / "projeto.zip").is_file():
        resultado["projeto"] = _extrair_zip(pasta / "projeto.zip", pasta_projeto_destino)
    return resultado
