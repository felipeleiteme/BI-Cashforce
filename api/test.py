import os
import json
import gspread
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Testar conexão Google Sheets
            credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_JSON')
            if not credentials_json:
                raise ValueError("GOOGLE_SHEETS_CREDENTIALS_JSON não configurado")

            credentials_dict = json.loads(credentials_json)
            gc = gspread.service_account_from_dict(credentials_dict)

            sheet_name = os.environ.get('GOOGLE_SHEET_NAME')
            if not sheet_name:
                raise ValueError("GOOGLE_SHEET_NAME não configurado")

            spreadsheet = gc.open(sheet_name)
            worksheet = spreadsheet.get_worksheet(0)

            # Informações básicas
            info = {
                "status": "success",
                "planilha": spreadsheet.title,
                "aba": worksheet.title,
                "total_linhas": worksheet.row_count,
                "total_colunas": worksheet.col_count,
            }

            # Ler registros com cabeçalho na linha 4
            records = worksheet.get_all_records(head=4)
            info["registros_encontrados"] = len(records)

            if records:
                info["primeiras_colunas"] = list(records[0].keys())[:10]
                info["primeiro_registro"] = records[0] if records else None

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(info, indent=2, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
