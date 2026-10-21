"""CPF e CNPJ: limpeza e conferência dos dígitos verificadores."""


def so_digitos(texto):
    return "".join(c for c in (texto or "") if c.isdigit())


def cpf_valido(valor):
    d = so_digitos(valor)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if int(d[tamanho]) != (soma * 10 % 11) % 10:
            return False
    return True


def cnpj_valido(valor):
    d = so_digitos(valor)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for tamanho, p in ((12, pesos), (13, [6] + pesos)):
        soma = sum(int(d[i]) * p[i] for i in range(tamanho))
        resto = soma % 11
        if int(d[tamanho]) != (0 if resto < 2 else 11 - resto):
            return False
    return True


def documento_valido(valor):
    """Devolve 'PF', 'PJ' ou None conforme o documento seja um CPF ou CNPJ válido."""
    d = so_digitos(valor)
    if len(d) == 11 and cpf_valido(d):
        return "PF"
    if len(d) == 14 and cnpj_valido(d):
        return "PJ"
    return None


def formatar_documento(valor):
    d = so_digitos(valor)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return valor
