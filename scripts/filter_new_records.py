#!/usr/bin/env python3
"""
Script para filtrar apenas registros novos (que não existem no Supabase).
"""

import pandas as pd
import requests
import sys

def get_existing_nfids():
    """Busca todos os NFIDs que já existem no Supabase."""

    print("🔍 Buscando NFIDs existentes no Supabase...")

    url = "https://ximsykesrzxgknonmxws.supabase.co/rest/v1/propostas"
    headers = {
        "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyNjQ1MTYsImV4cCI6MjA3Nzg0MDUxNn0.TsQuIWQofqXuHCXV9DlYWGYmtVDgrIrEZ2-YSQNvGdc",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyNjQ1MTYsImV4cCI6MjA3Nzg0MDUxNn0.TsQuIWQofqXuHCXV9DlYWGYmtVDgrIrEZ2-YSQNvGdc"
    }

    params = {
        "select": "nfid",
        "limit": 1000  # Ajustar se necessário
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        existing_nfids = set([item['nfid'] for item in data if item.get('nfid')])
        print(f"✅ Encontrados {len(existing_nfids)} NFIDs no banco")
        return existing_nfids
    else:
        print(f"❌ Erro ao buscar dados: {response.status_code}")
        return set()


def filter_new_records(input_file):
    """Filtra apenas registros que não existem no banco."""

    print(f"📂 Lendo arquivo: {input_file}")
    df = pd.read_csv(input_file)

    print(f"📊 Total de registros no CSV: {len(df)}")

    # Buscar NFIDs existentes
    existing_nfids = get_existing_nfids()

    # Filtrar apenas novos
    print(f"🧹 Filtrando registros novos...")
    df_new = df[~df['nfid'].isin(existing_nfids)]

    removed = len(df) - len(df_new)
    print(f"   ✅ Registros novos: {len(df_new)}")
    print(f"   ⏭️  Registros já existentes (ignorados): {removed}")

    # Salvar arquivo filtrado
    output_file = input_file.replace('_preparado.csv', '_novos.csv')
    df_new.to_csv(output_file, index=False)

    print(f"\n✅ CONCLUÍDO!")
    print(f"📁 Arquivo com registros novos: {output_file}")
    print(f"📊 Total de registros para importar: {len(df_new)}")

    if len(df_new) == 0:
        print(f"\n⚠️  Nenhum registro novo para importar. Todos já existem no banco!")
    else:
        print(f"\n🚀 Agora você pode importar o arquivo: {output_file}")

    return output_file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 filter_new_records.py <arquivo_preparado.csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    filter_new_records(input_file)
