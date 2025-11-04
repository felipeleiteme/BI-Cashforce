# BI-Cashforce - Pipeline ETL

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/felipeleiteme/BI-Cashforce)

Pipeline automatizado de ETL (Extração, Transformação e Carga) que sincroniza dados de operações financeiras do Google Sheets para o Supabase.

## 🚀 Início Rápido

```bash
# 1. Clone o repositório
git clone https://github.com/felipeleiteme/BI-Cashforce.git
cd BI-Cashforce

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Deploy na Vercel
vercel --prod
```

## 📋 Visão Geral

Este projeto implementa um pipeline serverless que:

- 📊 **Extrai** dados da planilha "Operações" no Google Sheets (59 colunas)
- 🔄 **Transforma** os dados (limpa, normaliza e mapeia colunas)
- 💾 **Carrega** no banco de dados Supabase (PostgreSQL)
- ⏰ **Executa automaticamente** a cada hora via Vercel Cron Job

## 🏗️ Arquitetura

```
Google Sheets → Vercel Cron → Python ETL → Supabase
```

### Stack Tecnológica

- **Runtime**: Python 3.9 (Vercel Serverless Functions)
- **Agendador**: Vercel Cron Jobs (horário)
- **Fonte**: Google Sheets API
- **Destino**: Supabase (PostgreSQL)
- **Libs**: gspread, pandas, supabase-py

## 📁 Estrutura do Projeto

```
BI-Cashforce/
├── api/
│   └── _cron/
│       └── etl_sync.py          # Função serverless do ETL
├── docs/
│   ├── README.md                # Documentação completa
│   ├── SETUP.md                 # Guia de configuração detalhado
│   └── DATABASE.md              # Schema e queries SQL
├── .env.example                 # Template de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados
├── vercel.json                  # Configuração Vercel + Cron
└── requirements.txt             # Dependências Python
```

## ⚙️ Configuração

### Pré-requisitos

- Conta [Google Cloud Platform](https://console.cloud.google.com)
- Conta [Supabase](https://supabase.com)
- Conta [Vercel](https://vercel.com) (Plano Pro para Cron Jobs)
- [Vercel CLI](https://vercel.com/cli) instalada

### Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | JSON da Service Account do Google Cloud |
| `GOOGLE_SHEET_NAME` | Nome da planilha (ex: "Operações") |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Service role key do Supabase |

### Setup Rápido

1. **Google Cloud**: Crie Service Account e habilite Google Sheets API
2. **Google Sheets**: Compartilhe planilha com email da Service Account
3. **Supabase**: Crie tabela `propostas` (veja `docs/DATABASE.md`)
4. **Vercel**: Configure variáveis de ambiente e faça deploy

📚 **Guia completo**: [docs/SETUP.md](./docs/SETUP.md)

## 🚀 Deploy

### Via Vercel CLI

```bash
# Login
vercel login

# Deploy
vercel --prod

# Configurar variáveis
vercel env add GOOGLE_SHEETS_CREDENTIALS_JSON
vercel env add GOOGLE_SHEET_NAME
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Redeploy
vercel --prod
```

### Via GitHub (Recomendado)

1. Conecte o repositório ao Vercel
2. Configure as variáveis de ambiente no dashboard
3. Deploy automático a cada push

## 📊 Mapeamento de Dados

O ETL mapeia **59 colunas** da planilha para o banco:

- **Proposta**: número, status, datas
- **Comprador**: razão social, CNPJ, grupo econômico
- **Nota Fiscal**: NFID (chave única), número, tipo
- **Fornecedor**: razão social, CNPJ
- **Financiador**: razão social, CNPJ, parceiro
- **Valores**: bruto, líquido, taxas, deságio, IOF
- **Pagamento**: forma, vencimento, status
- **Anexos**: termo, boleto, comprovante

Ver detalhes completos: [docs/DATABASE.md](./docs/DATABASE.md)

## ⏰ Agendamento

O Cron Job executa **a cada hora** (XX:00):

```json
{
  "schedule": "0 * * * *"
}
```

Para alterar a frequência, edite `vercel.json`:

- `*/30 * * * *` - A cada 30 minutos
- `0 */6 * * *` - A cada 6 horas
- `0 9 * * *` - Todo dia às 09:00

## 🔍 Monitoramento

### Logs

```bash
# Ver logs em tempo real
vercel logs --follow

# Logs da função ETL
vercel logs api/_cron/etl_sync.py
```

### Resposta da API

**Sucesso (200)**:
```json
{
  "status": "success",
  "rows_processed": 150
}
```

**Erro (500)**:
```json
{
  "status": "error",
  "message": "Descrição do erro"
}
```

## 🛠️ Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env

# Testar localmente com Vercel Dev
vercel dev

# Acessar: http://localhost:3000/api/_cron/etl_sync
```

## 🐛 Troubleshooting

### Erro: "Unable to open file"

**Solução**: Verificar se a planilha foi compartilhada com o email da Service Account

### Erro: "GOOGLE_SHEETS_CREDENTIALS_JSON não configurado"

**Solução**: Configurar variável de ambiente na Vercel

### Cron Job não executa

**Verificar**:
- Plano Pro/Enterprise da Vercel (Cron Jobs são pagos)
- `vercel.json` está commitado corretamente
- Status do Cron Job no dashboard da Vercel

📚 **Mais soluções**: [docs/README.md#troubleshooting](./docs/README.md#troubleshooting)

## 📚 Documentação Completa

- [📖 README Completo](./docs/README.md) - Arquitetura, funcionamento e troubleshooting
- [⚙️ Guia de Setup](./docs/SETUP.md) - Configuração passo a passo
- [💾 Schema do Banco](./docs/DATABASE.md) - Estrutura completa e queries úteis

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Changelog

### v1.0.0 (2025-11-04)

- ✅ Pipeline ETL inicial
- ✅ Mapeamento de 59 colunas
- ✅ Cron Job horário
- ✅ UPSERT com conflito por NFID
- ✅ Documentação completa

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📧 Contato

Felipe Leite - [@felipeleiteme](https://github.com/felipeleiteme)

Link do Projeto: [https://github.com/felipeleiteme/BI-Cashforce](https://github.com/felipeleiteme/BI-Cashforce)

---

**Desenvolvido com ❤️ usando [Claude Code](https://claude.com/claude-code)**
