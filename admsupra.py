import streamlit as st
import pyodbc
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(page_title="BI Administrativo - Suprasoft", layout="wide")

# --- Cabeçalho com Logos ---
# Dica: Substitua 'logo_supra.png' e 'logo_supramais.png' pelo nome exato dos arquivos das imagens que você tem na pasta
col1, col_espaco, col2 = st.columns([1, 4, 1])
with col1:
    try:
        st.image("logo_supra.png", width=150)
    except:
        st.write("[Logo Supra]")
with col2:
    try:
        st.image("logo_supramais.png", width=150)
    except:
        st.write("[Logo SupraMAIS]")

st.title("📊 BI Administrativo")
st.markdown("---")

# --- Conexão com o Banco de Dados ---
@st.cache_resource
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={st.secrets['database']['server']};"
        f"DATABASE={st.secrets['database']['database']};"
        f"UID={st.secrets['database']['username']};"
        f"PWD={st.secrets['database']['password']}"
    )

conn = init_connection()

# Função para executar consultas (cache de 5 minutos)
@st.cache_data(ttl=300)
def run_query(query):
    return pd.read_sql(query, conn)

# --- Consultas SQL ---
# 1. Contas a Receber (somente em aberto: sem data_quitacao)
# Obs: Ajuste os nomes das colunas ('cliente', 'valor', 'vencimento') conforme existem na sua view
query_receber = """
    SELECT * 
    FROM sgr_conta_receber 
    WHERE data_quitacao IS NULL
"""
df_receber = run_query(query_receber)

# 2. Últimas Notas Emitidas
# Obs: Ajuste as colunas conforme a sua view
query_notas = """
    SELECT * 
    FROM sgrp_ultimas_notas_clientes
"""
df_notas = run_query(query_notas)


# --- Visuais Dinâmicos ---

# Visão 1: Contas a Receber
st.subheader("Titulos em Aberto (Contas a Receber)")

if not df_receber.empty:
    # Caso as colunas tenham nomes diferentes na view da Supra, precisaremos alterar 'valor' e 'cliente' abaixo
    col_metric1, col_metric2 = st.columns(2)
    
    # Tenta somar a coluna de valor (substitua 'valor' pelo nome real da coluna na view)
    try:
        total_aberto = df_receber['valor'].sum()
        col_metric1.metric("Total em Aberto", f"R$ {total_aberto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    except KeyError:
        col_metric1.warning("Coluna de valor não encontrada na view.")
        
    col_metric2.metric("Qtd. de Títulos", len(df_receber))
    
    with st.expander("Visualizar Tabela de Contas a Receber", expanded=True):
        st.dataframe(df_receber, use_container_width=True)
else:
    st.success("Não há contas a receber em aberto no momento.")

st.markdown("---")

# Visão 2: Últimas Notas Emitidas
st.subheader("Últimas Notas Emitidas")

if not df_notas.empty:
    with st.expander("Visualizar Últimas Notas", expanded=True):
        st.dataframe(df_notas, use_container_width=True)
else:
    st.info("Nenhuma nota encontrada.")