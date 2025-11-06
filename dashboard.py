import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64tz_dtype
import plotly.express as px
import streamlit as st
from streamlit.components.v1 import html
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="BI Cashforce | Dashboard Executivo",
    page_icon="https://cashforce.com.br/wp-content/uploads/2022/04/cropped-favicon-32x32.png",  # Favicon da Cashforce
    initial_sidebar_state="expanded",
)

# --- 2. CSS CUSTOMIZADO (BRANDING CASHFORCE) ---
# Aqui aplicamos a identidade visual da Cashforce
st.markdown(
    """
    <style>
    /* --- Paleta de Cores Cashforce --- */
    :root {
        --font-size: 16px;
        --brand-green: #00D98E;
        --brand-green-dark: #00B876;
        --brand-green-light: #F0FFF9;
        --brand-dark-blue: #030213;
        --brand-text: #333333;
        --brand-text-light: #555555;
        --brand-bg: #FFFFFF;
        --brand-bg-muted: #F8FAFC;
        --brand-border: #E5E7EB;

        /* Override Streamlit Globals */
        --primary-color: var(--brand-green);
        --text-color: var(--brand-text);
        --background-color: var(--brand-bg);
        --secondary-background-color: var(--brand-bg-muted);
        --font: "ui-sans-serif", "Inter", "system-ui", "sans-serif";
    }

    * {
        font-family: var(--font);
    }

    html {
        font-size: var(--font-size);
    }

    /* --- Layout Principal --- */
    .stApp {
        background: var(--brand-bg); /* Fundo branco sólido */
    }

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {
        background-color: var(--brand-bg-muted);
        border-right: 1px solid var(--brand-border);
    }
    
    [data-testid="stSidebar"] h2 {
        font-size: 1.5rem;
        color: var(--brand-dark-blue);
    }
    
    [data-testid="stSidebar"] h3 {
        font-size: 1rem;
        color: var(--brand-dark-blue);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    /* --- Abas (Tabs) --- */
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-weight: 500;
        color: var(--brand-text-light);
        padding: 0.75rem 1.5rem;
        border-bottom: 2px solid transparent;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--brand-green-dark);
        border-bottom: 2px solid var(--brand-green);
        background: transparent;
    }

    /* Remove tab highlight bar (laranja padrão do Streamlit) */
    [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* --- INÍCIO: Correção Cores DatePicker (Branding Cashforce) --- */

    [data-baseweb="calendar"] .CalendarDay__selected,
    [data-baseweb="calendar"] .CalendarDay__selected:hover,
    [data-baseweb="calendar"] .CalendarDay__selected_span,
    [data-baseweb="calendar"] .CalendarDay__selected_span:hover,
    [data-baseweb="calendar"] .CalendarDay--selected,
    [data-baseweb="calendar"] .CalendarDay--selected:hover {
        background-color: var(--brand-green) !important;
        color: var(--brand-dark-blue) !important;
        border-radius: 50% !important;
        border: none !important;
    }

    [data-baseweb="calendar"] .CalendarDay__hovered_span,
    [data-baseweb="calendar"] .CalendarDay__hovered_span:hover,
    [data-baseweb="calendar"] .CalendarDay--hovered,
    [data-baseweb="calendar"] .CalendarDay--hovered:hover {
        background-color: var(--brand-green-light) !important;
        color: var(--brand-green-dark) !important;
        border-radius: 50% !important;
        border: none !important;
    }

    [data-baseweb="calendar"] .CalendarDay__selected_span,
    [data-baseweb="calendar"] .CalendarDay--selected-range {
        background-color: var(--brand-green-light) !important;
        color: var(--brand-green-dark) !important;
        border: none !important;
        border-radius: 0 !important;
    }

    /* --- FIM: Correção Cores DatePicker --- */

    /* --- Cards de KPI (Metrics) --- */
    [data-testid="stMetric"] {
        background: var(--brand-bg);
        border: 1px solid var(--brand-border);
        border-radius: 1rem; /* 16px */
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--brand-green);
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.05);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: var(--brand-dark-blue);
        font-weight: 600;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: var(--brand-text-light);
        font-weight: 500;
    }

    /* --- Gráficos (Plotly) --- */
    .js-plotly-plot {
        border-radius: 1rem;
        background: var(--brand-bg);
        border: 1px solid var(--brand-border);
        padding: 1rem;
    }

    /* --- Inputs (Remove Laranja/Vermelho) --- */
    
    /* Multiselect Tags (Parceiros, Financiadores) */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: var(--brand-green-light);
        color: var(--brand-green-dark);
        border: 1px solid var(--brand-green);
        border-radius: 0.5rem;
    }

    /* DateInput Borda */
    [data-testid="stDateInput"] div[data-baseweb="input"] {
        border-color: var(--brand-border);
        border-radius: 0.5rem;
    }
    [data-testid="stDateInput"] div[data-baseweb="input"]:focus-within {
         border-color: var(--brand-green) !important;
         box-shadow: 0 0 0 1px var(--brand-green) !important;
    }
    
    /* Mantém footer discreto */
    footer {visibility: hidden;}
    
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. CONSTANTES DE CORES E LOGO ---
LOGO_URL = "https://i.ibb.co/0p8WS2MV/logo-cashforce.png"
BRAND_COLOR_SCALE_PRIMARY = ["#00D98E", "#00B876", "#030213", "#5A6872", "#A9B5BE"]
BRAND_COLOR_SCALE_CONTINUOUS = [[0, "#F0FFF9"], [0.5, "#00D98E"], [1, "#00B876"]]


# --- 4. CONEXÃO SUPABASE (Cache) ---
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    SUPABASE_KEY = st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY"))
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")


@st.cache_resource
def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("⚠️ Defina SUPABASE_URL e SUPABASE_ANON_KEY para continuar.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase_client()


# --- 5. FUNÇÕES DE CARREGAMENTO DE DADOS ---
def _fetch_paginated(table_name: str, select: str, apply_filters=None, page_size: int = 1000):
    rows = []
    start = 0

    while True:
        query = supabase.table(table_name).select(select)
        if apply_filters:
            query = apply_filters(query)
        query = query.range(start, start + page_size - 1)
        response = query.execute()
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size

    return rows


@st.cache_data(ttl=3600)
def load_view_data() -> pd.DataFrame:
    try:
        data = _fetch_paginated("propostas_resumo_mensal", "*")
        df_view = pd.DataFrame(data)
        if df_view.empty:
            return df_view
        df_view["competencia"] = pd.to_datetime(df_view["competencia"], errors="coerce")
        if is_datetime64tz_dtype(df_view["competencia"]):
            df_view["competencia"] = df_view["competencia"].dt.tz_convert(None)
        numeric_cols = [
            "quantidade_operacoes",
            "total_nf_transportadas",
            "total_propostas",
            "total_bruto_duplicata",
            "total_liquido_duplicata",
            "total_receita_cashforce",
            "taxa_efetiva_media",
            "prazo_medio",
        ]
        for col in numeric_cols:
            if col in df_view.columns:
                df_view[col] = pd.to_numeric(df_view[col], errors="coerce")
        return df_view
    except Exception as exc:
        st.error(f"Erro ao carregar dados agregados: {exc}")
        return pd.DataFrame()


BASE_COLUMNS = [
    "nfid",
    "numero_proposta",
    "data_operacao",
    "grupo_economico",
    "razao_social_comprador",
    "cnpj_comprador",
    "razao_social_fornecedor",
    "cnpj_fornecedor",
    "parceiro",
    "razao_social_financiador",
    "valor_bruto_duplicata",
    "valor_liquido_duplicata",
    "status_pagamento",
    "status_proposta",
    "receita_cashforce",
    "prazo_medio_operacao",
    "taxa_efetiva_mes_percentual",
]


@st.cache_data(ttl=3600)
def load_base_data(
    start_date, end_date, selected_parceiros: tuple[str, ...], selected_financiadores: tuple[str, ...]
) -> pd.DataFrame:
    try:
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        parceiros_tuple = tuple(selected_parceiros)
        financiadores_tuple = tuple(selected_financiadores)

        def apply_filters_to_query(query):
            query = query.gte("data_operacao", start_iso)
            query = query.lte("data_operacao", end_iso)
            if parceiros_tuple:
                query = query.in_("parceiro", list(parceiros_tuple))
            if financiadores_tuple:
                query = query.in_("razao_social_financiador", list(financiadores_tuple))
            return query

        data = _fetch_paginated(
            "propostas",
            ",".join(BASE_COLUMNS),
            apply_filters=apply_filters_to_query,
        )
        df_base = pd.DataFrame(data)
        if df_base.empty:
            return pd.DataFrame(columns=BASE_COLUMNS)
        missing_cols = [col for col in BASE_COLUMNS if col not in df_base.columns]
        for col in missing_cols:
            df_base[col] = pd.NA
        df_base["data_operacao"] = pd.to_datetime(df_base["data_operacao"], errors="coerce")
        if is_datetime64tz_dtype(df_base["data_operacao"]):
            df_base["data_operacao"] = df_base["data_operacao"].dt.tz_convert(None)
        for col in [
            "valor_bruto_duplicata",
            "valor_liquido_duplicata",
            "receita_cashforce",
            "prazo_medio_operacao",
            "taxa_efetiva_mes_percentual",
        ]:
            if col in df_base.columns:
                df_base[col] = pd.to_numeric(df_base[col], errors="coerce")
        return df_base
    except Exception as exc:
        st.error(f"Erro ao carregar tabela de operações: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=900)
def load_kpi_data() -> dict:
    """Carrega KPIs adicionais como ritmo projetado."""
    try:
        response = supabase.table("kpis_atuais").select("*").eq("id", 1).single().execute()
        return response.data or {}
    except Exception as exc:
        print(f"Erro ao buscar KPIs de Ritmo: {exc}")
        return {}


# --- 6. FUNÇÕES HELPER DE FORMATAÇÃO ---
def format_currency(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_integer(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{int(round(value)):,}".replace(",", ".")


def weighted_average(values: pd.Series, weights: pd.Series) -> float | None:
    mask = (~values.isna()) & (~weights.isna())
    if not mask.any():
        return None
    result = np.average(values[mask], weights=weights[mask])
    if np.isnan(result):
        return None
    return float(result)


def format_percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.2f}%"


def format_duration(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f} dias"


# --- 7. CARGA DE DADOS INICIAL ---
df_view = load_view_data()
if df_view.empty:
    st.error("Nenhum dado disponível na view `propostas_resumo_mensal`.")
    st.stop()


min_competencia = df_view["competencia"].min()
max_competencia = df_view["competencia"].max()
min_date = min_competencia.date() if not pd.isna(min_competencia) else datetime.now().date() - timedelta(days=365)
max_date = (max_competencia + pd.offsets.MonthEnd(0)).date() if not pd.isna(max_competencia) else datetime.now().date()


# --- 8. LAYOUT DO HEADER (Logo + Título + Filtro de Data) ---
# Esta é a implementação da sua sugestão no vídeo

header_col1, header_col2, header_col3 = st.columns([1, 2, 2])

with header_col1:
    html(
        f"""
        <div style="margin-top: 10px; display: inline-block; cursor: pointer;"
             title="Voltar para a aba Overview"
             onclick="const firstTab = window.parent.document.querySelector('button[role=\\'tab\\']'); if (firstTab) {{ firstTab.click(); }}">
            <img src="{LOGO_URL}" alt="Cashforce Logo" width="200" style="display: block;" />
        </div>
        """,
        height=80,
    )

with header_col2:
    st.write("")

with header_col3:
    # Filtro de data movido da sidebar para o header
    default_start = max(min_date, max_date - timedelta(days=90))
    date_range = st.date_input(
        "Período de Análise",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
        key="header_date_range"
    )

st.markdown("<hr style='border: none; height: 1px; background-color: var(--brand-border); margin: 1rem 0 2rem 0;'>", unsafe_allow_html=True)


# --- 9. LAYOUT DA SIDEBAR (Outros Filtros) ---
st.sidebar.header("Filtros")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date_raw, end_date_raw = date_range
else:
    start_date_raw = end_date_raw = date_range  # type: ignore[assignment]

start_date = datetime.combine(start_date_raw, datetime.min.time())
end_date = datetime.combine(end_date_raw, datetime.min.time())

if end_date.date() > max_date:
    end_date = datetime.combine(max_date, datetime.min.time())

# Caption do período agora fica na sidebar
st.sidebar.caption(f"Período selecionado: 📆 {start_date.strftime('%d/%m/%Y')} — {end_date.strftime('%d/%m/%Y')}")

parceiros_options = sorted(df_view["parceiro"].dropna().unique().tolist())
selected_parceiros = st.sidebar.multiselect(
    "👥 Parceiros",
    options=parceiros_options,
    default=parceiros_options,
)

financiadores_options = sorted(df_view["razao_social_financiador"].dropna().unique().tolist())
selected_financiadores = st.sidebar.multiselect(
    "🏦 Financiadores",
    options=financiadores_options,
    default=financiadores_options,
)

# --- 10. FILTRAGEM E CARGA DE DADOS SECUNDÁRIA ---
df_filtered = df_view.copy()
start_month = datetime(start_date.year, start_date.month, 1)
end_month = datetime(end_date.year, end_date.month, 1)
df_filtered = df_filtered[
    (df_filtered["competencia"] >= pd.Timestamp(start_month))
    & (df_filtered["competencia"] <= pd.Timestamp(end_month))
]

if selected_parceiros:
    df_filtered = df_filtered[df_filtered["parceiro"].isin(selected_parceiros)]
if selected_financiadores:
    df_filtered = df_filtered[df_filtered["razao_social_financiador"].isin(selected_financiadores)]

if df_filtered.empty:
    scope_df = df_view.copy()
    if selected_parceiros:
        scope_df = scope_df[scope_df["parceiro"].isin(selected_parceiros)]
    if selected_financiadores:
        scope_df = scope_df[scope_df["razao_social_financiador"].isin(selected_financiadores)]

    if scope_df.empty:
        st.warning("Nenhum dado disponível para os parceiros/financiadores selecionados em qualquer período.")
    else:
        min_scope = scope_df["competencia"].min()
        max_scope = scope_df["competencia"].max()
        periodo_disp = f"{min_scope.strftime('%m/%Y')} — {max_scope.strftime('%m/%Y')}" if not pd.isna(min_scope) and not pd.isna(max_scope) else "período desconhecido"
        st.warning(
            f"Sem dados no intervalo escolhido. Este recorte possui informações apenas entre {periodo_disp}."
        )
    st.stop()

# Otimização: Carrega dados base SOMENTE com os filtros globais aplicados
df_base = load_base_data(start_date, end_date, tuple(selected_parceiros), tuple(selected_financiadores))
if df_base.empty:
    st.warning("Não foi possível carregar as operações detalhadas para análises de clientes e explorador.")

df_base_filtered = df_base


# --- 11. LAYOUT DAS ABAS ---
overview_tab, clients_tab, funding_tab, explorer_tab = st.tabs(
    ["🚀 Overview Estratégico", "👥 Análise de Clientes", "🏦 Análise de Funding", "🔍 Explorador Operacional"]
)


with overview_tab:
    st.subheader("Visão Executiva · Performance no Período")

    kpi_data = load_kpi_data()
    ritmo_projetado = kpi_data.get("ritmo_projetado", 0)
    dias_restantes_text = kpi_data.get("dias_restantes_mes", "N/A")
    updated_at_raw = kpi_data.get("updated_at")
    if isinstance(updated_at_raw, str) and updated_at_raw.endswith("Z"):
        updated_at_raw = updated_at_raw.replace("Z", "+00:00")
    try:
        updated_at_display = (
            datetime.fromisoformat(updated_at_raw).strftime("%d/%m/%Y %H:%M")
            if updated_at_raw
            else "N/A"
        )
    except Exception:
        updated_at_display = "N/A"

    dias_restantes_help = (
        f"{dias_restantes_text} dias restantes no mês (dados Google Sheets). Atualizado em {updated_at_display} UTC"
    )

    # KPIs da View Agregada (Rápidos)
    volume_total = df_filtered["total_bruto_duplicata"].sum()
    total_propostas = (
        df_base_filtered["numero_proposta"].dropna().nunique() if not df_base_filtered.empty else 0
    )
    total_nfids = (
        df_base_filtered["nfid"].dropna().nunique() if not df_base_filtered.empty else 0
    )
    total_duplicatas = len(df_base_filtered) if not df_base_filtered.empty else 0
    grupos_ativos = df_filtered["grupo_economico"].dropna().nunique()
    
    # KPIs da Tabela Base (Processamento Ponderado)
    sacados_ativos = (
        df_base_filtered["cnpj_comprador"].dropna().nunique() if not df_base_filtered.empty else None
    )
    fornecedores_ativos = (
        df_base_filtered["cnpj_fornecedor"].dropna().nunique() if not df_base_filtered.empty else None
    )

    # Otimização: KPIs de média agora usam a view agregada (mais rápido)
    prazo_medio = weighted_average(
        df_filtered.get("prazo_medio", pd.Series(dtype=float)),
        df_filtered.get("total_bruto_duplicata", pd.Series(dtype=float)),
    )
    taxa_media = weighted_average(
        df_filtered.get("taxa_efetiva_media", pd.Series(dtype=float)),
        df_filtered.get("total_bruto_duplicata", pd.Series(dtype=float)),
    )

    # Renderização dos KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Projeção (Ritmo) Mês", format_currency(ritmo_projetado), help=dias_restantes_help)
    col2.metric("Volume Operado (VOP)", format_currency(volume_total))
    col3.metric("Total de Propostas (Negócios)", format_integer(total_propostas))
    col4.metric("Total de Notas Fiscais (NFIDs)", format_integer(total_nfids))
    col5.metric("Total de Duplicatas (Linhas)", format_integer(total_duplicatas))

    if not ritmo_projetado:
        st.caption("ℹ️ Ritmo ainda não atualizado. Execute o ETL para puxar os valores da planilha de Ritmo.")

    col6, col7, col8, col9, col10 = st.columns(5)
    col6.metric("Grupos Econômicos Ativos", format_integer(grupos_ativos))
    col7.metric("Sacados Ativos (CNPJs)", format_integer(sacados_ativos))
    col8.metric("Fornecedores Ativos (CNPJs)", format_integer(fornecedores_ativos))
    col9.metric("Prazo Médio Ponderado", format_duration(prazo_medio))
    col10.metric("Taxa Efetiva Média", format_percent(taxa_media))

    st.markdown("### Evolução do Volume Operado (VOP)")
    volume_timeline = (
        df_filtered.groupby("competencia", as_index=False)["total_bruto_duplicata"].sum().sort_values("competencia")
    )
    fig_volume = px.area(
        volume_timeline,
        x="competencia",
        y="total_bruto_duplicata",
        labels={"total_bruto_duplicata": "Volume Operado (R$)", "competencia": "Competência"},
        color_discrete_sequence=[BRAND_COLOR_SCALE_PRIMARY[0]],
    )
    fig_volume.update_layout(showlegend=False, title_text="VOP Mensal", title_x=0.1)
    st.plotly_chart(fig_volume, use_container_width=True)

    # --- IMPLEMENTAÇÃO DA SOLUÇÃO (ABRIR A CAIXA-PRETA) ---
    with st.expander("Ver dados absolutos da Série Histórica (Valores Absolutos por Mês)"):
        st.caption("Estes são os 'valores absolutos' pré-calculados que alimentam o gráfico acima.")
        dados_grafico = volume_timeline.copy()
        dados_grafico["competencia"] = dados_grafico["competencia"].dt.strftime("%Y-%m (%b)")
        dados_grafico["total_bruto_duplicata"] = dados_grafico["total_bruto_duplicata"].map(format_currency)
        st.dataframe(
            dados_grafico.rename(
                columns={
                    "competencia": "Competência",
                    "total_bruto_duplicata": "Volume Absoluto (R$)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    # --- FIM DA IMPLEMENTAÇÃO ---

    st.markdown("### Visão Geral por Categoria")
    col_a, col_b = st.columns(2)

    if not df_base_filtered.empty:
        top_grupos = (
            df_base_filtered.groupby("grupo_economico", dropna=True)["valor_bruto_duplicata"]
            .sum()
            .nlargest(5)
            .reset_index()
        )
        if not top_grupos.empty:
            fig_grupos = px.bar(
                top_grupos,
                x="valor_bruto_duplicata",
                y="grupo_economico",
                orientation="h",
                labels={"valor_bruto_duplicata": "Volume (R$)", "grupo_economico": "Grupo"},
                title="Top 5 Grupos Econômicos por Volume",
                color="valor_bruto_duplicata",
                color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
            )
            fig_grupos.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            col_a.plotly_chart(fig_grupos, use_container_width=True)
        else:
            col_a.info("Sem volume registrado para grupos econômicos no recorte atual.")

        top_parceiros = (
            df_base_filtered.groupby("parceiro", dropna=True)["valor_bruto_duplicata"]
            .sum()
            .nlargest(5)
            .reset_index()
        )
        if not top_parceiros.empty:
            fig_parceiros = px.bar(
                top_parceiros,
                x="valor_bruto_duplicata",
                y="parceiro",
                orientation="h",
                labels={"valor_bruto_duplicata": "Volume (R$)", "parceiro": "Parceiro"},
                title="Top 5 Parceiros por Volume",
                color="valor_bruto_duplicata",
                color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
            )
            fig_parceiros.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            col_b.plotly_chart(fig_parceiros, use_container_width=True)
        else:
            col_b.info("Sem parceiros com volume no período selecionado.")
    else:
        col_a.info("Não foi possível carregar dados operacionais para consultar grupos.")
        col_b.info("Não foi possível carregar dados operacionais para consultar parceiros.")

    col_c, col_d = st.columns(2)

    if not df_base_filtered.empty:
        top_financiadores = (
            df_base_filtered.groupby("razao_social_financiador", dropna=True)["valor_bruto_duplicata"]
            .sum()
            .nlargest(5)
            .reset_index()
        )
        if not top_financiadores.empty:
            fig_financiadores = px.bar(
                top_financiadores,
                x="valor_bruto_duplicata",
                y="razao_social_financiador",
                orientation="h",
                labels={"valor_bruto_duplicata": "Volume (R$)", "razao_social_financiador": "Financiador"},
                title="Top 5 Financiadores por Volume",
                color="valor_bruto_duplicata",
                color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
            )
            fig_financiadores.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            col_c.plotly_chart(fig_financiadores, use_container_width=True)
        else:
            col_c.info("Sem financiadores com volume no recorte atual.")
    else:
        col_c.info("Não foi possível carregar dados operacionais para consultar financiadores.")

    receita_series = (
        df_filtered.groupby("competencia", as_index=False)["total_receita_cashforce"].sum().sort_values("competencia")
    )
    fig_receita = px.line(
        receita_series,
        x="competencia",
        y="total_receita_cashforce",
        labels={"total_receita_cashforce": "Receita (R$)", "competencia": "Competência"},
        title="Receita Cashforce · Evolução Mensal",
        markers=True,
        color_discrete_sequence=[BRAND_COLOR_SCALE_PRIMARY[1]],
    )
    col_d.plotly_chart(fig_receita, use_container_width=True)


with clients_tab:
    sacados_tab, fornecedores_tab = st.tabs(["🏢 Sacados (Compradores)", "🚚 Fornecedores (Cedentes)"])

    with sacados_tab:
        st.subheader("Sacados · Engajamento dos Compradores")

        grupos_total = df_base_filtered["grupo_economico"].nunique(dropna=True)
        sacados_total = df_base_filtered["cnpj_comprador"].nunique(dropna=True)

        col1, col2 = st.columns(2)
        col1.metric("Grupos Econômicos Ativos", format_integer(grupos_total))
        col2.metric("Sacados Ativos (CNPJs)", format_integer(sacados_total))

        st.markdown("### Crescimento de Novos Sacados (Primeira Operação)")
        if not df_base_filtered.empty:
            sacados_first_seen = (
                df_base_filtered.dropna(subset=["cnpj_comprador", "data_operacao"])
                .sort_values("data_operacao")
                .groupby("cnpj_comprador")["data_operacao"]
                .min()
            )

            if sacados_first_seen.empty:
                st.info("Nenhum sacado novo identificado no período selecionado.")
            else:
                novos_sacados = (
                    sacados_first_seen.dt.to_period("M")
                    .value_counts()
                    .sort_index()
                    .rename_axis("competencia_period")
                    .to_frame("novos_sacados")
                )

                period_range = pd.period_range(
                    start=pd.Period(start_date, freq="M"),
                    end=pd.Period(end_date, freq="M"),
                )

                novos_sacados = (
                    novos_sacados.reindex(period_range, fill_value=0)
                    .reset_index()
                    .rename(columns={"index": "competencia_period"})
                )
                novos_sacados["competencia"] = novos_sacados["competencia_period"].dt.to_timestamp()

                if novos_sacados["novos_sacados"].sum() == 0:
                    st.info("Nenhum sacado novo identificado no período selecionado.")
                else:
                    fig_novos = px.bar(
                        novos_sacados,
                        x="competencia",
                        y="novos_sacados",
                        labels={"novos_sacados": "Novos Sacados", "competencia": "Competência"},
                        color="novos_sacados",
                        color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
                    )
                    fig_novos.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_novos, use_container_width=True)
        else:
            st.info("Sem dados operacionais para calcular novos sacados.")

        st.markdown("### Ranking de Grupos Econômicos")
        ranking_grupos = (
            df_base_filtered.dropna(subset=["grupo_economico"])
            .groupby("grupo_economico")
            .agg(
                volume=("valor_bruto_duplicata", "sum"),
                duplicatas=("nfid", "count"),
                propostas=("numero_proposta", "nunique"),
            )
            .reset_index()
        )
        if not ranking_grupos.empty:
            ranking_grupos["ticket_medio"] = ranking_grupos["volume"] / ranking_grupos["propostas"].replace(0, np.nan)
            ranking_grupos = ranking_grupos.sort_values("volume", ascending=False)
            st.dataframe(
                ranking_grupos.assign(
                    volume=ranking_grupos["volume"].map(format_currency),
                    ticket_medio=ranking_grupos["ticket_medio"].map(format_currency),
                ).rename(columns={"duplicatas": "Duplicatas", "propostas": "Propostas"}),
                use_container_width=True,
            )
        else:
            st.info("Nenhum grupo econômico encontrado.")

        st.markdown("### Health Check · Última Operação por Grupo")
        health_check = (
            df_base_filtered.dropna(subset=["grupo_economico"])
            .groupby("grupo_economico")["data_operacao"]
            .max()
            .reset_index()
            .rename(columns={"data_operacao": "ultima_operacao"})
        )
        if not health_check.empty:
            health_check["dias_sem_operar"] = (
                pd.Timestamp(datetime.now().date()) - health_check["ultima_operacao"]
            ).dt.days
            health_display = health_check.sort_values("ultima_operacao", ascending=False).copy()
            health_display["ultima_operacao"] = health_display["ultima_operacao"].dt.strftime("%d/%m/%Y")

            def color_health(dias: float):
                if pd.isna(dias):
                    return ""
                if dias > 90:
                    return "background-color: rgba(255, 100, 100, 0.25)"  # Risco
                if dias > 30:
                    return "background-color: rgba(255, 240, 100, 0.25)"  # Atenção
                return "background-color: rgba(100, 255, 100, 0.2)"  # Saudável

            st.dataframe(
                health_display.style.applymap(color_health, subset=["dias_sem_operar"]),
                use_container_width=True,
            )
        else:
            st.info("Ainda não há histórico para calcular último engajamento.")

    with fornecedores_tab:
        st.subheader("Fornecedores · Cobertura da Base Cedente")

        fornecedores_total = df_base_filtered["cnpj_fornecedor"].nunique(dropna=True)
        st.metric("Fornecedores Ativos (CNPJs)", format_integer(fornecedores_total))

        st.markdown("### Top 10 Fornecedores por Volume")
        ranking_fornecedores = (
            df_base_filtered.dropna(subset=["cnpj_fornecedor"])
            .groupby(["cnpj_fornecedor", "razao_social_fornecedor"])
            .agg(volume=("valor_bruto_duplicata", "sum"), duplicatas=("nfid", "count"))
            .reset_index()
            .sort_values("volume", ascending=False)
            .head(10)
        )
        if not ranking_fornecedores.empty:
            fig_fornecedores = px.bar(
                ranking_fornecedores,
                x="volume",
                y="razao_social_fornecedor",
                orientation="h",
                labels={"volume": "Volume (R$)", "razao_social_fornecedor": "Fornecedor"},
                color="volume",
                color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
            )
            fig_fornecedores.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_fornecedores, use_container_width=True)
        else:
            st.info("Sem fornecedores cadastrados para o recorte atual.")

        st.markdown("### Fornecedores por Grupo Econômico")
        fornecedores_por_grupo = (
            df_base_filtered.dropna(subset=["grupo_economico"])
            .groupby("grupo_economico")["cnpj_fornecedor"]
            .nunique()
            .reset_index(name="fornecedores_ativos")
            .sort_values("fornecedores_ativos", ascending=False)
        )
        if not fornecedores_por_grupo.empty:
            st.dataframe(fornecedores_por_grupo, use_container_width=True)
        else:
            st.info("Não há combinação de fornecedor por grupo para exibir.")


with funding_tab:
    st.subheader("Funding · Performance dos Parceiros Financeiros")

    financiadores_total = df_base_filtered["razao_social_financiador"].nunique(dropna=True)
    taxa_media_fin = weighted_average(
        df_base_filtered.get("taxa_efetiva_mes_percentual"),
        df_base_filtered.get("valor_bruto_duplicata"),
    )
    prazo_ponderado = weighted_average(
        df_base_filtered.get("prazo_medio_operacao"),
        df_base_filtered.get("valor_bruto_duplicata"),
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Financiadores Ativos", format_integer(financiadores_total))
    col2.metric("Taxa Efetiva Média (ponderada)", format_percent(taxa_media_fin))
    col3.metric("Prazo Médio Ponderado", format_duration(prazo_ponderado))

    st.markdown("### Volume por Financiador")
    volume_financiador = (
        df_base_filtered.groupby("razao_social_financiador", dropna=True)["valor_bruto_duplicata"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    if not volume_financiador.empty:
        fig_volume_fin = px.bar(
            volume_financiador,
            x="valor_bruto_duplicata",
            y="razao_social_financiador",
            orientation="h",
            labels={"valor_bruto_duplicata": "Volume (R$)", "razao_social_financiador": "Financiador"},
            color="valor_bruto_duplicata",
            color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
        )
        fig_volume_fin.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_volume_fin, use_container_width=True)
    else:
        st.info("Sem financiadores para exibir.")

    st.markdown("### Taxa Efetiva por Financiador")
    taxa_financiador = (
        df_base_filtered.dropna(subset=["razao_social_financiador", "taxa_efetiva_mes_percentual"])
        .groupby("razao_social_financiador")
        .apply(lambda x: weighted_average(x["taxa_efetiva_mes_percentual"], x["valor_bruto_duplicata"]))
        .reset_index(name="taxa_media_ponderada")
        .sort_values("taxa_media_ponderada", ascending=False)
    )
    if not taxa_financiador.empty:
        fig_taxa = px.bar(
            taxa_financiador,
            x="taxa_media_ponderada",
            y="razao_social_financiador",
            orientation="h",
            labels={"taxa_media_ponderada": "Taxa Efetiva Ponderada (%)", "razao_social_financiador": "Financiador"},
            color="taxa_media_ponderada",
            color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
        )
        fig_taxa.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_taxa, use_container_width=True)
    else:
        st.info("Não há dados de taxa efetiva para o recorte atual.")

    st.markdown("### Prazo Médio por Financiador")
    prazo_financiador = (
        df_base_filtered.dropna(subset=["razao_social_financiador", "prazo_medio_operacao"])
        .groupby("razao_social_financiador")
        .apply(lambda x: weighted_average(x["prazo_medio_operacao"], x["valor_bruto_duplicata"]))
        .reset_index(name="prazo_medio_ponderado")
        .sort_values("prazo_medio_ponderado", ascending=False)
    )
    if not prazo_financiador.empty:
        fig_prazo = px.bar(
            prazo_financiador,
            x="prazo_medio_ponderado",
            y="razao_social_financiador",
            orientation="h",
            labels={"prazo_medio_ponderado": "Prazo Médio Ponderado (dias)", "razao_social_financiador": "Financiador"},
            color="prazo_medio_ponderado",
            color_continuous_scale=BRAND_COLOR_SCALE_CONTINUOUS,
        )
        fig_prazo.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_prazo, use_container_width=True)
    else:
        st.info("Sem dados de prazo médio para os financiadores selecionados.")

    st.markdown("### Receita Cashforce · Evolução")
    receita_funding = (
        df_filtered.groupby("competencia", as_index=False)["total_receita_cashforce"]
        .sum()
        .sort_values("competencia")
    )
    fig_receita_fin = px.line(
        receita_funding,
        x="competencia",
        y="total_receita_cashforce",
        labels={"total_receita_cashforce": "Receita (R$)", "competencia": "Competência"},
        markers=True,
        color_discrete_sequence=[BRAND_COLOR_SCALE_PRIMARY[1]],
    )
    st.plotly_chart(fig_receita_fin, use_container_width=True)


with explorer_tab:
    st.subheader("Explorador Operacional · Pesquisa de Operações")
    st.caption(
        "Filtra diretamente a tabela base `propostas`. Os filtros globais (período, parceiro, financiador) já estão aplicados."
    )

    if df_base_filtered.empty:
        st.info("Não foi possível carregar dados operacionais. Ajuste os filtros principais.")
    else:
        hoje = end_date
        default_explorer_start = max(start_date, hoje - timedelta(days=30))
        
        # --- FILTROS LOCAIS DA ABA ---
        col1, col2 = st.columns([2, 1])
        search_term = col1.text_input(
            "Pesquisa rápida (NFID, CNPJ Comprador/Fornecedor)",
            placeholder="Busque por NFID, CNPJ...",
        )
        # Filtro de data local, limitado pelo filtro global
        date_filter = col2.date_input(
            "Refinar período (dentro do filtro global)",
            value=(default_explorer_start, end_date),
            min_value=start_date,
            max_value=end_date,
            key="explorer_date_range"
        )

        if isinstance(date_filter, tuple) and len(date_filter) == 2:
            op_start, op_end = date_filter
        else:
            op_start = date_filter  # type: ignore[assignment]
            op_end = end_date

        status_pagamento_opts = sorted(df_base_filtered["status_pagamento"].dropna().unique().tolist())
        status_proposta_opts = sorted(df_base_filtered["status_proposta"].dropna().unique().tolist())

        col3, col4 = st.columns(2)
        selected_pagamentos = col3.multiselect("Status de Pagamento", status_pagamento_opts, default=status_pagamento_opts)
        selected_propostas = col4.multiselect("Status de Proposta", status_proposta_opts, default=status_proposta_opts)

        # --- APLICAÇÃO DOS FILTROS LOCAIS ---
        explorer_df = df_base_filtered.copy()
        
        # Filtro de data local
        explorer_df = explorer_df[
            (explorer_df["data_operacao"].dt.date >= op_start)
            & (explorer_df["data_operacao"].dt.date <= op_end)
        ]

        if selected_pagamentos:
            explorer_df = explorer_df[explorer_df["status_pagamento"].isin(selected_pagamentos)]
        if selected_propostas:
            explorer_df = explorer_df[explorer_df["status_proposta"].isin(selected_propostas)]

        if search_term:
            search_lower = search_term.lower()
            explorer_df = explorer_df[
                explorer_df["nfid"].fillna("").str.lower().str.contains(search_lower)
                | explorer_df["cnpj_comprador"].fillna("").str.lower().str.contains(search_lower)
                | explorer_df["cnpj_fornecedor"].fillna("").str.lower().str.contains(search_lower)
            ]

        # --- KPIS DE VALIDAÇÃO (PARA O CEO) ---
        st.markdown("### Totais de Validação (Dados Brutos Filtrados)")
        st.caption("Estes são os totais brutos dos registros filtrados abaixo (limitado a 500 linhas para exibição).")

        total_bruto_explorador = explorer_df['valor_bruto_duplicata'].sum()
        total_linhas_explorador = len(explorer_df)
        total_propostas_explorador = explorer_df['numero_proposta'].nunique()

        val_col1, val_col2, val_col3 = st.columns(3)
        val_col1.metric("Volume Bruto (Filtrado)", format_currency(total_bruto_explorador))
        val_col2.metric("Total de Linhas (Duplicatas)", format_integer(total_linhas_explorador))
        val_col3.metric("Total de Propostas Únicas", format_integer(total_propostas_explorador))
        
        st.markdown("---")
        
        # --- EXIBIÇÃO DA TABELA ---
        explorer_df = explorer_df.sort_values("data_operacao", ascending=False)
        display_cols = [
            "data_operacao",
            "nfid",
            "numero_proposta",
            "grupo_economico",
            "razao_social_comprador",
            "cnpj_comprador",
            "razao_social_fornecedor",
            "cnpj_fornecedor",
            "parceiro",
            "razao_social_financiador",
            "valor_bruto_duplicata",
            "status_pagamento",
            "status_proposta",
        ]
        # Garantir que colunas existem antes de selecionar
        display_cols_exist = [col for col in display_cols if col in explorer_df.columns]
        explorer_df_display = explorer_df[display_cols_exist].head(500).copy()

        explorer_df_display["data_operacao"] = explorer_df_display["data_operacao"].dt.strftime("%d/%m/%Y")
        explorer_df_display["valor_bruto_duplicata"] = explorer_df_display["valor_bruto_duplicata"].map(format_currency)

        st.dataframe(explorer_df_display, use_container_width=True, hide_index=True)

# --- 12. RODAPÉ DA SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **Dica:** Use o **Explorador Operacional** para
    investigações pontuais sem sair do dashboard.
    
    Os dados são atualizados a cada sincronização do ETL.
    """
)
