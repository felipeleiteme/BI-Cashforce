# Documentação do BI-Cashforce v2.0

Este diretório reúne todo o material de referência e operação do sistema BI-Cashforce completo: **Pipeline ETL + Dashboard Streamlit + Assistente GPT**. Use-o como índice para acessar guias detalhados, diagramas e scripts de apoio.

## 📌 Visão Geral

O BI-Cashforce é composto por 3 componentes independentes:

1. **Pipeline ETL** (Vercel Serverless)
   - Sincroniza a planilha **"Operações"** do Google Sheets (90k+ linhas) com o Supabase
   - Processa todo o histórico em **lotes de 5.000 registros** com UPSERT por `nfid`
   - Atualiza a materialized view `propostas_resumo_mensal` ao final de cada execução

2. **Dashboard Streamlit** (Streamlit Cloud)
   - Interface visual interativa com gráficos e KPIs em tempo real
   - 5 tabs de análise (Parceiro, Overview, Temporal, Operacional, Financeiro)
   - Lê da view `propostas_resumo_mensal` (fonte única de verdade)
   - Usa `SUPABASE_ANON_KEY` (seguro com RLS)

3. **Assistente GPT** (OpenAI)
   - Consultas em linguagem natural sobre operações
   - Lê da view `propostas_resumo_mensal` via REST API
   - Insights, análises e alertas automáticos

## 🔄 Fluxo de Dados Atualizado

```
Google Sheets → ETL (Vercel) → Supabase (propostas)
                                      ↓
                                      ↓ refresh_propostas_resumo_mensal()
                                      ↓
                            propostas_resumo_mensal (MV)
                            ✅ FONTE ÚNICA DE VERDADE
                                   ↙      ↘
                      Dashboard           GPT
                    (Streamlit)       (OpenAI)
                     Gráficos          Consultas
                       KPIs             Insights
```

## 📁 Estrutura da Documentação

### 📖 Guias Principais

| Caminho | Conteúdo |
|---------|----------|
| [`../README.md`](../README.md) | README principal do projeto |
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | 🆕 Arquitetura técnica completa v2.0 |
| [`docs/guides/setup.md`](./guides/setup.md) | Configuração completa (Google Cloud, Supabase, Vercel, Streamlit) |
| [`docs/guides/deploy.md`](./guides/deploy.md) | Checklist de deploy (APIs + Dashboard) |
| [`docs/guides/troubleshooting.md`](./guides/troubleshooting.md) | Procedimentos de diagnóstico e correção |

### 🔧 Referências Técnicas

| Caminho | Conteúdo |
|---------|----------|
| [`docs/reference/database.md`](./reference/database.md) | Esquema detalhado da tabela `propostas` (59 colunas) |
| [`docs/reference/openapi_schema.json`](./reference/openapi_schema.json) | Schema OpenAPI para GPT Actions |
| [`docs/assistant/gpt_setup.md`](./assistant/gpt_setup.md) | Configuração do assistente GPT customizado |

## 🛠️ Ferramentas e Scripts

| Caminho | Descrição |
|---------|-----------|
| [`scripts/filter_new_records.py`](../scripts/filter_new_records.py) | Filtra CSVs locais removendo NFIDs já existentes no Supabase |
| [`scripts/test_supabase_api.sh`](../scripts/test_supabase_api.sh) | Smoke tests para os endpoints REST do Supabase |
| [`supabase/propostas_resumo_mensal.sql`](../supabase/propostas_resumo_mensal.sql) | Cria a materialized view, índices e função `refresh_propostas_resumo_mensal()` |

## 🔍 Operações e Monitoramento

### ETL (Vercel)
- **Execução manual**: `curl https://bi-cashforce.vercel.app/api/etl_sync`
- **Logs**: `vercel logs --follow` ou `vercel logs api/etl_sync.py`
- **Alertas**: endpoint `GET /api/resumo-alert` com parâmetros `competencia_id`, `grupo`, `threshold`

### Dashboard (Streamlit Cloud)
- **URL**: https://seu-app.streamlit.app
- **Logs**: Dashboard do Streamlit Cloud
- **Cache**: TTL de 1 hora (3600s)
- **Refresh da view**: Automático após ETL ou manual via SQL

### Assistente GPT (OpenAI)
- **Teste**: Pergunte "Qual foi o volume total do Marfrig em outubro de 2024?"
- **Verificação**: Compare resposta com Dashboard
- **Debug**: Ver logs de actions no OpenAI Platform

## ❗ Troubleshooting Rápido

Consulte [`docs/guides/troubleshooting.md`](./guides/troubleshooting.md) para cenários comuns:
- Erros de autenticação no Google Sheets ou Supabase
- Timeouts da função serverless
- Divergências de totais entre Dashboard e GPT
- Dashboard não carrega dados (RLS, ANON_KEY, etc)
- API ETL retorna erro 500

## 🔐 Segurança

### Separação de Chaves (v2.0)

| Componente | Chave | Tipo | Permissões |
|------------|-------|------|------------|
| ETL | `SUPABASE_KEY` | Service Role | Leitura + Escrita |
| Dashboard | `SUPABASE_ANON_KEY` | Anon | Somente Leitura (RLS) |
| GPT | `SUPABASE_ANON_KEY` | Anon | Somente Leitura (RLS) |

**Benefícios**:
- ✅ Dashboard não tem acesso de escrita ao banco
- ✅ ANON_KEY pode ser exposta publicamente (com RLS)
- ✅ Reduz risco de operações acidentais/maliciosas

## ✅ Próximos Passos Recomendados

1. **Deploy do Dashboard**: Siga [`docs/guides/deploy.md`](./guides/deploy.md) para hospedar no Streamlit Cloud
2. **Configure RLS**: Certifique-se de que políticas de leitura pública estão ativas
3. **Teste Consistência**: Verifique se Dashboard e GPT mostram os mesmos números
4. **Mantenha Segredos Seguros**: Use `.env.local.secrets` localmente e variáveis de ambiente nos serviços

## 📝 Changelog v2.0

**Principais Mudanças**:
- 🔒 Dashboard usa `ANON_KEY` (era `SERVICE_ROLE_KEY`)
- ⚡ Dashboard lê da view agregada (era tabela base)
- ✅ Dashboard e GPT usam fonte única de verdade
- 🧹 Arquivos obsoletos removidos
- 📦 Dependências separadas (`requirements.txt` vs `requirements-dashboard.txt`)
- 🚀 Dashboard movido para Streamlit Cloud (era Vercel)

Ver changelog completo: [`../README.md#changelog`](../README.md#changelog)

---

Para sugestões ou ajustes, atualize este README e abra um Pull Request 🚀
