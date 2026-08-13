import streamlit as st
import pymssql
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(page_title="BI Administrativo - Suprasoft", layout="wide", initial_sidebar_state="collapsed")

# --- Customização de CSS ---
st.markdown("""
    <style>
        /* Forçar nitidez e suavização das fontes */
        * {
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
            text-rendering: optimizeLegibility !important;
        }
        
        /* Ajuste de Margens */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Cards de Métricas */
        [data-testid="stMetric"] {
            background-color: #1e1e2e;
            border-radius: 8px;
            padding: 10px 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            border-left: 4px solid #f95d24; 
        }
        
        /* Abas */
        button[data-baseweb="tab"] p {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        
        /* Botão de atualizar mais integrado ao layout */
        .stButton button {
            width: 100%;
            padding: 4px 10px;
            border-radius: 20px;
            border: 1px solid #444;
            background-color: transparent;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            border-color: #f95d24;
            color: #f95d24;
            background-color: rgba(249, 93, 36, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- Sistema de Cache e Conexão ---
@st.cache_resource
def init_connection():
    servidor = st.secrets['database']['server'].split(',')
    ip = servidor[0]
    porta = servidor[1] if len(servidor) > 1 else "1433"
    
    return pymssql.connect(
        server=ip,
        port=porta,
        user=st.secrets['database']['username'],
        password=st.secrets['database']['password'],
        database=st.secrets['database']['database']
    )

conn = init_connection()

@st.cache_data(ttl=300)
def run_query(query):
    return pd.read_sql(query, conn)

# Função para registrar a hora exata da última consulta
@st.cache_data(ttl=300)
def get_update_time():
    return datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

# --- Cabeçalho Ajustado (Proporções e Alinhamentos) ---
# Usando colunas bem distribuídas para acomodar logos e botão
col_logo1, col_titulo, col_att, col_logo2 = st.columns([1.5, 5.5, 2, 1.5])

with col_logo1:
    st.markdown("<br>", unsafe_allow_html=True) # Espaçamento para alinhar verticalmente
    try:
        st.image("logo_supra.png", width=140) # Aumentada para equilibrar com a da SupraMAIS
    except:
        st.write("[Logo Suprasoft]")
        
with col_titulo:
    st.markdown('<h1 style="text-align: center; font-size: 2.2rem; margin-top: 10px; padding: 0;">📊 Painel Administrativo</h1>', unsafe_allow_html=True)

with col_att:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    # Texto de atualização colado ao botão para não parecer "solto"
    st.markdown(f"<p style='text-align: center; font-size: 0.80rem; color: #a0a0a5; margin-top: -10px;'>Atualizado: {get_update_time()}</p>", unsafe_allow_html=True)

with col_logo2:
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        # Removido o HTML e usado o st.image nativo (tamanho reduzido para não ofuscar)
        st.image("logo_supramais.png", width=120) 
    except:
        st.write("[Logo SupraMAIS]")

st.markdown("---")


# --- Consultas SQL ---
query_receber = """
    SELECT 
        *,
        CONVERT(VARCHAR, Data_Vencimento, 103) AS data_vencimento_br,
        CONVERT(VARCHAR, Data_Emissao, 103) AS data_emissao_br,
        YEAR(Data_Vencimento) AS ano_vencimento,
        MONTH(Data_Vencimento) AS mes_vencimento
    FROM sgr_conta_receber_pedidos
"""
try:
    df_receber = run_query(query_receber)
    df_receber['Data_Vencimento'] = pd.to_datetime(df_receber['Data_Vencimento'], errors='coerce')
except Exception as e:
    st.error(f"Erro ao consultar sgr_conta_receber_pedidos: {e}")
    df_receber = pd.DataFrame()

query_notas = """
    SELECT 
        *,
        CONVERT(VARCHAR, ultima_nfe, 103) AS ultima_nfe_br,
        CONVERT(VARCHAR, ultima_nfse, 103) AS ultima_nfse_br
    FROM sgrp_ultimas_notas_clientes
"""
try:
    df_notas = run_query(query_notas)
except Exception as e:
    st.error(f"Erro ao consultar sgrp_ultimas_notas_clientes: {e}")
    df_notas = pd.DataFrame()


# --- Estrutura de Abas (Dashboard) ---
aba_cr, aba_notas = st.tabs(["💰 Contas a Receber (Em Aberto)", "📄 Últimas Notas Emitidas"])

# ==========================================
# ABA 1: CONTAS A RECEBER
# ==========================================
with aba_cr:
    if not df_receber.empty:
        ano_atual = datetime.now().year
        lista_anos = sorted(df_receber['ano_vencimento'].dropna().unique().tolist(), reverse=True)
        ano_padrao = [ano_atual] if ano_atual in lista_anos else []
        
        lista_meses = sorted(df_receber['mes_vencimento'].dropna().unique().tolist())

        # Filtros de Tempo (Linha 1)
        col_t1, col_t2, col_t3 = st.columns(3)
        anos_selecionados = col_t1.multiselect("Ano de Vencimento", options=lista_anos, default=ano_padrao, placeholder="Foco no ano corrente")
        meses_selecionados = col_t2.multiselect("Mês de Vencimento", options=lista_meses, placeholder="Selecione os meses...")
        periodo_selecionado = col_t3.date_input("Período Exato (Data de Vencimento)", value=[], format="DD/MM/YYYY", help="Selecione uma data inicial e uma data final")

        # Filtros de Categoria (Linha 2)
        col_f1, col_f2, col_f3 = st.columns(3)
        clientes_selecionados = col_f1.multiselect("Cliente", options=df_receber['Cliente'].dropna().unique().tolist(), placeholder="Todos os clientes...")
        formas_selecionadas = col_f2.multiselect("Forma de Cobrança", options=df_receber['Forma_Cobranca'].dropna().unique().tolist(), placeholder="Todas as formas...")
        tipos_selecionados = col_f3.multiselect("Tipo de Pedido", options=df_receber['Tipo_Pedido'].dropna().unique().tolist(), placeholder="Todos os tipos...")
        
        # Filtro de Busca (Linha 3)
        busca_descricao = st.text_input("Buscar palavra-chave na Descrição do Pedido:", placeholder="Ex: treinamento, licença...")
        
        # Aplicando os filtros
        df_cr_filtrado = df_receber.copy()
        
        # Filtros de Ano e Mês
        if anos_selecionados:
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['ano_vencimento'].isin(anos_selecionados)]
        if meses_selecionados:
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['mes_vencimento'].isin(meses_selecionados)]
            
        # Filtro de Período Exato (Calendário)
        if len(periodo_selecionado) == 2:
            data_inicio, data_fim = periodo_selecionado
            df_cr_filtrado = df_cr_filtrado[(df_cr_filtrado['Data_Vencimento'].dt.date >= data_inicio) & (df_cr_filtrado['Data_Vencimento'].dt.date <= data_fim)]
        elif len(periodo_selecionado) == 1:
            data_unica = periodo_selecionado[0]
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['Data_Vencimento'].dt.date == data_unica]

        # Restante dos Filtros
        if clientes_selecionados:
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['Cliente'].isin(clientes_selecionados)]
        if formas_selecionadas:
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['Forma_Cobranca'].isin(formas_selecionadas)]
        if tipos_selecionados:
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['Tipo_Pedido'].isin(tipos_selecionados)]
        if busca_descricao:
            df_cr_filtrado = df_cr_filtrado[df_cr_filtrado['Descricao_Pedido'].str.contains(busca_descricao, case=False, na=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Métricas
        total_aberto = df_cr_filtrado['Valor_parcela'].sum()
        qtd_titulos = len(df_cr_filtrado)
        
        col_met1, col_met2, col_met3 = st.columns(3)
        col_met1.metric("Total em Aberto", f"R$ {total_aberto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col_met2.metric("Qtd. de Títulos", qtd_titulos)
        col_met3.metric("Ticket Médio", f"R$ {(total_aberto/qtd_titulos if qtd_titulos > 0 else 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráficos 
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            top_clientes = df_cr_filtrado.groupby('Cliente')['Valor_parcela'].sum().reset_index().sort_values(by='Valor_parcela', ascending=False).head(10)
            fig_clientes = px.bar(top_clientes, x='Valor_parcela', y='Cliente', orientation='h', title="Top 10 Clientes em Aberto", labels={'Valor_parcela': 'Valor (R$)', 'Cliente': ''}, text_auto='.2s')
            fig_clientes.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), height=350)
            st.plotly_chart(fig_clientes, use_container_width=True)

        with col_graf2:
            graf_tipo = df_cr_filtrado.groupby('Tipo_Pedido')['Valor_parcela'].sum().reset_index()
            fig_tipo = px.pie(graf_tipo, values='Valor_parcela', names='Tipo_Pedido', title="Distribuição por Tipo de Pedido", hole=0.4)
            fig_tipo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), height=350)
            st.plotly_chart(fig_tipo, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Totalizadores
        st.markdown("### Totalizadores por Período (Mês/Ano)")
        df_cr_filtrado['Mes_Ano'] = df_cr_filtrado['ano_vencimento'].astype(str) + '-' + df_cr_filtrado['mes_vencimento'].astype(str).str.zfill(2)
        graf_mes_ano = df_cr_filtrado.groupby('Mes_Ano')['Valor_parcela'].sum().reset_index().sort_values('Mes_Ano')
        fig_mes_ano = px.bar(graf_mes_ano, x='Mes_Ano', y='Valor_parcela', title="Volume Financeiro em Aberto na Linha do Tempo", labels={'Mes_Ano': 'Período', 'Valor_parcela': 'Valor Total (R$)'}, text_auto='.2s')
        fig_mes_ano.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), height=300)
        st.plotly_chart(fig_mes_ano, use_container_width=True)

        # Tabela
        with st.expander("Visualizar Detalhamento dos Títulos", expanded=False):
            df_display = df_cr_filtrado.drop(columns=['ano_vencimento', 'mes_vencimento', 'Mes_Ano'], errors='ignore')
            st.dataframe(df_display, use_container_width=True, column_config={"Descricao_Pedido": st.column_config.TextColumn("Descrição do Pedido", width="medium", help="Passe o mouse por cima para ler a descrição completa.")})
    else:
        st.success("Nenhuma conta a receber em aberto no momento.")


# ==========================================
# ABA 2: ÚLTIMAS NOTAS EMITIDAS
# ==========================================
with aba_notas:
    if not df_notas.empty:
        
        # Função para verificar se a linha possui data preenchida
        def verificar_se_tem_nota(nfe, nfse):
            tem_nfe = pd.notna(nfe) and str(nfe).strip() not in ['', 'None', 'NaT']
            tem_nfse = pd.notna(nfse) and str(nfse).strip() not in ['', 'None', 'NaT']
            return tem_nfe or tem_nfse
            
        df_notas['tem_nota'] = df_notas.apply(lambda row: verificar_se_tem_nota(row['ultima_nfe'], row['ultima_nfse']), axis=1)

        # Filtros
        col_f_nota1, col_f_nota2 = st.columns(2)
        status_emissao = col_f_nota1.radio("Status de Emissão do Cliente", ["Todos", "Com Notas Emitidas", "Nunca Emitiram Notas"], horizontal=True)
        situacao_selecionada = col_f_nota2.multiselect("Filtrar por Situação do Contrato", options=df_notas['situacao_contrato'].dropna().unique().tolist(), placeholder="Todas as situações...")
        
        busca_global = st.text_input("Pesquisa Global nas Notas", placeholder="Pesquise por nome, CNPJ, código...")

        # Aplicando os filtros
        df_notas_filtrado = df_notas.copy()
        
        if status_emissao == "Com Notas Emitidas":
            df_notas_filtrado = df_notas_filtrado[df_notas_filtrado['tem_nota'] == True]
        elif status_emissao == "Nunca Emitiram Notas":
            df_notas_filtrado = df_notas_filtrado[df_notas_filtrado['tem_nota'] == False]
            
        if situacao_selecionada:
            df_notas_filtrado = df_notas_filtrado[df_notas_filtrado['situacao_contrato'].isin(situacao_selecionada)]
            
        if busca_global:
            mask = df_notas_filtrado.astype(str).apply(lambda col: col.str.contains(busca_global, case=False, na=False)).any(axis=1)
            df_notas_filtrado = df_notas_filtrado[mask]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Métrica Principal
        st.metric("Qtd. de Clientes / Contratos (Conforme filtros atuais)", len(df_notas_filtrado))
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Tabela de Dados
        st.markdown("### Detalhamento dos Contratos e Notas")
        df_notas_display = df_notas_filtrado.drop(columns=['tem_nota'], errors='ignore')
        st.dataframe(df_notas_display, use_container_width=True)
             
    else:
        st.info("Nenhuma nota ou contrato recente encontrado.")