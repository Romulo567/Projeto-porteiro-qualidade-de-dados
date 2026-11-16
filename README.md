# Data Quality Gatekeeper

Pipeline automatizado de **auditoria, higienização e governança de dados** em Python. O projeto atua como um "porteiro" (*gatekeeper*) para planilhas operacionais de vendas: recebe bases brutas sujeitas a erros manuais, aplica contratos de qualidade linha a linha, separa os registros confiáveis dos inválidos (quarentena) e entrega um relatório executivo formatado em Excel além de um painel interativo no Streamlit.

---

## Problema de Negócio

Em operações reais de e-commerce, financeiro e varejo, planilhas preenchidas manualmente costumam chegar aos times de BI e Engenharia com anomalias silenciosas — CPFs inválidos, datas no futuro, IDs duplicados, descontos maiores que o valor bruto e campos obrigatórios vazios. Sem uma camada automatizada de validação, esses dados quebram dashboards ou distorcem indicadores de faturamento.

O **Data Quality Gatekeeper** resolve esse gargalo padronizando a validação antes que o dado entre no banco ou no relatório gerencial.

---

## Arquitetura e Fluxo do Pipeline

```text
data-quality-gatekeeper/
├── assets/                   # Capturas de tela do dashboard, Excel e testes
├── data/
│   ├── raw/                  # Planilhas brutas de entrada (vendas_brutas.csv)
│   └── processed/            # Saídas limpas, quarentena e relatorio_auditoria.xlsx
├── src/
│   ├── generator.py          # Simulador de base de vendas com anomalias propositais
│   ├── schemas.py            # Contratos de dados e regras de validação
│   └── pipeline.py           # Motor de separação (Aprovados vs. Quarentena) e Excel
├── tests/
│   └── test_schemas.py       # Testes unitários automatizados com Pytest
├── app.py                    # Interface web interativa em Streamlit
├── requirements.txt
└── README.md
```

---

## Regras de Qualidade Auditadas (`src/schemas.py`)

- **CPF:** Validação matemática dos dois dígitos verificadores e bloqueio de sequências repetidas.
- **E-mail:** Validação sintática via expressão regular (bloqueando espaços, ausência de `@` e pontos consecutivos).
- **Data da Venda:** Padronização `YYYY-MM-DD` e bloqueio de datas futuras ou inexistentes (ex.: `29/02` em ano não bissexto).
- **Unidade Federativa (UF):** Conferência com as 27 siglas oficiais do Brasil.
- **Integridade de Chave:** Detecção de `id_pedido` ausente ou duplicado na base.
- **Consistência Financeira:** Bloqueio de quantidade `<= 0`, preço unitário `<= 0`, desconto negativo ou desconto maior que o valor bruto (`quantidade * preco_unitario`).
- **Status de Pagamento e Campos Obrigatórios:** Verificação de domínio permitido e valores nulos.

---

## 📸 Demonstração

### Painel Interativo (Streamlit)
Upload de arquivos `.csv`/`.xlsx` ou simulação instantânea, KPIs de qualidade, gráfico de ofensores e download direto dos resultados.
[assets/dashboard.png]

### Relatório Executivo Automatizado (Excel)
Geração de planilha `.xlsx` estilizada com 3 abas (`Resumo_Executivo`, `Dados_Aprovados` e `Quarentena_Erros`).
[assets/excel_resumo.png]

### Rastreabilidade de Quarentena e Testes Automatizados
Inspeção detalhada dos registros rejeitados com motivo exato da falha e cobertura de regras garantida via `pytest`.

| Aba de Quarentena | Suíte de Testes (`pytest`) |
| :---: | :---: |
| [assets/quarentena.png] | [assets/pytest.png] |

---

## Como Executar Localmente

### 1. Clonar o repositório e criar o ambiente virtual
```bash
git clone https://github.com/Romulo567/Projeto-porteiro-qualidade-de-dados.git
cd data-quality-gatekeeper

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Gerar a base simulada e rodar o pipeline CLI
```bash
python src/generator.py
python src/pipeline.py
```
Os arquivos processados serão salvos em `data/processed/` (`vendas_aprovadas.csv`, `vendas_quarentena.csv` e `relatorio_auditoria.xlsx`).

### 3. Executar os testes unitários
```bash
pytest -v
```

### 4. Abrir o painel interativo no navegador
```bash
streamlit run app.py
```

---

## Autor

Desenvolvido por **Rômulo Wagnes Ferreira**  
[GitHub](https://www.google.com/search?q=https://github.com/Romulo567)
