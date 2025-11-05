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
# Usar SUPABASE_KEY (service_role) para ter acesso completo aos dados
# A chave ANON tem Row Level Security (RLS) que limita o acesso
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def get_supabase_client():
    """Conexão com Supabase com cache usando service_role key para acesso completo"""
    try:
        if not SUPABASE_KEY:
            st.error("SUPABASE_KEY não configurada. Configure no arquivo .env")
            st.stop()
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        st.stop()

supabase = get_supabase_client()

# ==================== FUNÇÕES DE CARREGAMENTO DE DADOS ====================
@st.cache_data(ttl=3600)
def load_main_data():
    """Carrega dados da tabela propostas"""
    try:
        # Buscar TODOS os dados (sem limite de 1000)
        all_data = []
        page_size = 1000
        offset = 0

        while True:
            response = supabase.table("propostas").select("*").range(offset, offset + page_size - 1).execute()
            if not response.data:
                break
            all_data.extend(response.data)
            if len(response.data) < page_size:
                break
            offset += page_size

        df = pd.DataFrame(all_data)

        if not df.empty:
            # Converter datas
            date_columns = ['data_operacao', 'data_aceite_proposta', 'data_emissao_nf',
                          'vencimento', 'data_pagamento', 'data_pagamento_operacao',
                          'data_confirmacao_pagamento_operacao']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Converter valores numéricos
            numeric_columns = ['valor_bruto_duplicata', 'valor_liquido_duplicata', 'receita_cashforce',
                             'liquido_operacao', 'total_taxas_reais', 'desagio_reais', 'tarifa_reais',
                             'ad_valorem_reais', 'iof_reais', 'prazo', 'prazo_medio_operacao',
                             'taxa_mes_percentual', 'taxa_efetiva_mes_percentual', 'ad_valorem_percentual']

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
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
parceiros_all = sorted(df['parceiro'].dropna().unique().tolist()) if 'parceiro' in df.columns else []
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
if 'data_operacao' in df.columns:
    min_date = df['data_operacao'].min().date() if not pd.isna(df['data_operacao'].min()) else datetime.now().date() - timedelta(days=365)
    max_date = df['data_operacao'].max().date() if not pd.isna(df['data_operacao'].max()) else datetime.now().date()

    # Período padrão: 1 mês (30 dias)
    default_start = max_date - timedelta(days=30)

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

# Filtro de Grupo Econômico
grupos_economicos = sorted(df['grupo_economico'].dropna().unique().tolist()) if 'grupo_economico' in df.columns else []
selected_grupos = st.sidebar.multiselect(
    "Grupo Econômico",
    options=grupos_economicos,
    default=[]
)

# Filtro de Status de Pagamento
status_pagamento = sorted(df['status_pagamento'].dropna().unique().tolist()) if 'status_pagamento' in df.columns else []
selected_status = st.sidebar.multiselect(
    "Status de Pagamento",
    options=status_pagamento,
    default=[]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Informações")

# Contar registros por parceiro
parceiros_count = df.groupby('parceiro').size().to_dict() if 'parceiro' in df.columns else {}
parceiros_info = "\n".join([f"- **{p}**: {count:,} registros" for p, count in sorted(parceiros_count.items())])

st.sidebar.info(f"""
**Total de registros:** {len(df):,}

**Parceiros no sistema:**
{parceiros_info}

**Período disponível:** {min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}
""")

# ==================== APLICAR FILTROS ====================
df_filtered = df.copy()

# Filtro de data
if 'data_operacao' in df_filtered.columns:
    df_filtered = df_filtered[
        (df_filtered['data_operacao'].dt.date >= start_date) &
        (df_filtered['data_operacao'].dt.date <= end_date)
    ]

# Filtro de grupo econômico
if selected_grupos and 'grupo_economico' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['grupo_economico'].isin(selected_grupos)]

# Filtro de status
if selected_status and 'status_pagamento' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['status_pagamento'].isin(selected_status)]

# Filtro de parceiro
if selected_parceiros and 'parceiro' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['parceiro'].isin(selected_parceiros)]

# ==================== CALCULAR PERÍODO ANTERIOR PARA COMPARAÇÃO ====================
days_diff = (end_date - start_date).days
previous_start = start_date - timedelta(days=days_diff)
previous_end = start_date - timedelta(days=1)

df_previous = df.copy()
if 'data_operacao' in df_previous.columns:
    df_previous = df_previous[
        (df_previous['data_operacao'].dt.date >= previous_start) &
        (df_previous['data_operacao'].dt.date <= previous_end)
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

    if 'parceiro' not in df_filtered.columns or df_filtered.empty:
        st.warning(" Nenhum dado disponível para os filtros selecionados. Tente ajustar o período ou os filtros.")
    else:
        # Verificar se há dados para os parceiros selecionados
        parceiros_com_dados = df_filtered['parceiro'].dropna().unique().tolist()

        if not parceiros_com_dados:
            st.warning(" Nenhum dado encontrado para os parceiros selecionados no período escolhido. Tente ajustar os filtros.")
        elif len(parceiros_com_dados) < len(selected_parceiros):
            parceiros_sem_dados = set(selected_parceiros) - set(parceiros_com_dados)
            st.info(f" Os seguintes parceiros não possuem dados no período selecionado: {', '.join(parceiros_sem_dados)}")
        # Comparação entre Parceiros
        st.markdown("#### Comparação entre Parceiros")

        parceiro_stats = df_filtered.groupby('parceiro').agg({
            'valor_bruto_duplicata': 'sum',
            'receita_cashforce': 'sum',
            'id': 'count',
            'prazo_medio_operacao': 'mean',
            'taxa_efetiva_mes_percentual': 'mean'
        }).reset_index()

        parceiro_stats.columns = ['Parceiro', 'Volume Total', 'Receita CF', 'Operações', 'Prazo Médio', 'Taxa Média']
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
        if 'data_operacao' in df_filtered.columns:
            df_time_parceiro = df_filtered.copy()
            df_time_parceiro['data_mes'] = df_time_parceiro['data_operacao'].dt.to_period('M').dt.to_timestamp()

            time_parceiro = df_time_parceiro.groupby(['data_mes', 'parceiro'])['valor_bruto_duplicata'].sum().reset_index()

            fig_evolucao = px.line(
                time_parceiro,
                x='data_mes',
                y='valor_bruto_duplicata',
                color='parceiro',
                markers=True,
                line_shape='spline'
            )
            fig_evolucao.update_layout(
                height=450,
                xaxis_title="Mês",
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
        parceiro_display['Prazo Médio'] = parceiro_display['Prazo Médio'].apply(lambda x: f"{x:.0f} dias")
        parceiro_display['Taxa Média'] = parceiro_display['Taxa Média'].apply(lambda x: f"{x:.2f}%")
        parceiro_display['Margem %'] = parceiro_display['Margem %'].apply(lambda x: f"{x:.2f}%")

        st.dataframe(parceiro_display, use_container_width=True, hide_index=True)

# ==================== TAB 2: OVERVIEW GERAL ====================
with tab2:
    # KPIs Principais
    st.markdown("### Indicadores Principais")

    col1, col2, col3, col4, col5 = st.columns(5)

    # Volume Total
    with col1:
        volume_atual = df_filtered['valor_bruto_duplicata'].sum() if 'valor_bruto_duplicata' in df_filtered.columns else 0
        volume_anterior = df_previous['valor_bruto_duplicata'].sum() if 'valor_bruto_duplicata' in df_previous.columns else 0
        delta_volume = ((volume_atual - volume_anterior) / volume_anterior * 100) if volume_anterior > 0 else 0

        st.metric(
            label="Volume Total",
            value=f"R$ {volume_atual:,.0f}",
            delta=f"{delta_volume:+.1f}%"
        )

    # Número de Operações
    with col2:
        ops_atual = len(df_filtered)
        ops_anterior = len(df_previous)
        delta_ops = ((ops_atual - ops_anterior) / ops_anterior * 100) if ops_anterior > 0 else 0

        st.metric(
            label="Operações",
            value=f"{ops_atual:,}",
            delta=f"{delta_ops:+.1f}%"
        )

    # Receita Cashforce
    with col3:
        receita_atual = df_filtered['receita_cashforce'].sum() if 'receita_cashforce' in df_filtered.columns else 0
        receita_anterior = df_previous['receita_cashforce'].sum() if 'receita_cashforce' in df_previous.columns else 0
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
        st.markdown("#### Top 10 Grupos Econômicos")
        if 'grupo_economico' in df_filtered.columns and 'valor_bruto_duplicata' in df_filtered.columns:
            top_grupos = df_filtered.groupby('grupo_economico')['valor_bruto_duplicata'].sum().sort_values(ascending=False).head(10)

            fig_grupos = px.bar(
                x=top_grupos.values,
                y=top_grupos.index,
                orientation='h',
                labels={'x': 'Volume (R$)', 'y': 'Grupo Econômico'},
                color=top_grupos.values,
                color_continuous_scale='Blues'
            )
            fig_grupos.update_layout(
                showlegend=False,
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Volume (R$)",
                yaxis_title=""
            )
            st.plotly_chart(fig_grupos, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar o gráfico.")

    with col_right:
        st.markdown("#### Distribuição por Status de Pagamento")
        if 'status_pagamento' in df_filtered.columns:
            status_counts = df_filtered['status_pagamento'].value_counts()

            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig_status.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=True
            )
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar o gráfico.")

    # Treemap de Grupos Econômicos
    st.markdown("#### Mapa de Grupos Econômicos (Treemap)")
    if 'grupo_economico' in df_filtered.columns and 'valor_bruto_duplicata' in df_filtered.columns:
        top_20_grupos = df_filtered.groupby('grupo_economico').agg({
            'valor_bruto_duplicata': 'sum',
            'id': 'count'
        }).reset_index()
        top_20_grupos.columns = ['grupo_economico', 'volume', 'quantidade']
        top_20_grupos = top_20_grupos.nlargest(20, 'volume')

        fig_treemap = px.treemap(
            top_20_grupos,
            path=['grupo_economico'],
            values='volume',
            color='volume',
            color_continuous_scale='Viridis',
            hover_data={'quantidade': ':,', 'volume': ':,.2f'}
        )
        fig_treemap.update_layout(
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

# ==================== TAB 3: ANÁLISE TEMPORAL ====================
with tab3:
    st.markdown("### Evolução Temporal")

    if 'data_operacao' in df_filtered.columns:
        # Preparar dados temporais
        df_time = df_filtered.copy()
        df_time['ano_mes'] = df_time['data_operacao'].dt.to_period('M').astype(str)
        df_time['data_mes'] = df_time['data_operacao'].dt.to_period('M').dt.to_timestamp()

        # Agregação mensal
        time_agg = df_time.groupby('data_mes').agg({
            'valor_bruto_duplicata': 'sum',
            'receita_cashforce': 'sum',
            'id': 'count'
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
            xaxis_title="Mês",
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

        # Heatmap de Operações
        st.markdown("#### Heatmap de Operações (Dia da Semana x Mês)")
        df_heatmap = df_filtered.copy()
        df_heatmap['dia_semana'] = df_heatmap['data_operacao'].dt.day_name()
        df_heatmap['mes'] = df_heatmap['data_operacao'].dt.month_name()

        heatmap_data = df_heatmap.groupby(['dia_semana', 'mes']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='dia_semana', columns='mes', values='count').fillna(0)

        # Ordenar dias da semana
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex([d for d in dias_ordem if d in heatmap_pivot.index])

        fig_heatmap = px.imshow(
            heatmap_pivot,
            color_continuous_scale='YlOrRd',
            aspect='auto',
            labels=dict(x="Mês", y="Dia da Semana", color="Operações")
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

# ==================== TAB 4: OPERACIONAL ====================
with tab4:
    st.markdown("### Análise Operacional")

    col1, col2, col3 = st.columns(3)

    with col1:
        prazo_medio = df_filtered['prazo_medio_operacao'].mean() if 'prazo_medio_operacao' in df_filtered.columns else 0
        st.metric("Prazo Médio", f"{prazo_medio:.0f} dias")

    with col2:
        taxa_media = df_filtered['taxa_efetiva_mes_percentual'].mean() if 'taxa_efetiva_mes_percentual' in df_filtered.columns else 0
        st.metric("Taxa Efetiva Média", f"{taxa_media:.2f}%")

    with col3:
        if 'status_antecipacao' in df_filtered.columns:
            antecipadas = len(df_filtered[df_filtered['status_antecipacao'] == 'Antecipada'])
            taxa_antecipacao = (antecipadas / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
            st.metric("Taxa de Antecipação", f"{taxa_antecipacao:.1f}%")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Distribuição de Prazos")
        if 'prazo' in df_filtered.columns:
            fig_prazo = px.histogram(
                df_filtered,
                x='prazo',
                nbins=30,
                color_discrete_sequence=['#667eea']
            )
            fig_prazo.update_layout(
                height=350,
                xaxis_title="Prazo (dias)",
                yaxis_title="Frequência",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_prazo, use_container_width=True)

    with col_right:
        st.markdown("#### Forma de Pagamento")
        if 'forma_pagamento' in df_filtered.columns:
            forma_counts = df_filtered['forma_pagamento'].value_counts()
            fig_forma = px.bar(
                x=forma_counts.index,
                y=forma_counts.values,
                color=forma_counts.values,
                color_continuous_scale='Purples'
            )
            fig_forma.update_layout(
                height=350,
                showlegend=False,
                xaxis_title="Forma",
                yaxis_title="Quantidade",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_forma, use_container_width=True)

    # Top Compradores
    st.markdown("#### Top 15 Compradores por Volume")
    if 'razao_social_comprador' in df_filtered.columns and 'valor_bruto_duplicata' in df_filtered.columns:
        top_compradores = df_filtered.groupby('razao_social_comprador').agg({
            'valor_bruto_duplicata': 'sum',
            'id': 'count'
        }).reset_index()
        top_compradores.columns = ['comprador', 'volume', 'operacoes']
        top_compradores = top_compradores.nlargest(15, 'volume')

        fig_compradores = px.bar(
            top_compradores,
            x='volume',
            y='comprador',
            orientation='h',
            color='volume',
            color_continuous_scale='Teal',
            hover_data={'operacoes': ':,'}
        )
        fig_compradores.update_layout(
            height=500,
            showlegend=False,
            xaxis_title="Volume (R$)",
            yaxis_title="",
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_compradores, use_container_width=True)

# ==================== TAB 5: FINANCEIRO ====================
with tab5:
    st.markdown("### Análise Financeira")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_taxas = df_filtered['total_taxas_reais'].sum() if 'total_taxas_reais' in df_filtered.columns else 0
        st.metric("Total de Taxas", f"R$ {total_taxas:,.0f}")

    with col2:
        desagio_total = df_filtered['desagio_reais'].sum() if 'desagio_reais' in df_filtered.columns else 0
        st.metric("Deságio Total", f"R$ {desagio_total:,.0f}")

    with col3:
        iof_total = df_filtered['iof_reais'].sum() if 'iof_reais' in df_filtered.columns else 0
        st.metric("IOF Total", f"R$ {iof_total:,.0f}")

    with col4:
        liquido_total = df_filtered['liquido_operacao'].sum() if 'liquido_operacao' in df_filtered.columns else 0
        st.metric("Líquido Total", f"R$ {liquido_total:,.0f}")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Composição de Valores")
        if all(col in df_filtered.columns for col in ['valor_bruto_duplicata', 'total_taxas_reais', 'liquido_operacao']):
            valores = pd.DataFrame({
                'Categoria': ['Valor Bruto', 'Taxas', 'Líquido'],
                'Valor': [
                    df_filtered['valor_bruto_duplicata'].sum(),
                    df_filtered['total_taxas_reais'].sum(),
                    df_filtered['liquido_operacao'].sum()
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
        st.markdown("#### Taxa Efetiva Mensal")
        if 'taxa_efetiva_mes_percentual' in df_filtered.columns:
            fig_taxa = px.box(
                df_filtered,
                y='taxa_efetiva_mes_percentual',
                color_discrete_sequence=['#764ba2']
            )
            fig_taxa.update_layout(
                height=350,
                yaxis_title="Taxa Efetiva (%)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_taxa, use_container_width=True)

    # Análise de Concentração (Curva ABC)
    st.markdown("#### Curva ABC - Concentração de Receita por Grupo")
    if 'grupo_economico' in df_filtered.columns and 'receita_cashforce' in df_filtered.columns:
        abc_data = df_filtered.groupby('grupo_economico')['receita_cashforce'].sum().reset_index()
        abc_data = abc_data.sort_values('receita_cashforce', ascending=False).reset_index(drop=True)
        abc_data['percentual'] = abc_data['receita_cashforce'] / abc_data['receita_cashforce'].sum() * 100
        abc_data['acumulado'] = abc_data['percentual'].cumsum()

        # Classificação ABC
        abc_data['classe'] = 'C'
        abc_data.loc[abc_data['acumulado'] <= 80, 'classe'] = 'A'
        abc_data.loc[(abc_data['acumulado'] > 80) & (abc_data['acumulado'] <= 95), 'classe'] = 'B'

        fig_abc = go.Figure()

        fig_abc.add_trace(go.Bar(
            x=abc_data.index,
            y=abc_data['percentual'],
            name='% Receita',
            marker_color='lightblue',
            yaxis='y'
        ))

        fig_abc.add_trace(go.Scatter(
            x=abc_data.index,
            y=abc_data['acumulado'],
            name='% Acumulado',
            mode='lines+markers',
            line=dict(color='red', width=3),
            yaxis='y2'
        ))

        fig_abc.update_layout(
            height=400,
            xaxis_title="Grupos Econômicos (ordenados)",
            yaxis=dict(title="% Receita Individual", side='left'),
            yaxis2=dict(title="% Acumulado", side='right', overlaying='y'),
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_abc, use_container_width=True)

        # Mostrar classificação ABC
        col1, col2, col3 = st.columns(3)

        classe_a = len(abc_data[abc_data['classe'] == 'A'])
        classe_b = len(abc_data[abc_data['classe'] == 'B'])
        classe_c = len(abc_data[abc_data['classe'] == 'C'])

        with col1:
            st.info(f"**Classe A:** {classe_a} grupos (80% da receita)")
        with col2:
            st.info(f"**Classe B:** {classe_b} grupos (15% da receita)")
        with col3:
            st.info(f"**Classe C:** {classe_c} grupos (5% da receita)")

# ==================== RODAPÉ ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: var(--text-light); padding: 2rem 0 1rem 0; font-size: 0.75rem;'>
    <p>BI Cashforce Dashboard | Dados via Supabase</p>
</div>
""", unsafe_allow_html=True)
