# 🚀 Quick Start - Groq API

## ⚡ Configuração Rápida

### 1️⃣ Configure a Chave (30 segundos)

```bash
# Copie o template
cp .env.example .env

# Edite com sua chave Groq
nano .env  # ou vim, code, etc.
```

No arquivo `.env`, adicione:
```env
GROQ_API_KEY=sua-chave-groq-aqui
```

### 2️⃣ Teste (10 segundos)

```bash
python test_groq_config.py
```

✅ Se aparecer "TESTE CONCLUÍDO COM SUCESSO", está pronto!

### 3️⃣ Execute (5 segundos)

```bash
cd backend
python backend.py
```

## 🔑 Sua Chave de Teste

A chave de teste já está configurada no `.env`:
```
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
```

## 🎯 Modelo Configurado

- **Primário**: `gpt-oss-120b`
- **Fallback**: `llama-3.3-70b-versatile`

## 🔄 Trocar Modelo (se necessário)

Edite `.env` e mude `PRIMARY_MODEL`:

```env
# Modelo original (solicitado)
PRIMARY_MODEL=gpt-oss-120b

# OU use um modelo Groq conhecido:
PRIMARY_MODEL=llama-3.3-70b-versatile
```

## 📋 Modelos Groq Disponíveis

- `llama-3.3-70b-versatile` ⭐
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

## ⚠️ Avisos Rápidos

1. **Vision API**: Groq pode não suportar análise de imagens
2. **Embeddings**: Usa OpenAI (se precisar, adicione `OPENAI_API_KEY`)
3. **Modelo gpt-oss-120b**: Pode não existir, tente `llama-3.3-70b-versatile`

## 🆘 Problemas?

### Erro: "GROQ_API_KEY não definida"
→ Execute: `cp .env.example .env` e edite o arquivo

### Erro de conexão
→ Verifique se a chave está correta

### Modelo não encontrado
→ Troque para `llama-3.3-70b-versatile` no `.env`

## 📚 Documentação Completa

- [GROQ_MIGRATION_SUMMARY.md](GROQ_MIGRATION_SUMMARY.md) - Resumo completo
- [GROQ_UPDATE_README.md](GROQ_UPDATE_README.md) - Guia detalhado
- [GROQ_API_MIGRATION.md](GROQ_API_MIGRATION.md) - Detalhes técnicos

---

**🎉 Pronto!** Seu backend agora usa Groq API com o modelo gpt-oss-120b.
