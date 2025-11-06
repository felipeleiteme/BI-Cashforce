import os
import json
import gspread
import pandas as pd
from gspread.exceptions import WorksheetNotFound
from supabase import create_client, Client
from http.server import BaseHTTPRequestHandler
from datetime import datetime


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
            # Cabeçalho está na linha 4, então pular as 3 primeiras linhas
            records = worksheet.get_all_records(head=4)

            if not records:
                raise ValueError("Nenhum registro encontrado na planilha")

            # Passo 3: Transformar com Pandas
            df = pd.DataFrame(records)

            if df.empty:
                raise ValueError("DataFrame está vazio após conversão")

            # Ordenar por data de operação (mais recente primeiro)
            if 'Data da operação' in df.columns:
                df['Data da operação'] = pd.to_datetime(df['Data da operação'], errors='coerce')
                df = df.sort_values('Data da operação', ascending=False)

            # Passo 4: Limpeza e Mapeamento
            column_mapping = {
                # Informações da Proposta
                "Numero da Proposta": "numero_proposta",
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
                "Liquido da Operação": "liquido_operacao",  # Sem acento!

                # Taxas Percentuais
                "Taxa ao mês %": "taxa_mes_percentual",
                "Ad Valorem &": "ad_valorem_percentual",  # Atenção: & não %
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

            # --- NOVO BLOCO DE SANITIZAÇÃO DE TEXTO ---
            # Padroniza colunas de texto para evitar inconsistências
            # Converte "pendente ", "PENDENTE", "Pendente" -> "Pendente"
            print("[INFO] Sanitizando colunas de texto (status, parceiro, etc.)...")
            text_columns_to_sanitize = [
                'status_proposta',
                'grupo_economico',
                'razao_social_comprador',
                'status_comprador',
                'tipo_nota',
                'razao_social_fornecedor',
                'status_fornecedor',
                'razao_social_financiador',
                'parceiro',
                'faixa_taxa_cashforce',
                'forma_pagamento',
                'status_pagamento',
                'status_antecipacao'
            ]

            for col in text_columns_to_sanitize:
                if col in df.columns:
                    # Garante que é string antes de aplicar métodos .str
                    df[col] = df[col].astype(str).str.strip().str.title()
                    # Substitui strings vazias ou 'None' (que virou "None") por valor Nulo real
                    df[col] = df[col].replace({'': None, 'None': None, 'Nan': None})

            # --- FIM DO NOVO BLOCO ---

            # Remover linhas onde nfid está vazio (obrigatório)
            df = df[df['nfid'].notna() & (df['nfid'] != '')]

            if df.empty:
                raise ValueError("Nenhum registro válido encontrado (NFID obrigatório)")

            # Remover duplicatas por NFID (manter o mais recente)
            df = df.drop_duplicates(subset=['nfid'], keep='first')

            # Substituir valores vazios por None para campos numéricos e booleanos
            df = df.replace('', None)
            df = df.replace('nan', None)
            df = df.replace('NaN', None)
            df = df.replace('---', None)

            # Substituir NaN do pandas por None
            df = df.where(pd.notna(df), None)

            # Converter campos monetários (remover R$ e converter para número)
            def clean_currency(value):
                if pd.isna(value) or value == '' or value == '---':
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    value = value.replace('R$', '').strip()
                    value = value.replace(' ', '')
                    # Se houver vírgula, assumimos formato brasileiro (1.234,56)
                    if ',' in value:
                        value = value.replace('.', '').replace(',', '.')
                    try:
                        return float(value)
                    except:
                        return None
                return None

            money_columns = ['valor_bruto_duplicata', 'valor_liquido_duplicata', 'desconto_contrato',
                           'abatimento', 'desagio_reais', 'tarifa_reais', 'ad_valorem_reais',
                           'iof_reais', 'total_taxas_reais', 'liquido_operacao', 'receita_cashforce']

            for col in money_columns:
                if col in df.columns:
                    df[col] = df[col].apply(clean_currency)

            # Converter campos percentuais (remover % e converter para número)
            def clean_percentage(value):
                if pd.isna(value) or value == '' or value == '---':
                    return None
                if isinstance(value, str):
                    value = value.replace('%', '').replace(' ', '').replace(',', '.')
                    try:
                        return float(value)
                    except:
                        return None
                return value

            percentage_columns = ['taxa_mes_percentual', 'ad_valorem_percentual', 'taxa_efetiva_mes_percentual']

            for col in percentage_columns:
                if col in df.columns:
                    df[col] = df[col].apply(clean_percentage)

            # Converter campos de data para string (formato ISO)
            date_columns = ['data_operacao', 'data_aceite_proposta', 'data_inclusao_nf',
                           'data_emissao_nf', 'vencimento', 'data_pagamento',
                           'data_pagamento_operacao', 'data_confirmacao_pagamento_operacao', 'dia_atual']

            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df[col] = df[col].dt.strftime('%Y-%m-%d').replace('NaT', None)

            # Converter campos booleanos
            def clean_boolean(value):
                if pd.isna(value) or value == '' or value == '---':
                    return None
                if isinstance(value, str):
                    return value.lower() in ['sim', 'yes', 'true', '1']
                return bool(value)

            boolean_columns = ['termo_anexado', 'boleto_anexado', 'comprovante_deposito']

            for col in boolean_columns:
                if col in df.columns:
                    df[col] = df[col].apply(clean_boolean)

            # Converter campos inteiros (arredondar)
            def clean_integer(value):
                if pd.isna(value) or value == '' or value == '---':
                    return None
                try:
                    return int(round(float(value)))
                except:
                    return None

            integer_columns = ['prazo', 'prazo_medio_operacao']

            for col in integer_columns:
                if col in df.columns:
                    df[col] = df[col].apply(clean_integer)

            # Converter DataFrame para lista de dicionários e limpar valores inválidos
            data_to_upsert = []
            for record in df.to_dict('records'):
                clean_record = {}
                for key, value in record.items():
                    # Limpar valores inválidos
                    if value in ['NaN', 'nan', 'None', '---', '']:
                        clean_record[key] = None
                    elif isinstance(value, float) and pd.isna(value):
                        clean_record[key] = None
                    else:
                        clean_record[key] = value
                data_to_upsert.append(clean_record)

            # Passo 5: Autenticar no Supabase
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados")

            supabase: Client = create_client(supabase_url, supabase_key)

            # Passo 6: Fazer o UPSERT em lotes para evitar timeouts
            total_rows = len(data_to_upsert)
            batch_size = 5000

            print(f"[INFO] Iniciando UPSERT de {total_rows} registros em lotes de {batch_size}...")

            for start in range(0, total_rows, batch_size):
                end = start + batch_size
                batch = data_to_upsert[start:end]
                print(f"[INFO] Processando lote {start // batch_size + 1} ({len(batch)} registros)...")
                supabase.table('propostas').upsert(
                    batch,
                    on_conflict='nfid'
                ).execute()

            print("[INFO] UPSERT em lotes concluído.")

            # --- INÍCIO DA MELHORIA: BUSCAR KPI DE RITMO ---
            print("[INFO] Buscando KPIs de Ritmo do Google Sheets...")
            try:
                def get_worksheet_safe(sheet, title):
                    try:
                        return sheet.worksheet(title)
                    except WorksheetNotFound:
                        for ws in sheet.worksheets():
                            if ws.title.strip().lower() == title.strip().lower():
                                return ws
                        raise

                worksheet_ritmo = get_worksheet_safe(spreadsheet, "Ritmo")
                worksheet_dias = get_worksheet_safe(spreadsheet, "Dias para o fim do mês")

                ritmo_bruto_str = worksheet_ritmo.acell('B2').value or ""
                dias_restantes_str = worksheet_dias.acell('A2').value or ""

                ritmo_projetado = clean_currency(ritmo_bruto_str)
                dias_restantes = clean_integer(dias_restantes_str)
                dias_restantes_text = str(dias_restantes) if dias_restantes is not None else "N/A"

                payload = {
                    'id': 1,
                    'updated_at': datetime.utcnow().isoformat()
                }
                if ritmo_projetado is not None:
                    payload['ritmo_projetado'] = ritmo_projetado
                if dias_restantes_text:
                    payload['dias_restantes_mes'] = dias_restantes_text

                supabase.table('kpis_atuais').upsert(payload).execute()
                print(f"[INFO] KPIs de Ritmo atualizados: R$ {ritmo_projetado or 0}, Dias {dias_restantes_text}")

            except Exception as kpi_error:
                print(f"[WARN] Falha ao buscar KPIs de Ritmo: {kpi_error}")
            # --- FIM DA MELHORIA ---

            # Passo 6.1: Atualizar agregados (materialized view)
            try:
                supabase.rpc('refresh_propostas_resumo_mensal').execute()
            except Exception as refresh_error:
                # Não interromper o fluxo principal se a atualização falhar,
                # mas registrar para inspeção nos logs da função.
                print(f"[WARN] Falha ao atualizar resumo mensal: {refresh_error}")

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
