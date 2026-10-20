"""Criptografia dos backups enviados para fora do Railway (E4.4, D-029).

Esquema híbrido: cada arquivo recebe uma chave AES-256 nova, que é "embrulhada"
com a chave PÚBLICA RSA (RSA-OAEP, SHA-256). O servidor só tem a chave pública:
consegue criptografar, mas NÃO consegue abrir. A chave privada fica só com o
responsável. O conteúdo é cifrado em blocos de 1 MiB com AES-GCM; cada bloco é
autenticado, e o último é marcado, de modo que adulteração, troca de ordem e
arquivo cortado são detectados.

Formato do arquivo .enc:
  "GCBK1\\n" | tamanho da chave embrulhada (2 bytes) | chave embrulhada |
  prefixo do nonce (4 bytes) | blocos: [final (1 byte)][tamanho (4 bytes)][cifrado]
"""
import base64
import os
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGICO = b"GCBK1\n"
BLOCO = 1024 * 1024
BITS_RSA = 4096


class ErroCripto(Exception):
    """Falha ao criptografar ou descriptografar (mensagem em português)."""


def _oaep():
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
    )


def gerar_par_de_chaves(senha, bits=BITS_RSA):
    """Devolve (privada_pem protegida por senha, publica_pem), ambos em bytes."""
    if not senha:
        raise ErroCripto("A chave privada precisa de uma senha.")
    privada = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    privada_pem = privada.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(senha.encode("utf-8")),
    )
    publica_pem = privada.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return privada_pem, publica_pem


def publica_do_texto(texto):
    """Aceita o PEM puro ou o PEM em base64 (cabe em uma variável de ambiente)."""
    bruto = (texto or "").strip()
    if not bruto:
        raise ErroCripto("A chave pública do backup não está configurada.")
    try:
        if not bruto.startswith("-----BEGIN"):
            bruto = base64.b64decode(bruto, validate=True).decode("utf-8")
        chave = serialization.load_pem_public_key(bruto.replace("\\n", "\n").encode("utf-8"))
    except Exception as erro:  # noqa: BLE001
        raise ErroCripto("A chave pública do backup é inválida.") from erro
    if not isinstance(chave, rsa.RSAPublicKey):
        raise ErroCripto("A chave pública do backup precisa ser RSA.")
    return chave


def criptografar_arquivo(origem, destino, chave_publica, tamanho_bloco=BLOCO):
    """Cifra `origem` em `destino` usando a chave pública (objeto RSAPublicKey)."""
    chave = AESGCM.generate_key(bit_length=256)
    embrulhada = chave_publica.encrypt(chave, _oaep())
    prefixo = os.urandom(4)
    aesgcm = AESGCM(chave)
    with open(origem, "rb") as entrada, open(destino, "wb") as saida:
        saida.write(MAGICO + struct.pack(">H", len(embrulhada)) + embrulhada + prefixo)
        contador = 0
        atual = entrada.read(tamanho_bloco)
        while True:
            proximo = entrada.read(tamanho_bloco)
            final = 0 if proximo else 1
            nonce = prefixo + struct.pack(">Q", contador)
            cifrado = aesgcm.encrypt(nonce, atual, MAGICO + bytes([final]))
            saida.write(bytes([final]) + struct.pack(">I", len(cifrado)) + cifrado)
            if final:
                break
            atual = proximo
            contador += 1


def descriptografar_arquivo(origem, destino, chave_privada_pem, senha):
    """Abre `origem` (.enc) em `destino` com a chave privada (PEM, bytes) e a senha."""
    try:
        privada = serialization.load_pem_private_key(chave_privada_pem, senha.encode("utf-8"))
    except Exception as erro:  # noqa: BLE001
        raise ErroCripto("Chave privada ou senha incorreta.") from erro
    try:
        with open(origem, "rb") as entrada, open(destino, "wb") as saida:
            if entrada.read(len(MAGICO)) != MAGICO:
                raise ErroCripto("Este arquivo não é um backup criptografado do sistema.")
            (tamanho,) = struct.unpack(">H", _ler(entrada, 2))
            embrulhada = _ler(entrada, tamanho)
            prefixo = _ler(entrada, 4)
            try:
                chave = privada.decrypt(embrulhada, _oaep())
            except ValueError as erro:
                raise ErroCripto("Esta chave privada não corresponde a este backup.") from erro
            aesgcm = AESGCM(chave)
            contador = 0
            while True:
                final = _ler(entrada, 1)[0]
                (tam,) = struct.unpack(">I", _ler(entrada, 4))
                cifrado = _ler(entrada, tam)
                nonce = prefixo + struct.pack(">Q", contador)
                try:
                    saida.write(aesgcm.decrypt(nonce, cifrado, MAGICO + bytes([final])))
                except InvalidTag as erro:
                    raise ErroCripto("O arquivo está corrompido ou foi alterado.") from erro
                if final:
                    if entrada.read(1):
                        raise ErroCripto("O arquivo tem dados sobrando depois do fim.")
                    return
                contador += 1
    except ErroCripto:
        _apagar(destino)
        raise


def _ler(arquivo, quantos):
    dados = arquivo.read(quantos)
    if len(dados) != quantos:
        raise ErroCripto("O arquivo está incompleto (cortado).")
    return dados


def _apagar(caminho):
    try:
        os.remove(caminho)
    except OSError:
        pass
