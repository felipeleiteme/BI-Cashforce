import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

st.set_page_config(
    layout="wide",
    page_title="BI Cashforce | Dashboard Executivo",
    page_icon="■",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --font-size: 16px;
        --background: #ffffff;
        --foreground: #24292f;
        --primary: #030213;
        --primary-foreground: #ffffff;
        --muted: #ececf0;
        --muted-foreground: #717182;
        --border: rgba(0, 0, 0, 0.1);
        --teal-50: #f0fdfa;
        --teal-200: #99f6e4;
        --teal-500: #14b8a6;
        --teal-600: #0d9488;
        --teal-700: #0f766e;
        --emerald-500: #10b981;
        --emerald-600: #059669;
        --slate-50: #f8fafc;
        --slate-200: #e2e8f0;
        --slate-500: #64748b;
        --slate-600: #475569;
        --slate-700: #334155;
        --slate-900: #0f172a;
        --radius: 0.625rem;
        --radius-2xl: 1rem;
        --font-weight-medium: 500;
        --font-weight-normal: 400;
    }

    * {
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    html {
        font-size: var(--font-size);
    }

    .stApp {
        background: linear-gradient(135deg, var(--slate-50) 0%, rgba(240, 253, 250, 0.2) 50%, var(--slate-50) 100%);
    }

    [data-testid="stSidebar"] {
        background-color: var(--slate-50);
        border-right: 1px solid var(--border);
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-weight: var(--font-weight-medium);
        color: var(--slate-600);
        padding: 0.75rem 1.5rem;
        border-bottom: 2px solid transparent;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--teal-700);
        border-bottom: 2px solid var(--teal-600);
        background: transparent;
    }

    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--slate-200);
        border-radius: var(--radius-2xl);
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
    }

    [data-testid="stMetric"]:hover {
        box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 10px 10px -5px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: var(--slate-900);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: var(--slate-500);
    }

    .js-plotly-plot {
        border-radius: var(--radius-2xl);
        background: #fff;
        border: 1px solid var(--slate-200);
        padding: 1rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--teal-500) 0%, var(--emerald-500) 100%);
        color: #fff;
        border-radius: var(--radius);
        border: none;
        font-weight: var(--font-weight-medium);
        padding: 0.5rem 1.5rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--teal-600) 0%, var(--emerald-600) 100%);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


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


df_view = load_view_data()
if df_view.empty:
    st.error("Nenhum dado disponível na view `propostas_resumo_mensal`.")
    st.stop()


min_competencia = df_view["competencia"].min()
max_competencia = df_view["competencia"].max()
min_date = min_competencia.date() if not pd.isna(min_competencia) else datetime.now().date() - timedelta(days=365)
max_date = (max_competencia + pd.offsets.MonthEnd(0)).date() if not pd.isna(max_competencia) else datetime.now().date()

st.markdown(
    """
    <div style='padding: 1.5rem 0 1rem 0; border-bottom: 1px solid var(--border); margin-bottom: 2rem;'>
        <h1 style='margin: 0; font-size: 1.75rem; font-weight: 500; color: var(--primary);'>
            BI Cashforce · Painel Executivo
        </h1>
        <p style='margin: 0.5rem 0 0 0; color: var(--slate-600); font-size: 0.95rem;'>
            Visão consolidada das operações. Use os filtros laterais para ajustar o contexto de análise.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Filtros")

default_start = max(min_date, max_date - timedelta(days=90))
date_range = st.sidebar.date_input(
    "Período",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range  # type: ignore[assignment]

if end_date > max_date:
    end_date = max_date

st.sidebar.caption(f"📆 {start_date.strftime('%d/%m/%Y')} — {end_date.strftime('%d/%m/%Y')}")

parceiros_options = sorted(df_view["parceiro"].dropna().unique().tolist())
selected_parceiros = st.sidebar.multiselect(
    "Parceiros",
    options=parceiros_options,
    default=parceiros_options,
)

financiadores_options = sorted(df_view["razao_social_financiador"].dropna().unique().tolist())
selected_financiadores = st.sidebar.multiselect(
    "Financiadores",
    options=financiadores_options,
    default=financiadores_options,
)

df_filtered = df_view.copy()
df_filtered = df_filtered[
    (df_filtered["competencia"].dt.date >= start_date) & (df_filtered["competencia"].dt.date <= end_date)
]

if selected_parceiros:
    df_filtered = df_filtered[df_filtered["parceiro"].isin(selected_parceiros)]
if selected_financiadores:
    df_filtered = df_filtered[df_filtered["razao_social_financiador"].isin(selected_financiadores)]

if df_filtered.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

df_base = load_base_data(start_date, end_date, tuple(selected_parceiros), tuple(selected_financiadores))
if df_base.empty:
    st.warning("Não foi possível carregar a tabela base de operações para análises detalhadas.")

df_base_filtered = df_base

overview_tab, clients_tab, funding_tab, explorer_tab = st.tabs(
    ["🚀 Overview Estratégico", "👥 Análise de Clientes", "🏦 Análise de Funding", "🔍 Explorador Operacional"]
)


with overview_tab:
    st.subheader("Visão Executiva · Estamos crescendo?")

    volume_total = df_filtered["total_bruto_duplicata"].sum()
    total_operacoes = df_filtered["quantidade_operacoes"].sum()
    total_propostas = df_filtered.get("total_propostas", pd.Series(dtype=float)).sum()
    duplicatas_transacionadas = df_filtered["total_nf_transportadas"].sum()

    grupos_ativos = df_filtered["grupo_economico"].dropna().nunique()
    sacados_ativos = (
        df_base_filtered["cnpj_comprador"].dropna().nunique() if not df_base_filtered.empty else None
    )
    fornecedores_ativos = (
        df_base_filtered["cnpj_fornecedor"].dropna().nunique() if not df_base_filtered.empty else None
    )

    prazo_medio = weighted_average(
        df_filtered.get("prazo_medio", pd.Series(dtype=float)),
        df_filtered.get("total_bruto_duplicata", pd.Series(dtype=float)),
    )
    taxa_media = weighted_average(
        df_filtered.get("taxa_efetiva_media", pd.Series(dtype=float)),
        df_filtered.get("total_bruto_duplicata", pd.Series(dtype=float)),
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volume Operado (VOP)", format_currency(volume_total))
    col2.metric("Duplicatas Transacionadas (NFIDs)", format_integer(duplicatas_transacionadas))
    col3.metric("Total de Operações", format_integer(total_operacoes))
    col4.metric("Total de Propostas", format_integer(total_propostas))

    col5, col6, col7, col8, col9 = st.columns(5)
    col5.metric("Grupos Econômicos Ativos", format_integer(grupos_ativos))
    col6.metric("Sacados Ativos (CNPJs)", format_integer(sacados_ativos))
    col7.metric("Fornecedores Ativos (CNPJs)", format_integer(fornecedores_ativos))
    col8.metric("Prazo Médio", format_duration(prazo_medio))
    col9.metric("Taxa Efetiva Média", format_percent(taxa_media))

    st.markdown("### Evolução do Volume Operado")
    volume_timeline = (
        df_filtered.groupby("competencia", as_index=False)["total_bruto_duplicata"].sum().sort_values("competencia")
    )
    fig_volume = px.area(
        volume_timeline,
        x="competencia",
        y="total_bruto_duplicata",
        labels={"total_bruto_duplicata": "Volume Operado (R$)", "competencia": "Competência"},
        title="VOP mensal",
        color_discrete_sequence=["#0f766e"],
    )
    fig_volume.update_layout(showlegend=False)
    st.plotly_chart(fig_volume, use_container_width=True)

    with st.expander("Ver dados absolutos da Série Histórica (Valores Absolutos por Mês)"):
        st.caption("Estes são os valores absolutos pré-calculados que alimentam o gráfico acima.")
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
                color_continuous_scale="teal",
            )
            fig_grupos.update_layout(coloraxis_showscale=False)
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
                color_continuous_scale="teal",
            )
            fig_parceiros.update_layout(coloraxis_showscale=False)
            col_b.plotly_chart(fig_parceiros, use_container_width=True)
        else:
            col_b.info("Sem parceiros com volume no período selecionado.")
    else:
        col_a.info("Carregue dados operacionais para consultar grupos.")
        col_b.info("Carregue dados operacionais para consultar parceiros.")

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
                color_continuous_scale="teal",
            )
            fig_financiadores.update_layout(coloraxis_showscale=False)
            col_c.plotly_chart(fig_financiadores, use_container_width=True)
        else:
            col_c.info("Sem financiadores com volume no recorte atual.")
    else:
        col_c.info("Carregue dados operacionais para consultar financiadores.")

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
        color_discrete_sequence=["#0f766e"],
    )
    col_d.plotly_chart(fig_receita, use_container_width=True)


with clients_tab:
    sacados_tab, fornecedores_tab = st.tabs(["🏢 Sacados", "🚚 Fornecedores"])

    with sacados_tab:
        st.subheader("Sacados · Engajamento dos Compradores")

        grupos_total = df_base_filtered["grupo_economico"].nunique(dropna=True)
        sacados_total = df_base_filtered["cnpj_comprador"].nunique(dropna=True)

        col1, col2 = st.columns(2)
        col1.metric("Grupos Econômicos Ativos", format_integer(grupos_total))
        col2.metric("Sacados Ativos (CNPJs)", format_integer(sacados_total))

        st.markdown("### Crescimento de Novos Sacados")
        if not df_base_filtered.empty:
            sacados_first_seen = (
                df_base_filtered.dropna(subset=["cnpj_comprador", "data_operacao"])
                .sort_values("data_operacao")
                .groupby("cnpj_comprador")["data_operacao"]
                .min()
            )
            novos_sacados = (
                sacados_first_seen.dt.to_period("M")
                .value_counts()
                .sort_index()
                .to_timestamp()
                .reset_index(name="novos_sacados")
                .rename(columns={"index": "competencia"})
            )
            if not novos_sacados.empty and {"competencia", "novos_sacados"}.issubset(novos_sacados.columns):
                fig_novos = px.bar(
                    novos_sacados,
                    x="competencia",
                    y="novos_sacados",
                    labels={"novos_sacados": "Novos Sacados", "competencia": "Competência"},
                    color="novos_sacados",
                    color_continuous_scale="teal",
                )
                fig_novos.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_novos, use_container_width=True)
            else:
                st.info("Sem dados para calcular novos sacados.")
        else:
            st.info("Sem dados para calcular novos sacados.")

        st.markdown("### Ranking de Grupos Econômicos")
        ranking_grupos = (
            df_base_filtered.dropna(subset=["grupo_economico"])
            .groupby("grupo_economico")
            .agg(
                volume=("valor_bruto_duplicata", "sum"),
                operacoes=("nfid", "count"),
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
                ),
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
                    return "background-color: rgba(255, 100, 100, 0.25)"
                if dias > 30:
                    return "background-color: rgba(255, 240, 100, 0.25)"
                return "background-color: rgba(100, 255, 100, 0.2)"

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
            .agg(volume=("valor_bruto_duplicata", "sum"), operacoes=("nfid", "count"))
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
                color_continuous_scale="teal",
            )
            fig_fornecedores.update_layout(coloraxis_showscale=False)
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
        df_base_filtered["taxa_efetiva_mes_percentual"] if "taxa_efetiva_mes_percentual" in df_base_filtered else pd.Series(dtype=float),
        df_base_filtered["valor_bruto_duplicata"] if "valor_bruto_duplicata" in df_base_filtered else pd.Series(dtype=float),
    )
    prazo_ponderado = weighted_average(
        df_base_filtered["prazo_medio_operacao"] if "prazo_medio_operacao" in df_base_filtered else pd.Series(dtype=float),
        df_base_filtered["valor_bruto_duplicata"] if "valor_bruto_duplicata" in df_base_filtered else pd.Series(dtype=float),
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
            color_continuous_scale="teal",
        )
        fig_volume_fin.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_volume_fin, use_container_width=True)
    else:
        st.info("Sem financiadores para exibir.")

    st.markdown("### Taxa Efetiva por Financiador")
    taxa_financiador = (
        df_base_filtered.dropna(subset=["razao_social_financiador"])
        .groupby("razao_social_financiador")["taxa_efetiva_mes_percentual"]
        .mean()
        .reset_index()
    )
    if not taxa_financiador.empty:
        fig_taxa = px.bar(
            taxa_financiador,
            x="taxa_efetiva_mes_percentual",
            y="razao_social_financiador",
            orientation="h",
            labels={"taxa_efetiva_mes_percentual": "Taxa Efetiva (%)", "razao_social_financiador": "Financiador"},
            color="taxa_efetiva_mes_percentual",
            color_continuous_scale="teal",
        )
        fig_taxa.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_taxa, use_container_width=True)
    else:
        st.info("Não há dados de taxa efetiva para o recorte atual.")

    st.markdown("### Prazo Médio por Financiador")
    prazo_financiador = (
        df_base_filtered.dropna(subset=["razao_social_financiador"])
        .groupby("razao_social_financiador")["prazo_medio_operacao"]
        .mean()
        .reset_index()
    )
    if not prazo_financiador.empty:
        fig_prazo = px.bar(
            prazo_financiador,
            x="prazo_medio_operacao",
            y="razao_social_financiador",
            orientation="h",
            labels={"prazo_medio_operacao": "Prazo Médio (dias)", "razao_social_financiador": "Financiador"},
            color="prazo_medio_operacao",
            color_continuous_scale="teal",
        )
        fig_prazo.update_layout(coloraxis_showscale=False)
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
        color_discrete_sequence=["#047857"],
    )
    st.plotly_chart(fig_receita_fin, use_container_width=True)


with explorer_tab:
    st.subheader("Explorador Operacional · Pesquisa de Operações")
    st.caption(
        "Filtra diretamente a tabela base `propostas`. Os filtros globais continuam ativos; refine abaixo para consultas pontuais."
    )

    if df_base_filtered.empty:
        st.info("Carregue dados da tabela base para utilizar o explorador.")
    else:
        hoje = end_date
        default_explorer_start = max(start_date, hoje - timedelta(days=30))
        col1, col2 = st.columns([2, 1])
        search_term = col1.text_input(
            "Pesquisa rápida",
            placeholder="Busque por NFID, CNPJ do comprador ou fornecedor",
        )
        date_filter = col2.date_input(
            "Período de referência",
            value=(default_explorer_start, end_date),
            min_value=start_date,
            max_value=end_date,
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

        explorer_df = df_base_filtered.copy()
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
        explorer_df = explorer_df[display_cols].head(500).copy()

        explorer_df["data_operacao"] = explorer_df["data_operacao"].dt.strftime("%d/%m/%Y")
        explorer_df["valor_bruto_duplicata"] = explorer_df["valor_bruto_duplicata"].map(format_currency)

        st.dataframe(explorer_df, use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Dica:** Use o Explorador Operacional para investigações pontuais sem sair do dashboard. "
    "Os dados são atualizados a cada sincronização do ETL."
)
