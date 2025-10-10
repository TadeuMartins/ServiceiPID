# Implementação: Carregamento de API Key via arquivo .env

## Resumo
Alterado o código para sempre buscar a API key da OpenAI de um arquivo `.env` em vez de usar valores hardcoded como fallback.

## Mudanças Implementadas

### 1. Adicionado python-dotenv às dependências
**Arquivo:** `backend/requirements.txt`
- Adicionada biblioteca `python-dotenv` para carregar variáveis de ambiente de arquivos `.env`

### 2. Atualizado backend/backend.py
**Mudanças:**
- Importado `load_dotenv` de `python-dotenv`
- Adicionada chamada `load_dotenv()` no início do módulo para carregar o arquivo `.env`
- Removido valor hardcoded da API key do `os.getenv()` 
- Atualizado `make_client()` para retornar `None` se a API key não estiver definida (evita crash)
- Atualizadas mensagens de erro para indicar que a chave deve estar no arquivo `.env`

**Antes:**
```python
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "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"
)
```

**Depois:**
```python
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### 3. Atualizado backend/system_matcher.py
**Mudanças:**
- Importado `load_dotenv` de `python-dotenv`
- Adicionada chamada `load_dotenv()` no início do módulo
- Removido valor hardcoded da API key
- Atualizada mensagem de erro para indicar uso do arquivo `.env`

**Antes:**
```python
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "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"
)
```

**Depois:**
```python
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### 4. Criado arquivo .env.example
**Arquivo:** `.env.example`
- Template com todas as variáveis de ambiente configuráveis
- Inclui comentários explicativos
- Serve como guia para usuários criarem seu próprio `.env`

**Conteúdo:**
```
# OpenAI API Configuration
OPENAI_API_KEY=sua-chave-openai-aqui

# Optional: Model Configuration
# PRIMARY_MODEL=gpt-5
# FALLBACK_MODEL=gpt-4o

# Optional: Request Timeout (in seconds)
# OPENAI_REQUEST_TIMEOUT=600

# Optional: Server Port
# PORT=8000

# Optional: Reference Excel Path
# REF_XLSX_PATH=referencia_systems.xlsx
```

### 5. Atualizado .gitignore
**Mudanças:**
- Adicionada seção para arquivos de ambiente
- Garantido que `.env`, `.env.local` e variantes não sejam commitados

**Adicionado:**
```
# Environment variables
.env
.env.local
.env.*.local
```

### 6. Atualizado README.md
**Mudanças:**
- Substituídas instruções de configuração via variáveis de ambiente por instruções de uso do `.env`
- Adicionado passo para copiar `.env.example` para `.env`
- Atualizada seção de troubleshooting sobre API key

**Antes:**
```bash
export OPENAI_API_KEY="sua-chave-aqui"
# ou
set OPENAI_API_KEY=sua-chave-aqui
```

**Depois:**
```bash
cp .env.example .env
# Depois edite o arquivo .env e adicione sua chave
```

## Como Usar

### Para Desenvolvedores
1. Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` e adicione sua chave OpenAI:
   ```
   OPENAI_API_KEY=sua-chave-openai-real-aqui
   ```

3. Inicie a aplicação normalmente:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn backend:app --reload --port 8000
   ```

### Variáveis de Ambiente Disponíveis
- `OPENAI_API_KEY` (obrigatória): Chave de API da OpenAI
- `PRIMARY_MODEL` (opcional): Modelo principal a usar (padrão: gpt-5)
- `FALLBACK_MODEL` (opcional): Modelo de fallback (padrão: gpt-4o)
- `OPENAI_REQUEST_TIMEOUT` (opcional): Timeout em segundos (padrão: 600)
- `PORT` (opcional): Porta do servidor (padrão: 8000)
- `REF_XLSX_PATH` (opcional): Caminho para a planilha de referência

## Benefícios

1. **Segurança**: API keys não estão mais hardcoded no código
2. **Facilidade**: Usuários só precisam editar um arquivo `.env`
3. **Flexibilidade**: Fácil alternar entre diferentes chaves/ambientes
4. **Padrão da Indústria**: Uso de `.env` é uma best practice amplamente adotada
5. **Desenvolvimento Local**: Cada desenvolvedor pode ter sua própria configuração

## Testes Realizados

✅ Arquivo `.env` é carregado corretamente  
✅ API key é lida do arquivo `.env`  
✅ Aplicação inicia sem erro quando `.env` existe  
✅ Mensagens de erro claras quando `.env` está faltando  
✅ Arquivo `.env` não é commitado (protegido por `.gitignore`)  
✅ Template `.env.example` funciona corretamente  
✅ Cliente OpenAI não é criado quando API key está faltando (evita crash)  

## Arquivos Modificados

```
.gitignore                    | 4 linhas adicionadas
.env.example                  | novo arquivo (15 linhas)
README.md                     | 20 linhas modificadas
backend/requirements.txt      | 1 linha adicionada
backend/backend.py            | 11 linhas modificadas
backend/system_matcher.py     | 6 linhas modificadas
```

## Notas Importantes

- O arquivo `.env` **nunca deve ser commitado** no repositório
- Sempre use `.env.example` como template
- Em produção, considere usar secrets management mais robusto
- O carregamento do `.env` é automático - não precisa de configuração adicional
