# Schema do Banco de Dados - BI-Cashforce

Documentação completa da estrutura da tabela `propostas` no Supabase.

## 📊 Visão Geral

- **Tabela**: `propostas`
- **Engine**: PostgreSQL (via Supabase)
- **Total de Colunas**: 63 (59 de dados + 4 de controle)
- **Chave Primária**: `id` (SERIAL)
- **Chave Única**: `nfid` (usado no UPSERT)

---

## 🏗️ Estrutura da Tabela

### Colunas de Controle

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | SERIAL PRIMARY KEY | ID auto-incremental |
| `created_at` | TIMESTAMP | Data de criação do registro |
| `updated_at` | TIMESTAMP | Data da última atualização |

---

## 📋 Colunas de Dados

### 1. Informações da Proposta

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Número da Proposta | `numero_proposta` | TEXT | Identificador único da proposta |
| Status da Proposta | `status_proposta` | TEXT | Status atual (ex: Aprovada, Pendente, Rejeitada) |
| Data da operação | `data_operacao` | DATE | Data em que a operação foi realizada |
| Data do Aceite da Proposta | `data_aceite_proposta` | DATE | Data em que a proposta foi aceita |

**Queries úteis:**
```sql
-- Propostas por status
SELECT status_proposta, COUNT(*) FROM propostas GROUP BY status_proposta;

-- Propostas do mês atual
SELECT * FROM propostas WHERE data_operacao >= DATE_TRUNC('month', CURRENT_DATE);
```

---

### 2. Grupo Econômico e Comprador

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Grupo Econômico | `grupo_economico` | TEXT | Grupo empresarial do comprador |
| Razão Social Comprador | `razao_social_comprador` | TEXT | Nome legal da empresa compradora |
| CNPJ do Comprador | `cnpj_comprador` | TEXT | CNPJ do comprador |
| Status comprador | `status_comprador` | TEXT | Status cadastral do comprador |

**Queries úteis:**
```sql
-- Top 10 grupos econômicos
SELECT grupo_economico, COUNT(*) as total_operacoes
FROM propostas
GROUP BY grupo_economico
ORDER BY total_operacoes DESC
LIMIT 10;

-- Compradores por CNPJ
SELECT cnpj_comprador, razao_social_comprador, COUNT(*) as operacoes
FROM propostas
GROUP BY cnpj_comprador, razao_social_comprador
ORDER BY operacoes DESC;
```

---

### 3. Nota Fiscal e Duplicata

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| NFID | `nfid` | TEXT UNIQUE NOT NULL | Identificador único da NF (chave de conflito) |
| Nº da Nota Fiscal | `numero_nota_fiscal` | TEXT | Número da nota fiscal |
| Tipo da nota | `tipo_nota` | TEXT | Tipo (ex: NF-e, NFS-e) |
| Nº da Duplicata | `numero_duplicata` | TEXT | Número da duplicata |
| Data de Inclusão da NF | `data_inclusao_nf` | DATE | Data em que a NF foi incluída no sistema |
| Data de Emissão da NF | `data_emissao_nf` | DATE | Data de emissão da nota fiscal |
| Descrição | `descricao` | TEXT | Descrição da operação |

**Queries úteis:**
```sql
-- Verificar duplicatas de NFID
SELECT nfid, COUNT(*) FROM propostas GROUP BY nfid HAVING COUNT(*) > 1;

-- NFs por tipo
SELECT tipo_nota, COUNT(*) FROM propostas GROUP BY tipo_nota;
```

---

### 4. Fornecedor

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Razão Social do Fornecedor | `razao_social_fornecedor` | TEXT | Nome legal do fornecedor |
| CNPJ do Fornecedor | `cnpj_fornecedor` | TEXT | CNPJ do fornecedor |
| Status fornecedor | `status_fornecedor` | TEXT | Status cadastral do fornecedor |

**Queries úteis:**
```sql
-- Top fornecedores
SELECT razao_social_fornecedor, COUNT(*) as total_nfs
FROM propostas
GROUP BY razao_social_fornecedor
ORDER BY total_nfs DESC
LIMIT 10;
```

---

### 5. Financiador

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Razão Social do Financiador | `razao_social_financiador` | TEXT | Nome legal do financiador |
| CNPJ Financiador | `cnpj_financiador` | TEXT | CNPJ do financiador |
| Parceiro | `parceiro` | TEXT | Parceiro comercial |

**Queries úteis:**
```sql
-- Volume por financiador
SELECT razao_social_financiador,
       COUNT(*) as operacoes,
       SUM(valor_bruto_duplicata) as volume_total
FROM propostas
GROUP BY razao_social_financiador;
```

---

### 6. Valores e Taxas (R$)

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Valor Bruto da Duplicata | `valor_bruto_duplicata` | NUMERIC(15,2) | Valor bruto da duplicata |
| Valor Líquido da Duplicata | `valor_liquido_duplicata` | NUMERIC(15,2) | Valor líquido após descontos |
| Desconto contrato | `desconto_contrato` | NUMERIC(15,2) | Desconto contratual |
| Abatimento | `abatimento` | NUMERIC(15,2) | Valor de abatimento |
| Deságio R$ | `desagio_reais` | NUMERIC(15,2) | Deságio em reais |
| Tarifa R$ | `tarifa_reais` | NUMERIC(15,2) | Tarifa cobrada |
| Ad Valorem R$ | `ad_valorem_reais` | NUMERIC(15,2) | Taxa ad valorem em reais |
| IOF R$ | `iof_reais` | NUMERIC(15,2) | IOF cobrado |
| Total de taxas R$ | `total_taxas_reais` | NUMERIC(15,2) | Soma de todas as taxas |
| Líquido da Operação | `liquido_operacao` | NUMERIC(15,2) | Valor líquido final da operação |

**Queries úteis:**
```sql
-- Total financiado no mês
SELECT
  DATE_TRUNC('month', data_operacao) as mes,
  SUM(valor_bruto_duplicata) as total_bruto,
  SUM(liquido_operacao) as total_liquido
FROM propostas
GROUP BY mes
ORDER BY mes DESC;

-- Média de taxas
SELECT
  AVG(desagio_reais) as media_desagio,
  AVG(tarifa_reais) as media_tarifa,
  AVG(total_taxas_reais) as media_taxas_total
FROM propostas;

-- Ticket médio
SELECT AVG(valor_bruto_duplicata) as ticket_medio FROM propostas;
```

---

### 7. Taxas Percentuais (%)

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Taxa ao mês % | `taxa_mes_percentual` | NUMERIC(8,4) | Taxa mensal em percentual |
| Ad Valorem % | `ad_valorem_percentual` | NUMERIC(8,4) | Ad valorem em percentual |
| Taxa efetiva ao mês % | `taxa_efetiva_mes_percentual` | NUMERIC(8,4) | Taxa efetiva mensal |
| Faixa de Taxa Cashforce | `faixa_taxa_cashforce` | TEXT | Faixa de classificação da taxa |

**Queries úteis:**
```sql
-- Distribuição de faixas de taxa
SELECT faixa_taxa_cashforce, COUNT(*) as operacoes
FROM propostas
GROUP BY faixa_taxa_cashforce;

-- Taxa média por grupo econômico
SELECT grupo_economico, AVG(taxa_efetiva_mes_percentual) as taxa_media
FROM propostas
GROUP BY grupo_economico
ORDER BY taxa_media DESC;
```

---

### 8. Pagamento

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Forma de pagamento | `forma_pagamento` | TEXT | Forma de pagamento (Boleto, TED, PIX, etc.) |
| Vencimento | `vencimento` | DATE | Data de vencimento |
| Data de pagamento | `data_pagamento` | DATE | Data do pagamento |
| Status de Pagamento | `status_pagamento` | TEXT | Status (Pago, Pendente, Atrasado, etc.) |
| Data do Pagamento da Operação | `data_pagamento_operacao` | DATE | Data efetiva do pagamento |
| Data da Confirmação do Pagamento da Operação | `data_confirmacao_pagamento_operacao` | DATE | Data de confirmação do pagamento |

**Queries úteis:**
```sql
-- Pagamentos em atraso
SELECT * FROM propostas
WHERE vencimento < CURRENT_DATE
  AND status_pagamento != 'Pago';

-- Taxa de adimplência
SELECT
  status_pagamento,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentual
FROM propostas
GROUP BY status_pagamento;

-- Formas de pagamento
SELECT forma_pagamento, COUNT(*) FROM propostas GROUP BY forma_pagamento;
```

---

### 9. Antecipação

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Status da Antecipação | `status_antecipacao` | TEXT | Status da antecipação |

---

### 10. Prazos

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Prazo | `prazo` | INTEGER | Prazo em dias |
| Prazo Médio da operação | `prazo_medio_operacao` | INTEGER | Prazo médio em dias |

**Queries úteis:**
```sql
-- Prazo médio geral
SELECT AVG(prazo) as prazo_medio_dias FROM propostas;

-- Distribuição de prazos
SELECT
  CASE
    WHEN prazo <= 30 THEN '0-30 dias'
    WHEN prazo <= 60 THEN '31-60 dias'
    WHEN prazo <= 90 THEN '61-90 dias'
    ELSE '90+ dias'
  END as faixa_prazo,
  COUNT(*) as operacoes
FROM propostas
GROUP BY faixa_prazo;
```

---

### 11. Receita

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Receita Cashforce | `receita_cashforce` | NUMERIC(15,2) | Receita gerada para a Cashforce |

**Queries úteis:**
```sql
-- Receita total
SELECT SUM(receita_cashforce) as receita_total FROM propostas;

-- Receita por mês
SELECT
  DATE_TRUNC('month', data_operacao) as mes,
  SUM(receita_cashforce) as receita_mensal
FROM propostas
GROUP BY mes
ORDER BY mes DESC;
```

---

### 12. Anexos

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Termo anexado? | `termo_anexado` | BOOLEAN | Se o termo foi anexado |
| Boleto anexado? | `boleto_anexado` | BOOLEAN | Se o boleto foi anexado |
| Comprovante de depósito? | `comprovante_deposito` | BOOLEAN | Se o comprovante foi anexado |

**Queries úteis:**
```sql
-- Operações com documentação incompleta
SELECT * FROM propostas
WHERE termo_anexado = FALSE
   OR boleto_anexado = FALSE
   OR comprovante_deposito = FALSE;

-- Taxa de documentação completa
SELECT
  COUNT(*) FILTER (WHERE termo_anexado AND boleto_anexado AND comprovante_deposito) as completas,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE termo_anexado AND boleto_anexado AND comprovante_deposito) / COUNT(*), 2) as percentual
FROM propostas;
```

---

### 13. Controle

| Coluna Google Sheets | Coluna Banco | Tipo | Descrição |
|---------------------|--------------|------|-----------|
| Dia atual | `dia_atual` | DATE | Data de controle |

---

## 🔍 Índices

Para otimizar as consultas, foram criados os seguintes índices:

```sql
CREATE INDEX idx_propostas_nfid ON propostas(nfid);
CREATE INDEX idx_propostas_numero_proposta ON propostas(numero_proposta);
CREATE INDEX idx_propostas_cnpj_comprador ON propostas(cnpj_comprador);
CREATE INDEX idx_propostas_data_operacao ON propostas(data_operacao);
```

---

## 🔄 Triggers

### Atualização Automática de `updated_at`

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_propostas_updated_at BEFORE UPDATE
    ON propostas FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

Toda vez que um registro é atualizado, `updated_at` é automaticamente atualizado.

---

## 📊 Queries Analíticas Avançadas

### Dashboard Executivo

```sql
-- KPIs principais
SELECT
  COUNT(*) as total_operacoes,
  COUNT(DISTINCT cnpj_comprador) as total_compradores,
  COUNT(DISTINCT cnpj_fornecedor) as total_fornecedores,
  SUM(valor_bruto_duplicata) as volume_total,
  AVG(valor_bruto_duplicata) as ticket_medio,
  SUM(receita_cashforce) as receita_total
FROM propostas
WHERE data_operacao >= DATE_TRUNC('month', CURRENT_DATE);
```

### Análise de Performance por Parceiro

```sql
SELECT
  parceiro,
  COUNT(*) as operacoes,
  SUM(valor_bruto_duplicata) as volume,
  AVG(taxa_efetiva_mes_percentual) as taxa_media,
  SUM(receita_cashforce) as receita
FROM propostas
GROUP BY parceiro
ORDER BY volume DESC;
```

### Cohort de Vencimentos

```sql
SELECT
  DATE_TRUNC('week', vencimento) as semana_vencimento,
  COUNT(*) as operacoes,
  SUM(valor_bruto_duplicata) as valor_total,
  COUNT(*) FILTER (WHERE status_pagamento = 'Pago') as pagas,
  COUNT(*) FILTER (WHERE status_pagamento = 'Pendente') as pendentes
FROM propostas
WHERE vencimento >= CURRENT_DATE
GROUP BY semana_vencimento
ORDER BY semana_vencimento;
```

### Taxa de Conversão de Propostas

```sql
SELECT
  status_proposta,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentual
FROM propostas
WHERE data_operacao >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status_proposta
ORDER BY total DESC;
```

---

## 🛡️ Segurança

### Row Level Security (RLS)

Para habilitar RLS (recomendado em produção):

```sql
-- Habilitar RLS
ALTER TABLE propostas ENABLE ROW LEVEL SECURITY;

-- Política de leitura (exemplo: apenas usuários autenticados)
CREATE POLICY "Usuários autenticados podem ler propostas"
  ON propostas FOR SELECT
  USING (auth.role() = 'authenticated');

-- Política de escrita (exemplo: apenas service_role)
CREATE POLICY "Apenas service role pode inserir/atualizar"
  ON propostas FOR ALL
  USING (auth.role() = 'service_role');
```

---

## 🧹 Manutenção

### Limpeza de Dados Antigos

```sql
-- Deletar propostas rejeitadas com mais de 1 ano
DELETE FROM propostas
WHERE status_proposta = 'Rejeitada'
  AND data_operacao < CURRENT_DATE - INTERVAL '1 year';
```

### Backup

```bash
# Via Supabase CLI
supabase db dump -f backup_propostas_$(date +%Y%m%d).sql

# Restore
supabase db reset --db-url "postgresql://..."
```

---

## 📈 Métricas de Uso

### Tamanho da Tabela

```sql
SELECT
  pg_size_pretty(pg_total_relation_size('propostas')) as tamanho_total,
  pg_size_pretty(pg_relation_size('propostas')) as tamanho_dados,
  pg_size_pretty(pg_total_relation_size('propostas') - pg_relation_size('propostas')) as tamanho_indices;
```

### Estatísticas de Linhas

```sql
SELECT
  schemaname,
  relname,
  n_live_tup as linhas_ativas,
  n_dead_tup as linhas_mortas,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
WHERE relname = 'propostas';
```

---

## 🔗 Relacionamentos Futuros

Caso o sistema evolua para múltiplas tabelas:

```sql
-- Exemplo: Tabela de Compradores
CREATE TABLE compradores (
  id SERIAL PRIMARY KEY,
  cnpj TEXT UNIQUE NOT NULL,
  razao_social TEXT,
  grupo_economico TEXT,
  status TEXT
);

-- Adicionar FK em propostas
ALTER TABLE propostas
  ADD CONSTRAINT fk_comprador
  FOREIGN KEY (cnpj_comprador)
  REFERENCES compradores(cnpj);
```

---

## 📚 Referências

- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [Supabase Database Guide](https://supabase.com/docs/guides/database)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)

---

**Última atualização**: 2025-11-04
