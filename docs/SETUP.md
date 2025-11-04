# Guia de Configuração - BI-Cashforce

Este guia detalha todos os passos necessários para configurar o projeto do zero.

## 📋 Índice

1. [Google Cloud Platform](#1-google-cloud-platform)
2. [Google Sheets](#2-google-sheets)
3. [Supabase](#3-supabase)
4. [Vercel](#4-vercel)
5. [Teste Local](#5-teste-local)

---

## 1. Google Cloud Platform

### 1.1 Criar Projeto

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Clique em **"Select a project"** → **"New Project"**
3. Nome: `BI-Cashforce` (ou outro nome)
4. Clique em **"Create"**

### 1.2 Habilitar Google Sheets API

1. No menu lateral, vá em **"APIs & Services"** → **"Library"**
2. Busque por **"Google Sheets API"**
3. Clique em **"Enable"**

### 1.3 Criar Service Account

1. Vá em **"APIs & Services"** → **"Credentials"**
2. Clique em **"Create Credentials"** → **"Service Account"**
3. Preencha:
   - **Name**: `bi-cashforce-etl`
   - **Description**: `Service Account para pipeline ETL`
4. Clique em **"Create and Continue"**
5. **Role**: Selecione `Editor` (ou crie role customizada)
6. Clique em **"Done"**

### 1.4 Gerar Chave JSON

1. Clique na Service Account criada
2. Vá na aba **"Keys"**
3. Clique em **"Add Key"** → **"Create new key"**
4. Selecione **JSON**
5. Clique em **"Create"**
6. **Salve o arquivo JSON** (será usado nas variáveis de ambiente)

### 1.5 Copiar Email da Service Account

No JSON baixado, copie o valor de `client_email`:

```json
{
  "client_email": "bi-cashforce-etl@projeto-123456.iam.gserviceaccount.com"
}
```

---

## 2. Google Sheets

### 2.1 Criar/Preparar Planilha

1. Acesse [sheets.google.com](https://sheets.google.com)
2. Abra a planilha **"Operações"** (ou crie uma nova)
3. Certifique-se que a primeira linha contém os cabeçalhos exatos:

```
Número da Proposta | Status da Proposta | Data da operação | ...
```

### 2.2 Compartilhar com Service Account

1. Clique em **"Share"** (Compartilhar)
2. Cole o email da Service Account copiado no passo 1.5
3. Permissão: **Editor** ou **Viewer** (Viewer é suficiente para ETL)
4. **Desmarque** "Notify people"
5. Clique em **"Share"**

### 2.3 Copiar Nome da Planilha

Copie o nome exato da planilha (ex: `Operações`). Será usado em `GOOGLE_SHEET_NAME`.

---

## 3. Supabase

### 3.1 Criar Projeto

1. Acesse [supabase.com](https://supabase.com)
2. Clique em **"New Project"**
3. Preencha:
   - **Name**: `bi-cashforce`
   - **Database Password**: (crie uma senha forte)
   - **Region**: Escolha a mais próxima (ex: South America - São Paulo)
4. Clique em **"Create new project"**
5. Aguarde ~2 minutos para o projeto ser provisionado

### 3.2 Criar Tabela

1. No menu lateral, vá em **"SQL Editor"**
2. Clique em **"New query"**
3. Cole o SQL completo:

```sql
CREATE TABLE propostas (
  id SERIAL PRIMARY KEY,

  -- Informações da Proposta
  numero_proposta TEXT,
  status_proposta TEXT,
  data_operacao DATE,
  data_aceite_proposta DATE,

  -- Grupo Econômico e Comprador
  grupo_economico TEXT,
  razao_social_comprador TEXT,
  cnpj_comprador TEXT,
  status_comprador TEXT,

  -- Nota Fiscal e Duplicata
  nfid TEXT UNIQUE NOT NULL,
  numero_nota_fiscal TEXT,
  tipo_nota TEXT,
  numero_duplicata TEXT,
  data_inclusao_nf DATE,
  data_emissao_nf DATE,
  descricao TEXT,

  -- Fornecedor
  razao_social_fornecedor TEXT,
  cnpj_fornecedor TEXT,
  status_fornecedor TEXT,

  -- Financiador
  razao_social_financiador TEXT,
  cnpj_financiador TEXT,
  parceiro TEXT,

  -- Valores e Taxas
  valor_bruto_duplicata NUMERIC(15,2),
  valor_liquido_duplicata NUMERIC(15,2),
  desconto_contrato NUMERIC(15,2),
  abatimento NUMERIC(15,2),
  desagio_reais NUMERIC(15,2),
  tarifa_reais NUMERIC(15,2),
  ad_valorem_reais NUMERIC(15,2),
  iof_reais NUMERIC(15,2),
  total_taxas_reais NUMERIC(15,2),
  liquido_operacao NUMERIC(15,2),

  -- Taxas Percentuais
  taxa_mes_percentual NUMERIC(8,4),
  ad_valorem_percentual NUMERIC(8,4),
  taxa_efetiva_mes_percentual NUMERIC(8,4),
  faixa_taxa_cashforce TEXT,

  -- Pagamento
  forma_pagamento TEXT,
  vencimento DATE,
  data_pagamento DATE,
  status_pagamento TEXT,
  data_pagamento_operacao DATE,
  data_confirmacao_pagamento_operacao DATE,

  -- Antecipação
  status_antecipacao TEXT,

  -- Prazos
  prazo INTEGER,
  prazo_medio_operacao INTEGER,

  -- Receita
  receita_cashforce NUMERIC(15,2),

  -- Anexos
  termo_anexado BOOLEAN,
  boleto_anexado BOOLEAN,
  comprovante_deposito BOOLEAN,

  -- Controle
  dia_atual DATE,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_propostas_nfid ON propostas(nfid);
CREATE INDEX idx_propostas_numero_proposta ON propostas(numero_proposta);
CREATE INDEX idx_propostas_cnpj_comprador ON propostas(cnpj_comprador);
CREATE INDEX idx_propostas_data_operacao ON propostas(data_operacao);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_propostas_updated_at BEFORE UPDATE
    ON propostas FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

4. Clique em **"Run"** (ou `Ctrl+Enter`)

### 3.3 Copiar Credenciais

1. Vá em **"Settings"** → **"API"**
2. Copie:
   - **Project URL**: `https://xxx.supabase.co` → `SUPABASE_URL`
   - **service_role key** (em "Project API keys") → `SUPABASE_KEY`

⚠️ **Importante**: Use `service_role` key, não a `anon` key (o ETL precisa de permissões completas)

---

## 4. Vercel

### 4.1 Instalar CLI

```bash
npm install -g vercel
```

### 4.2 Login

```bash
vercel login
```

### 4.3 Deploy Inicial

```bash
cd /caminho/para/BI-Cashforce
vercel --prod
```

Responda:
- **Set up and deploy**: `Y`
- **Which scope**: Escolha sua conta
- **Link to existing project**: `N`
- **Project name**: `bi-cashforce` (ou outro)
- **Directory**: `.` (Enter)
- **Override settings**: `N`

### 4.4 Configurar Variáveis de Ambiente

#### Opção 1: Via CLI

```bash
# Google Sheets Credentials (cole o conteúdo completo do JSON)
vercel env add GOOGLE_SHEETS_CREDENTIALS_JSON
# Cole o JSON completo quando solicitado, depois Enter

# Nome da planilha
vercel env add GOOGLE_SHEET_NAME
# Digite: Operações

# Supabase URL
vercel env add SUPABASE_URL
# Digite: https://xxx.supabase.co

# Supabase Key
vercel env add SUPABASE_KEY
# Digite: eyJhbG...
```

Para cada variável:
1. Selecione ambiente: **Production** (pressione Espaço, depois Enter)
2. Confirme com Enter

#### Opção 2: Via Dashboard

1. Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
2. Selecione o projeto `bi-cashforce`
3. Vá em **"Settings"** → **"Environment Variables"**
4. Adicione cada variável:
   - Key: Nome da variável
   - Value: Valor
   - Environment: Marque **Production**
   - Clique em **"Save"**

### 4.5 Redeploy

Após configurar as variáveis:

```bash
vercel --prod
```

### 4.6 Verificar Cron Job

1. No dashboard, vá em **"Cron Jobs"**
2. Você deve ver: `/api/_cron/etl_sync` com schedule `0 * * * *`
3. Status deve estar **Active**

⚠️ **Nota**: Cron Jobs requerem plano **Pro** ou superior da Vercel

---

## 5. Teste Local

### 5.1 Configurar Ambiente Local

```bash
# Clonar repositório (se aplicável)
git clone <url-do-repo>
cd BI-Cashforce

# Criar .env
cp .env.example .env
```

### 5.2 Editar .env

Abra `.env` e preencha:

```env
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
GOOGLE_SHEET_NAME=Operações
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbG...
```

### 5.3 Instalar Dependências

```bash
pip install -r requirements.txt
```

### 5.4 Teste Manual (Opcional)

Crie um arquivo `test_local.py`:

```python
import os
from dotenv import load_dotenv
load_dotenv()

# Importar e executar a lógica do ETL
# (adaptar conforme necessário)
```

Execute:
```bash
python test_local.py
```

### 5.5 Teste com Vercel Dev

```bash
vercel dev
```

Acesse: `http://localhost:3000/api/_cron/etl_sync`

---

## ✅ Checklist Final

Antes de considerar o setup completo:

- [ ] Service Account criada no Google Cloud
- [ ] Google Sheets API habilitada
- [ ] Planilha compartilhada com Service Account
- [ ] Tabela `propostas` criada no Supabase
- [ ] Índices criados no Supabase
- [ ] Projeto deployado na Vercel
- [ ] 4 variáveis de ambiente configuradas na Vercel
- [ ] Cron Job ativo no dashboard da Vercel
- [ ] Teste manual executado com sucesso

---

## 🆘 Problemas Comuns

### "Permission denied" ao acessar planilha

**Solução**: Verificar se compartilhou a planilha com o email correto da Service Account

### "Cannot find module 'gspread'"

**Solução**: Executar `pip install -r requirements.txt`

### Cron Job não aparece no dashboard

**Solução**:
1. Verificar se `vercel.json` está commitado
2. Fazer redeploy: `vercel --prod`
3. Verificar plano da Vercel (Pro necessário)

### "Invalid credentials" no Supabase

**Solução**: Usar `service_role` key, não `anon` key

---

## 📚 Próximos Passos

Após o setup completo:

1. Monitorar primeira execução do Cron (hora cheia)
2. Verificar logs: `vercel logs --follow`
3. Consultar dados no Supabase: `SELECT * FROM propostas LIMIT 10;`
4. Configurar alertas (opcional)
5. Criar dashboard de BI (Power BI, Looker, etc.)

---

**Setup concluído!** 🎉

Para dúvidas, consulte [README.md](./README.md) ou [DATABASE.md](./DATABASE.md).
