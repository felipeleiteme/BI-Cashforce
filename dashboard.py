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

# ==================== CSS CUSTOMIZADO - DESIGN SYSTEM GLOBALS.CSS ====================
st.markdown("""
    <style>
    /* ==================== DESIGN SYSTEM - INSPIRADO EM GLOBALS.CSS ==================== */

    /* Color Tokens - Baseado no design system */
    :root {
        --font-size: 16px;
        --background: #ffffff;
        --foreground: #24292f;
        --primary: #030213;
        --primary-foreground: #ffffff;
        --muted: #ececf0;
        --muted-foreground: #717182;
        --border: rgba(0, 0, 0, 0.1);

        /* Teal/Emerald Scale */
        --teal-50: #f0fdfa;
        --teal-100: #ccfbf1;
        --teal-200: #99f6e4;
        --teal-500: #14b8a6;
        --teal-600: #0d9488;
        --teal-700: #0f766e;
        --teal-900: #134e4a;
        --emerald-50: #ecfdf5;
        --emerald-500: #10b981;
        --emerald-600: #059669;
        --emerald-700: #047857;

        /* Slate Scale */
        --slate-50: #f8fafc;
        --slate-200: #e2e8f0;
        --slate-300: #cbd5e1;
        --slate-400: #94a3b8;
        --slate-500: #64748b;
        --slate-600: #475569;
        --slate-700: #334155;
        --slate-900: #0f172a;

        /* Design tokens */
        --radius: 0.625rem;
        --radius-2xl: 1rem;
        --font-weight-medium: 500;
        --font-weight-normal: 400;
    }

    /* Typography */
    * {
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    html {
        font-size: var(--font-size);
    }

    /* Background gradient like App.tsx */
    .stApp {
        background: linear-gradient(135deg, var(--slate-50) 0%, rgba(240, 253, 250, 0.2) 50%, var(--slate-50) 100%);
    }

    /* Header styling */
    .main-header {
        background: #ffffff;
        padding: 1.5rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }

    .main-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: var(--font-weight-medium);
        color: var(--primary);
        line-height: 1.5;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 0.875rem;
        color: var(--slate-500);
        font-weight: var(--font-weight-normal);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--slate-50);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] .css-1d391kg {
        background-color: var(--slate-50);
    }

    /* Tabs - Clean design like components */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid var(--border);
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 0.75rem 1.5rem;
        font-weight: var(--font-weight-medium);
        font-size: 0.875rem;
        color: var(--slate-600);
        border-bottom: 2px solid transparent;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--slate-50);
        color: var(--slate-900);
    }

    .stTabs [aria-selected="true"] {
        color: var(--teal-700);
        border-bottom-color: var(--teal-600);
        background-color: transparent;
    }

    /* Metric Cards - Like MetricsCards.tsx */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--slate-200);
        border-radius: var(--radius-2xl);
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        border-color: var(--teal-200);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: var(--font-weight-medium);
        color: var(--slate-900);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: var(--font-weight-medium);
        color: var(--slate-500);
        text-transform: none;
        letter-spacing: 0;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
    }

    /* Chart containers */
    .js-plotly-plot {
        border-radius: var(--radius-2xl);
        background: white;
        border: 1px solid var(--slate-200);
        padding: 1rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--teal-500) 0%, var(--emerald-500) 100%);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: 0.5rem 1.5rem;
        font-weight: var(--font-weight-medium);
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--teal-600) 0%, var(--emerald-600) 100%);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }

    /* Download button */
    .stDownloadButton > button {
        background: white;
        color: var(--teal-700);
        border: 1px solid var(--teal-200);
        border-radius: var(--radius);
        padding: 0.5rem 1.5rem;
        font-weight: var(--font-weight-medium);
        transition: all 0.3s ease;
    }

    .stDownloadButton > button:hover {
        background: var(--teal-50);
        border-color: var(--teal-600);
    }

    /* Dataframes */
    .dataframe {
        font-size: 0.875rem;
        border: 1px solid var(--slate-200);
        border-radius: var(--radius);
    }

    /* Section headers */
    h3 {
        font-size: 1.125rem;
        font-weight: var(--font-weight-medium);
        color: var(--slate-900);
        margin-top: 2rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }

    h4 {
        font-size: 1rem;
        font-weight: var(--font-weight-medium);
        color: var(--slate-700);
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        line-height: 1.5;
    }

    /* Hide unnecessary elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .css-1v0mbdj {display: none;}

    /* Container spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Info/Warning boxes */
    .stAlert {
        border-radius: var(--radius);
        border: 1px solid var(--slate-200);
    }

    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: var(--teal-50);
        color: var(--teal-900);
        border-radius: var(--radius);
        font-size: 0.875rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONEXÃO COM SUPABASE ====================
# Tentar carregar de secrets do Streamlit Cloud primeiro, depois de .env
try:
    # Streamlit Cloud usa st.secrets
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    SUPABASE_KEY = st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY"))
except:
    # Fallback para .env local
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

@st.cache_resource
def get_supabase_client():
    """Conexão com Supabase com cache usando anon key (chave pública segura)"""
    try:
        if not SUPABASE_KEY:
            st.error("⚠️ SUPABASE_ANON_KEY não configurada.")
            st.info("""
                **Para Streamlit Cloud:** Configure em Settings → Secrets

                **Para desenvolvimento local:** Adicione ao arquivo .env:
                ```
                SUPABASE_URL=https://ximsykesrzxgknonmxws.supabase.co
                SUPABASE_ANON_KEY=sua_chave_aqui
                ```
            """)
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
if 'competencia' in df.columns:
    min_date = df['competencia'].min().date() if not pd.isna(df['competencia'].min()) else datetime.now().date() - timedelta(days=365)

    # max_date deve ser o ÚLTIMO DIA DO MÊS da competência máxima, não o primeiro
    max_competencia = df['competencia'].max()
    if not pd.isna(max_competencia):
        # Ir para o próximo mês e voltar 1 dia para pegar o último dia do mês atual
        next_month = max_competencia + pd.DateOffset(months=1)
        max_date = (next_month - timedelta(days=1)).date()
    else:
        max_date = datetime.now().date()

    # Período padrão: últimos 3 meses (mas garantindo que não ultrapasse max_date)
    default_start = max(min_date, max_date - timedelta(days=90))

    # IMPORTANTE: Streamlit só aceita tuplas se ambas as datas estiverem dentro do range
    # Usar key única para forçar recriação do widget quando os dados mudarem
    date_range = st.sidebar.date_input(
        "Período",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
        key=f"date_range_{min_date}_{max_date}"
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]
else:
    start_date = datetime.now().date() - timedelta(days=365)
    end_date = datetime.now().date()

# ==================== COMPARAÇÃO DE PERÍODOS ====================
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='border-left: 3px solid var(--teal-600); padding-left: 1rem; margin-bottom: 1rem;'>
        <h4 style='margin: 0 0 0.25rem 0; font-size: 0.875rem; font-weight: 600; color: var(--slate-900);'>
            Comparação de Períodos
        </h4>
        <p style='margin: 0; font-size: 0.75rem; color: var(--slate-500);'>
            Compare dois períodos diferentes
        </p>
    </div>
""", unsafe_allow_html=True)

enable_comparison = st.sidebar.checkbox("Ativar comparação", value=False)

if enable_comparison:
    st.sidebar.info("📊 Modo comparação ativo", icon="ℹ️")

    if 'competencia' in df.columns:
        # Período de comparação com mesmo range de datas disponíveis
        date_range_comp = st.sidebar.date_input(
            "Período de Comparação",
            value=(min_date, min_date + timedelta(days=90)),
            min_value=min_date,
            max_value=max_date,
            key=f"date_range_comp_{min_date}_{max_date}"
        )

        if isinstance(date_range_comp, tuple) and len(date_range_comp) == 2:
            start_date_comp, end_date_comp = date_range_comp
        else:
            start_date_comp = end_date_comp = date_range_comp if not isinstance(date_range_comp, tuple) else date_range_comp[0]
    else:
        start_date_comp = datetime.now().date() - timedelta(days=730)
        end_date_comp = datetime.now().date() - timedelta(days=365)
else:
    start_date_comp = None
    end_date_comp = None

# ==================== HEADER (após definição dos filtros) ====================
col_logo, col_title = st.columns([1, 4])

with col_logo:
    pass

with col_title:
    if enable_comparison and start_date_comp:
        periodo_texto = f"<strong>Período 1:</strong> {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')} | <strong>Período 2:</strong> {start_date_comp.strftime('%d/%m/%Y')} - {end_date_comp.strftime('%d/%m/%Y')}"
    else:
        periodo_texto = f"<strong>Período:</strong> {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

    st.markdown(f"""
    <div class="main-header">
        <h1>Dashboard Executivo BI Cashforce</h1>
        <p>Inteligência de Negócios | {periodo_texto} | Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)

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
parceiros_count = df.groupby('parceiro')['quantidade_operacoes'].sum().to_dict() if 'parceiro' in df.columns else {}
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
if selected_parceiros and 'parceiro' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['parceiro'].isin(selected_parceiros)]

# ==================== APLICAR FILTROS PERÍODO DE COMPARAÇÃO ====================
df_filtered_comp = None
if enable_comparison and start_date_comp and end_date_comp:
    df_filtered_comp = df.copy()

    # Filtro de data (período de comparação)
    if 'competencia' in df_filtered_comp.columns:
        df_filtered_comp = df_filtered_comp[
            (df_filtered_comp['competencia'].dt.date >= start_date_comp) &
            (df_filtered_comp['competencia'].dt.date <= end_date_comp)
        ]

    # Filtro de parceiro (mesmos parceiros)
    if selected_parceiros and 'parceiro' in df_filtered_comp.columns:
        df_filtered_comp = df_filtered_comp[df_filtered_comp['parceiro'].isin(selected_parceiros)]

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
    "Overview Geral",
    "Análise por Parceiro",
    "Análise Temporal",
    "Operacional",
    "Financeiro"
])

# ==================== TAB 2: ANÁLISE POR PARCEIRO ====================
with tab2:
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
                <div style='background: white;
                            border: 1px solid var(--slate-200);
                            border-radius: var(--radius-2xl);
                            padding: 1.5rem;
                            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
                            transition: all 0.3s ease;
                            text-align: center;'>
                    <div style='width: 3.5rem; height: 3.5rem; margin: 0 auto 1rem;
                                background: linear-gradient(135deg, var(--teal-500) 0%, var(--emerald-500) 100%);
                                border-radius: var(--radius-2xl);
                                display: flex; align-items: center; justify-content: center;
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                        <span style='color: white; font-size: 1.5rem; font-weight: 600;'>{row['Parceiro'][0]}</span>
                    </div>
                    <h3 style='margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 600; color: var(--slate-900);'>{row['Parceiro']}</h3>
                    <p style='font-size: 1.5rem; font-weight: 600; margin: 0.25rem 0; color: var(--slate-900);'>R$ {row['Volume Total']:,.0f}</p>
                    <p style='margin: 0.25rem 0; font-size: 0.875rem; color: var(--slate-500);'>{int(row['Operações']):,} operações</p>
                    <div style='display: inline-flex; align-items: center; gap: 0.25rem; margin-top: 0.5rem;
                                padding: 0.25rem 0.75rem; border-radius: var(--radius); font-size: 0.875rem;
                                background: var(--emerald-50); color: var(--emerald-700);'>
                        <span>Margem: {row['Margem %']:.2f}%</span>
                    </div>
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
                color_discrete_sequence=['#14b8a6', '#10b981', '#0d9488', '#059669', '#0f766e']
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
                color_discrete_sequence=['#14b8a6', '#10b981', '#0d9488', '#059669', '#0f766e']
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
                color_continuous_scale=[[0, '#ccfbf1'], [0.5, '#14b8a6'], [1, '#0d9488']]
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
                color_continuous_scale=[[0, '#ecfdf5'], [0.5, '#10b981'], [1, '#059669']]
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
            time_parceiro = df_filtered.groupby(['competencia', 'parceiro'])['total_bruto_duplicata'].sum().reset_index()

            fig_evolucao = px.line(
                time_parceiro,
                x='competencia',
                y='total_bruto_duplicata',
                color='parceiro',
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

        # --- NOVA SEÇÃO: Tabela Dinâmica Mês a Mês ---
        st.markdown("---")
        st.markdown("#### Série Histórica Detalhada")

        col_info1, col_info2 = st.columns([3, 1])
        with col_info1:
            st.caption("Visão mês a mês por parceiro e métrica para análise histórica")
        with col_info2:
            st.caption("💾 Exportável para Excel")

        try:
            # 1. Preparar dados para pivot
            df_pivot = df_filtered.copy()
            df_pivot['mes_ano'] = df_pivot['competencia'].dt.strftime('%Y-%m')

            # 2. Criar dataframe 'derretido' com métricas como linhas
            df_melted = df_pivot.melt(
                id_vars=['mes_ano', 'parceiro'],
                value_vars=['total_bruto_duplicata', 'total_liquido_duplicata', 'total_receita_cashforce', 'quantidade_operacoes'],
                var_name='metrica',
                value_name='valor'
            )

            # 3. Renomear métricas para legibilidade
            metrica_map = {
                'total_bruto_duplicata': 'Volume Bruto',
                'total_liquido_duplicata': 'Volume Líquido',
                'total_receita_cashforce': 'Receita Cashforce',
                'quantidade_operacoes': 'Nº Operações'
            }
            df_melted['metrica'] = df_melted['metrica'].map(metrica_map)

            # 4. Criar tabela dinâmica (Pivot Table)
            pivot_table = df_melted.pivot_table(
                index=['parceiro', 'metrica'],
                columns='mes_ano',
                values='valor',
                aggfunc='sum',
                fill_value=0
            )

            # 5. Ordenar colunas (meses) cronologicamente
            pivot_table = pivot_table.reindex(sorted(pivot_table.columns), axis=1)

            # 6. Formatar valores monetários vs operações
            def format_value(val, metric):
                if 'Nº Operações' in metric:
                    return f"{int(val):,}"
                else:
                    return f"R$ {val:,.2f}"

            # Aplicar formatação condicional
            styled_pivot = pivot_table.style.format(lambda x: f"R$ {x:,.2f}" if x != 0 else "-")

            # 7. Exibir tabela
            st.dataframe(
                styled_pivot,
                use_container_width=True,
                height=600
            )

            # Botão de download minimalista
            csv = pivot_table.to_csv().encode('utf-8')
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name=f"serie_historica_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Baixar tabela completa em formato CSV (compatível com Excel)"
            )

        except Exception as e:
            st.warning(f"⚠️ Não foi possível gerar a tabela pivot. Erro: {e}")

        st.markdown("---")

        # Tabela Comparativa (Agregada)
        st.markdown("#### Resumo Agregado por Parceiro")
        parceiro_display = parceiro_stats.copy()
        parceiro_display['Volume Total'] = parceiro_display['Volume Total'].apply(lambda x: f"R$ {x:,.2f}")
        parceiro_display['Receita CF'] = parceiro_display['Receita CF'].apply(lambda x: f"R$ {x:,.2f}")
        parceiro_display['Ticket Médio'] = parceiro_display['Ticket Médio'].apply(lambda x: f"R$ {x:,.2f}")
        parceiro_display['Margem %'] = parceiro_display['Margem %'].apply(lambda x: f"{x:.2f}%")
        parceiro_display['Operações'] = parceiro_display['Operações'].apply(lambda x: f"{int(x):,}")

        st.dataframe(parceiro_display, use_container_width=True, hide_index=True)

# ==================== TAB 1: OVERVIEW GERAL ====================
with tab1:
    # Banner minimalista de comparação ativa
    if enable_comparison and df_filtered_comp is not None:
        st.info("Modo comparação: métricas comparando P1 vs P2", icon="🔄")

    # KPIs Principais
    st.markdown("### Indicadores Principais")

    col1, col2, col3, col4, col5 = st.columns(5)

    # Volume Total
    with col1:
        volume_atual = df_filtered['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered.columns else 0

        # Usar período de comparação se ativado, senão usar período anterior automático
        if enable_comparison and df_filtered_comp is not None:
            volume_comp = df_filtered_comp['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered_comp.columns else 0
            delta_volume = ((volume_atual - volume_comp) / volume_comp * 100) if volume_comp > 0 else 0
            delta_label = f"{delta_volume:+.1f}% vs P2"
        else:
            volume_anterior = df_previous['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_previous.columns else 0
            delta_volume = ((volume_atual - volume_anterior) / volume_anterior * 100) if volume_anterior > 0 else 0
            delta_label = f"{delta_volume:+.1f}%"

        st.metric(
            label="Volume Total (P1)" if enable_comparison else "Volume Total",
            value=f"R$ {volume_atual:,.0f}",
            delta=delta_label
        )

    # Número de Operações
    with col2:
        ops_atual = df_filtered['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_filtered.columns else 0

        if enable_comparison and df_filtered_comp is not None:
            ops_comp = df_filtered_comp['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_filtered_comp.columns else 0
            delta_ops = ((ops_atual - ops_comp) / ops_comp * 100) if ops_comp > 0 else 0
            delta_label_ops = f"{delta_ops:+.1f}% vs P2"
        else:
            ops_anterior = df_previous['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_previous.columns else 0
            delta_ops = ((ops_atual - ops_anterior) / ops_anterior * 100) if ops_anterior > 0 else 0
            delta_label_ops = f"{delta_ops:+.1f}%"

        st.metric(
            label="Operações (P1)" if enable_comparison else "Operações",
            value=f"{int(ops_atual):,}",
            delta=delta_label_ops
        )

    # Receita Cashforce
    with col3:
        receita_atual = df_filtered['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_filtered.columns else 0

        if enable_comparison and df_filtered_comp is not None:
            receita_comp = df_filtered_comp['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_filtered_comp.columns else 0
            delta_receita = ((receita_atual - receita_comp) / receita_comp * 100) if receita_comp > 0 else 0
            delta_label_receita = f"{delta_receita:+.1f}% vs P2"
        else:
            receita_anterior = df_previous['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_previous.columns else 0
            delta_receita = ((receita_atual - receita_anterior) / receita_anterior * 100) if receita_anterior > 0 else 0
            delta_label_receita = f"{delta_receita:+.1f}%"

        st.metric(
            label="Receita CF (P1)" if enable_comparison else "Receita Cashforce",
            value=f"R$ {receita_atual:,.0f}",
            delta=delta_label_receita
        )

    # Ticket Médio
    with col4:
        ticket_atual = volume_atual / ops_atual if ops_atual > 0 else 0

        if enable_comparison and df_filtered_comp is not None:
            volume_comp = df_filtered_comp['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered_comp.columns else 0
            ops_comp = df_filtered_comp['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_filtered_comp.columns else 0
            ticket_comp = volume_comp / ops_comp if ops_comp > 0 else 0
            delta_ticket = ((ticket_atual - ticket_comp) / ticket_comp * 100) if ticket_comp > 0 else 0
            delta_label_ticket = f"{delta_ticket:+.1f}% vs P2"
        else:
            volume_anterior = df_previous['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_previous.columns else 0
            ops_anterior = df_previous['quantidade_operacoes'].sum() if 'quantidade_operacoes' in df_previous.columns else 0
            ticket_anterior = volume_anterior / ops_anterior if ops_anterior > 0 else 0
            delta_ticket = ((ticket_atual - ticket_anterior) / ticket_anterior * 100) if ticket_anterior > 0 else 0
            delta_label_ticket = f"{delta_ticket:+.1f}%"

        st.metric(
            label="Ticket Médio (P1)" if enable_comparison else "Ticket Médio",
            value=f"R$ {ticket_atual:,.0f}",
            delta=delta_label_ticket
        )

    # Margem Cashforce
    with col5:
        margem_atual = (receita_atual / volume_atual * 100) if volume_atual > 0 else 0

        if enable_comparison and df_filtered_comp is not None:
            volume_comp = df_filtered_comp['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_filtered_comp.columns else 0
            receita_comp = df_filtered_comp['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_filtered_comp.columns else 0
            margem_comp = (receita_comp / volume_comp * 100) if volume_comp > 0 else 0
            delta_margem = margem_atual - margem_comp
            delta_label_margem = f"{delta_margem:+.2f}pp vs P2"
        else:
            volume_anterior = df_previous['total_bruto_duplicata'].sum() if 'total_bruto_duplicata' in df_previous.columns else 0
            receita_anterior = df_previous['total_receita_cashforce'].sum() if 'total_receita_cashforce' in df_previous.columns else 0
            margem_anterior = (receita_anterior / volume_anterior * 100) if volume_anterior > 0 else 0
            delta_margem = margem_atual - margem_anterior
            delta_label_margem = f"{delta_margem:+.2f}pp"

        st.metric(
            label="Margem % (P1)" if enable_comparison else "Margem %",
            value=f"{margem_atual:.2f}%",
            delta=delta_label_margem
        )

    st.markdown("---")

    # Gráficos Overview
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Volume por Parceiro")
        if 'parceiro' in df_filtered.columns and 'total_bruto_duplicata' in df_filtered.columns:
            parceiro_volume = df_filtered.groupby('parceiro')['total_bruto_duplicata'].sum().sort_values(ascending=False)

            fig_parceiros = px.bar(
                x=parceiro_volume.values,
                y=parceiro_volume.index,
                orientation='h',
                labels={'x': 'Volume (R$)', 'y': 'Parceiro'},
                color=parceiro_volume.values,
                color_continuous_scale=[[0, '#ccfbf1'], [0.5, '#14b8a6'], [1, '#0d9488']]
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
        if 'parceiro' in df_filtered.columns:
            ops_counts = df_filtered.groupby('parceiro')['quantidade_operacoes'].sum()

            fig_ops_pie = px.pie(
                values=ops_counts.values,
                names=ops_counts.index,
                color_discrete_sequence=['#14b8a6', '#10b981', '#0d9488', '#059669', '#0f766e'],
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
        fig_time.update_traces(
            line_color='#14b8a6',
            line_width=3,
            marker=dict(size=8, color='#14b8a6'),
            hovertemplate='<b>%{x|%b/%Y}</b><br>Volume: R$ %{y:,.2f}<extra></extra>'
        )
        fig_time.update_layout(
            height=400,
            xaxis_title="Competência",
            yaxis_title="Volume (R$)",
            yaxis=dict(tickformat=',.0f', tickprefix='R$ '),
            xaxis=dict(tickformat='%b/%Y'),
            hovermode='x unified',
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
            line=dict(color='#14b8a6', width=3),
            fill='tozeroy',
            fillcolor='rgba(20, 184, 166, 0.2)',
            marker=dict(color='#14b8a6')
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
                color_continuous_scale=[[0, '#ccfbf1'], [0.5, '#14b8a6'], [1, '#0d9488']]
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
            fig_ticket.update_traces(line_color='#10b981', line_width=3, marker=dict(color='#10b981'))
            fig_ticket.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_ticket, use_container_width=True)

        # Comparação de métricas
        st.markdown("#### Comparação: Volume vs Receita")
        fig_compare = make_subplots(specs=[[{"secondary_y": True}]])

        fig_compare.add_trace(
            go.Bar(x=time_agg['data'], y=time_agg['volume'], name='Volume', marker_color='#14b8a6'),
            secondary_y=False
        )

        fig_compare.add_trace(
            go.Scatter(x=time_agg['data'], y=time_agg['receita'], name='Receita CF',
                      mode='lines+markers', line=dict(color='#10b981', width=3), marker=dict(color='#10b981')),
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
    if 'parceiro' in df_filtered.columns and 'competencia' in df_filtered.columns:
        ops_parceiro_time = df_filtered.groupby(['competencia', 'parceiro'])['quantidade_operacoes'].sum().reset_index()

        fig_ops_time = px.bar(
            ops_parceiro_time,
            x='competencia',
            y='quantidade_operacoes',
            color='parceiro',
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
                color_discrete_sequence=['#14b8a6', '#10b981', '#059669']
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
            fig_receita.update_traces(line_color='#10b981', line_width=3, marker=dict(color='#10b981'))
            fig_receita.update_layout(
                height=350,
                xaxis_title="Competência",
                yaxis_title="Receita CF (R$)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_receita, use_container_width=True)

    # Análise de Margem por Parceiro
    st.markdown("#### Margem % por Parceiro ao Longo do Tempo")
    if 'parceiro' in df_filtered.columns:
        df_margem = df_filtered.copy()
        df_margem['margem_pct'] = (df_margem['total_receita_cashforce'] / df_margem['total_bruto_duplicata'] * 100)

        fig_margem_time = px.line(
            df_margem,
            x='competencia',
            y='margem_pct',
            color='parceiro',
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
