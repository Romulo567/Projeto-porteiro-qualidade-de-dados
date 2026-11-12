from datetime import datetime
import re
from typing import Any
import pandas as pd

UFS_BRASIL = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

STATUS_PAGAMENTO_VALIDOS = {"Aprovado", "Pendente", "Cancelado", "Estornado"}

EMAIL_REGEX = re.compile(r"^[^@\s.]+(?:\.[^@\s.]+)*@[^@\s.]+(?:\.[^@\s.]+)+$")

def _eh_nulo(valor: Any) -> bool:

    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    if isinstance(valor, str) and valor.strip() == "":
        return True
    return False

def validar_cpf(cpf: Any) -> bool:

    if _eh_nulo(cpf):
        return False

    digitos = re.sub(r"\D", "", str(cpf))
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False

    numeros = [int(d) for d in digitos]

    soma1 = sum(numeros[i] * (10 - i) for i in range(9))
    d1 = (soma1 * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if numeros[9] != d1:
        return False

    soma2 = sum(numeros[i] * (11 - i) for i in range(10))
    d2 = (soma2 * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return numeros[10] == d2

def validar_email(email: Any) -> bool:

    if _eh_nulo(email):
        return False
    return bool(EMAIL_REGEX.match(str(email).strip()))

def validar_data_venda(data_str: Any, data_limite: datetime | None = None) -> bool:

    if _eh_nulo(data_str):
        return False

    limite = data_limite or datetime(2026, 12, 31)
    try:
        dt = datetime.strptime(str(data_str).strip(), "%Y-%m-%d")
        return datetime(2020, 1, 1) <= dt <= limite
    except ValueError:
        return False

def validar_uf(uf: Any) -> bool:

    if _eh_nulo(uf):
        return False
    return str(uf).strip().upper() in UFS_BRASIL

def auditar_registro(registro: dict[str, Any] | pd.Series, ids_duplicados: set[str] | None = None) -> list[str]:

    erros: list[str] = []
    duplicados = ids_duplicados or set()

    id_pedido = registro.get("id_pedido")
    if _eh_nulo(id_pedido):
        erros.append("ID do pedido ausente")
    elif str(id_pedido).strip() in duplicados:
        erros.append("ID do pedido duplicado")

    if not validar_data_venda(registro.get("data_venda")):
        erros.append("Data de venda inválida ou no futuro")

    if _eh_nulo(registro.get("cpf_cliente")):
        erros.append("CPF ausente")
    elif not validar_cpf(registro.get("cpf_cliente")):
        erros.append("CPF inválido")

    if not validar_email(registro.get("email_cliente")):
        erros.append("E-mail inválido ou ausente")

    if not validar_uf(registro.get("uf")):
        erros.append("UF inválida")

    if _eh_nulo(registro.get("produto")):
        erros.append("Produto ausente")

    qtd = registro.get("quantidade")
    preco = registro.get("preco_unitario")
    desconto = registro.get("desconto")

    qtd_valida = False
    if _eh_nulo(qtd):
        erros.append("Quantidade ausente")
    else:
        try:
            qtd_num = int(float(qtd))
            if qtd_num <= 0:
                erros.append("Quantidade menor ou igual a zero")
            else:
                qtd_valida = True
        except (ValueError, TypeError):
            erros.append("Quantidade não numerica")

    preco_valido = False
    if _eh_nulo(preco):
        erros.append("Preço unitário ausente")
    else:
        try:
            preco_num = float(preco)
            if preco_num <= 0:
                erros.append("Preço unitário menor ou igual a zero")
            else:
                preco_valido = True
        except (ValueError, TypeError):
            erros.append("Preço unitário não numérico")

    if not _eh_nulo(desconto):
        try:
            desconto_num = float(desconto)
            if desconto_num < 0:
                erros.append("Desconto negativo")
            elif qtd_valida and preco_valido and desconto_num > (float(preco) * int(float(qtd))):
                erros.append("Desconto maior que o valor bruto")
        except (ValueError, TypeError):
            erros.append("Desconto não numérico")

    status_pagamento = registro.get("status_pagamento")
    if _eh_nulo(status_pagamento) or str(status_pagamento).strip() not in STATUS_PAGAMENTO_VALIDOS:
        erros.append("Status de pagamento inválido ou ausente")

    return erros