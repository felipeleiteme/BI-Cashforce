#!/usr/bin/env bash
# Smoke tests for Supabase REST endpoints used by the GPT assistant.
# Usage:
#   export SUPABASE_URL="https://....supabase.co"
#   export SUPABASE_ANON_KEY="..."
#   ./scripts/test_supabase_api.sh 2025-10 "MARFRIG"
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Uso: $0 <competencia YYYY-MM> <filtro grupo (ex.: MARFRIG)>" >&2
  exit 1
fi

: "${SUPABASE_URL:?Defina SUPABASE_URL}"
: "${SUPABASE_ANON_KEY:?Defina SUPABASE_ANON_KEY}"

competencia="$1"
grupo_filter="$2"
base_headers=(
  -H "apikey: ${SUPABASE_ANON_KEY}"
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}"
  -H "Accept: application/json"
)

echo "==> Testando consolidados (getResumoMensal)"
curl -sS "${SUPABASE_URL}/rest/v1/propostas_resumo_mensal?competencia_id=eq.${competencia}&grupo_economico=ilike.*${grupo_filter}*&limit=5" \
  "${base_headers[@]}" | jq .

echo
echo "==> Testando detalhes (getPropostas com paginação)"
curl -sS "${SUPABASE_URL}/rest/v1/propostas?grupo_economico=ilike.*${grupo_filter}*&data_operacao=gte.${competencia}-01&limit=5&order=data_operacao.desc" \
  "${base_headers[@]}" | jq .

echo
echo "==> Testando página 2 (offset)"
curl -sS "${SUPABASE_URL}/rest/v1/propostas?grupo_economico=ilike.*${grupo_filter}*&data_operacao=gte.${competencia}-01&limit=5&offset=5&order=data_operacao.desc" \
  "${base_headers[@]}" | jq .
