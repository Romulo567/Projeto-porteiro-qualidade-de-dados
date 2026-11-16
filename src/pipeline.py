from collections import Counter
from io import BytesIO
from pathlib import Path
import sys
from typing import Any

import pandas as pd 
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.generator import salvar_base_bruta
from src.schemas import auditar_registro

def processar_dataframe(df_bruto: pd.DataFrame) -> dict[str, Any]:

    df = df_bruto.copy()

    series_ids = df["id_pedido"].dropna().astype(str).str.strip()
    ids_duplicados = set(series_ids[series_ids.duplicated(keep=False)].unique())

    lista_erros: list[list[str]] = []
    contador_erros: Counter[str] = Counter()

    for _, row in df.iterrows():
        erros_linha = auditar_registro(row, ids_duplicados=ids_duplicados)
        lista_erros.append(erros_linha)
        for erro in erros_linha:
            contador_erros[erro] += 1

    df["qtd_erros"] = [len(e) for e in lista_erros]
    df["motivo_erro"] = [" | ".join(e) if e else "OK" for e in lista_erros]

    df_aprovados = df[df["qtd_erros"] == 0].drop(columns=["qtd_erros", "motivo_erro"]).copy()
    df_quarentena = df[df["qtd_erros"] > 0].copy()

    if not df_aprovados.empty:
        df_aprovados["uf"] = df_aprovados["uf"].astype(str).str.strip().str.upper()
        df_aprovados["email_cliente"] = df_aprovados["email_cliente"].astype(str).str.strip().str.lower()
        df_aprovados["quantidade"] = df_aprovados["quantidade"].astype(int)
        df_aprovados["preco_unitario"] = df_aprovados["preco_unitario"].astype(float).round(2)
        df_aprovados["desconto"] = df_aprovados["desconto"].fillna(0.0).astype(float).round(2)
        df_aprovados["valor_bruto"] = (df_aprovados["quantidade"] * df_aprovados["preco_unitario"]).round(2)
        df_aprovados["valor_liquido"] = (df_aprovados["valor_bruto"] - df_aprovados["desconto"]).round(2)

    total_registros = len(df)
    total_aprovados = len(df_aprovados)
    total_quarentena = len(df_quarentena)
    taxa_aprovacao = round((total_aprovados / total_registros) * 100, 2) if total_registros > 0 else 0.0

    linhas_ranking = []
    for tipo_erro, ocorrencias in contador_erros.most_common():
        linhas_ranking.append({
            "tipo_erro": tipo_erro,
            "ocorrencias": ocorrencias,
            "percentual_registros_afetados": round((ocorrencias / total_registros) * 100, 2) if total_registros > 0 else 0.0,
            })
    df_ranking_erros = pd.DataFrame(
        linhas_ranking,
        columns=["tipo_erro", "ocorrencias", "percentual_registros_afetados"]
        )

    kpis = {
        "total_registros": total_registros,
        "total_aprovados": total_aprovados,
        "total_quarentena": total_quarentena,
        "taxa_aprovacao_pct": taxa_aprovacao,
        "taxa_rejeicao_pct": round(100.0 - taxa_aprovacao, 2) if total_registros > 0 else 0.0,
        "total_ocorrencias_erros": sum(contador_erros.values()),
        "receita_liquida_aprovada": round(float(df_aprovados["valor_liquido"].sum()), 2) if not df_aprovados.empty else 0.0,
    }

    return{
        "aprovados": df_aprovados,
        "quarentena": df_quarentena,
        "ranking_erros": df_ranking_erros,
        "kpis": kpis,
    }

def _estilizar_aba(ws, cor_cabecalho: str = "1F4E78") -> None:
    fill_header = PatternFill(start_color=cor_cabecalho, end_color=cor_cabecalho, fill_type="solid")
    font_header = Font(color="FFFFFF", bold=True)

    for cell in ws[1]:
        if cell.value is not None:
            cell.fill = fill_header
            cell.font = font_header
            cell.alignment = Alignment(horizontal="center", vertical="center")

    for col in ws.columns:
        max_len = max (len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 48)

def exportar_relatorio_excel(resultado: dict[str, Any], destino: str | Path | None = None) -> bytes:

    kpis = resultado["kpis"]
    df_resumo_kpis = pd.DataFrame([
        {"Indicador": "Total de registros recebidos", "Valor": kpis["total_registros"]},
        {"Indicador": "Total de registros aprovados (Limpos)", "Valor": kpis["total_aprovados"]},
        {"Indicador": "Total de registros em quarentena (com erros)", "Valor": kpis["total_quarentena"]},
        {"Indicador": "Taxa de qualidade / aprovação (%)", "Valor": f"{kpis["taxa_aprovacao_pct"]}%"},
        {"Indicador": "Taxa de anomalias detectadas", "Valor":  f"{kpis["taxa_rejeicao_pct"]}%"},
        {"Indicador": "Receita líquida validada (R$)", "Valor": f"R$ {kpis["receita_liquida_aprovada"]:,.2F}"},
    ])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resumo_kpis.to_excel(writer, sheet_name="Resumo_Executivo", index=False, startrow=0)
        df_ranking_exibicao = resultado["ranking_erros"].rename(columns={
            "tipo_erro": "Tipo de Erro",
            "ocorrencias": "Ocorrências",
            "percentual_registros_afetados": "% da Base Total",
        })
        df_ranking_exibicao["% da Base Total"] = df_ranking_exibicao["% da Base Total"].map(lambda x: f"{x}%")
        df_ranking_exibicao.to_excel(
            writer,
            sheet_name="Resumo_Executivo",
            index=False,
            startrow=len(df_resumo_kpis) + 3,
        )
        resultado["aprovados"].to_excel(writer, sheet_name="Dados_Aprovados", index=False)
        resultado["quarentena"].to_excel(writer, sheet_name="Quarentena_Erros", index=False)

        wb = writer.book
        _estilizar_aba(wb["Resumo_Executivo"], cor_cabecalho="1F4E78")
        _estilizar_aba(wb["Dados_Aprovados"], cor_cabecalho="2E7D32")
        _estilizar_aba(wb["Quarentena_Erros"], cor_cabecalho="C62828")

        linha_header_ranking = len(df_resumo_kpis) + 4
        fill_ranking = PatternFill(start_color="37474F", end_color="37474F", fill_type="solid")
        for cell in wb["Resumo_Executivo"][linha_header_ranking]:
            cell.fill = fill_ranking
            cell.font = Font(color="FFFFFF", bold=True)

    conteudo_bytes = buffer.getvalue()
    if destino is not None:
        caminho = Path(destino)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(conteudo_bytes)
    
    return conteudo_bytes

def executar_pipeline(
        caminho_entrada: str | Path = "data/raw/vendas_brutas.csv",
        pasta_saida: str | Path = "data/processed",
) -> dict[str, Any]:

    entrada = Path(caminho_entrada)
    if not entrada.exists():
        salvar_base_bruta(entrada)

    df_bruto = pd.read_csv(entrada)
    resultado = processar_dataframe(df_bruto)

    saida_dir = Path(pasta_saida)
    saida_dir.mkdir(parents=True, exist_ok=True)

    caminho_aprovados = saida_dir / "vendas_aprovadas.csv"
    caminho_quarentena = saida_dir / "vendas_quarentena.csv"
    caminho_excel = saida_dir / "relatorio_auditoria.xlsx"

    resultado["aprovados"].to_csv(caminho_aprovados, index=False, encoding="utf-8-sig")
    resultado["quarentena"].to_csv(caminho_quarentena, index=False, encoding="utf-8-sig")
    exportar_relatorio_excel(resultado, destino=caminho_excel)

    kpis = resultado["kpis"]
    print("=" * 60)
    print("RESUMO DA AUDITORIA - DATA QUALITY GATEKEEPER")
    print("=" * 60)
    print(f"Total recebido    : {kpis['total_registros']} linhas")
    print(f"Aprovados (limpos): {kpis['total_aprovados']} ({kpis['taxa_aprovacao_pct']}%)")
    print(f"Quarentena (erros): {kpis['total_quarentena']} ({kpis['taxa_rejeicao_pct']}%)")
    print(f"Receita validada  : R$ {kpis['receita_liquida_aprovada']:,.2f}")
    print("-" * 60)
    print(f"[OK] CSV Aprovados : {caminho_aprovados}")
    print(f"[OK] CSV Quarentena: {caminho_quarentena}")
    print(f"[OK] Excel Executivo: {caminho_excel}")
    print("=" * 60)

    return resultado

if __name__ == "__main__":
    executar_pipeline()