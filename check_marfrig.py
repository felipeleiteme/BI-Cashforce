#!/usr/bin/env python3
from supabase import create_client
import os
import pandas as pd

SUPABASE_URL = "https://ximsykesrzxgknonmxws.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjI2NDUxNiwiZXhwIjoyMDc3ODQwNTE2fQ.Jt5ijc9SqbJtWbnA_PhHvMwkfaiW6oI2CKt98Fl4Evs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Consultar dados
response = supabase.table('propostas').select('*').execute()
df = pd.DataFrame(response.data)

print(f"Total de registros no banco: {len(df)}")
print(f"\nColunas disponíveis: {list(df.columns)[:10]}...")

# Verificar se existe coluna de cliente/grupo
if 'cliente' in df.columns:
    print(f"\nClientes únicos: {df['cliente'].nunique()}")
    marfrig = df[df['cliente'].str.contains('MARFRIG', case=False, na=False)]
    print(f"\nRegistros com 'MARFRIG': {len(marfrig)}")
    if len(marfrig) > 0:
        print(f"Clientes Marfrig: {marfrig['cliente'].unique()}")

# Verificar coluna de data
if 'data_operacao' in df.columns:
    df['data_operacao'] = pd.to_datetime(df['data_operacao'], errors='coerce')
    df['ano_mes'] = df['data_operacao'].dt.to_period('M')

    print(f"\nPeríodos disponíveis (top 10):")
    print(df['ano_mes'].value_counts().sort_index().tail(10))

    # Outubro 2025
    out_2025 = df[df['ano_mes'] == '2025-10']
    print(f"\nTotal de registros em outubro/2025: {len(out_2025)}")

    if 'cliente' in df.columns and len(out_2025) > 0:
        marfrig_out = out_2025[out_2025['cliente'].str.contains('MARFRIG', case=False, na=False)]
        print(f"Registros Marfrig em outubro/2025: {len(marfrig_out)}")

        if len(marfrig_out) > 0:
            # Totais
            if 'valor_operacao' in marfrig_out.columns:
                total_valor = marfrig_out['valor_operacao'].sum()
                print(f"\nTotal valor operação: R$ {total_valor:,.2f}")

            if 'valor_liquido' in marfrig_out.columns:
                total_liquido = marfrig_out['valor_liquido'].sum()
                print(f"Total valor líquido: R$ {total_liquido:,.2f}")
        else:
            print("\nNenhum registro Marfrig encontrado em outubro/2025")
            print("\nTodos clientes em outubro/2025:")
            if 'cliente' in out_2025.columns:
                print(out_2025['cliente'].value_counts())
