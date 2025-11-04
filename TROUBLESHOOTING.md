# 🔧 Troubleshooting - BI-Cashforce ETL

## Problema: Timeout na função ETL

### Sintomas:
- Requisição HTTP demora mais de 60 segundos
- Banco de dados permanece vazio
- Sem mensagem de erro clara

### Causas Possíveis:

#### 1. Limite de Timeout da Vercel (Plano Hobby)
- **Plano Hobby**: 10 segundos máximo
- **Plano Pro**: 60 segundos
- **Solução**: Upgrade para Pro ou otimizar processamento

#### 2. Muitos Dados na Planilha
- Grande volume de linhas causa processamento lento
- **Solução**: Processar em lotes

#### 3. Conexão Lenta com Google Sheets
- API do Google pode estar lenta
- **Solução**: Implementar timeout e retry

---

## Soluções Rápidas

### Solução 1: Verificar Dados da Planilha

1. Abra a planilha "Operações"
2. Verifique:
   - Quantas linhas de dados existem? (sem contar cabeçalho)
   - O cabeçalho está mesmo na linha 4?
   - Existe a coluna "NFID" preenchida?

### Solução 2: Testar Localmente

```bash
cd "/Users/Felipe/Documents/Projetos/Integrações/BI-Cashforce"

# Criar script de teste
cat > test_local.py << 'EOF'
import os
import json
import gspread
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

print("🔧 Testando ETL localmente...")

# 1. Autenticar Google Sheets
print("\n1️⃣ Conectando ao Google Sheets...")
credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
credentials_dict = json.loads(credentials_json)
gc = gspread.service_account_from_dict(credentials_dict)

# 2. Ler Planilha
print("2️⃣ Lendo planilha...")
sheet_name = os.getenv('GOOGLE_SHEET_NAME')
spreadsheet = gc.open(sheet_name)
worksheet = spreadsheet.get_worksheet(0)

print(f"   ✓ Planilha: {spreadsheet.title}")
print(f"   ✓ Aba: {worksheet.title}")
print(f"   ✓ Total de linhas: {worksheet.row_count}")
print(f"   ✓ Total de colunas: {worksheet.col_count}")

# 3. Ler registros
print("\n3️⃣ Lendo registros (cabeçalho na linha 4)...")
records = worksheet.get_all_records(head=4)
print(f"   ✓ Registros encontrados: {len(records)}")

if records:
    print(f"   ✓ Primeiro registro: {list(records[0].keys())[:5]}...")
    df = pd.DataFrame(records)
    print(f"   ✓ DataFrame shape: {df.shape}")

    # Verificar NFID
    if 'NFID' in df.columns:
        nfid_count = df['NFID'].notna().sum()
        print(f"   ✓ Registros com NFID: {nfid_count}")
    else:
        print(f"   ⚠️  Coluna NFID não encontrada!")
        print(f"   Colunas disponíveis: {list(df.columns)[:10]}")

# 4. Testar Supabase
print("\n4️⃣ Testando conexão Supabase...")
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

# Contar registros existentes
result = supabase.table('propostas').select('id', count='exact').execute()
print(f"   ✓ Registros no banco: {result.count}")

print("\n✅ Teste concluído!")
EOF

# Executar teste
python test_local.py
```

### Solução 3: Adicionar Limite de Processamento

Editar `api/etl_sync.py` para processar apenas primeiros N registros:

```python
# Após df = pd.DataFrame(records)
# Limitar a 100 registros por execução
df = df.head(100)
```

### Solução 4: Habilitar Logs Detalhados

Acessar dashboard da Vercel:
1. https://vercel.com/felipeleites-projects-24aa8fa9/bi-cashforce
2. Clicar em "Functions"
3. Clicar em `/api/etl_sync`
4. Ver "Logs" da última execução

### Solução 5: Aumentar Timeout (Requer Plano Pro)

Em `vercel.json`:
```json
{
  "functions": {
    "api/etl_sync.py": {
      "maxDuration": 60
    }
  }
}
```

---

## Checklist de Diagnóstico

- [ ] Planilha "Operações" existe e está compartilhada?
- [ ] Cabeçalho está na linha 4?
- [ ] Coluna "NFID" existe e tem dados?
- [ ] Quantas linhas de dados? (Se > 1000, considerar lotes)
- [ ] Variáveis de ambiente configuradas na Vercel?
- [ ] Service Account tem permissão na planilha?
- [ ] Tabela `propostas` existe no Supabase?
- [ ] Service role key (não anon) está configurada?

---

## Verificações no Dashboard

### Vercel
1. **Functions**: Ver tempo de execução
2. **Logs**: Verificar erros
3. **Environment Variables**: Confirmar que estão setadas

### Supabase
```sql
-- Ver se há dados
SELECT COUNT(*) FROM propostas;

-- Ver últimos registros inseridos
SELECT * FROM propostas ORDER BY created_at DESC LIMIT 5;

-- Ver se NFID está sendo inserido
SELECT nfid FROM propostas WHERE nfid IS NOT NULL LIMIT 10;
```

### Google Sheets
1. Verificar se Service Account tem acesso
2. Email: `bi-cashforce-etl@cashforce.iam.gserviceaccount.com`
3. Permissão: Viewer ou Editor

---

## Próximos Passos

Se nada funcionar, considere:

1. **Migrar para Railway/Render** (sem limite de 10s)
2. **Upgrade Vercel Pro** ($20/mês para 60s timeout)
3. **Processar em Background** (queue system)
4. **Reduzir dados** (filtrar últimos 30 dias apenas)

---

## Contato

Issues: https://github.com/felipeleiteme/BI-Cashforce/issues
