import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import numpy as np

# Carregar variáveis de ambiente
load_dotenv()

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    layout="wide",
    page_title="BI Cashforce | Dashboard Executivo",
    page_icon="■",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO - DESIGN MINIMALISTA ====================
st.markdown("""
    <style>
    /* Paleta minimalista */
    :root {
        --primary: #2c3e50;
        --secondary: #34495e;
        --accent: #3498db;
        --background: #ffffff;
        --border: #e0e0e0;
        --text: #2c3e50;
        --text-light: #7f8c8d;
    }

    /* Reset e base */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Estilo do header minimalista */
    .main-header {
        background: #ffffff;
        padding: 2rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }

    .main-header h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--primary);
        letter-spacing: -0.5px;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 0.875rem;
        color: var(--text-light);
        font-weight: 400;
    }

    /* Sidebar minimalista */
    .css-1d391kg {
        background-color: #fafafa;
    }

    /* Tabs minimalistas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 0.875rem;
        color: var(--text-light);
        border-bottom: 2px solid transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f8f9fa;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary);
        border-bottom-color: var(--accent);
    }

    /* Métricas minimalistas */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--primary);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-light);
    }

    /* Ocultar elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .css-1v0mbdj {display: none;}

    /* Espaçamento limpo */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Títulos de seção */
    h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--primary);
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0.5rem;
    }

    h4 {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--primary);
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Dataframes limpos */
    .dataframe {
        font-size: 0.875rem;
        border: 1px solid var(--border);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONEXÃO COM SUPABASE ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Usar SUPABASE_ANON_KEY (chave pública) - mais seguro para dashboard público
# RLS garante acesso somente aos dados permitidos
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

@st.cache_resource
def get_supabase_client():
    """Conexão com Supabase com cache usando anon key (chave pública segura)"""
    try:
        if not SUPABASE_KEY:
            st.error("SUPABASE_ANON_KEY não configurada. Configure no arquivo .env")
            st.stop()
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        st.stop()

supabase = get_supabase_client()

# ==================== FUNÇÕES DE CARREGAMENTO DE DADOS ====================
@st.cache_data(ttl=3600)
def load_main_data():
    """Carrega dados da VIEW CONSOLIDADA propostas_resumo_mensal (fonte única de verdade)"""
    try:
        # USA A VIEW PRÉ-AGREGADA, NÃO A TABELA BRUTA (consistente com GPT + 1000x mais rápido)
        response = supabase.table("propostas_resumo_mensal").select("*").execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            # Converter competencia (formato YYYY-MM) para datetime
            df['competencia'] = pd.to_datetime(df['competencia'], errors='coerce')

            # Converter valores numéricos da view
            numeric_columns = ['quantidade_operacoes', 'total_bruto_duplicata',
                             'total_liquido_duplicata', 'total_receita_cashforce']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da view: {e}")
        return pd.DataFrame()

# ==================== CARREGAR DADOS ====================
df = load_main_data()

if df.empty:
    st.error(" Nenhum dado disponível. Verifique a conexão com o Supabase.")
    st.stop()

# ==================== HEADER ====================
col_logo, col_title = st.columns([1, 4])

with col_logo:
    pass

with col_title:
    st.markdown(f"""
    <div class="main-header">
        <h1>Dashboard Executivo BI Cashforce</h1>
        <p>Inteligência de Negócios | Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)

# ==================== SIDEBAR - FILTROS ====================
st.sidebar.header("Filtros Principais")

# FILTRO PRINCIPAL: PARCEIRO (em destaque)
st.sidebar.markdown("### Parceiro (Principal)")
# Buscar TODOS os parceiros disponíveis (sem filtros de data)
parceiros_all = sorted(df['nome_parceiro'].dropna().unique().tolist()) if 'nome_parceiro' in df.columns else []
selected_parceiros = st.sidebar.multiselect(
    "Selecione os Parceiros",
    options=parceiros_all,
    default=parceiros_all,  # Todos selecionados por padrão
    help="Filtro principal para análise por parceiro"
)

# Mostrar informações dos parceiros selecionados
if selected_parceiros:
    st.sidebar.info(f" {len(selected_parceiros)} parceiro(s) selecionado(s): {', '.join(selected_parceiros)}")
else:
    st.sidebar.warning(" Nenhum parceiro selecionado")

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros Secundários")

# Filtro de Período
if 'competencia' in df.columns:
    min_date = df['competencia'].min().date() if not pd.isna(df['competencia'].min()) else datetime.now().date() - timedelta(days=365)
    max_date = df['competencia'].max().date() if not pd.isna(df['competencia'].max()) else datetime.now().date()

    # Período padrão: últimos 3 meses
    default_start = max_date - timedelta(days=90)

    date_range = st.sidebar.date_input(
        "Período",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]
else:
    start_date = datetime.now().date() - timedelta(days=365)
    end_date = datetime.now().date()

# Filtro de Grupo Econômico (não existe na view, remover)
# grupos_economicos = sorted(df['grupo_economico'].dropna().unique().tolist()) if 'grupo_economico' in df.columns else []
# selected_grupos = st.sidebar.multiselect(
#     "Grupo Econômico",
#     options=grupos_economicos,
#     default=[]
# )
selected_grupos = []

# Filtro de Status de Pagamento (não existe na view, remover)
# status_pagamento = sorted(df['status_pagamento'].dropna().unique().tolist()) if 'status_pagamento' in df.columns else []
# selected_status = st.sidebar.multiselect(
#     "Status de Pagamento",
#     options=status_pagamento,
#     default=[]
# )
selected_status = []

st.sidebar.markdown("---")
st.sidebar.markdown("### Informações")

# Contar registros por parceiro
parceiros_count = df.groupby('nome_parceiro')['quantidade_operacoes'].sum().to_dict() if 'nome_parceiro' in df.columns else {}
parceiros_info = "\n".join([f"- **{p}**: {int(count):,} operações" for p, count in sorted(parceiros_count.items())])

st.sidebar.info(f"""
**Total de competências:** {len(df):,}

**Parceiros no sistema:**
{parceiros_info}

**Período disponível:** {min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}
""")

# ==================== APLICAR FILTROS ====================
df_filtered = df.copy()

# Filtro de data (competencia)
if 'competencia' in df_filtered.columns:
    df_filtered = df_filtered[
        (df_filtered['competencia'].dt.date >= start_date) &
        (df_filtered['competencia'].dt.date <= end_date)
    ]

# Filtro de parceiro
if selected_parceiros and 'nome_parceiro' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['nome_parceiro'].isin(selected_parceiros)]

# ==================== CALCULAR PERÍODO ANTERIOR PARA COMPARAÇÃO ====================
days_diff = (end_date - start_date).days
previous_start = start_date - timedelta(days=days_diff)
previous_end = start_date - timedelta(days=1)

df_previous = df.copy()
if 'competencia' in df_previous.columns:
    df_previous = df_previous[
        (df_previous['competencia'].dt.date >= previous_start) &
        (df_previous['competencia'].dt.date <= previous_end)
    ]

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Análise por Parceiro",
    "Overview Geral",
    "Análise Temporal",
    "Operacional",
    "Financeiro"
])

# ==================== TAB 1: ANÁLISE POR PARCEIRO ====================
with tab1:
    st.markdown("### Análise por Parceiro")

    if 'nome_parceiro' not in df_filtered.columns or df_filtered.empty:
        st.warning(" Nenhum dado disponível para os filtros selecionados. Tente ajustar o período ou os filtros.")
    else:
        # Verificar se há dados para os parceiros selecionados
        parceiros_com_dados = df_filtered['nome_parceiro'].dropna().unique().tolist()

        if not parceiros_com_dados:
            st.warning(" Nenhum dado encontrado para os parceiros selecionados no período escolhido. Tente ajustar os filtros.")
        elif len(parceiros_com_dados) < len(selected_parceiros):
            parceiros_sem_dados = set(selected_parceiros) - set(parceiros_com_dados)
            st.info(f" Os seguintes parceiros não possuem dados no período selecionado: {', '.join(parceiros_sem_dados)}")
        # Comparação entre Parceiros
        st.markdown("#### Comparação entre Parceiros")

        parceiro_stats = df_filtered.groupby('nome_parceiro').agg({
            'total_bruto_duplicata': 'sum',
            'total_receita_cashforce': 'sum',
            'quantidade_operacoes': 'sum'
        }).reset_index()

        parceiro_stats.columns = ['Parceiro', 'Volume Total', 'Receita CF', 'Operações']
        parceiro_stats['Ticket Médio'] = parceiro_stats['Volume Total'] / parceiro_stats['Operações']
        parceiro_stats['Margem %'] = (parceiro_stats['Receita CF'] / parceiro_stats['Volume Total'] * 100)

        # Cards de KPI por Parceiro
        num_parceiros = len(parceiro_stats)
        cols = st.columns(num_parceiros if num_parceiros <= 4 else 4)

        for idx, row in parceiro_stats.iterrows():
            col_idx = idx % 4 if num_parceiros > 4 else idx
            with cols[col_idx]:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 1.5rem; border-radius: 10px; color: white; text-align: center;'>
                    <h3 style='margin: 0; font-size: 1.5rem;'>{row['Parceiro']}</h3>
                    <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>R$ {row['Volume Total']:,.0f}</p>
                    <p style='margin: 0; opacity: 0.9;'>{int(row['Operações']):,} operações</p>
                    <p style='margin: 0; opacity: 0.9;'>Margem: {row['Margem %']:.2f}%</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Gráficos de Comparação
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Volume por Parceiro")
            fig_volume_parceiro = px.bar(
                parceiro_stats,
                x='Parceiro',
                y='Volume Total',
                color='Parceiro',
                text='Volume Total',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_volume_parceiro.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
            fig_volume_parceiro.update_layout(
                height=400,
                showlegend=False,
                yaxis_title="Volume (R$)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_volume_parceiro, use_container_width=True)

        with col2:
            st.markdown("#### Número de Operações por Parceiro")
            fig_ops_parceiro = px.bar(
                parceiro_stats,
                x='Parceiro',
                y='Operações',
                color='Parceiro',
                text='Operações',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_ops_parceiro.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig_ops_parceiro.update_layout(
                height=400,
                showlegend=False,
                yaxis_title="Quantidade",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_ops_parceiro, use_container_width=True)

        # Métricas Operacionais
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Ticket Médio por Parceiro")
            fig_ticket_parceiro = px.bar(
                parceiro_stats,
                x='Parceiro',
                y='Ticket Médio',
                color='Ticket Médio',
                text='Ticket Médio',
                color_continuous_scale='Blues'
            )
            fig_ticket_parceiro.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
            fig_ticket_parceiro.update_layout(
                height=400,
                showlegend=False,
                yaxis_title="Ticket Médio (R$)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_ticket_parceiro, use_container_width=True)

        with col2:
            st.markdown("#### Margem % por Parceiro")
            fig_margem_parceiro = px.bar(
                parceiro_stats,
                x='Parceiro',
                y='Margem %',
                color='Margem %',
                text='Margem %',
                color_continuous_scale='Greens'
            )
            fig_margem_parceiro.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_margem_parceiro.update_layout(
                height=400,
                showlegend=False,
                yaxis_title="Margem (%)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_margem_parceiro, use_container_width=True)

        # Evolução Temporal por Parceiro
        st.markdown("#### Evolução do Volume por Parceiro")
        if 'competencia' in df_filtered.columns:
            time_parceiro = df_filtered.groupby(['competencia', 'nome_parceiro'])['total_bruto_duplicata'].sum().reset_index()

            fig_evolucao = px.line(
                time_parceiro,
                x='competencia',
                y='total_bruto_duplicata',
                color='nome_parceiro',
                markers=True,
                line_shape='spline'
            )
            fig_evolucao.update_layout(
                height=450,
                xaxis_title="Competência",
                yaxis_title="Volume (R$)",
                hovermode='x unified',
                legend_title="Parceiro",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)

        # Tabela Comparativa
        st.markdown("#### Tabela Comparativa")
        parceiro_display = parceiro_stats.copy()
        parceiro_display['Volume Total'] = parceiro_display['Volume Total'].apply(lambda x: f"R$ {x:,.2f}")
        parceiro_display['Receita CF'] = parceiro_display['Receita CF'].apply(lambda x: f"R$ {x:,.2f}")
        parceiro_display['Ticket Médio'] = parceiro_display['Ticket Médio'].apply(lambda x: f"R$ {x:,.2f}")
        parceiro_display['Margem %'] = parceiro_display['Margem %'].apply(lambda x: f"{x:.2f}%")
        parceiro_display['Operações'] = parceiro_display['Operações'].apply(lambda x: f"{int(x):,}")

        st.dataframe(parceiro_display, use_container_width=True, hide_index=True)

# ==================== TAB 2: OVERVIEW GERAL ====================
with tab2:
    # KPIs Principais
    st.markdown("### Indicadores Principais")

    col1, col2, col3, col4, col5 = st.columns(5)

    # Volume Total
    with col1:
        volume_atual = df_filtered['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered.columns else 0
        volume_anterior = df_previous['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_previous.columns else 0
        delta_volume = ((volume_atual - volume_anterior) / volume_anterior * 100) if volume_anterior > 0 else 0

        st.metric(
            label="Volume Total",
            value=f"R$ {volume_atual:,.0f}",
            delta=f"{delta_volume:+.1f}%"
        )

    # Número de Operações
    with col2:
        ops_atual = df_filtered['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_filtered.columns else 0
        ops_anterior = df_previous['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_previous.columns else 0
        delta_ops = ((ops_atual - ops_anterior) / ops_anterior * 100) if ops_anterior > 0 else 0

        st.metric(
            label="Operações",
            value=f"{int(ops_atual):,}",
            delta=f"{delta_ops:+.1f}%"
        )

    # Receita Cashforce
    with col3:
        receita_atual = df_filtered['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_filtered.columns else 0
        receita_anterior = df_previous['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_previous.columns else 0
        delta_receita = ((receita_atual - receita_anterior) / receita_anterior * 100) if receita_anterior > 0 else 0

        st.metric(
            label="Receita Cashforce",
            value=f"R$ {receita_atual:,.0f}",
            delta=f"{delta_receita:+.1f}%"
        )

    # Ticket Médio
    with col4:
        ticket_atual = volume_atual / ops_atual if ops_atual > 0 else 0
        ticket_anterior = volume_anterior / ops_anterior if ops_anterior > 0 else 0
        delta_ticket = ((ticket_atual - ticket_anterior) / ticket_anterior * 100) if ticket_anterior > 0 else 0

        st.metric(
            label="Ticket Médio",
            value=f"R$ {ticket_atual:,.0f}",
            delta=f"{delta_ticket:+.1f}%"
        )

    # Margem Cashforce
    with col5:
        margem_atual = (receita_atual / volume_atual * 100) if volume_atual > 0 else 0
        margem_anterior = (receita_anterior / volume_anterior * 100) if volume_anterior > 0 else 0
        delta_margem = margem_atual - margem_anterior

        st.metric(
            label="Margem %",
            value=f"{margem_atual:.2f}%",
            delta=f"{delta_margem:+.2f}pp"
        )

    st.markdown("---")

    # Gráficos Overview
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Volume por Parceiro")
        if 'nome_parceiro' in df_filtered.columns and 'total_bruto_duplicata' in df_filtered.columns:
            parceiro_volume = df_filtered.groupby('nome_parceiro')['total_bruto_duplicata'].sum().sort_values(ascending=False)

            fig_parceiros = px.bar(
                x=parceiro_volume.values,
                y=parceiro_volume.index,
                orientation='h',
                labels={'x': 'Volume (R$)', 'y': 'Parceiro'},
                color=parceiro_volume.values,
                color_continuous_scale='Blues'
            )
            fig_parceiros.update_layout(
                showlegend=False,
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Volume (R$)",
                yaxis_title=""
            )
            st.plotly_chart(fig_parceiros, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar o gráfico.")

    with col_right:
        st.markdown("#### Distribuição de Operações por Parceiro")
        if 'nome_parceiro' in df_filtered.columns:
            ops_counts = df_filtered.groupby('nome_parceiro')['quantidade_operacoes'].sum()

            fig_ops_pie = px.pie(
                values=ops_counts.values,
                names=ops_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig_ops_pie.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=True
            )
            fig_ops_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_ops_pie, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar o gráfico.")

    # Evolução temporal (já temos competencia, mostrar evolução)
    st.markdown("#### Evolução do Volume Total")
    if 'competencia' in df_filtered.columns and 'total_bruto_duplicata' in df_filtered.columns:
        time_series = df_filtered.groupby('competencia')['total_bruto_duplicata'].sum().reset_index()

        fig_time = px.line(
            time_series,
            x='competencia',
            y='total_bruto_duplicata',
            markers=True
        )
        fig_time.update_traces(line_color='#667eea', line_width=3)
        fig_time.update_layout(
            height=400,
            xaxis_title="Competência",
            yaxis_title="Volume (R$)",
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_time, use_container_width=True)

# ==================== TAB 3: ANÁLISE TEMPORAL ====================
with tab3:
    st.markdown("### Evolução Temporal")

    if 'competencia' in df_filtered.columns:
        # Agregação mensal (já vem agregado da view)
        time_agg = df_filtered.groupby('competencia').agg({
            'total_bruto_duplicata': 'sum',
            'total_receita_cashforce': 'sum',
            'quantidade_operacoes': 'sum'
        }).reset_index()
        time_agg.columns = ['data', 'volume', 'receita', 'operacoes']
        time_agg['ticket_medio'] = time_agg['volume'] / time_agg['operacoes']

        # Gráfico de Volume ao Longo do Tempo
        st.markdown("#### Volume de Operações Mensal")

        fig_volume_time = go.Figure()

        fig_volume_time.add_trace(go.Scatter(
            x=time_agg['data'],
            y=time_agg['volume'],
            mode='lines+markers',
            name='Volume',
            line=dict(color='#667eea', width=3),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)'
        ))

        fig_volume_time.update_layout(
            height=400,
            xaxis_title="Competência",
            yaxis_title="Volume (R$)",
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_volume_time, use_container_width=True)

        # Gráficos combinados
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Número de Operações")
            fig_ops = px.bar(
                time_agg,
                x='data',
                y='operacoes',
                color='operacoes',
                color_continuous_scale='Blues'
            )
            fig_ops.update_layout(
                height=350,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_ops, use_container_width=True)

        with col2:
            st.markdown("#### Ticket Médio")
            fig_ticket = px.line(
                time_agg,
                x='data',
                y='ticket_medio',
                markers=True
            )
            fig_ticket.update_traces(line_color='#ff7f0e', line_width=3)
            fig_ticket.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_ticket, use_container_width=True)

        # Comparação de métricas
        st.markdown("#### Comparação: Volume vs Receita")
        fig_compare = make_subplots(specs=[[{"secondary_y": True}]])

        fig_compare.add_trace(
            go.Bar(x=time_agg['data'], y=time_agg['volume'], name='Volume', marker_color='#667eea'),
            secondary_y=False
        )

        fig_compare.add_trace(
            go.Scatter(x=time_agg['data'], y=time_agg['receita'], name='Receita CF',
                      mode='lines+markers', line=dict(color='#2ca02c', width=3)),
            secondary_y=True
        )

        fig_compare.update_layout(
            height=400,
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig_compare.update_xaxes(title_text="Competência")
        fig_compare.update_yaxes(title_text="Volume (R$)", secondary_y=False)
        fig_compare.update_yaxes(title_text="Receita CF (R$)", secondary_y=True)

        st.plotly_chart(fig_compare, use_container_width=True)

# ==================== TAB 4: OPERACIONAL ====================
with tab4:
    st.markdown("### Análise Operacional")

    st.info("⚠️ Esta aba requer dados detalhados da tabela `propostas`. Como o dashboard agora usa a view agregada `propostas_resumo_mensal`, algumas análises operacionais não estão disponíveis.")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_ops = df_filtered['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_filtered.columns else 0
        st.metric("Total de Operações", f"{int(total_ops):,}")

    with col2:
        total_volume = df_filtered['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered.columns else 0
        st.metric("Volume Total", f"R$ {total_volume:,.0f}")

    with col3:
        ticket_medio = total_volume / total_ops if total_ops > 0 else 0
        st.metric("Ticket Médio", f"R$ {ticket_medio:,.0f}")

    st.markdown("---")

    st.markdown("#### Operações por Parceiro e Competência")
    if 'nome_parceiro' in df_filtered.columns and 'competencia' in df_filtered.columns:
        ops_parceiro_time = df_filtered.groupby(['competencia', 'nome_parceiro'])['quantidade_operacoes'].sum().reset_index()

        fig_ops_time = px.bar(
            ops_parceiro_time,
            x='competencia',
            y='quantidade_operacoes',
            color='nome_parceiro',
            barmode='group'
        )
        fig_ops_time.update_layout(
            height=400,
            xaxis_title="Competência",
            yaxis_title="Quantidade de Operações",
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_ops_time, use_container_width=True)

# ==================== TAB 5: FINANCEIRO ====================
with tab5:
    st.markdown("### Análise Financeira")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        bruto_total = df_filtered['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered.columns else 0
        st.metric("Total Bruto", f"R$ {bruto_total:,.0f}")

    with col2:
        liquido_total = df_filtered['total_liquido_duplicata'].sum() if 'total_liquido_duplicata' in df_filtered.columns else 0
        st.metric("Total Líquido", f"R$ {liquido_total:,.0f}")

    with col3:
        receita_total = df_filtered['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_filtered.columns else 0
        st.metric("Receita Cashforce", f"R$ {receita_total:,.0f}")

    with col4:
        margem_total = (receita_total / bruto_total * 100) if bruto_total > 0 else 0
        st.metric("Margem %", f"{margem_total:.2f}%")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Composição de Valores")
        if all(col in df_filtered.columns for col in ['total_bruto_duplicata', 'total_liquido_duplicata', 'total_receita_cashforce']):
            valores = pd.DataFrame({
                'Categoria': ['Valor Bruto', 'Valor Líquido', 'Receita CF'],
                'Valor': [
                    df_filtered['total_bruto_duplicata'].sum(),
                    df_filtered['total_liquido_duplicata'].sum(),
                    df_filtered['total_receita_cashforce'].sum()
                ]
            })

            fig_valores = px.bar(
                valores,
                x='Categoria',
                y='Valor',
                color='Categoria',
                color_discrete_sequence=['#667eea', '#ff7f0e', '#2ca02c']
            )
            fig_valores.update_layout(
                height=350,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_valores, use_container_width=True)

    with col_right:
        st.markdown("#### Evolução da Receita Cashforce")
        if 'competencia' in df_filtered.columns and 'total_receita_cashforce' in df_filtered.columns:
            receita_time = df_filtered.groupby('competencia')['total_receita_cashforce'].sum().reset_index()

            fig_receita = px.line(
                receita_time,
                x='competencia',
                y='total_receita_cashforce',
                markers=True
            )
            fig_receita.update_traces(line_color='#2ca02c', line_width=3)
            fig_receita.update_layout(
                height=350,
                xaxis_title="Competência",
                yaxis_title="Receita CF (R$)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_receita, use_container_width=True)

    # Análise de Margem por Parceiro
    st.markdown("#### Margem % por Parceiro ao Longo do Tempo")
    if 'nome_parceiro' in df_filtered.columns:
        df_margem = df_filtered.copy()
        df_margem['margem_pct'] = (df_margem['total_receita_cashforce'] / df_margem['total_bruto_duplicata'] * 100)

        fig_margem_time = px.line(
            df_margem,
            x='competencia',
            y='margem_pct',
            color='nome_parceiro',
            markers=True
        )
        fig_margem_time.update_layout(
            height=400,
            xaxis_title="Competência",
            yaxis_title="Margem (%)",
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_margem_time, use_container_width=True)

# ==================== RODAPÉ ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: var(--text-light); padding: 2rem 0 1rem 0; font-size: 0.75rem;'>
    <p>BI Cashforce Dashboard | Dados via Supabase</p>
</div>
""", unsafe_allow_html=True)
