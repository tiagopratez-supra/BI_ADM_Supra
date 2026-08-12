import streamlit as st
import pyodbc
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(page_title="BI Administrativo - Suprasoft", layout="wide")

# --- Cabeçalho com Logos ---
col_logo1, col_espaco, col_logo2 = st.columns([1, 4, 1])
with col_logo1:
    try:
        st.image("logo_supra.png", width=150)
    except:
        st.write("[Logo Suprasoft]")
with col_logo2:
    try:
        st.image("logo_supramais.png", width=150)
    except:
        st.write("[Logo SupraMAIS]")

st.title("📊 Painel Administrativo")
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

@st.cache_data(ttl=300) # Cache de 5 minutos
def run_query(query):
    return pd.read_sql(query, conn)

# --- Consultas SQL ---
# Nota: Substitua 'data_vencimento', 'valor' e 'cliente' pelos nomes exatos das colunas na sua view, se forem diferentes.

# 1. Contas a Receber (Apenas em aberto)
query_receber = """
    SELECT 
        *,
        CONVERT(VARCHAR, data_vencimento, 103) AS data_vencimento_br 
    FROM sgr_conta_receber
    WHERE data_quitacao IS NULL
"""
try:
    df_receber = run_query(query_receber)
except Exception as e:
    st.error(f"Erro ao consultar sgr_conta_receber: {e}")
    df_receber = pd.DataFrame()

# 2. Últimas Notas Emitidas
query_notas = """
    SELECT 
        *,
        CONVERT(VARCHAR, data_emissao, 103) AS data_emissao_br 
    FROM sgrp_ultimas_notas_clientes
"""
try:
    df_notas = run_query(query_notas)
except Exception as e:
    st.error(f"Erro ao consultar sgrp_ultimas_notas_clientes: {e}")
    df_notas = pd.DataFrame()

# --- Visuais Dinâmicos ---

# Visão 1: Contas a Receber em Aberto
st.subheader("Títulos em Aberto (Contas a Receber)")

if not df_receber.empty:
    col_met1, col_met2 = st.columns(2)
    
    # Tenta somar a coluna de valor (ajuste 'valor' para o nome correto da sua view)
    try:
        total_aberto = df_receber['valor'].sum()
        col_met1.metric("Total em Aberto", f"R$ {total_aberto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    except KeyError:
        col_met1.warning("Coluna de 'valor' não encontrada para totalização.")
        
    col_met2.metric("Qtd. de Títulos", len(df_receber))
    
    with st.expander("Visualizar Tabela de Contas a Receber", expanded=True):
        st.dataframe(df_receber, use_container_width=True)
else:
    st.success("Nenhuma conta a receber em aberto no momento.")

st.markdown("---")

# Visão 2: Últimas Notas Emitidas
st.subheader("Últimas Notas Emitidas")

if not df_notas.empty:
    with st.expander("Visualizar Tabela de Últimas Notas", expanded=True):
         st.dataframe(df_notas, use_container_width=True)
else:
    st.info("Nenhuma nota recente encontrada.")