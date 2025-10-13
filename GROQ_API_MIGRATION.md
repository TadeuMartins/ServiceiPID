# Migração para Groq API

## Resumo das Alterações

Este documento descreve as alterações feitas para migrar do OpenAI para Groq API.

## Alterações Implementadas

### 1. Backend (`backend/backend.py`)

**Configuração da API:**
- Alterado de `OPENAI_API_KEY` para `GROQ_API_KEY`
- Adicionado `GROQ_BASE_URL` para apontar para `https://api.groq.com/openai/v1`
- Modelo primário alterado para `gpt-oss-120b` (conforme solicitado)
- Modelo de fallback alterado para `llama-3.3-70b-versatile`

**Função `make_client()`:**
- Atualizada para usar `GROQ_API_KEY` e `GROQ_BASE_URL`
- Mantém suporte para SSL/não-SSL

**Função `llm_call()`:**
- Atualizada para usar variáveis `PRIMARY_MODEL` e `FALLBACK_MODEL` dinamicamente
- Removidos hardcoded "gpt-5" e substituídos por variáveis configuráveis

**Mensagens de erro:**
- Atualizadas para mencionar `GROQ_API_KEY` em vez de `OPENAI_API_KEY`
- Startup event agora mostra "Groq API" em vez de "OpenAI"

### 2. System Matcher (`backend/system_matcher.py`)

**Sem alterações** - Mantém uso de OpenAI para embeddings, pois Groq não suporta embeddings atualmente.

### 3. Arquivo de Configuração (`.env.example`)

Atualizado para refletir a nova configuração:
```
GROQ_API_KEY=sua-chave-groq-aqui
GROQ_BASE_URL=https://api.groq.com/openai/v1
PRIMARY_MODEL=gpt-oss-120b
FALLBACK_MODEL=llama-3.3-70b-versatile
```

### 4. Arquivo de Teste (`.env`)

Criado com a chave de teste fornecida:
```
GROQ_API_KEY=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
PRIMARY_MODEL=gpt-oss-120b
```

## ⚠️ Limitações Conhecidas

1. **Vision API**: O Groq atualmente não suporta Vision API (análise de imagens). O código ainda tenta usar `image_url` nas mensagens, o que pode falhar dependendo do modelo.

2. **Embeddings**: O Groq não suporta embeddings. O `system_matcher.py` continua usando OpenAI para embeddings. Se você não precisa dessa funcionalidade, pode comentá-la.

3. **Modelo "gpt-oss-120b"**: Este modelo foi especificado conforme solicitado, mas pode não existir no Groq. Modelos conhecidos do Groq incluem:
   - `llama-3.3-70b-versatile`
   - `llama-3.1-70b-versatile`
   - `mixtral-8x7b-32768`
   - `gemma2-9b-it`

## Como Usar

1. **Copie o arquivo .env.example para .env:**
   ```bash
   cp .env.example .env
   ```

2. **Edite o .env com suas credenciais:**
   ```bash
   GROQ_API_KEY=sua-chave-groq-real
   PRIMARY_MODEL=llama-3.3-70b-versatile  # ou outro modelo Groq
   ```

3. **Inicie o servidor:**
   ```bash
   cd backend
   python backend.py
   ```

## Testes Realizados

- ✅ Sintaxe Python validada (sem erros)
- ✅ Servidor inicia corretamente
- ✅ Configuração Groq carregada
- ⚠️ Conexão com Groq API (limitado pelo ambiente de teste)

## Próximos Passos

1. **Validar modelo**: Verificar se "gpt-oss-120b" existe ou usar um modelo Groq conhecido
2. **Vision API**: Se necessário, considerar manter OpenAI para análise de imagens
3. **Embeddings**: Decidir se OpenAI será mantido para embeddings ou se será removido

## Arquivos Modificados

- `backend/backend.py` - Configuração principal da API
- `.env.example` - Template de configuração
- `.env` - Arquivo de configuração com chave de teste (não commitado)
