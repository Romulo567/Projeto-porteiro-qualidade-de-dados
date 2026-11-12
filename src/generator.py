from pathlib import Path
import random
from datetime import datetime, timedelta
import pandas as pd

def gerar_cpf_valido() -> str:
    def calcular_digito(digitos: list[int]) -> int:
        peso = len(digitos) + 1
        soma = sum(d * (peso - idx) for idx, d in enumerate(digitos))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto
        
    nove_digitos = [random.randint(0, 9) for _ in range(9)]
    if len(set(nove_digitos)) == 1:
        nove_digitos[0] = (nove_digitos[0] + 1) % 10

    d1 = calcular_digito(nove_digitos)
    d2 = calcular_digito(nove_digitos + [d1])
    cpf = nove_digitos + [d1, d2]

    return (
        f"{cpf[0]}{cpf[1]}{cpf[2]}."
        f"{cpf[3]}{cpf[4]}{cpf[5]}."
        f"{cpf[6]}{cpf[7]}{cpf[8]}-"
        f"{cpf[9]}{cpf[10]}"
    )

def gerar_base_vendas_suja(total_linhas: int = 500, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)

    produtos = [
        ("Notebook Pro 16", "Eletrônicos", 6499.90),
        ("Monitor Ultrawide 34", "Periféricos", 2899.00),
        ("Teclado Mecânico RGB", "Periféricos", 459.90),
        ("Mouse Wireless Ergonomic", "Periféricos", 289.50),
        ("Headset Noise Cancelling", "Áudio", 899.00),
        ("Cadeira Ergonômica Mesh", "Escritório", 1590.00),
    ]
    ufs_validas = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "DF", "PE", "GO"]
    canais = ["Site Oficial", "App Mobile", "Marketplace", "WhatsApp Comercial"]
    status_pagamento = ["Aprovado", "Pendente", "Cancelado", "Estornado"]

    data_base = datetime(2026, 10, 1)
    registros = []

    for i in range(1, total_linhas + 1):
        nome_prod, categoria, preco_base = random.choice(produtos)
        qtd = random.randint(1, 5)
        desconto = round(random.choice([0.0, 0.0, 0.05, 0.10, 0.15]) * (preco_base * qtd), 2)
        dt_venda = data_base + timedelta(days=random.randint(0, 35))

        registro = {
            "id_pedido": f"PED-{10000 + i}",
            "data_venda": dt_venda.strftime("%Y-%m-%d"),
            "cpf_cliente": gerar_cpf_valido(),
            "email_cliente": f"cliente{i}@dominio.com.br",
            "uf": random.choice(ufs_validas),
            "produto": nome_prod,
            "categoria": categoria,
            "quantidade": qtd,
            "preco_unitario": preco_base,
            "desconto": desconto,
            "canal_venda": random.choice(canais),
            "status_pagamento": random.choice(status_pagamento),
        }

        if random.random() < 0.22:
            tipo_erro = random.choice([
                "cpf_invalido",
                "email_invalido",
                "data_futura_ou_invalida",
                "quantidade_negativa_ou_zero",
                "desconto_maior_que_total",
                "uf_inexistente",
                "valor_nulo",
                "id_duplicado",
            ])

            if tipo_erro == "cpf_invalido":
                registro["cpf_cliente"] = random.choice(["111.111.111-11", "123.456.789-00", "99999999999", "ABC.123.456-99"])
            elif tipo_erro == "email_invalido":
                registro["email_cliente"] = random.choice([f"cliente{i}_sem_arroba.com", "email@", "   ", None])
            elif tipo_erro == "data_futura_ou_invalida":
                registro["data_venda"] = random.choice(["2099-12-31", "31/02/2026", "data_pendente"])
            elif tipo_erro == "quantidade_negativa_ou_zero":
                registro["quantidade"] = random.choice([0, -2, -1])
            elif tipo_erro == "desconto_maior_que_total":
                registro["desconto"] = round(preco_base * qtd * 1.5, 2)
            elif tipo_erro == "uf_inexistente":
                registro["uf"] = random.choice(["XX", "BR", "SPO", "12"])
            elif tipo_erro == "valor_nulo":
                campo_nulo = random.choice(["cpf_cliente", "produto", "preco_unitario"])
                registro[campo_nulo] = None
            elif tipo_erro == "id_duplicado" and i > 1:
                registro["id_pedido"] = f"PED-{10000 + i - 1}"

        registros.append(registro)

    return pd.DataFrame(registros)

def salvar_base_bruta(caminho_saida: str | Path = "data/raw/vendas_brutas.csv", total_linhas: int = 500) -> Path:

    destino = Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df = gerar_base_vendas_suja(total_linhas=total_linhas)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"[OK] Base bruta gerada em '{destino}' com {len(df)} registros.")
    return destino

if __name__ == "__main__":
    salvar_base_bruta()