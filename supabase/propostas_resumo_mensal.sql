-- Consolidated monthly view + materialized view + refresh helper
-- Execute this script no Supabase SQL Editor

-- Garantir que a versão antiga seja removida (evita falta de colunas novas)
drop view if exists public.propostas_resumo_mensal cascade;
drop materialized view if exists public.propostas_resumo_mensal_mv cascade;

-- 1. Materialized view com agregações mensais
create materialized view if not exists public.propostas_resumo_mensal_mv as
select
    date_trunc('month', data_operacao::date) as competencia,
    to_char(date_trunc('month', data_operacao::date), 'YYYY-MM') as competencia_id,
    extract(year from data_operacao::date)::int as ano,
    extract(month from data_operacao::date)::int as mes,
    coalesce(grupo_economico, 'Sem grupo') as grupo_economico,
    coalesce(razao_social_comprador, 'Sem comprador') as razao_social_comprador,
    coalesce(parceiro, 'Sem parceiro') as parceiro,
    coalesce(razao_social_financiador, 'Sem financiador') as razao_social_financiador, -- NOVA COLUNA

    -- Contagens e KPIs
    count(*) as quantidade_operacoes, -- Equivale a "# Operações"
    coalesce(count(distinct nfid), 0)::int as total_nf_transportadas, -- NOVO KPI
    coalesce(count(distinct cnpj_comprador), 0)::int as total_sacados, -- NOVO KPI
    coalesce(count(distinct cnpj_fornecedor), 0)::int as total_fornecedores, -- NOVO KPI

    -- Valores
    coalesce(sum(valor_bruto_duplicata), 0)::numeric(18,2) as total_bruto_duplicata,
    coalesce(sum(valor_liquido_duplicata), 0)::numeric(18,2) as total_liquido_duplicata,
    coalesce(sum(receita_cashforce), 0)::numeric(18,2) as total_receita_cashforce,
    coalesce(count(distinct numero_proposta), 0)::int as total_propostas,

    -- Médias (Novos KPIs)
    coalesce(avg(taxa_efetiva_mes_percentual), 0)::numeric(8,4) as taxa_efetiva_media,
    coalesce(avg(prazo_medio_operacao), 0)::numeric(10,2) as prazo_medio

from public.propostas
where data_operacao is not null
group by 1,2,3,4,5,6,7,8 -- ADICIONADO CAMPO 8
with no data;

-- 2. Índices para suportar refresh concorrente e filtros
create unique index if not exists propostas_resumo_mensal_mv_uq
    on public.propostas_resumo_mensal_mv (competencia_id, grupo_economico, razao_social_comprador, parceiro, razao_social_financiador);

create index if not exists propostas_resumo_mensal_mv_competencia_idx
    on public.propostas_resumo_mensal_mv (competencia desc);

-- 3. Atualiza dados iniciais (executado somente na primeira vez)
refresh materialized view public.propostas_resumo_mensal_mv;

-- 4. View utilizada pelo PostgREST (security_invoker garante RLS da base)
create or replace view public.propostas_resumo_mensal
with (security_invoker = true) as
select * from public.propostas_resumo_mensal_mv;

-- 5. Garantir RLS/autorizações (tabela já deve ter RLS habilitado)
grant select on public.propostas_resumo_mensal_mv to anon, authenticated, service_role;
grant select on public.propostas_resumo_mensal to anon, authenticated, service_role;

-- 6. Função helper para refrescar a view após o ETL
create or replace function public.refresh_propostas_resumo_mensal()
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
    result json;
begin
    begin
        refresh materialized view concurrently public.propostas_resumo_mensal_mv;
    exception
        when feature_not_supported or object_not_in_prerequisite_state then
            refresh materialized view public.propostas_resumo_mensal_mv;
    end;

    result := json_build_object(
        'status', 'ok',
        'refreshed_at', now()
    );

    return result;
end;
$$;

grant execute on function public.refresh_propostas_resumo_mensal() to service_role;
grant execute on function public.refresh_propostas_resumo_mensal() to authenticated;

comment on materialized view public.propostas_resumo_mensal_mv is
    'Consolidados mensais de propostas por grupo econômico, comprador, parceiro e financiador';

comment on function public.refresh_propostas_resumo_mensal() is
    'Atualiza a materialized view propostas_resumo_mensal_mv após o ETL';
