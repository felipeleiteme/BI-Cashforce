# BI-Cashforce - Pipeline ETL

Pipeline automatizado de ETL (Extração, Transformação e Carga) que sincroniza dados de operações financeiras do Google Sheets para o Supabase.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configuração](#configuração)
- [Deploy](#deploy)
- [Manutenção](#manutenção)
- [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

Este projeto implementa um pipeline serverless que:

1. **Extrai** dados da planilha "Operações" no Google Sheets
2. **Transforma** os dados (renomeia colunas, limpa dados)
3. **Carrega** no banco de dados Supabase (PostgreSQL)
4. **Executa automaticamente** a cada hora via Vercel Cron Job

## 🏗️ Arquitetura

```
┌─────────────────┐
│  Google Sheets  │
│   "Operações"   │
└────────┬────────┘
         │
         │ (1) Leitura via API
         ▼
┌─────────────────┐
│  Vercel Cron    │
│  (a cada hora)  │
└────────┬────────┘
         │
         │ (2) Aciona
         ▼
┌─────────────────┐
│ Python Function │
│   etl_sync.py   │
└────────┬────────┘
         │
         │ (3) UPSERT
         ▼
┌─────────────────┐
│    Supabase     │
│   (PostgreSQL)  │
└─────────────────┘
```

### Tecnologias

- **Runtime**: Python 3.9 (Vercel Serverless)
- **Agendador**: Vercel Cron Jobs
- **Fonte de Dados**: Google Sheets API
- **Banco de Dados**: Supabase (PostgreSQL)
- **Bibliotecas**: gspread, pandas, supabase-py

## 📁 Estrutura do Projeto

```
BI-Cashforce/
├── api/
│   └── _cron/
│       └── etl_sync.py          # Função serverless principal
├── docs/
│   ├── README.md                # Esta documentação
│   ├── SETUP.md                 # Guia de configuração
│   └── DATABASE.md              # Schema do banco de dados
├── .env                         # Variáveis de ambiente (local)
├── vercel.json                  # Configuração da Vercel
└── requirements.txt             # Dependências Python
```

## ⚙️ Configuração

### Pré-requisitos

1. Conta no [Google Cloud Platform](https://console.cloud.google.com)
2. Conta no [Supabase](https://supabase.com)
3. Conta na [Vercel](https://vercel.com)
4. CLI da Vercel instalada: `npm i -g vercel`

### Variáveis de Ambiente

Configurar as seguintes variáveis na Vercel:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | JSON da Service Account do Google | `{"type":"service_account",...}` |
| `GOOGLE_SHEET_NAME` | Nome da planilha | `Operações` |
| `SUPABASE_URL` | URL do projeto Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Service role key do Supabase | `eyJhbG...` |

### Configuração Local

1. Clone o repositório
2. Copie `.env.example` para `.env`
3. Preencha as credenciais no `.env`
4. Instale dependências: `pip install -r requirements.txt`

## 🚀 Deploy

### Deploy Inicial

```bash
# 1. Login na Vercel
vercel login

# 2. Deploy para produção
vercel --prod

# 3. Configurar variáveis de ambiente
vercel env add GOOGLE_SHEETS_CREDENTIALS_JSON
vercel env add GOOGLE_SHEET_NAME
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# 4. Redeploy para aplicar as variáveis
vercel --prod
```

### Atualizações

```bash
# Após modificar o código
git add .
git commit -m "Descrição das mudanças"
git push

# Deploy automático via Vercel Git Integration
# Ou deploy manual:
vercel --prod
```

## 🔄 Funcionamento

### Fluxo do ETL

1. **Trigger**: Cron Job executa às XX:00 de cada hora
2. **Autenticação Google**: Service Account autentica via OAuth2
3. **Extração**: Lê todos os registros da primeira aba da planilha
4. **Transformação**:
   - Converte para DataFrame do Pandas
   - Renomeia 59 colunas (PT → snake_case)
   - Limpa dados vazios/nulos
5. **Carga**: Executa UPSERT usando `nfid` como chave única
6. **Resposta**: Retorna JSON com status e número de linhas processadas

### Mapeamento de Colunas

O ETL mapeia as 59 colunas da planilha:

- **Proposta**: número, status, datas
- **Comprador**: razão social, CNPJ, grupo econômico
- **Nota Fiscal**: NFID, número, tipo, duplicata
- **Fornecedor**: razão social, CNPJ, status
- **Financiador**: razão social, CNPJ, parceiro
- **Valores**: bruto, líquido, taxas, deságio, IOF
- **Taxas %**: ao mês, ad valorem, efetiva
- **Pagamento**: forma, vencimento, status, datas
- **Prazos**: prazo, prazo médio
- **Anexos**: termo, boleto, comprovante
- **Controle**: dia atual

Ver detalhes em [DATABASE.md](./DATABASE.md)

### Agendamento

O Cron Job está configurado em `vercel.json`:

```json
{
  "crons": [{
    "path": "/api/_cron/etl_sync",
    "schedule": "0 * * * *"  // A cada hora
  }]
}
```

**Formato**: `minuto hora dia mês dia-da-semana`

Exemplos de outros agendamentos:
- `*/30 * * * *` - A cada 30 minutos
- `0 */6 * * *` - A cada 6 horas
- `0 9 * * *` - Todo dia às 09:00
- `0 0 * * 0` - Todo domingo à meia-noite

## 🔍 Monitoramento

### Logs da Vercel

```bash
# Ver logs em tempo real
vercel logs --follow

# Ver logs de uma função específica
vercel logs api/_cron/etl_sync.py
```

### Dashboard Vercel

1. Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
2. Selecione o projeto "BI-Cashforce"
3. Navegue para "Logs" ou "Cron Jobs"

### Verificar Execução

A função retorna:

**Sucesso (200)**:
```json
{
  "status": "success",
  "rows_processed": 150
}
```

**Erro (500)**:
```json
{
  "status": "error",
  "message": "Descrição do erro"
}
```

## 🛠️ Manutenção

### Adicionar Nova Coluna

1. Adicionar no Google Sheets
2. Atualizar `column_mapping` em `etl_sync.py`
3. Adicionar coluna no Supabase:
   ```sql
   ALTER TABLE propostas ADD COLUMN nova_coluna TEXT;
   ```
4. Deploy: `vercel --prod`

### Alterar Frequência do Cron

1. Modificar `schedule` em `vercel.json`
2. Commit e push
3. A Vercel aplicará automaticamente

### Backup do Banco

```bash
# Via Supabase CLI
supabase db dump -f backup.sql

# Via pg_dump (se tiver acesso direto)
pg_dump -h db.xxx.supabase.co -U postgres -d postgres > backup.sql
```

## 🐛 Troubleshooting

### Erro: "GOOGLE_SHEETS_CREDENTIALS_JSON não configurado"

**Solução**: Verificar se a variável está configurada na Vercel
```bash
vercel env ls
```

### Erro: "Unable to open file"

**Causas possíveis**:
1. Nome da planilha incorreto em `GOOGLE_SHEET_NAME`
2. Service Account sem permissão de leitura
3. Planilha não compartilhada com o email da Service Account

**Solução**: Compartilhar planilha com o email da Service Account (encontrado no JSON)

### Erro: "duplicate key value violates unique constraint"

**Causa**: Registro com `nfid` duplicado

**Solução**: O UPSERT deveria prevenir isso. Verificar se `on_conflict='nfid'` está configurado

### Cron Job não executa

**Verificar**:
1. Projeto está em plano Pro/Enterprise da Vercel (Cron Jobs são pagos)
2. `vercel.json` está correto e commitado
3. Logs da Vercel para mensagens de erro

### Dados não atualizam

**Verificar**:
1. Logs do Cron Job (se executou)
2. Estrutura da planilha (nomes das colunas)
3. Dados no Supabase (query manual)
4. Permissões da Service Account

## 📚 Recursos Adicionais

- [Documentação Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Supabase Docs](https://supabase.com/docs)
- [gspread Docs](https://docs.gspread.org/)

## 📝 Changelog

### v1.0.0 (2025-11-04)
- ✅ Pipeline ETL inicial
- ✅ Mapeamento de 59 colunas
- ✅ Cron Job horário
- ✅ UPSERT com conflito por NFID

## 📧 Suporte

Para questões ou problemas, abra uma issue no repositório ou contate o time de desenvolvimento.
