from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.generator import gerar_base_vendas_suja
from src.pipeline import exportar_relatorio_excel, processar_dataframe

st.set_page_config(
    page_title="Data Quality Gatekeeper",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Data Quality Gatekeeper")
st.caption(
    "Auditoria automatizada de planilhas de vendas: validação de contratos, "
    "separação de quarentena e exportação executiva."
)

# Barra lateral para seleção da fonte de dados
with st.sidebar:
    st.header("Fonte dos Dados")
    modo = st.radio(
        "Escolha como carregar a planilha:",
        options=["Simular base com erros", "Enviar arquivo (CSV ou Excel)"],
    )

    df_entrada: pd.DataFrame | None = None

    if modo == "Simular base com erros":
        qtd_linhas = st.slider(
            "Quantidade de linhas simuladas",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
        )
        seed = st.number_input("Seed aleatória", min_value=1, max_value=9999, value=42)
        df_entrada = gerar_base_vendas_suja(total_linhas=qtd_linhas, seed=int(seed))
    else:
        arquivo = st.file_uploader(
            "Selecione um arquivo .csv ou .xlsx",
            type=["csv", "xlsx"],
        )
        if arquivo is not None:
            if arquivo.name.lower().endswith(".csv"):
                df_entrada = pd.read_csv(arquivo)
            else:
                df_entrada = pd.read_excel(arquivo)

    st.divider()
    st.markdown(
        "**Regras auditadas:**\n"
        "- CPF válido (dígitos verificadores)\n"
        "- E-mail e UF válidos\n"
        "- Data válida e não futura\n"
        "- IDs únicos (sem duplicidade)\n"
        "- Quantidade, preço e desconto consistentes"
    )

if df_entrada is None or df_entrada.empty:
    st.info("Envie uma planilha CSV ou Excel na barra lateral para iniciar a auditoria.")
    st.stop()

# Executa o motor de auditoria
resultado = processar_dataframe(df_entrada)
kpis = resultado["kpis"]
df_aprovados = resultado["aprovados"]
df_quarentena = resultado["quarentena"]
df_ranking = resultado["ranking_erros"]

# Cartões de KPIs no topo
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Recebido", f"{kpis['total_registros']:,}")
col2.metric(
    "Registros Aprovados",
    f"{kpis['total_aprovados']:,}",
    delta=f"{kpis['taxa_aprovacao_pct']}% da base",
)
col3.metric(
    "Em Quarentena",
    f"{kpis['total_quarentena']:,}",
    delta=f"-{kpis['taxa_rejeicao_pct']}% com erro",
    delta_color="inverse",
)
col4.metric(
    "Receita Líquida Validada",
    f"R$ {kpis['receita_liquida_aprovada']:,.2f}",
)

st.divider()

# Gráfico de ofensores + botões de download
col_graf, col_down = st.columns([2, 1])

with col_graf:
    st.subheader("Principais Motivos de Rejeição")
    if df_ranking.empty:
        st.success("Nenhuma anomalia encontrada na base!")
    else:
        grafico_df = df_ranking.set_index("tipo_erro")[["ocorrencias"]]
        st.bar_chart(grafico_df, horizontal=True)

with col_down:
    st.subheader("Exportar Resultados")
    st.write("Baixe o relatório executivo formatado ou as bases separadas:")

    excel_bytes = exportar_relatorio_excel(resultado)
    st.download_button(
        label="📥 Baixar Relatório Executivo (.xlsx)",
        data=excel_bytes,
        file_name="relatorio_auditoria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.download_button(
        label="✅ Baixar Base Aprovada (.csv)",
        data=df_aprovados.to_csv(index=False, encoding="utf-8-sig"),
        file_name="vendas_aprovadas.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.download_button(
        label="🚨 Baixar Base em Quarentena (.csv)",
        data=df_quarentena.to_csv(index=False, encoding="utf-8-sig"),
        file_name="vendas_quarentena.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

# Abas de inspeção detalhada
aba_quarentena, aba_aprovados, aba_ranking = st.tabs([
    f"🚨 Quarentena ({len(df_quarentena)})",
    f"✅ Dados Aprovados ({len(df_aprovados)})",
    "📊 Ranking de Anomalias",
])

with aba_quarentena:
    if df_quarentena.empty:
        st.success("Nenhum registro em quarentena.")
    else:
        tipos_disponiveis = ["Todos"] + df_ranking["tipo_erro"].tolist()
        filtro_erro = st.selectbox("Filtrar por motivo de erro:", options=tipos_disponiveis)

        df_exibir = df_quarentena
        if filtro_erro != "Todos":
            df_exibir = df_quarentena[df_quarentena["motivo_erro"].str.contains(filtro_erro, regex=False)]

        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

with aba_aprovados:
    if df_aprovados.empty:
        st.warning("Nenhum registro aprovado.")
    else:
        st.dataframe(df_aprovados, use_container_width=True, hide_index=True)

with aba_ranking:
    if df_ranking.empty:
        st.info("Sem erros registrados.")
    else:
        st.dataframe(
            df_ranking.rename(columns={
                "tipo_erro": "Tipo de Erro",
                "ocorrencias": "Ocorrências",
                "percentual_registros_afetados": "% da Base Total",
            }),
            use_container_width=True,
            hide_index=True,
        )