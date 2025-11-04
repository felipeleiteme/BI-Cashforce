# 🚀 Guia de Deploy - BI-Cashforce

## Passo 1: Instalar Vercel CLI

Execute no terminal:

```bash
sudo npm install -g vercel
```

Digite sua senha quando solicitado.

---

## Passo 2: Login na Vercel

```bash
vercel login
```

Escolha o método de autenticação (GitHub, GitLab, Bitbucket ou Email).

---

## Passo 3: Deploy do Projeto

No diretório do projeto:

```bash
cd "/Users/Felipe/Documents/Projetos/Integrações/BI-Cashforce"
vercel --prod
```

Responda as perguntas:
- **Set up and deploy**: `Y`
- **Which scope**: Escolha sua conta
- **Link to existing project**: `N`
- **Project name**: `bi-cashforce`
- **Directory**: `.` (Enter)
- **Override settings**: `N`

---

## Passo 4: Configurar Variáveis de Ambiente

### Opção A: Via CLI (Recomendado)

```bash
cd "/Users/Felipe/Documents/Projetos/Integrações/BI-Cashforce"

# 1. Google Sheets Credentials
vercel env add GOOGLE_SHEETS_CREDENTIALS_JSON
# Cole o JSON completo quando solicitado, depois Enter
# Selecione: Production (pressione Espaço + Enter)

# 2. Nome da Planilha
vercel env add GOOGLE_SHEET_NAME
# Digite: Operações
# Selecione: Production

# 3. Supabase URL
vercel env add SUPABASE_URL
# Digite: https://ximsykesrzxgknonmxws.supabase.co
# Selecione: Production

# 4. Supabase Key (SERVICE ROLE KEY - não a anon key!)
vercel env add SUPABASE_KEY
# Cole a service_role key
# Selecione: Production
```

### Opção B: Via Dashboard da Vercel

1. Acesse https://vercel.com/dashboard
2. Selecione o projeto `bi-cashforce`
3. Vá em **Settings** → **Environment Variables**
4. Adicione cada variável:

| Key | Value | Environment |
|-----|-------|-------------|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | JSON da Service Account completo | Production |
| `GOOGLE_SHEET_NAME` | `Operações` | Production |
| `SUPABASE_URL` | `https://ximsykesrzxgknonmxws.supabase.co` | Production |
| `SUPABASE_KEY` | Service role key do Supabase | Production |

---

## Passo 5: Obter a Service Role Key do Supabase

⚠️ **IMPORTANTE**: Você precisa usar a **service_role** key, não a **anon** key!

1. Acesse https://supabase.com/dashboard/project/ximsykesrzxgknonmxws
2. Vá em **Settings** → **API**
3. Na seção **Project API keys**, copie a chave **service_role** (não a anon!)
4. Use essa chave no `SUPABASE_KEY`

**Por quê?** A `service_role` key permite operações de escrita (UPSERT), enquanto a `anon` key tem permissões limitadas.

---

## Passo 6: Configurar as Credenciais do Google Sheets

Você precisa do JSON completo da Service Account:

### Se já tem o arquivo JSON:

```bash
cat caminho/para/credentials.json
```

Copie todo o conteúdo e cole em `GOOGLE_SHEETS_CREDENTIALS_JSON`.

### Se não tem:

1. Acesse https://console.cloud.google.com
2. Vá em **APIs & Services** → **Credentials**
3. Clique na Service Account `bi-cashforce-etl@cashforce.iam.gserviceaccount.com`
4. Vá na aba **Keys**
5. Clique em **Add Key** → **Create new key**
6. Escolha **JSON**
7. Baixe o arquivo
8. Copie todo o conteúdo do JSON

---

## Passo 7: Redeploy

Após configurar as variáveis:

```bash
vercel --prod
```

Ou pelo dashboard:
1. Vá em **Deployments**
2. Clique em **Redeploy** no último deployment

---

## ✅ Verificação

### 1. Verificar se o Cron Job está ativo

1. Acesse https://vercel.com/dashboard
2. Selecione o projeto `bi-cashforce`
3. Vá em **Cron Jobs**
4. Deve aparecer: `/api/etl_sync` com schedule `0 * * * *`
5. Status: **Active** ✅

### 2. Testar a função manualmente

Acesse a URL do projeto + `/api/etl_sync`:

```
https://bi-cashforce.vercel.app/api/etl_sync
```

Deve retornar:

```json
{
  "status": "success",
  "rows_processed": 73227
}
```

### 3. Validar os consolidados mensais

Execute a consulta abaixo no Supabase SQL Editor ou via `curl`:

```sql
SELECT competencia_id, grupo_economico, quantidade_operacoes, total_bruto_duplicata
FROM propostas_resumo_mensal
ORDER BY competencia_id DESC
LIMIT 5;
```

Os totais do mês corrente devem refletir a última execução do ETL (ex.: `MARFRIG` em `2025-10` com 64 operações).

### 4. Ver os logs

```bash
vercel logs --follow
```

Ou no dashboard: **Deployments** → Clique no último → **Functions** → `/api/etl_sync.py`

---

## 🐛 Troubleshooting

### Erro: "GOOGLE_SHEETS_CREDENTIALS_JSON não configurado"

**Solução**: A variável não foi adicionada ou não está no ambiente Production.

```bash
vercel env ls
```

Deve aparecer todas as 4 variáveis no ambiente **production**.

### Erro: "Unable to open file"

**Causas**:
1. Nome da planilha está incorreto
2. Planilha não foi compartilhada com `bi-cashforce-etl@cashforce.iam.gserviceaccount.com`
3. Service Account não tem permissão

**Solução**:
1. Verifique se `GOOGLE_SHEET_NAME` está exatamente como `Operações`
2. Abra a planilha no Google Sheets
3. Clique em **Compartilhar**
4. Adicione o email: `bi-cashforce-etl@cashforce.iam.gserviceaccount.com`
5. Permissão: **Viewer** (suficiente para leitura)
6. Desmarque "Notify people"
7. Clique em **Share**

### Erro: "Invalid credentials" ou "Unauthorized" no Supabase

**Solução**: Você está usando a `anon` key ao invés da `service_role` key.

1. Acesse Supabase Dashboard
2. Settings → API
3. Copie a **service_role** key (não a anon!)
4. Atualize a variável:
   ```bash
   vercel env rm SUPABASE_KEY production
   vercel env add SUPABASE_KEY
   # Cole a service_role key
   ```
5. Redeploy: `vercel --prod`

### Cron Job não está executando

**Verificações**:

1. **Plano da Vercel**: Cron Jobs requerem plano **Pro** ou superior
   - Acesse: https://vercel.com/account/billing
   - Upgrade se necessário

2. **Configuração**: Verifique se `vercel.json` está correto
   ```bash
   cat vercel.json
   ```

3. **Status**: No dashboard, vá em **Cron Jobs** e verifique o status

### Logs mostram erro de syntax ou import

**Causa**: Dependências não foram instaladas corretamente.

**Solução**: Verifique se `requirements.txt` está na raiz do projeto:
```bash
ls requirements.txt
cat requirements.txt
```

Deve conter:
```
gspread==5.12.0
pandas==2.1.4
supabase==2.3.0
python-dotenv==1.0.0
oauth2client==4.1.3
```

---

## 📊 Monitoramento

### Ver execuções do Cron Job

```bash
vercel logs api/etl_sync.py --follow
```

### Dashboard da Vercel

1. **Deployments**: Ver histórico de deploys
2. **Functions**: Ver execuções das funções serverless
3. **Cron Jobs**: Ver histórico de execuções do Cron
4. **Logs**: Logs em tempo real

### Supabase

Verificar se os dados estão sendo inseridos:

```sql
-- Ver últimos registros
SELECT * FROM propostas ORDER BY created_at DESC LIMIT 10;

-- Contar total de registros
SELECT COUNT(*) FROM propostas;

-- Ver registros atualizados hoje
SELECT * FROM propostas WHERE updated_at::date = CURRENT_DATE;
```

---

## 🎯 Próximos Passos

Após o deploy bem-sucedido:

1. ✅ Aguardar próxima execução do Cron (próxima hora cheia)
2. ✅ Verificar logs no dashboard
3. ✅ Consultar dados no Supabase
4. ✅ Criar dashboards de BI (Power BI, Looker, etc.)

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `vercel logs --follow`
2. Consulte a documentação: `docs/README.md` e `docs/guides/setup.md`
3. Abra uma issue no GitHub

---

**Deploy concluído!** 🎉

O pipeline ETL está rodando e sincronizando sua planilha com o Supabase automaticamente a cada hora.
