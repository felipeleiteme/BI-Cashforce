# ⚠️ AÇÃO URGENTE: Criar View no Supabase

## 🚨 Erro Atual
```
Could not find the table 'public.propostas_resumo_mensal' in the schema cache
```

**Causa**: A view SQL ainda não foi criada no banco de dados Supabase.

---

## 📋 SOLUÇÃO: Aplicar SQL no Supabase (5 minutos)

### Passo 1: Acessar Supabase SQL Editor
1. Acesse: https://supabase.com/dashboard
2. Selecione seu projeto **BI-Cashforce**
3. No menu lateral esquerdo, clique em **SQL Editor**
4. Clique em **New query** (botão verde no canto superior direito)

---

### Passo 2: Colar o Script SQL

Copie **TODO** o conteúdo do arquivo:
```
supabase/propostas_resumo_mensal.sql
```

**OU** use o script abaixo (versão simplificada):

```sql
-- ==================== SCRIPT COMPLETO ====================
-- Execute TUDO de uma vez (Ctrl+A, Ctrl+C, Ctrl+V no SQL Editor)

-- 1. Dropar view antiga se existir
DROP MATERIALIZED VIEW IF EXISTS public.propostas_resumo_mensal_mv CASCADE;
DROP VIEW IF EXISTS public.propostas_resumo_mensal CASCADE;

-- 2. Criar materialized view atualizada
CREATE MATERIALIZED VIEW public.propostas_resumo_mensal_mv AS
SELECT
    date_trunc('month', data_operacao::date) as competencia,
    to_char(date_trunc('month', data_operacao::date), 'YYYY-MM') as competencia_id,
    extract(year from data_operacao::date)::int as ano,
    extract(month from data_operacao::date)::int as mes,
    coalesce(grupo_economico, 'Sem grupo') as grupo_economico,
    coalesce(razao_social_comprador, 'Sem comprador') as razao_social_comprador,
    coalesce(parceiro, 'Sem parceiro') as parceiro,
    coalesce(razao_social_financiador, 'Sem financiador') as razao_social_financiador,

    -- Contagens e KPIs
    count(*) as quantidade_operacoes,
    coalesce(count(distinct nfid), 0)::int as total_nf_transportadas,
    coalesce(count(distinct cnpj_comprador), 0)::int as total_sacados,
    coalesce(count(distinct cnpj_fornecedor), 0)::int as total_fornecedores,

    -- Valores
    coalesce(sum(valor_bruto_duplicata), 0)::numeric(18,2) as total_bruto_duplicata,
    coalesce(sum(valor_liquido_duplicata), 0)::numeric(18,2) as total_liquido_duplicata,
    coalesce(sum(receita_cashforce), 0)::numeric(18,2) as total_receita_cashforce,

    -- Médias
    coalesce(avg(taxa_efetiva_mes_percentual), 0)::numeric(8,4) as taxa_efetiva_media,
    coalesce(avg(prazo_medio_operacao), 0)::numeric(10,2) as prazo_medio

FROM public.propostas
WHERE data_operacao IS NOT NULL
GROUP BY 1,2,3,4,5,6,7,8
WITH NO DATA;

-- 3. Índices para performance
CREATE UNIQUE INDEX propostas_resumo_mensal_mv_uq
    ON public.propostas_resumo_mensal_mv (competencia_id, grupo_economico, razao_social_comprador, parceiro, razao_social_financiador);

CREATE INDEX propostas_resumo_mensal_mv_competencia_idx
    ON public.propostas_resumo_mensal_mv (competencia DESC);

-- 4. Popular dados iniciais (IMPORTANTE!)
REFRESH MATERIALIZED VIEW public.propostas_resumo_mensal_mv;

-- 5. Criar view para PostgREST
CREATE OR REPLACE VIEW public.propostas_resumo_mensal
WITH (security_invoker = true) AS
SELECT * FROM public.propostas_resumo_mensal_mv;

-- 6. Permissões
GRANT SELECT ON public.propostas_resumo_mensal_mv TO anon, authenticated, service_role;
GRANT SELECT ON public.propostas_resumo_mensal TO anon, authenticated, service_role;

-- 7. Função para refresh (usada pelo ETL)
CREATE OR REPLACE FUNCTION public.refresh_propostas_resumo_mensal()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result json;
BEGIN
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY public.propostas_resumo_mensal_mv;
    EXCEPTION
        WHEN feature_not_supported OR object_not_in_prerequisite_state THEN
            REFRESH MATERIALIZED VIEW public.propostas_resumo_mensal_mv;
    END;

    result := json_build_object(
        'status', 'ok',
        'refreshed_at', now()
    );

    RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION public.refresh_propostas_resumo_mensal() TO service_role, authenticated;

-- 8. Comentários
COMMENT ON MATERIALIZED VIEW public.propostas_resumo_mensal_mv IS
    'Consolidados mensais de propostas por grupo econômico, comprador, parceiro e financiador';

COMMENT ON FUNCTION public.refresh_propostas_resumo_mensal() IS
    'Atualiza a materialized view propostas_resumo_mensal_mv após o ETL';
```

---

### Passo 3: Executar o Script
1. Após colar o script completo no SQL Editor
2. Clique no botão **Run** (ou pressione `Ctrl+Enter`)
3. Aguarde a execução (pode levar 30-60 segundos)

---

### Passo 4: Validar Criação

Execute esta query para validar:

```sql
-- Verificar estrutura da view
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'propostas_resumo_mensal_mv'
ORDER BY ordinal_position;

-- Verificar se há dados
SELECT COUNT(*) as total_linhas
FROM propostas_resumo_mensal;

-- Ver amostra dos dados
SELECT *
FROM propostas_resumo_mensal
LIMIT 5;
```

**Resultado esperado**:
- 17 colunas listadas
- `total_linhas` > 0 (pelo menos algumas linhas)
- Dados visíveis na amostra

---

## ⚠️ Possíveis Erros e Soluções

### Erro: "column does not exist"
**Causa**: Algum campo da tabela `propostas` não existe com o nome esperado.

**Solução**: Verificar nomes de colunas na tabela base:
```sql
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'propostas'
ORDER BY column_name;
```

Campos críticos que devem existir:
- `razao_social_financiador`
- `nfid`
- `cnpj_comprador`
- `cnpj_fornecedor`
- `taxa_efetiva_mes_percentual`
- `prazo_medio_operacao`

Se algum campo estiver **com nome diferente**, edite o script SQL antes de executar.

---

### Erro: "permission denied"
**Causa**: Usuário atual não tem permissão para criar views.

**Solução**: Execute como superusuário (postgres) no Supabase Dashboard.

---

### Erro: "out of memory"
**Causa**: Tabela `propostas` muito grande para criar índice único.

**Solução**: Remover índice único temporariamente:
```sql
-- Comentar a linha do índice único no script:
-- CREATE UNIQUE INDEX propostas_resumo_mensal_mv_uq ...
```

---

## ✅ Checklist Pós-Execução

- [ ] Script executado sem erros
- [ ] Query de validação retornou 17 colunas
- [ ] View tem dados (`COUNT(*) > 0`)
- [ ] Dashboard carrega sem erro (recarregar página)
- [ ] Filtros funcionam corretamente
- [ ] KPIs exibem valores realistas

---

## 🔄 Após Aplicar a View

1. **Recarregue o Dashboard** (F5 no navegador)
2. **Teste os filtros**: Período, Parceiro, Financiador
3. **Valide os KPIs**: Valores devem aparecer (não zeros)
4. **Verifique a Tab 4**: Novos KPIs operacionais

---

## 📞 Suporte

Se o erro persistir após executar o script:

1. **Capture a mensagem de erro completa** do SQL Editor
2. **Execute a query de validação** e compartilhe o resultado
3. **Verifique se a tabela base `propostas` existe**:
   ```sql
   SELECT COUNT(*) FROM propostas;
   ```

---

**Tempo estimado**: 5 minutos
**Dificuldade**: Fácil (copy/paste)
**Impacto**: Crítico (dashboard não funciona sem a view)

**⚠️ AÇÃO REQUERIDA AGORA** ⚠️
