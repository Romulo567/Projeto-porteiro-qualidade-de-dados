from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.generator import gerar_cpf_valido
from src.schemas import (
    auditar_registro,
    validar_cpf,
    validar_data_venda,
    validar_email,
    validar_uf,
)

def test_validar_cpf_gerado_valido():
    cpf = gerar_cpf_valido()
    assert validar_cpf(cpf) is True

def test_validar_cpf_invalido_digitos_iguais_ou_errados():
    assert validar_cpf("111.111.111-11") is False
    assert validar_cpf("123.456.789-00") is False
    assert validar_cpf("123.456.789-AB") is False
    assert validar_cpf("12345678900") is False
    assert validar_cpf("123.456.789-0") is False
    assert validar_cpf("123.456.789-000") is False
    assert validar_cpf(None) is False

def test_validar_email():
    assert validar_email("cliente10@dominio.com.br") is True
    assert validar_email("cliente_sem_arroba.com") is False
    assert validar_email("   ") is False
    assert validar_email("cliente@dominio") is False
    assert validar_email("cliente@dominio.") is False
    assert validar_email("cliente@dominio..com") is False
    assert validar_email(None) is False

def test_validar_data_venda():
    assert validar_data_venda("2026-10-15") is True
    assert validar_data_venda("2026-02-29") is False  # 2026 não é ano bissexto
    assert validar_data_venda("2026-13-01") is False  # Mês inválido
    assert validar_data_venda("2026-00-10") is False  # Mês inválido
    assert validar_data_venda("2026-01-32") is False  # Dia inválido
    assert validar_data_venda("2026-01-00") is False  # Dia inválido
    assert validar_data_venda("2099-12-31") is False  # Data futura
    assert validar_data_venda(None) is False

def test_validar_uf():
    assert validar_uf("SP") is True
    assert validar_uf("ms") is True
    assert validar_uf("XX") is False 
    assert validar_uf("") is False 
    assert validar_uf(None) is False 

def test_auditar_registro_perfeito():
    registro = {
        "id_pedido": "PED-10001",
        "data_venda": "2026-10-20",
        "cpf_cliente": gerar_cpf_valido(),
        "email_cliente": "comprador@empresa.com.br",
        "uf": "SP",
        "produto": "Notebook Pro 16",
        "categoria": "Eletrônicos",
        "quantidade": 2,
        "preco_unitario": 6499.90,
        "desconto": 500.00,
        "canal_venda": "Site Oficial",
        "status_pagamento": "Aprovado",
    }
    erros = auditar_registro(registro)
    assert erros == []

def test_auditar_registro_multiplos_erros():
    registro = {
        "id_pedido": "PED-10002",
        "data_venda": "2099-12-31",
        "cpf_cliente": "111.111.111-11",
        "email_cliente": "invalido_sem_arroba",
        "uf": "XX",
        "produto": None,
        "categoria": "Periféricos",
        "quantidade": -1,
        "preco_unitario": 100.0,
        "desconto": 500.0,
        "canal_venda": "App Mobile",
        "status_pagamento": "Aprovado",
    }
    erros = auditar_registro(registro, ids_duplicados={"PED-10002"})
    assert "ID do pedido duplicado" in erros
    assert "Data de venda inválida ou no futuro" in erros
    assert "CPF inválido" in erros
    assert "E-mail inválido ou ausente" in erros
    assert "UF inválida" in erros
    assert "Produto ausente" in erros
    assert "Quantidade menor ou igual a zero" in erros