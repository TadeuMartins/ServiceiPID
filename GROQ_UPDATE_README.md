# 🔄 Atualização: Migração para Groq API

## 📌 O que mudou?

O backend foi atualizado para usar a **Groq API** em vez da OpenAI, permitindo o uso de modelos open-source de alta performance.

### Chave da API
- **Antes**: OpenAI API Key
- **Agora**: Groq API Key (formato: `gsk_...`)

### Modelos
- **Modelo Primário**: `gpt-oss-120b` (configurado conforme solicitado)
- **Modelo Fallback**: `llama-3.3-70b-versatile`

### Base URL
- **Groq API**: `https://api.groq.com/openai/v1`

## 🚀 Como usar

### 1. Configure a chave da API

Edite o arquivo `.env` (ou crie a partir do `.env.example`):

```bash
# Copiar o exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env  # ou use seu editor preferido
```

Adicione sua chave Groq:

```env
GROQ_API_KEY=sua-chave-groq-aqui
GROQ_BASE_URL=https://api.groq.com/openai/v1
PRIMARY_MODEL=gpt-oss-120b
FALLBACK_MODEL=llama-3.3-70b-versatile
```

### 2. Teste a configuração

Execute o script de teste:

```bash
python test_groq_config.py
```

Saída esperada:
```
✅ TESTE CONCLUÍDO COM SUCESSO
O backend está configurado para usar Groq API
```

### 3. Inicie o servidor

```bash
cd backend
python backend.py
```

## ⚠️ Limitações Importantes

### 1. Vision API
A Groq atualmente **não suporta Vision API** (análise de imagens). O código tenta usar a funcionalidade de visão, mas isso pode resultar em erros dependendo do modelo escolhido.

**Impacto**: A análise de P&ID via imagem pode não funcionar com alguns modelos Groq.

### 2. Embeddings
A Groq **não suporta embeddings**. O módulo `system_matcher.py` ainda usa OpenAI para embeddings.

**Solução**: Se você precisa de embeddings, mantenha também uma chave OpenAI no `.env`:

```env
GROQ_API_KEY=sua-chave-groq
OPENAI_API_KEY=sua-chave-openai  # Para embeddings
```

### 3. Modelo "gpt-oss-120b"
Este modelo foi configurado conforme solicitado, mas pode não existir no catálogo Groq.

**Modelos Groq conhecidos:**
- `llama-3.3-70b-versatile` (recomendado)
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

Para usar um modelo diferente, edite o `.env`:

```env
PRIMARY_MODEL=llama-3.3-70b-versatile
```

## 📁 Arquivos Modificados

- **backend/backend.py**: Atualizado para usar Groq API
- **.env.example**: Template atualizado com configuração Groq
- **GROQ_API_MIGRATION.md**: Documentação detalhada da migração
- **test_groq_config.py**: Script de teste da configuração

## 🔍 Mais Informações

Para detalhes técnicos completos sobre a migração, consulte:
- [GROQ_API_MIGRATION.md](GROQ_API_MIGRATION.md)

## 🆘 Suporte

Se encontrar problemas:

1. **Verifique a chave**: Certifique-se de que sua chave Groq está correta
2. **Execute o teste**: `python test_groq_config.py`
3. **Verifique os logs**: O servidor mostra mensagens detalhadas de erro
4. **Modelos**: Tente usar um modelo Groq conhecido (ex: `llama-3.3-70b-versatile`)
