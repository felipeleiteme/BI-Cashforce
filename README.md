# BI-Cashforce - Pipeline ETL + Dashboard + GPT Integrado

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/felipeleiteme/BI-Cashforce)

Pipeline automatizado de ETL (Extração, Transformação e Carga) que sincroniza dados de operações financeiras do Google Sheets para o Supabase + Dashboard Streamlit interativo + Assistente GPT customizado para consultas inteligentes.

## 🚀 Início Rápido

```bash
# 1. Clone o repositório
git clone https://github.com/felipeleiteme/BI-Cashforce.git
cd BI-Cashforce

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Deploy na Vercel (apenas APIs)
vercel --prod

# 4. Deploy do Dashboard no Streamlit Cloud
# Siga o guia em docs/guides/deploy.md
```

## 📋 Visão Geral

Este projeto implementa uma solução completa de Business Intelligence com 3 componentes principais:

### 1. Pipeline ETL (Vercel Serverless)
- 📊 **Extrai** dados da planilha "Operações" no Google Sheets (90 mil+ registros, 59 colunas)
- 🔄 **Transforma** os dados (limpa, normaliza, converte tipos, remove duplicatas)
- 💾 **Carrega** todo o histórico no Supabase (PostgreSQL) via UPSERT em lotes de 5k registros
- 🔁 **Atualiza** a materialized view `propostas_resumo_mensal` após cada sincronização
- ✅ **73.227 registros** sincronizados na última execução completa

### 2. Dashboard Streamlit (Visualização)
- 📊 **Interface visual interativa** - Dashboard moderno com gráficos e KPIs em tempo real
- 🎯 **Filtros dinâmicos** - Por período, parceiro e competência
- 📈 **5 Tabs de análise**:
  - **Análise por Parceiro** - Comparação de volume, operações, ticket médio e margem
  - **Overview Geral** - KPIs principais com comparação de períodos
  - **Análise Temporal** - Evolução de volume, operações e ticket médio
  - **Operacional** - Distribuição de operações por parceiro e competência
  - **Financeiro** - Composição de valores, receita e margem por parceiro
- 🔒 **Seguro e rápido** - Usa `SUPABASE_ANON_KEY` com RLS + leitura da view agregada

### 3. Assistente GPT Integrado (Consultas Inteligentes)
- 🤖 **Consultas em linguagem natural** - Pergunte em português sobre suas operações
- 📈 **Análises automáticas** - Totalizadores, médias, insights e comparações
- 🔍 **Filtros inteligentes** - Por CNPJ, grupo, status, data, valor, etc.
- 📊 **Apresentação formatada** - Tabelas, resumos e recomendações
- 🎯 **Fonte única de verdade** - Lê da mesma view `propostas_resumo_mensal` que o Dashboard

## 🏗️ Arquitetura Atualizada

```
┌─────────────────┐
│  Google Sheets  │  90k+ registros (fonte)
│   "Operações"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vercel API     │  ETL Serverless
│  /api/etl_sync  │  (invoke manual ou GitHub Actions)
└────────┬────────┘
         │
         ▼
┌────────────────────────────┐
│   Supabase (PostgreSQL)    │
│  ┌──────────────────────┐  │
│  │ propostas (tabela)   │  │  73k+ registros
│  └──────────┬───────────┘  │
│             │               │
│             ▼               │
│  ┌──────────────────────────┐
│  │ propostas_resumo_mensal  │  View materializada
│  │ (agregação por mês)      │  (fonte única de verdade)
│  └────┬─────────────────┬───┘
└───────┼─────────────────┼────┘
        │                 │
        ▼                 ▼
┌────────────────┐  ┌─────────────────┐
│ Dashboard      │  │   GPT Custom    │
│ (Streamlit)    │  │  (OpenAI)       │
│ Visualização   │  │  Consultas NLP  │
└────────────────┘  └─────────────────┘
   • Gráficos         • Análises
   • KPIs             • Insights
   • Filtros          • Alertas
```

### Stack Tecnológica

**Backend ETL:**
- **Runtime**: Python 3.9 (Vercel Serverless Functions)
- **Fonte**: Google Sheets API (gspread + oauth2client)
- **Destino**: Supabase PostgreSQL (supabase-py v2.7.4)
- **Transformação**: pandas v2.2.0
- **Deploy**: Vercel CLI

**Dashboard:**
- **Framework**: Streamlit v1.33.0
- **Gráficos**: Plotly v5.18.0
- **Deploy**: Streamlit Cloud
- **Segurança**: SUPABASE_ANON_KEY + RLS

**Assistente GPT:**
- **Plataforma**: OpenAI GPT-4
- **API**: Supabase REST API (PostgREST)
- **Schema**: OpenAPI 3.1.0
- **Autenticação**: Bearer token (anon key)

## 📁 Estrutura do Projeto

```
BI-Cashforce/
├── api/
│   ├── etl_sync.py              # Função serverless principal do ETL
│   └── resumo_alert.py          # Endpoint para alertas de volume
├── docs/
│   ├── README.md                # Índice da documentação
│   ├── assistant/
│   │   └── gpt_setup.md         # Guia do assistente GPT
│   ├── guides/
│   │   ├── deploy.md            # Passo a passo de deploy
│   │   ├── setup.md             # Configuração completa
│   │   └── troubleshooting.md   # Checklists e correções
│   └── reference/
│       ├── database.md          # Esquema detalhado da tabela propostas
│       └── openapi_schema.json  # Schema OpenAPI para Actions
├── scripts/
│   ├── filter_new_records.py    # CLI para filtrar CSVs locais
│   └── test_supabase_api.sh     # Smoke tests dos endpoints REST
├── supabase/
│   └── propostas_resumo_mensal.sql # Materialized View + função de refresh
├── planilhas/
│   └── prepare_csv_import.py    # Utilitário para preparar CSVs
├── dashboard.py                 # Dashboard Streamlit (deploy separado)
├── requirements.txt             # Dependências das APIs (Vercel)
├── requirements-dashboard.txt   # Dependências do Dashboard (Streamlit Cloud)
├── vercel.json                  # Configuração Vercel
├── .vercelignore                # Arquivos ignorados no deploy
└── README.md                    # Este arquivo
```

## ⚙️ Configuração

### Pré-requisitos

- Conta [Google Cloud Platform](https://console.cloud.google.com)
- Conta [Supabase](https://supabase.com)
- Conta [Vercel](https://vercel.com) (Hobby é suficiente)
- Conta [Streamlit Cloud](https://share.streamlit.io) (grátis)
- [Vercel CLI](https://vercel.com/cli) instalada

### Variáveis de Ambiente

| Variável | Onde Usar | Descrição |
|----------|-----------|-----------|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Vercel | JSON da Service Account do Google Cloud |
| `GOOGLE_SHEET_NAME` | Vercel | Nome da planilha (ex: "Operações") |
| `SUPABASE_URL` | Vercel + Streamlit | URL do projeto Supabase |
| `SUPABASE_KEY` | Vercel apenas | Service role key (para ETL com escrita) |
| `SUPABASE_ANON_KEY` | Streamlit apenas | Anon key (para Dashboard com RLS) |

### Setup Rápido

1. **Google Cloud**: Crie Service Account e habilite Google Sheets API
2. **Google Sheets**: Compartilhe planilha com email da Service Account
3. **Supabase**: Crie tabela `propostas` e view `propostas_resumo_mensal`
4. **Vercel**: Configure env vars e faça deploy das APIs
5. **Streamlit Cloud**: Configure env vars e faça deploy do dashboard

📚 **Guia completo**: [docs/guides/setup.md](./docs/guides/setup.md)

## 🚀 Deploy

### 1. Deploy das APIs (Vercel)

```bash
# Login
vercel login

# Deploy
vercel --prod

# Configurar variáveis (apenas para APIs)
vercel env add GOOGLE_SHEETS_CREDENTIALS_JSON
vercel env add GOOGLE_SHEET_NAME
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Testar API
curl https://seu-projeto.vercel.app/api/etl_sync
```

### 2. Deploy do Dashboard (Streamlit Cloud)

1. Vá em https://share.streamlit.io
2. Conecte seu repositório GitHub
3. Configure o arquivo principal: `dashboard.py`
4. Configure as variáveis de ambiente:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
5. Clique em "Deploy"

📚 **Guia completo de deploy**: [docs/guides/deploy.md](./docs/guides/deploy.md)

## 📊 Fonte Única de Verdade: `propostas_resumo_mensal`

Para garantir **consistência total** entre Dashboard e GPT, ambos leem da **mesma view materializada**:

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

**Benefícios:**
- ✅ **Consistência**: Dashboard e GPT mostram os mesmos números
- ✅ **Performance**: 1000x mais rápido que ler 73k registros
- ✅ **Segurança**: Dashboard usa ANON_KEY (público seguro com RLS)

## 🔍 Monitoramento

### Logs das APIs

```bash
# Ver logs em tempo real
vercel logs --follow

# Logs da função ETL
vercel logs api/etl_sync.py
```

### Resposta da API

**Sucesso (200)**:
```json
{
  "status": "success",
  "rows_processed": 73227
}
```

**Erro (500)**:
```json
{
  "status": "error",
  "message": "Descrição do erro"
}
```

## 🛠️ Desenvolvimento Local

### Executar o Dashboard Localmente

```bash
# Instalar dependências do dashboard
pip install -r requirements-dashboard.txt

# Configurar .env
cp .env.example .env
# Adicione SUPABASE_URL e SUPABASE_ANON_KEY

# Executar o dashboard
streamlit run dashboard.py

# Acessar: http://localhost:8501
```

### Testar API ETL Localmente

```bash
# Instalar dependências das APIs
pip install -r requirements.txt

# Testar localmente com Vercel Dev
vercel dev

# Acessar: http://localhost:3000/api/etl_sync
```

## 🐛 Troubleshooting

### Dashboard não carrega dados

**Verificar**:
- `SUPABASE_ANON_KEY` está configurada corretamente
- View `propostas_resumo_mensal` existe no Supabase
- RLS está configurado permitindo leitura pública

### API ETL retorna erro 500

**Verificar**:
- `GOOGLE_SHEETS_CREDENTIALS_JSON` está correto (JSON válido)
- Planilha foi compartilhada com o email da Service Account
- `SUPABASE_KEY` (service_role) tem permissões de escrita

### Números inconsistentes entre Dashboard e GPT

**Solução**: Ambos devem ler da view `propostas_resumo_mensal`. Verifique:
```sql
-- Atualizar a view manualmente se necessário
SELECT refresh_propostas_resumo_mensal();
```

📚 **Mais soluções**: [docs/guides/troubleshooting.md](./docs/guides/troubleshooting.md)

## 📚 Documentação Completa

- [📖 README Completo](./docs/README.md) - Arquitetura, funcionamento e troubleshooting
- [⚙️ Guia de Setup](./docs/guides/setup.md) - Configuração passo a passo
- [🚀 Guia de Deploy](./docs/guides/deploy.md) - Checklist de produção
- [🛠️ Troubleshooting](./docs/guides/troubleshooting.md) - Diagnóstico rápido
- [💾 Schema do Banco](./docs/reference/database.md) - Estrutura e consultas úteis
- [🤖 Configuração do GPT](./docs/assistant/gpt_setup.md) - Assistente GPT customizado

## 📝 Changelog

### v2.0.0 (2025-11-05) - Dashboard Refactor

**Correções Críticas:**
- 🔒 **Segurança**: Dashboard agora usa `SUPABASE_ANON_KEY` em vez de service_role key
- ⚡ **Performance**: Dashboard lê da view `propostas_resumo_mensal` (1000x mais rápido)
- ✅ **Consistência**: Dashboard e GPT agora usam a mesma fonte de verdade
- 🧹 **Limpeza**: Removidos arquivos obsoletos (check_marfrig*.py, dashboard_backup.py, etc)
- 📦 **Dependências**: Separadas em `requirements.txt` (APIs) e `requirements-dashboard.txt`
- 🚀 **Deploy**: Dashboard movido para Streamlit Cloud (Vercel só APIs)

**Arquivos Removidos:**
- `check_marfrig.py` (debug temporário)
- `check_marfrig_oct.py` (debug temporário)
- `dashboard_backup.py` (backup obsoleto)
- `sync_csv_to_supabase.py` (substituído por api/etl_sync.py)
- `api/test.py` (debug temporário)

### v1.1.0 (2025-11-05)

- ✅ ETL em lotes (5k) cobrindo todo o histórico da planilha
- ✅ Refresh automático da materialized view `propostas_resumo_mensal`
- ✅ Novo endpoint de alertas (`api/resumo_alert.py`)
- ✅ Estrutura de documentação reorganizada (guides / reference / assistant)
- ✅ Scripts utilitários movidos para `scripts/`

### v1.0.0 (2025-11-04)

- ✅ Pipeline ETL inicial
- ✅ Mapeamento de 59 colunas
- ✅ UPSERT com conflito por NFID
- ✅ Documentação inicial
- ✅ Assistente GPT customizado integrado

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📧 Contato

Felipe Leite - [@felipeleiteme](https://github.com/felipeleiteme)

Link do Projeto: [https://github.com/felipeleiteme/BI-Cashforce](https://github.com/felipeleiteme/BI-Cashforce)

---

**Desenvolvido com ❤️ usando [Claude Code](https://claude.com/claude-code)**
