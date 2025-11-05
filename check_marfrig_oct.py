#!/usr/bin/env python3
from supabase import create_client
import pandas as pd

SUPABASE_URL = "https://ximsykesrzxgknonmxws.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjI2NDUxNiwiZXhwIjoyMDc3ODQwNTE2fQ.Jt5ijc9SqbJtWbnA_PhHvMwkfaiW6oI2CKt98Fl4Evs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Buscar TODOS os dados com paginação
print("Buscando todos os dados do Supabase...")
all_data = []
page_size = 1000
offset = 0

while True:
    response = supabase.table("propostas").select("*").range(offset, offset + page_size - 1).execute()
    if not response.data:
        break
    all_data.extend(response.data)
    if len(response.data) < page_size:
        break
    offset += page_size

df = pd.DataFrame(all_data)
print(f"Total de registros carregados: {len(df):,}")

# Processar datas
df['data_operacao'] = pd.to_datetime(df['data_operacao'], errors='coerce')
df['ano_mes'] = df['data_operacao'].dt.to_period('M')

# Filtrar outubro 2025
df_out_2025 = df[df['ano_mes'] == '2025-10']
print(f"\nTotal em outubro/2025: {len(df_out_2025):,} registros")

# Verificar Grupo Marfrig
if 'grupo_economico' in df.columns:
    marfrig = df_out_2025[df_out_2025['grupo_economico'].str.contains('MARFRIG', case=False, na=False)]
    print(f"\nGrupo Marfrig em outubro/2025: {len(marfrig):,} registros")

    if len(marfrig) > 0:
        # Valores consolidados
        colunas_valor = ['valor_bruto_duplicata', 'valor_liquido_duplicata', 'receita_cashforce',
                        'liquido_operacao', 'total_taxas_reais']

        print("\n=== CONSOLIDADO GRUPO MARFRIG - OUTUBRO/2025 ===")
        for col in colunas_valor:
            if col in marfrig.columns:
                total = pd.to_numeric(marfrig[col], errors='coerce').sum()
                print(f"{col}: R$ {total:,.2f}")

        # Detalhes
        print(f"\nParceiros Marfrig:")
        if 'parceiro' in marfrig.columns:
            print(marfrig['parceiro'].value_counts())
    else:
        print("\nNenhum registro do Grupo Marfrig encontrado em outubro/2025")
        print("\nGrupos econômicos em outubro/2025:")
        if 'grupo_economico' in df_out_2025.columns:
            print(df_out_2025['grupo_economico'].value_counts().head(10))
