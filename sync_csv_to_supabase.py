#!/usr/bin/env python3
"""
Script local para sincronizar CSV com Supabase
Carrega o arquivo Operações - Relatório_preparado.csv para a tabela propostas
"""

import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Conectar ao Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("🔄 Iniciando sincronização do CSV com Supabase...")
print(f"📊 Conectando ao Supabase...")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ler o CSV
print("📁 Lendo CSV...")
df = pd.read_csv('planilhas/Operações - Relatório_preparado.csv', low_memory=False)

print(f"✅ CSV carregado: {len(df):,} registros")

# Verificar parceiros únicos
parceiros = df['parceiro'].dropna().unique()
print(f"📦 Parceiros encontrados: {len(parceiros)}")
for p in sorted(parceiros):
    count = len(df[df['parceiro'] == p])
    print(f"   - {p}: {count:,} registros")

# Substituir NaN por None (compatível com JSON/PostgreSQL)
print("\n🔄 Preparando dados para upload...")
df = df.replace({pd.NA: None, pd.NaT: None})
df = df.where(pd.notnull(df), None)

# Converter DataFrame para lista de dicionários
records = df.to_dict('records')

# Inserir em lotes de 1000
BATCH_SIZE = 1000
total_inserted = 0
total_errors = 0

print(f"\n📤 Inserindo dados em lotes de {BATCH_SIZE}...")

for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE

    try:
        # UPSERT usando NFID como chave única
        result = supabase.table('propostas').upsert(
            batch,
            on_conflict='nfid',
            count='exact'
        ).execute()

        total_inserted += len(batch)
        print(f"   ✅ Lote {batch_num}/{total_batches}: {len(batch)} registros inseridos (Total: {total_inserted:,})")

    except Exception as e:
        total_errors += len(batch)
        print(f"   ❌ Erro no lote {batch_num}: {str(e)[:100]}")

print(f"\n{'='*60}")
print(f"✅ Sincronização concluída!")
print(f"📊 Total processado: {total_inserted:,} registros")
print(f"❌ Erros: {total_errors:,} registros")
print(f"{'='*60}")

# Verificar parceiros no Supabase
print("\n🔍 Verificando parceiros no Supabase...")
response = supabase.table('propostas').select('parceiro').execute()
df_supabase = pd.DataFrame(response.data)
parceiros_supabase = df_supabase['parceiro'].dropna().unique()

print(f"📦 Parceiros no Supabase: {len(parceiros_supabase)}")
for p in sorted(parceiros_supabase):
    count = len(df_supabase[df_supabase['parceiro'] == p])
    print(f"   - {p}: {count:,} registros")

print("\n✅ Script finalizado!")
