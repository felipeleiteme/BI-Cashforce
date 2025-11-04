# Documentação do BI-Cashforce

Este diretório reúne todo o material de referência e operação do pipeline ETL + GPT. Use-o como índice para acessar guias detalhados, diagramas e scripts de apoio.

## 📌 Visão Geral

- Sincroniza a planilha **"Operações"** do Google Sheets (90k+ linhas) com o Supabase
- Processa todo o histórico em **lotes de 5.000 registros** com UPSERT por `nfid`
- Atualiza a materialized view `propostas_resumo_mensal` ao final de cada execução
- Disponibiliza dados consolidados para o assistente GPT e para alertas operacionais (`api/resumo_alert.py`)

## 🔄 Fluxo Principal

```
Google Sheets → Vercel Cron / GitHub Actions → api/etl_sync.py → Supabase (propostas)
                                                           ↘ refresh_propostas_resumo_mensal()
                                                            → View propostas_resumo_mensal → GPT Actions / Alertas
```

## 📁 Estrutura da Documentação

| Caminho | Conteúdo |
|---------|----------|
| [`docs/guides/setup.md`](./guides/setup.md) | Configuração completa (Google Cloud, Supabase, Vercel) |
| [`docs/guides/deploy.md`](./guides/deploy.md) | Checklist de deploy e validações pós-publicação |
| [`docs/guides/troubleshooting.md`](./guides/troubleshooting.md) | Procedimentos de diagnóstico e correção |
| [`docs/reference/database.md`](./reference/database.md) | Esquema detalhado da tabela `propostas` e campos derivados |
| [`docs/reference/openapi_schema.json`](./reference/openapi_schema.json) | Schema OpenAPI utilizado pelo GPT Actions |
| [`docs/assistant/gpt_setup.md`](./assistant/gpt_setup.md) | Passo a passo para habilitar o assistente GPT |

## 🛠️ Ferramentas e Scripts

| Caminho | Descrição |
|---------|-----------|
| [`scripts/filter_new_records.py`](../scripts/filter_new_records.py) | Filtra CSVs locais removendo NFIDs já existentes no Supabase |
| [`scripts/test_supabase_api.sh`](../scripts/test_supabase_api.sh) | Smoke tests para os endpoints REST do Supabase |
| [`supabase/propostas_resumo_mensal.sql`](../supabase/propostas_resumo_mensal.sql) | Cria a materialized view, índices e função `refresh_propostas_resumo_mensal()` |

## 🔍 Operações e Monitoramento

- **Cron Job**: configurado em `vercel.json` (padrão diário) e reforçado pelo workflow [`etlsync`](../.github/workflows/etl-sync.yml)
- **Execução manual**: `curl https://bi-cashforce.vercel.app/api/etl_sync`
- **Logs**: `vercel logs https://bi-cashforce.vercel.app --scope felipeleites-projects-24aa8fa9`
- **Alertas**: endpoint `GET /api/resumo-alert` com parâmetros `competencia_id`, `grupo`, `threshold`

## ❗ Troubleshooting Rápido

Consulte [`docs/guides/troubleshooting.md`](./guides/troubleshooting.md) para cenários comuns:
- Erros de autenticação no Google Sheets ou Supabase
- Timeouts da função serverless
- Divergências de totais (sanitização de moedas e refresh da MV)

## ✅ Próximos Passos Recomendados

1. Revise o checklist de setup e deploy para garantir que todas as variáveis de ambiente estão atualizadas.
2. Execute os smoke tests após cada carregamento para validar filtros e paginação.
3. Mantenha as chaves sensíveis fora do repositório (use `.env.local.secrets` localmente e variáveis na Vercel).

Para sugestões ou ajustes, atualize este README e abra um Pull Request 🚀
