import os
import json
import gspread
import pandas as pd
from supabase import create_client, Client
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Passo 1: Autenticar no Google Sheets
            credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_JSON')
            if not credentials_json:
                raise ValueError("GOOGLE_SHEETS_CREDENTIALS_JSON não configurado")

            credentials_dict = json.loads(credentials_json)
            gc = gspread.service_account_from_dict(credentials_dict)

            # Passo 2: Ler a Planilha
            sheet_name = os.environ.get('GOOGLE_SHEET_NAME')
            if not sheet_name:
                raise ValueError("GOOGLE_SHEET_NAME não configurado")

            spreadsheet = gc.open(sheet_name)
            worksheet = spreadsheet.get_worksheet(0)
            records = worksheet.get_all_records()

            # Passo 3: Transformar com Pandas
            df = pd.DataFrame(records)

            # Passo 4: Limpeza e Mapeamento
            column_mapping = {
                # Informações da Proposta
                "Número da Proposta": "numero_proposta",
                "Status da Proposta": "status_proposta",
                "Data da operação": "data_operacao",
                "Data do Aceite da Proposta": "data_aceite_proposta",

                # Grupo Econômico e Comprador
                "Grupo Econômico": "grupo_economico",
                "Razão Social Comprador": "razao_social_comprador",
                "CNPJ do Comprador": "cnpj_comprador",
                "Status comprador": "status_comprador",

                # Nota Fiscal e Duplicata
                "NFID": "nfid",
                "Nº da Nota Fiscal": "numero_nota_fiscal",
                "Tipo da nota": "tipo_nota",
                "Nº da Duplicata": "numero_duplicata",
                "Data de Inclusão da NF": "data_inclusao_nf",
                "Data de Emissão da NF": "data_emissao_nf",
                "Descrição": "descricao",

                # Fornecedor
                "Razão Social do Fornecedor": "razao_social_fornecedor",
                "CNPJ do Fornecedor": "cnpj_fornecedor",
                "Status fornecedor": "status_fornecedor",

                # Financiador
                "Razão Social do Financiador": "razao_social_financiador",
                "CNPJ Financiador": "cnpj_financiador",
                "Parceiro": "parceiro",

                # Valores e Taxas
                "Valor Bruto da Duplicata": "valor_bruto_duplicata",
                "Valor Líquido da Duplicata": "valor_liquido_duplicata",
                "Desconto contrato": "desconto_contrato",
                "Abatimento": "abatimento",
                "Deságio R$": "desagio_reais",
                "Tarifa R$": "tarifa_reais",
                "Ad Valorem R$": "ad_valorem_reais",
                "IOF R$": "iof_reais",
                "Total de taxas R$": "total_taxas_reais",
                "Líquido da Operação": "liquido_operacao",

                # Taxas Percentuais
                "Taxa ao mês %": "taxa_mes_percentual",
                "Ad Valorem %": "ad_valorem_percentual",
                "Taxa efetiva ao mês %": "taxa_efetiva_mes_percentual",
                "Faixa de Taxa Cashforce": "faixa_taxa_cashforce",

                # Pagamento
                "Forma de pagamento": "forma_pagamento",
                "Vencimento": "vencimento",
                "Data de pagamento": "data_pagamento",
                "Status de Pagamento": "status_pagamento",
                "Data do Pagamento da Operação": "data_pagamento_operacao",
                "Data da Confirmação do Pagamento da Operação": "data_confirmacao_pagamento_operacao",

                # Antecipação
                "Status da Antecipação": "status_antecipacao",

                # Prazos
                "Prazo": "prazo",
                "Prazo Médio da operação": "prazo_medio_operacao",

                # Receita
                "Receita Cashforce": "receita_cashforce",

                # Anexos
                "Termo anexado?": "termo_anexado",
                "Boleto anexado?": "boleto_anexado",
                "Comprovante de depósito?": "comprovante_deposito",

                # Controle
                "Dia atual": "dia_atual"
            }

            df = df.rename(columns=column_mapping)
            data_to_upsert = df.to_dict('records')

            # Passo 5: Autenticar no Supabase
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

            supabase: Client = create_client(supabase_url, supabase_key)

            # Passo 6: Fazer o UPSERT
            response = supabase.table('propostas').upsert(
                data_to_upsert,
                on_conflict='nfid'
            ).execute()

            # Passo 7: Responder ao Cron
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            response_data = {
                "status": "success",
                "rows_processed": len(data_to_upsert)
            }
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            # Passo 8: Tratamento de Erros
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
