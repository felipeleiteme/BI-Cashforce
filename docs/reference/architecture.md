# Arquitetura do BI-Cashforce

Este documento descreve a arquitetura técnica completa do sistema BI-Cashforce v2.0.

## 🏗️ Visão Geral

O BI-Cashforce é uma solução de Business Intelligence composta por 3 componentes independentes que compartilham uma **fonte única de verdade** (materialized view `propostas_resumo_mensal`):

```
┌─────────────────────────────────────────────────────────────┐
│                     FONTE DE DADOS                          │
│                   Google Sheets API                         │
│              "Operações" - 90k+ registros                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  COMPONENTE 1: ETL                          │
│                 Vercel Serverless                           │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  /api/etl_sync.py                            │          │
│  │  - Extração (Google Sheets API)              │          │
│  │  - Transformação (Pandas)                    │          │
│  │  - Carga (Supabase UPSERT em lotes)         │          │
│  │  - Refresh da Materialized View              │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  Trigger: Manual ou GitHub Actions (schedule)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE PERSISTÊNCIA                         │
│                 Supabase PostgreSQL                         │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  propostas (tabela base)                     │          │
│  │  - 73k+ registros                            │          │
│  │  - 59 colunas                                │          │
│  │  - PK: nfid (chave única da NF)             │          │
│  └────────────────┬─────────────────────────────┘          │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────┐          │
│  │  propostas_resumo_mensal (MV)                │          │
│  │  ✅ FONTE ÚNICA DE VERDADE                  │          │
│  │  - Agregação mensal por parceiro             │          │
│  │  - 6 colunas: competencia, parceiro,         │          │
│  │    qtd_operacoes, total_bruto, total_liquido,│          │
│  │    total_receita_cashforce                   │          │
│  │  - Refresh automático após ETL               │          │
│  └────────────────┬─────────────────────────────┘          │
└───────────────────┼─────────────────────────────────────────┘
                    │
           ┌────────┴─────────┐
           │                  │
           ▼                  ▼
┌─────────────────────┐  ┌──────────────────────┐
│  COMPONENTE 2:      │  │  COMPONENTE 3:       │
│  DASHBOARD          │  │  ASSISTENTE GPT      │
│  Streamlit Cloud    │  │  OpenAI GPT-4        │
│                     │  │                      │
│  dashboard.py       │  │  Custom Actions      │
│  - Lê MV via        │  │  - Lê MV via         │
│    ANON_KEY         │  │    REST API          │
│  - 5 tabs análise   │  │  - NLP queries       │
│  - Gráficos Plotly  │  │  - Insights          │
│  - Filtros tempo    │  │  - Alertas           │
└─────────────────────┘  └──────────────────────┘
```

## 📦 Componentes Detalhados

### 1. Pipeline ETL (Vercel Serverless)

**Localização**: `api/etl_sync.py`

**Responsabilidades**:
- Autenticar no Google Sheets via Service Account
- Ler todos os registros da planilha "Operações" (linha 4 como header)
- Transformar dados:
  - Normalizar nomes de colunas
  - Converter tipos (datas, números, booleanos)
  - Remover duplicatas por NFID
  - Sanitizar valores inválidos
- Carregar no Supabase:
  - UPSERT em lotes de 5k registros
  - Conflito resolvido por `nfid` (ON CONFLICT)
- Atualizar materialized view via `refresh_propostas_resumo_mensal()`

**Stack**:
- Python 3.9
- gspread v5.12.0 (Google Sheets API)
- oauth2client v4.1.3 (autenticação)
- pandas v2.2.0 (transformação)
- supabase-py v2.7.4 (persistência)
- python-dotenv v1.0.0 (config)

**Deploy**:
- Plataforma: Vercel Serverless Functions
- Timeout: 300s (5 minutos)
- Trigger: Manual ou GitHub Actions

**Env Vars**:
```bash
GOOGLE_SHEETS_CREDENTIALS_JSON  # Service Account JSON
GOOGLE_SHEET_NAME               # Nome da planilha
SUPABASE_URL                    # URL do projeto
SUPABASE_KEY                    # Service role key (escrita)
```

---

### 2. Dashboard (Streamlit Cloud)

**Localização**: `dashboard.py`

**Responsabilidades**:
- Carregar dados da view `propostas_resumo_mensal`
- Apresentar 5 tabs de análise:
  1. **Análise por Parceiro**: KPIs, comparação, evolução temporal
  2. **Overview Geral**: Indicadores principais, comparação de períodos
  3. **Análise Temporal**: Evolução mensal de volume, ops e ticket médio
  4. **Operacional**: Distribuição de ops por parceiro e competência
  5. **Financeiro**: Composição de valores, receita e margem
- Filtros: período, parceiro
- Cache de dados: 1 hora (TTL=3600s)

**Stack**:
- streamlit v1.33.0 (framework)
- plotly v5.18.0 (gráficos)
- pandas v2.2.0 (manipulação)
- supabase-py v2.7.4 (leitura)
- python-dotenv v1.0.0 (config)

**Deploy**:
- Plataforma: Streamlit Cloud (grátis)
- Arquivo: `requirements-dashboard.txt`
- Repositório: GitHub (autodeploy)

**Env Vars**:
```bash
SUPABASE_URL       # URL do projeto
SUPABASE_ANON_KEY  # Anon key (leitura pública com RLS)
```

**Segurança**:
- ✅ Usa `ANON_KEY` (não `SERVICE_ROLE_KEY`)
- ✅ RLS (Row Level Security) no Supabase
- ✅ Sem acesso de escrita ao banco
- ✅ Dados públicos controlados por políticas

---

### 3. Assistente GPT (OpenAI)

**Responsabilidades**:
- Responder consultas em linguagem natural
- Ler dados via Supabase REST API
- Executar operações:
  - `getResumoMensal`: Totais agregados da MV
  - `getTOP10GruposEconomicos`: Ranking de grupos
  - `getOperacoesPorCNPJ`: Busca por CNPJ específico
- Gerar insights, alertas e recomendações

**Stack**:
- GPT-4 (OpenAI)
- Supabase PostgREST (REST API)
- OpenAPI 3.1.0 (schema de actions)

**Autenticação**:
```http
Authorization: Bearer <SUPABASE_ANON_KEY>
```

**Endpoint Base**:
```
https://ximsykesrzxgknonmxws.supabase.co/rest/v1/
```

**Schema**:
- Ver `docs/reference/openapi_schema.json`
- Ver `docs/assistant/gpt_setup.md`

---

## 🔄 Fluxo de Dados Completo

### 1. Sincronização (ETL)

```
1. Trigger Manual/GitHub Actions
   ↓
2. Vercel invoca /api/etl_sync
   ↓
3. Autentica Google Sheets (Service Account)
   ↓
4. Lê todos os registros (head=4)
   ↓
5. Transforma dados (pandas)
   ↓
6. UPSERT em lotes (5k registros)
   ↓
7. Refresh da MV via função SQL
   ↓
8. Retorna status (200 OK ou 500 Error)
```

### 2. Visualização (Dashboard)

```
1. Usuário acessa Streamlit app
   ↓
2. Dashboard conecta Supabase (ANON_KEY)
   ↓
3. Lê propostas_resumo_mensal
   ↓
4. Cache (TTL 1h)
   ↓
5. Aplica filtros (período, parceiro)
   ↓
6. Renderiza gráficos (Plotly)
   ↓
7. Usuário interage (filtros, tabs)
```

### 3. Consulta (GPT)

```
1. Usuário pergunta em linguagem natural
   ↓
2. GPT escolhe action apropriada
   ↓
3. GPT invoca Supabase REST API
   ↓
4. Supabase retorna dados da MV
   ↓
5. GPT processa e formata resposta
   ↓
6. Usuário recebe análise + insights
```

---

## 🗄️ Modelo de Dados

### Tabela Base: `propostas`

**Colunas principais (59 no total)**:
```sql
- nfid (PK, TEXT)                 # Chave única da NF
- numero_proposta (INT)           # Número da proposta
- data_operacao (TIMESTAMP)       # Data da operação
- razao_social_comprador (TEXT)   # Razão social do comprador
- cnpj_comprador (TEXT)           # CNPJ do comprador
- grupo_economico (TEXT)          # Grupo econômico
- nome_parceiro (TEXT)            # Nome do parceiro (ex: Marfrig, Agrotools)
- valor_bruto_duplicata (NUMERIC) # Valor bruto
- valor_liquido_duplicata (NUMERIC) # Valor líquido
- receita_cashforce (NUMERIC)    # Receita Cashforce
- status_pagamento (TEXT)         # Status do pagamento
```

Ver esquema completo: `docs/reference/database.md`

---

### Materialized View: `propostas_resumo_mensal`

**✅ FONTE ÚNICA DE VERDADE**

```sql
CREATE MATERIALIZED VIEW propostas_resumo_mensal AS
SELECT
  DATE_TRUNC('month', data_operacao) AS competencia,
  nome_parceiro,
  COUNT(*) AS quantidade_operacoes,
  SUM(valor_bruto_duplicata) AS total_bruto_duplicata,
  SUM(valor_liquido_duplicata) AS total_liquido_duplicata,
  SUM(receita_cashforce) AS total_receita_cashforce
FROM propostas
WHERE data_operacao IS NOT NULL
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

**Função de Refresh**:
```sql
CREATE OR REPLACE FUNCTION refresh_propostas_resumo_mensal()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW propostas_resumo_mensal;
END;
$$ LANGUAGE plpgsql;
```

**Uso**:
- Dashboard: lê via `supabase.table("propostas_resumo_mensal").select("*")`
- GPT: lê via REST API `GET /rest/v1/propostas_resumo_mensal`
- ETL: atualiza via `SELECT refresh_propostas_resumo_mensal()`

**Benefícios**:
- 🚀 **Performance**: 1000x mais rápido (agregação pré-calculada)
- ✅ **Consistência**: Dashboard e GPT leem os mesmos dados
- 🔒 **Segurança**: Dados públicos com RLS

---

## 🔐 Segurança

### Service Role Key (SUPABASE_KEY)
- **Uso**: ETL apenas
- **Permissões**: Leitura + Escrita + DDL
- **Segurança**: Mantida em segredo (Vercel env vars)
- **Risco**: Alto (acesso total ao banco)

### Anon Key (SUPABASE_ANON_KEY)
- **Uso**: Dashboard + GPT
- **Permissões**: Controladas por RLS
- **Segurança**: Pública (pode ser exposta no frontend)
- **Risco**: Baixo (RLS limita acesso)

### Row Level Security (RLS)

```sql
-- Permitir leitura pública da view resumo
CREATE POLICY "Public read access"
ON propostas_resumo_mensal
FOR SELECT
TO anon
USING (true);
```

---

## 📊 Performance

### Benchmarks

| Operação | Tempo | Notas |
|----------|-------|-------|
| ETL completo (73k registros) | ~120s | Lotes de 5k |
| Refresh da MV | ~2s | Agregação mensal |
| Dashboard load (MV) | <1s | Cache 1h |
| GPT query (MV) | ~500ms | REST API |
| Dashboard load (tabela base) | ~30s | ❌ Não recomendado |

### Otimizações Aplicadas

1. **ETL em lotes**: 5k registros por vez (vs 1 registro)
2. **UPSERT**: Apenas registros novos/alterados
3. **Materialized View**: Agregação pré-calculada
4. **Cache no Dashboard**: TTL 1h
5. **Anon Key no Dashboard**: Sem overhead de auth

---

## 🚀 Deploy e Escalabilidade

### Limites Atuais

**Vercel (Hobby)**:
- ✅ Serverless functions ilimitadas
- ✅ Bandwidth 100GB/mês
- ❌ Cron Jobs: máx 2 (já atingido)
- Timeout: 300s/function

**Streamlit Cloud (Free)**:
- ✅ 1 app público
- ✅ GitHub autodeploy
- ✅ HTTPS incluso
- Limite: 1GB RAM

**Supabase (Free)**:
- ✅ 500MB storage
- ✅ 2GB bandwidth/mês
- ✅ 50k Row Level Security checks/dia
- Limite: 500 concurrent connections

### Escalabilidade Horizontal

Para escalar acima dos limites gratuitos:

1. **ETL**: GitHub Actions (grátis, ilimitado)
2. **Dashboard**: Streamlit for Teams ($250/mês)
3. **Banco**: Supabase Pro ($25/mês) ou Postgres dedicado

---

## 🔄 Manutenção e Troubleshooting

### Logs

**Vercel**:
```bash
vercel logs --follow
vercel logs api/etl_sync.py
```

**Streamlit**:
- Ver logs no dashboard do Streamlit Cloud

**Supabase**:
- Ver logs SQL no dashboard do Supabase

### Health Checks

```bash
# Testar API ETL
curl https://bi-cashforce.vercel.app/api/etl_sync

# Testar Supabase REST
curl -H "Authorization: Bearer <ANON_KEY>" \
  https://ximsykesrzxgknonmxws.supabase.co/rest/v1/propostas_resumo_mensal?limit=10

# Testar Dashboard
# Acessar: https://seu-app.streamlit.app
```

### Refresh Manual da MV

```sql
-- Via Supabase Dashboard ou psql
SELECT refresh_propostas_resumo_mensal();
```

---

## 📚 Referências Técnicas

- [Supabase REST API](https://supabase.com/docs/guides/api)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Streamlit Cloud](https://docs.streamlit.io/streamlit-cloud)
- [OpenAI GPT Actions](https://platform.openai.com/docs/actions)
- [Google Sheets API](https://developers.google.com/sheets/api)

---

**Última atualização**: 2025-11-05 (v2.0.0)
