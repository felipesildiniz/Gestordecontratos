"""Verificação em duas etapas (MFA) por aplicativo autenticador (E4.3b, D-030).

Obrigatória para todo Admin. Usa TOTP (RFC 6238: 6 dígitos, passo de 30 s),
feito só com a biblioteca padrão do Python, e códigos de recuperação de uso
único. O que é guardado no banco:
- o segredo do aplicativo (texto; quem lê o banco já tem o backup inteiro);
- dos códigos de recuperação, somente o hash (SHA-256): o código aparece uma
  única vez, na tela, quando é gerado.
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import timedelta
from urllib.parse import quote

from django.db import transaction
from django.utils import timezone

from .models import CodigoRecuperacao, DispositivoMFA

CHAVE_SESSAO = "mfa_ok"
EMISSOR = "Gestor de Contratos"
PASSO = 30
DIGITOS = 6
JANELA = 1  # aceita o passo anterior e o seguinte (relógio do celular)
QTD_CODIGOS = 8
LIMITE_FALHAS = 5
BLOQUEIO = timedelta(minutes=15)
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O/1/I


def _agora_ts():
    return time.time()


def _agora():
    return timezone.now()


def gerar_segredo():
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")  # 32 letras


def codigo_em(segredo, passo):
    """Código de 6 dígitos do segredo no passo (contador) dado."""
    chave = base64.b32decode(segredo + "=" * (-len(segredo) % 8), casefold=True)
    resumo = hmac.new(chave, struct.pack(">Q", passo), hashlib.sha1).digest()
    inicio = resumo[-1] & 0x0F
    numero = struct.unpack(">I", resumo[inicio:inicio + 4])[0] & 0x7FFFFFFF
    return str(numero % 10 ** DIGITOS).zfill(DIGITOS)


def uri_otpauth(usuario, segredo):
    rotulo = quote(f"{EMISSOR}:{usuario}")
    return (
        f"otpauth://totp/{rotulo}?secret={segredo}&issuer={quote(EMISSOR)}"
        f"&digits={DIGITOS}&period={PASSO}"
    )


def segredo_legivel(segredo):
    return " ".join(segredo[i:i + 4] for i in range(0, len(segredo), 4))


def svg_qr(uri):
    """QR code em SVG; se a biblioteca faltar, a tela mostra só a chave."""
    try:
        import segno

        return segno.make(uri, error="m").svg_inline(scale=4, border=2)
    except Exception:  # noqa: BLE001 - o QR é só conveniência
        return ""


def _so_digitos(texto):
    return "".join(c for c in (texto or "") if c.isdigit())


def conferir_totp(dispositivo, texto):
    """True se o código está certo e ainda não foi usado. Grava o passo usado."""
    codigo = _so_digitos(texto)
    if len(codigo) != DIGITOS:
        return False
    atual = int(_agora_ts() // PASSO)
    for passo in range(atual - JANELA, atual + JANELA + 1):
        if passo > dispositivo.ultimo_passo and hmac.compare_digest(
            codigo_em(dispositivo.segredo, passo), codigo
        ):
            dispositivo.ultimo_passo = passo
            dispositivo.save(update_fields=["ultimo_passo"])
            return True
    return False


def _hash_codigo(texto):
    limpo = "".join(c for c in (texto or "").upper() if c.isalnum())
    return hashlib.sha256(limpo.encode("utf-8")).hexdigest()


def gerar_codigos(usuario):
    """Troca os códigos de recuperação por um conjunto novo e devolve o texto."""
    CodigoRecuperacao.objects.filter(usuario=usuario).delete()
    codigos = []
    for _ in range(QTD_CODIGOS):
        bruto = "".join(secrets.choice(ALFABETO) for _ in range(10))
        codigos.append(f"{bruto[:5]}-{bruto[5:]}")
        CodigoRecuperacao.objects.create(usuario=usuario, hash=_hash_codigo(bruto))
    return codigos


def codigos_restantes(usuario):
    return CodigoRecuperacao.objects.filter(usuario=usuario, usado_em__isnull=True).count()


def _usar_codigo(usuario, texto):
    return (
        CodigoRecuperacao.objects.filter(
            usuario=usuario, hash=_hash_codigo(texto), usado_em__isnull=True
        ).update(usado_em=_agora())
        == 1
    )


def dispositivo_confirmado(usuario):
    return DispositivoMFA.objects.filter(usuario=usuario, confirmado=True).first()


def bloqueado_ate(dispositivo):
    if dispositivo.bloqueado_ate and dispositivo.bloqueado_ate > _agora():
        return dispositivo.bloqueado_ate
    return None


def verificar_segundo_fator(usuario, texto):
    """Confere o código do aplicativo ou um código de recuperação.

    Devolve "ok", "recuperacao" (entrou com código de recuperação), "errado" ou
    "bloqueado". Erros seguidos bloqueiam por 15 minutos (conta por dispositivo,
    não zera ao entrar de novo com a senha: impede adivinhar os 6 dígitos).
    """
    with transaction.atomic():
        disp = (
            DispositivoMFA.objects.select_for_update()
            .filter(usuario=usuario, confirmado=True)
            .first()
        )
        if disp is None:
            return "errado"
        if bloqueado_ate(disp):
            return "bloqueado"
        resultado = None
        if len(_so_digitos(texto)) == DIGITOS and conferir_totp(disp, texto):
            resultado = "ok"
        elif _usar_codigo(usuario, texto):
            resultado = "recuperacao"
        if resultado:
            disp.falhas = 0
            disp.bloqueado_ate = None
            disp.save(update_fields=["falhas", "bloqueado_ate"])
            return resultado
        disp.falhas += 1
        if disp.falhas >= LIMITE_FALHAS:
            disp.falhas = 0
            disp.bloqueado_ate = _agora() + BLOQUEIO
        disp.save(update_fields=["falhas", "bloqueado_ate"])
        return "errado"


def redefinir(usuario):
    """Apaga o MFA do usuário (aplicativo e códigos). Devolve quantos itens saíram."""
    apagados = DispositivoMFA.objects.filter(usuario=usuario).delete()[0]
    apagados += CodigoRecuperacao.objects.filter(usuario=usuario).delete()[0]
    return apagados
