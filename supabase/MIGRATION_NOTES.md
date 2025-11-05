# Migration Notes: propostas_resumo_mensal v2

## Data da Migração
2025-11-05

## Objetivo
Expandir a view consolidada `propostas_resumo_mensal` para suportar novos filtros e KPIs solicitados pelo negócio, mantendo a performance e consistência da "fonte única de verdade".

## Alterações Estruturais

### 1. Nova Dimensão: Razão Social do Financiador
- **Campo adicionado**: `razao_social_financiador`
- **Impacto no GROUP BY**: Agora agrupa por 8 dimensões (antes eram 7)
- **Índice único atualizado**: Inclui `razao_social_financiador` na chave composta

### 2. Novos KPIs - Contagens Distintas
| KPI | Campo | Tipo | Descrição |
|-----|-------|------|-----------|
| # NFs Transportadas | `total_nf_transportadas` | int | COUNT(DISTINCT nfid) |
| # Sacados | `total_sacados` | int | COUNT(DISTINCT cnpj_comprador) |
| # Fornecedores | `total_fornecedores` | int | COUNT(DISTINCT cnpj_fornecedor) |

### 3. Novos KPIs - Médias Ponderadas
| KPI | Campo | Tipo | Descrição |
|-----|-------|------|-----------|
| Taxa Efetiva Média | `taxa_efetiva_media` | numeric(8,4) | AVG(taxa_efetiva_mes_percentual) |
| Prazo Médio | `prazo_medio` | numeric(10,2) | AVG(prazo_medio_operacao) |

## Impactos Esperados

### Performance
- **Positivo**: Mantém agregação pré-calculada (materialized view)
- **Neutro**: Adição de 1 dimensão pode aumentar levemente o número de linhas
- **Mitigado**: Índices garantem refresh concorrente eficiente

### Compatibilidade
- ✅ **Backward compatible**: Campos antigos mantidos intactos
- ⚠️ **Atenção**: Dashboards devem ser atualizados para consumir novos campos
- 🔄 **Refresh necessário**: Executar `refresh materialized view` após deploy

## Passos para Aplicar

### 1. Backup (Recomendado)
```sql
-- Snapshot da view antiga (opcional, para rollback)
create table propostas_resumo_mensal_backup as
select * from propostas_resumo_mensal_mv;
```

### 2. Dropar View Antiga (Obrigatório)
```sql
-- Remove a materialized view antiga
drop materialized view if exists public.propostas_resumo_mensal_mv cascade;
```

### 3. Executar Script Atualizado
```bash
# Executar no Supabase SQL Editor:
supabase/propostas_resumo_mensal.sql
```

### 4. Validar Estrutura
```sql
-- Verificar colunas criadas
select column_name, data_type
from information_schema.columns
where table_name = 'propostas_resumo_mensal_mv'
order by ordinal_position;

-- Verificar contagem de registros
select count(*) from propostas_resumo_mensal_mv;
```

### 5. Testar Consulta com Novos Campos
```sql
-- Exemplo de consulta para validar novos KPIs
select
    competencia_id,
    razao_social_financiador,
    total_sacados,
    total_fornecedores,
    taxa_efetiva_media,
    prazo_medio
from propostas_resumo_mensal
where competencia_id = '2025-10'
limit 10;
```

## Rollback Plan

Caso necessário reverter:

```sql
-- 1. Dropar view nova
drop materialized view if exists public.propostas_resumo_mensal_mv cascade;

-- 2. Recriar view antiga (versão v1, sem novos campos)
-- (usar script anterior do git history)

-- 3. Restaurar dados do backup
insert into propostas_resumo_mensal_mv
select * from propostas_resumo_mensal_backup;
```

## Checklist de Deploy

- [ ] Executar backup da view atual
- [ ] Dropar view antiga com CASCADE
- [ ] Executar novo script SQL no Supabase
- [ ] Validar estrutura de colunas
- [ ] Executar refresh inicial (`refresh materialized view`)
- [ ] Testar consultas com novos filtros
- [ ] Atualizar dashboard.py para consumir novos campos
- [ ] Atualizar documentação do GPT Assistant
- [ ] Monitorar performance após deploy

## Próximos Passos

Após aplicar esta migração:
1. Atualizar `dashboard.py` para incluir:
   - Filtro por Razão Social do Financiador
   - Cards KPI para # Sacados, # Fornecedores, Taxa Média
2. Atualizar `gpt_setup.md` com instruções para consumir novos campos
3. Criar testes de integração para validar novos KPIs

## Referências

- Script original: `supabase/propostas_resumo_mensal.sql` (versão anterior)
- Script atualizado: `supabase/propostas_resumo_mensal.sql` (esta versão)
- Issue/Task: Atualização arquitetônica solicitada em 2025-11-05
