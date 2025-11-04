import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from supabase import create_client, Client


def _parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        competencia = params.get('competencia_id', [None])[0]
        grupo = params.get('grupo', [None])[0]
        parceiro = params.get('parceiro', [None])[0]

        default_threshold = os.environ.get('ALERT_THRESHOLD_BRUTO', '10000000')
        threshold = _parse_float(params.get('threshold', [None])[0], _parse_float(default_threshold, 10000000))

        if not competencia:
            self._respond(400, {"status": "error", "message": "Parametro competencia_id é obrigatório (formato YYYY-MM)."})
            return

        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        if not supabase_url or not supabase_key:
            self._respond(500, {"status": "error", "message": "SUPABASE_URL ou SUPABASE_KEY não configurados"})
            return

        supabase: Client = create_client(supabase_url, supabase_key)

        query = supabase.table('propostas_resumo_mensal').select("*").eq('competencia_id', competencia)

        if grupo:
            query = query.ilike('grupo_economico', f'%{grupo}%')

        if parceiro:
            query = query.eq('parceiro', parceiro)

        try:
            data = query.execute().data  # type: ignore[attr-defined]
        except Exception as supabase_error:
            self._respond(500, {"status": "error", "message": f"Erro ao consultar resumo: {supabase_error}"})
            return

        total_bruto = sum(item.get('total_bruto_duplicata', 0) or 0 for item in data)
        total_liquido = sum(item.get('total_liquido_duplicata', 0) or 0 for item in data)
        quantidade_total = sum(item.get('quantidade_operacoes', 0) or 0 for item in data)

        alert_triggered = total_bruto >= threshold

        response = {
            "status": "success",
            "competencia_id": competencia,
            "grupo_filter": grupo,
            "parceiro_filter": parceiro,
            "quantidade_operacoes": quantidade_total,
            "total_bruto_duplicata": total_bruto,
            "total_liquido_duplicata": total_liquido,
            "threshold_bruto": threshold,
            "alert_triggered": alert_triggered
        }

        # Inclui os registros retornados para inspeção opcional
        response["items"] = data

        self._respond(200, response)

    def _respond(self, status_code: int, payload: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload, default=str).encode())
