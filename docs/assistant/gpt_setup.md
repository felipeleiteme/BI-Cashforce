# 🤖 Guia de Configuração do GPT - BI-Cashforce

Este guia te ajuda a criar um GPT customizado que consulta os dados do Supabase.

---

## 📋 Pré-requisitos

Antes de começar, tenha em mãos:

- ✅ **Project URL**: `https://ximsykesrzxgknonmxws.supabase.co`
- ✅ **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyNjQ1MTYsImV4cCI6MjA3Nzg0MDUxNn0.TsQuIWQofqXuHCXV9DlYWGYmtVDgrIrEZ2-YSQNvGdc`

⚠️ **IMPORTANTE**:
- Use a **anon key** (pública) para o GPT
- A **service_role key** é SOMENTE para o ETL
- Proteja os dados com RLS (Row Level Security) no Supabase

---

## 🚀 Passo 1: Criar o GPT

1. Acesse: https://chat.openai.com/gpts/editor
2. Clique em **"Create a GPT"** ou **"+ Create"**
3. Na aba **"Configure"**, preencha:

### Nome
```
Assistente BI Cashforce
```

### Descrição
```
Assistente inteligente para consultar operações financeiras, notas fiscais e propostas do Cashforce. Acessa dados em tempo real do Supabase.
```

### Instruções (Instructions)
Cole o texto abaixo:

```
Você é um assistente especializado em análise de operações financeiras do Cashforce.

## Suas Capacidades:
- Consultar propostas e operações financeiras em tempo real
- Filtrar por CNPJ, NFID, grupo econômico, parceiro, status, datas e faixas de valor
- Calcular totais, médias, variações e estatísticas históricas
- Sinalizar quando os totais consolidados ultrapassarem thresholds definidos (ou um padrão)
- Apresentar dados de forma clara, organizada e com próximos passos sugeridos

## Como Usar a API:

### 1. Obter Consolidados Mensais (sempre comece por aqui)
Use a ação `getResumoMensal` para recuperar os totais agregados por mês, grupo econômico, comprador e parceiro. Isso evita estourar o limite de tokens quando existirem muitas operações.

**Exemplo de uso (totais de outubro/2025 para Marfrig):**
```
?competencia_id=eq.2025-10&grupo_economico=ilike.*MARFRIG*&limit=50
```

Sempre retorne `quantidade_operacoes`, `total_bruto_duplicata`, `total_liquido_duplicata` e `total_receita_cashforce`. Destaque se o total bruto ultrapassar um threshold (use o valor informado pelo usuário ou assuma R$10.000.000 como padrão). Se o usuário pedir outra competência, ajuste apenas o filtro correspondente.

### 2. Buscar Operações Detalhadas (apenas se o usuário pedir)
Use a ação `getPropostas` para consultar a tabela base quando o usuário solicitar detalhes.

- Sempre inclua `limit=50` e `order=data_operacao.desc`
- Controle a paginação com `offset=50`, `offset=100`, etc., confirmando com o usuário antes de avançar
- Para restringir períodos específicos, combine filtros de data (`gte` / `lte`)
- Ao responder, informe a página atual (ex.: “Página 1 de n, 50 registros por página”)

### 3. Filtros Disponíveis:

**Por CNPJ:**
```
cnpj_comprador=eq.02.183.783/0009-79
```

**Por NFID:**
```
nfid=eq.NFe35221109161713000101550010000203311800421109
```

**Por Grupo Econômico (busca parcial):**
```
grupo_economico=ilike.*LOJAS SUMIRÊ*
```

**Por Razão Social (busca parcial, case insensitive):**
```
razao_social_comprador=ilike.*sumire*
```

**Por Status da Proposta:**
```
status_proposta=eq.Aprovada
```

**Por Status de Pagamento (valores exatos após sanitização):**
```
status_pagamento=eq.A Receber    # Operações pendentes/aguardando pagamento
status_pagamento=eq.Pago          # Operações pagas
status_pagamento=eq.Vencido       # Operações vencidas
```

**Por Parceiro:**
```
parceiro=eq.CASHFORCE
```

**Por Data (maior ou igual):**
```
data_operacao=gte.2023-01-01
```

**Por Valor Bruto (menor ou igual):**
```
valor_bruto_duplicata=lte.10000.00
```

### 4. Ordenação e Limite:

**Ordenar por data (mais recente primeiro):**
```
order=data_operacao.desc
```

**Limitar resultados (obrigatório para listas detalhadas):**
```
limit=50
```

### 5. Exemplos de Uso:

**Buscar últimas 50 operações:**
```
?limit=50&order=data_operacao.desc
```

**Buscar operações de um CNPJ:**
```
?cnpj_comprador=eq.02.183.783/0009-79&limit=50&order=data_operacao.desc
```

**Buscar operações pagas em 2023 (intervalo completo):**
```
?status_pagamento=eq.Pago&data_operacao=gte.2023-01-01&data_operacao=lte.2023-12-31&limit=50&order=data_operacao.desc
```

**Buscar operações a receber (pendentes):**
```
?status_pagamento=eq.A Receber&limit=50&order=data_operacao.desc
```

**Buscar por grupo econômico (paginaçao iniciando na página 1):**
```
?grupo_economico=ilike.*LOJAS*&limit=50&order=data_operacao.desc&offset=0
```

## Formato de Resposta:

Sempre apresente os dados de forma organizada:

1. **Resumo**: Informe filtros aplicados, quantidade de linhas retornadas, destaque os totais consolidados (via `getResumoMensal`) e mencione o threshold, quando relevante
2. **Consolidados**: Mostre `quantidade_operacoes`, `total_bruto_duplicata`, `total_liquido_duplicata`, `total_receita_cashforce` e sinalize excessos de threshold
3. **Principais Dados (detalhes, se solicitados)**: Liste até 50 operações por página, informando a página atual, com:
   - Número da Proposta
   - NFID
   - Comprador (Razão Social + CNPJ)
   - Fornecedor
   - Valor Bruto
   - Status de Pagamento
   - Data da Operação
4. **Insight/Próximos Passos**: Sugira filtros adicionais, confirme interesse em próximas páginas ou destaque parceiros/grupos relevantes

## Regras:
- **REGRA DE TRADUÇÃO CRÍTICA:** O usuário usará termos como "pendente", "em aberto" ou "aguardando pagamento". Você DEVE traduzir isso para o filtro de sistema correto: `status_pagamento=eq.A Receber`. Nunca use `eq.Pendente`.
- SEMPRE inicie com `getResumoMensal` antes de listar detalhes
- Use `limit=50` em `getPropostas` por padrão; ajuste somente se o usuário pedir outra quantidade
- Controle paginação com `offset` e confirme com o usuário antes de prosseguir
- Para buscas por texto, use `ilike.*termo*` (case insensitive)
- Para valores exatos, use `eq.valor`
- Para datas, use formato ISO `YYYY-MM-DD`
- Se não encontrar dados, informe claramente o resultado, sugira filtros alternativos e recapitule os filtros utilizados
```

### Conversation Starters (Exemplos de Perguntas)
Adicione estes 4 exemplos:

```
1. Traga o total consolidado de outubro/2025 para o Grupo Marfrig
2. Mostre as últimas 50 operações registradas
3. Busque operações do CNPJ 02.183.783/0009-79
4. Qual o total de operações pagas em 2023?
```

### Knowledge (Opcional)
Deixe em branco por enquanto.

---

## 🔗 Passo 2: Configurar a Ação (Action)

1. Role até a seção **"Actions"** (Ações)
2. Clique em **"Create new action"** ou **"+ Add Action"**

### 2.1 Authentication

1. Clique em **"Authentication"**
2. Selecione **"API Key"**
3. Preencha:
   - **API Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyNjQ1MTYsImV4cCI6MjA3Nzg0MDUxNn0.TsQuIWQofqXuHCXV9DlYWGYmtVDgrIrEZ2-YSQNvGdc`
   - **Auth Type**: **Bearer**
   - **Header Name**: `Authorization`

4. Adicione um **Custom Header**:
   - Clique em **"Add header"** ou similar
   - **Header Name**: `apikey`
   - **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhpbXN5a2Vzcnp4Z2tub25teHdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyNjQ1MTYsImV4cCI6MjA3Nzg0MDUxNn0.TsQuIWQofqXuHCXV9DlYWGYmtVDgrIrEZ2-YSQNvGdc`

### 2.2 Schema

No campo **"Schema"**, cole o conteúdo do arquivo `OPENAPI_SCHEMA.json`:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "BI-Cashforce API",
    "description": "API para consultar operações financeiras do Cashforce via Supabase",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://ximsykesrzxgknonmxws.supabase.co/rest/v1"
    }
  ],
  "paths": {
    "/propostas": {
      "get": {
        "operationId": "getPropostas",
        "summary": "Buscar propostas/operações financeiras",
        "description": "Retorna lista de propostas com filtros opcionais",
        "parameters": [
          {
            "name": "cnpj_comprador",
            "in": "query",
            "description": "Filtrar por CNPJ do comprador. Use formato: eq.02.183.783/0009-79",
            "schema": { "type": "string" }
          },
          {
            "name": "nfid",
            "in": "query",
            "description": "Filtrar por NFID. Use formato: eq.NFe35221109161713000101550010000203311800421109",
            "schema": { "type": "string" }
          },
          {
            "name": "grupo_economico",
            "in": "query",
            "description": "Filtrar por grupo econômico. Use formato: ilike.*LOJAS*",
            "schema": { "type": "string" }
          },
          {
            "name": "razao_social_comprador",
            "in": "query",
            "description": "Filtrar por razão social. Use formato: ilike.*nome*",
            "schema": { "type": "string" }
          },
          {
            "name": "status_proposta",
            "in": "query",
            "description": "Filtrar por status. Use formato: eq.Aprovada",
            "schema": { "type": "string" }
          },
          {
            "name": "status_pagamento",
            "in": "query",
            "description": "Filtrar por status de pagamento. Use formato: eq.Pago",
            "schema": { "type": "string" }
          },
          {
            "name": "data_operacao",
            "in": "query",
            "description": "Filtrar por data. Use formato: gte.2023-01-01",
            "schema": { "type": "string" }
          },
          {
            "name": "select",
            "in": "query",
            "description": "Colunas a retornar. Padrão: *",
            "schema": { "type": "string", "default": "*" }
          },
          {
            "name": "order",
            "in": "query",
            "description": "Ordenação. Exemplo: data_operacao.desc",
            "schema": { "type": "string", "default": "created_at.desc" }
          },
          {
            "name": "limit",
            "in": "query",
            "description": "Limite de resultados. Máximo: 100",
            "schema": { "type": "integer", "default": 10, "maximum": 100 }
          }
        ],
        "responses": {
          "200": {
            "description": "Lista de propostas",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "type": "object" }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

> ℹ️ **Materialized view**: execute `supabase/propostas_resumo_mensal.sql` no SQL Editor do Supabase para criar a materialized view, índices e a função `refresh_propostas_resumo_mensal()`. O ETL (`api/etl_sync.py`) já chama essa função após cada sincronização para manter os consolidados atualizados.

3. Clique em **"Save"** ou **"Test"**

---

## 🧪 Passo 3: Testar

1. Clique em **"Test"** ou **"Preview"** no canto superior direito
2. Teste com estas perguntas:

```
Mostre as últimas 5 operações
```

```
Busque operações do CNPJ 02.183.783/0009-79
```

```
Qual o total de operações pagas?
```

Se funcionar corretamente, você verá os dados formatados!

---

## 🔒 Passo 4: Configurar Segurança no Supabase (RLS)

✅ **STATUS**: RLS está **CONFIGURADO e ATIVO** na tabela `propostas`.

### Configuração Atual (Implementada)

A seguinte configuração já foi aplicada para proteger os dados:

```sql
-- Habilitar RLS
ALTER TABLE propostas ENABLE ROW LEVEL SECURITY;

-- Permitir leitura pública (para GPT e consultas via anon key)
CREATE POLICY "Permitir leitura pública"
  ON propostas FOR SELECT
  USING (true);
```

**Como funciona:**
- ✅ **Leitura pública permitida** - GPT pode consultar os dados via anon key
- ✅ **Escrita bloqueada** - INSERT, UPDATE, DELETE são bloqueados para anon key
- ✅ **ETL protegido** - Apenas service_role key (ETL) pode modificar dados
- ✅ **Sem vulnerabilidades** - Supabase Security Advisor aprovado

### Opções Alternativas (Se Quiser Restringir Mais)

Se você quiser restringir o acesso apenas a usuários autenticados:

```sql
-- Deletar policy atual
DROP POLICY "Permitir leitura pública" ON propostas;

-- Opção 1: Apenas usuários autenticados
CREATE POLICY "Apenas usuários autenticados podem ler"
  ON propostas FOR SELECT
  USING (auth.role() = 'authenticated');

-- Opção 2: Apenas emails de um domínio específico
CREATE POLICY "Apenas emails @cashforce.com"
  ON propostas FOR SELECT
  USING (
    auth.jwt() ->> 'email' LIKE '%@cashforce.com'
  );
```

⚠️ **ATENÇÃO**: Se você mudar para opção 1 ou 2, o GPT precisará de autenticação adicional.

Execute qualquer alteração em: https://supabase.com/dashboard/project/ximsykesrzxgknonmxws/editor

---

## 🎨 Passo 5: Personalizar (Opcional)

### Logo/Avatar
- Faça upload de uma imagem 512x512px
- Pode ser o logo do Cashforce

### Capabilities (Habilidades)
Marque conforme necessário:
- ✅ Web Browsing (se quiser que busque info externa)
- ❌ DALL-E (não necessário)
- ❌ Code Interpreter (não necessário)

---

## 💡 Exemplos de Perguntas que o GPT Pode Responder

### Consultas Básicas
```
- Mostre as últimas 10 operações
- Qual foi a última operação registrada?
- Liste operações de hoje
```

### Filtros Específicos
```
- Busque operações do CNPJ 02.183.783/0009-79
- Mostre operações do grupo LOJAS SUMIRÊ
- Liste operações do parceiro CASHFORCE
- Quais operações estão com status "Pago"?
```

### Análises
```
- Qual o total de operações pagas em 2023?
- Qual o valor médio das duplicatas?
- Quantas operações foram feitas este mês?
- Mostre as 5 maiores operações por valor
```

### Combinações
```
- Busque operações pagas do grupo LOJAS SUMIRÊ em 2023
- Mostre operações pendentes acima de R$ 10.000
- Liste fornecedores com mais de 5 operações
```

---

## 🐛 Troubleshooting

### Erro: "Authentication failed"
- Verifique se a anon key está correta
- Confirme que adicionou o header `apikey`

### Erro: "No data returned"
- Verifique se o RLS está configurado
- Teste a query direto no Supabase SQL Editor

### Erro: "Too many results"
- Sempre use `limit` nas queries
- Padrão é 10, máximo recomendado é 100

---

## 📚 Recursos Adicionais

- **Supabase API Docs**: https://supabase.com/docs/guides/api
- **PostgREST Operators**: https://postgrest.org/en/stable/references/api/tables_views.html
- **GPT Actions Guide**: https://platform.openai.com/docs/actions

---

## ✅ Checklist Final

Status da configuração do GPT:

- [x] Nome e descrição configurados
- [x] Instruções detalhadas adicionadas
- [x] Ação criada com schema OpenAPI
- [x] Authentication configurada (anon key + apikey header)
- [x] Testado com queries básicas
- [x] **RLS configurado e ativo no Supabase**
- [x] Conversation starters adicionados
- [x] **GPT funcionando e retornando dados corretamente**

---

**Pronto!** Seu GPT customizado está configurado e funcionando! 🎉

Agora qualquer pessoa com acesso ao seu GPT pode consultar os dados do Cashforce de forma natural, em linguagem humana.

---

## 📝 ATUALIZAÇÃO: Valores Corretos de Status de Pagamento

### ⚠️ INFORMAÇÃO CRÍTICA PARA COPIAR NO GPT

**Adicione esta seção nas instruções do GPT** (na seção "Como Usar a API" ou no final das instruções):

```
## Valores Válidos de Status de Pagamento (OBRIGATÓRIO)

Após análise do banco de dados (73.290 registros), os ÚNICOS valores válidos de `status_pagamento` são:

1. **"A Receber"** (56.915 operações - 77.7%)
   - Representa operações PENDENTES/AGUARDANDO PAGAMENTO
   - Use: `status_pagamento=eq.A Receber`
   - ❌ NÃO use "Pendente", "Em Aberto" ou "Aguardando"

2. **"Pago"** (10.582 operações - 14.4%)
   - Representa operações PAGAS/QUITADAS
   - Use: `status_pagamento=eq.Pago`

3. **"Vencido"** (5.793 operações - 7.9%)
   - Representa operações VENCIDAS/ATRASADAS
   - Use: `status_pagamento=eq.Vencido`

### Exemplos de Consultas Corretas:

**Buscar operações pendentes (a receber):**
```
?status_pagamento=eq.A Receber&limit=50&order=data_operacao.desc
```

**Buscar operações pagas:**
```
?status_pagamento=eq.Pago&limit=50&order=data_operacao.desc
```

**Buscar operações vencidas:**
```
?status_pagamento=eq.Vencido&limit=50&order=data_operacao.desc
```

### Como Responder ao Usuário:

Quando o usuário perguntar sobre operações "pendentes", "em aberto" ou "não pagas", você deve:

1. Entender que ele está se referindo a **"A Receber"**
2. Usar o filtro correto: `status_pagamento=eq.A Receber`
3. Informar na resposta: "Busquei operações com status 'A Receber' (operações pendentes)"

### Importante:

- Todos os valores de status foram padronizados usando `.str.title()` no ETL
- Os valores são case-sensitive (use exatamente "A Receber", não "a receber")
- Se o usuário usar termos diferentes, traduza para os valores válidos
```

### Como Adicionar no GPT:

1. Acesse o GPT Editor: https://chat.openai.com/gpts/editor
2. Vá na seção **"Instructions"**
3. **Cole o texto acima no FINAL das instruções atuais**
4. Clique em **"Save"** ou **"Update"**
5. Teste com: "Mostre operações pendentes" ou "Liste operações a receber"

---

## 🧪 Testes Recomendados Após Atualização:

```
✅ "Mostre operações com status de pagamento = A Receber"
✅ "Liste operações pendentes"
✅ "Quantas operações estão aguardando pagamento?"
✅ "Qual o total de operações a receber do Marfrig?"
✅ "Mostre operações pagas em outubro de 2024"
✅ "Liste operações vencidas"
```

Se todas essas consultas funcionarem, o GPT está 100% configurado! ✅
