"""Envio de arquivos ao Google Drive (E4.4, D-029), só com a biblioteca padrão.

Usa OAuth com um "refresh token" gerado uma vez pelo responsável (veja
autorizar_google_drive.py). O escopo é `drive.file`: o sistema só enxerga o que
ele mesmo criou, inclusive a pasta dos backups, que ele cria sozinho.
"""
import http.client
import json
import os
import time
import urllib.parse

ENDERECO_TOKEN = "https://oauth2.googleapis.com/token"
ENDERECO_API = "https://www.googleapis.com/drive/v3"
ENDERECO_ENVIO = "https://www.googleapis.com/upload/drive/v3/files"
TIPO_PASTA = "application/vnd.google-apps.folder"
BLOCO_ENVIO = 8 * 1024 * 1024  # múltiplo de 256 KiB, como exige o Google
TENTATIVAS = 3


class ErroDrive(Exception):
    """Falha ao falar com o Google Drive (mensagem em português, sem segredos)."""


def _http(metodo, endereco, cabecalhos=None, corpo=b"", timeout=300):
    """Faz uma requisição. Devolve (status, cabeçalhos em minúsculas, corpo)."""
    partes = urllib.parse.urlsplit(endereco)
    caminho = partes.path + ("?" + partes.query if partes.query else "")
    try:
        conexao = http.client.HTTPSConnection(partes.netloc, timeout=timeout)
        try:
            conexao.request(metodo, caminho, body=corpo, headers=cabecalhos or {})
            resposta = conexao.getresponse()
            dados = resposta.read()
            return (
                resposta.status,
                {k.lower(): v for k, v in resposta.getheaders()},
                dados,
            )
        finally:
            conexao.close()
    except (OSError, http.client.HTTPException) as erro:
        raise ErroDrive(f"Sem conexão com o Google ({type(erro).__name__}).") from erro


def _resumo(corpo):
    try:
        dado = json.loads(corpo.decode("utf-8"))
        erro = dado.get("error")
        if isinstance(erro, dict):
            return erro.get("message", "")[:200]
        return str(erro or dado.get("error_description", ""))[:200]
    except (ValueError, AttributeError):
        return ""


class ClienteDrive:
    def __init__(self, client_id, client_secret, refresh_token, http=_http, dormir=time.sleep):
        self._credenciais = (client_id, client_secret, refresh_token)
        self._http = http
        self._dormir = dormir
        self._token = None

    # --- autenticação ---
    def token(self):
        if self._token:
            return self._token
        client_id, client_secret, refresh_token = self._credenciais
        corpo = urllib.parse.urlencode({
            "client_id": client_id, "client_secret": client_secret,
            "refresh_token": refresh_token, "grant_type": "refresh_token",
        }).encode()
        status, _, dados = self._http(
            "POST", ENDERECO_TOKEN,
            {"Content-Type": "application/x-www-form-urlencoded"}, corpo,
        )
        if status != 200:
            raise ErroDrive(
                f"O Google recusou a autorização do Drive (código {status}: {_resumo(dados)}). "
                "Gere uma nova autorização com autorizar_google_drive.py."
            )
        self._token = json.loads(dados)["access_token"]
        return self._token

    def _json(self, metodo, endereco, corpo=None, esperado=(200,)):
        cabecalhos = {"Authorization": f"Bearer {self.token()}"}
        dados = b""
        if corpo is not None:
            dados = json.dumps(corpo).encode("utf-8")
            cabecalhos["Content-Type"] = "application/json; charset=UTF-8"
        status, _, resposta = self._http(metodo, endereco, cabecalhos, dados)
        if status not in esperado:
            raise ErroDrive(f"O Drive respondeu com erro {status}: {_resumo(resposta)}")
        return json.loads(resposta) if resposta else {}

    # --- pasta ---
    def achar_ou_criar_pasta(self, nome):
        aspas = nome.replace("\\", "\\\\").replace("'", "\\'")
        consulta = f"mimeType='{TIPO_PASTA}' and name='{aspas}' and trashed=false"
        achados = self._json(
            "GET",
            f"{ENDERECO_API}/files?" + urllib.parse.urlencode(
                {"q": consulta, "fields": "files(id,name)", "pageSize": 10}),
        ).get("files", [])
        if achados:
            return achados[0]["id"]
        return self._json(
            "POST", f"{ENDERECO_API}/files?fields=id",
            {"name": nome, "mimeType": TIPO_PASTA},
        )["id"]

    def listar(self, pasta_id):
        """Arquivos da pasta: lista de {id, name, size}."""
        arquivos, pagina = [], None
        while True:
            parametros = {
                "q": f"'{pasta_id}' in parents and trashed=false",
                "fields": "nextPageToken,files(id,name,size)",
                "pageSize": 1000,
            }
            if pagina:
                parametros["pageToken"] = pagina
            resposta = self._json(
                "GET", f"{ENDERECO_API}/files?" + urllib.parse.urlencode(parametros))
            arquivos += resposta.get("files", [])
            pagina = resposta.get("nextPageToken")
            if not pagina:
                return arquivos

    def apagar(self, arquivo_id):
        cabecalhos = {"Authorization": f"Bearer {self.token()}"}
        status, _, resposta = self._http(
            "DELETE", f"{ENDERECO_API}/files/{arquivo_id}", cabecalhos)
        if status not in (200, 204, 404):
            raise ErroDrive(f"Não foi possível apagar no Drive (erro {status}: {_resumo(resposta)})")

    # --- envio ---
    def enviar(self, caminho, nome, pasta_id):
        """Envia o arquivo em blocos e devolve {id, name, size}. Confere o tamanho."""
        total = os.path.getsize(caminho)
        if total == 0:
            raise ErroDrive("O arquivo a enviar está vazio.")
        cabecalhos = {
            "Authorization": f"Bearer {self.token()}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "application/octet-stream",
            "X-Upload-Content-Length": str(total),
        }
        corpo = json.dumps({"name": nome, "parents": [pasta_id]}).encode("utf-8")
        status, saida, resposta = self._http(
            "POST", f"{ENDERECO_ENVIO}?uploadType=resumable&fields=id,name,size",
            cabecalhos, corpo)
        if status != 200 or "location" not in saida:
            raise ErroDrive(f"O Drive não aceitou iniciar o envio (erro {status}: {_resumo(resposta)})")
        sessao = saida["location"]

        with open(caminho, "rb") as arquivo:
            inicio = 0
            while inicio < total:
                arquivo.seek(inicio)
                bloco = arquivo.read(BLOCO_ENVIO)
                fim = inicio + len(bloco) - 1
                status, _, resposta = self._enviar_bloco(sessao, bloco, inicio, fim, total)
                if status in (200, 201):
                    resultado = json.loads(resposta)
                    if int(resultado.get("size", -1)) != total:
                        raise ErroDrive("O Drive guardou o arquivo com tamanho diferente do enviado.")
                    return resultado
                if status != 308:
                    raise ErroDrive(f"O envio ao Drive falhou (erro {status}: {_resumo(resposta)})")
                inicio = fim + 1
        raise ErroDrive("O envio ao Drive terminou sem confirmação do Google.")

    def _enviar_bloco(self, sessao, bloco, inicio, fim, total):
        cabecalhos = {
            "Content-Length": str(len(bloco)),
            "Content-Range": f"bytes {inicio}-{fim}/{total}",
        }
        ultimo = None
        for tentativa in range(1, TENTATIVAS + 1):
            try:
                status, saida, resposta = self._http("PUT", sessao, cabecalhos, bloco)
            except ErroDrive as erro:
                ultimo = erro
            else:
                if status < 500:
                    return status, saida, resposta
                ultimo = ErroDrive(f"O Drive respondeu com erro {status}.")
            self._dormir(2 * tentativa)
        raise ultimo
