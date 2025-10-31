# Implementação: Verificação de Embeddings e Prompts Específicos por Tipo de Diagrama

## Resumo das Mudanças

Esta implementação resolve dois problemas principais:

1. **Verificação e criação automática de embeddings no startup do backend**
2. **Correção da alucinação da IA ao gerar diagramas elétricos** (estava gerando descrições de P&ID em vez de diagrama elétrico)

## Mudanças Implementadas

### 1. system_matcher.py

#### Nova Função: `ensure_embeddings_exist()`

```python
def ensure_embeddings_exist():
    """
    Garante que os embeddings existam para P&ID e Diagramas Elétricos.
    Chamada no startup do backend para inicializar embeddings caso não existam.
    """
```

Esta função:
- Verifica se existe o arquivo de cache `ref_embeddings_pid.pkl`
- Verifica se existe o arquivo de cache `ref_embeddings_electrical.pkl`
- Se não existirem, cria os embeddings automaticamente
- Registra todo o processo com logs claros

**Benefício**: O backend agora garante que os embeddings estejam disponíveis antes de processar qualquer requisição, evitando erros durante a análise.

### 2. backend.py

#### Atualização do Startup Event

```python
@app.on_event("startup")
async def startup_event():
    # ... código existente ...
    
    # Verifica e garante que embeddings existam
    log_to_front("🔍 Verificando embeddings...")
    ensure_embeddings_exist()
```

**Benefício**: Embeddings são verificados e criados automaticamente quando o backend inicia.

#### Atualização da Função `build_prompt()`

Adicionado parâmetro `diagram_type`:

```python
def build_prompt(width_mm: float, height_mm: float, scope: str = "global", 
                origin=(0, 0), quad_label: str = "", diagram_type: str = "pid") -> str:
```

**Mudanças no prompt**:

- **Para P&ID (`diagram_type="pid"`)**: Mantém o prompt original focado em:
  - Equipamentos de processo (bombas, tanques, trocadores)
  - Instrumentação ISA S5.1 (PI, PT, FT, LT, etc.)
  - Válvulas e tubulações

- **Para Diagrama Elétrico (`diagram_type="electrical"`)**: Novo prompt focado em:
  - Transformadores (TR-XXX, T-XXX)
  - Motores elétricos (M-XXX, MOT-XXX)
  - Geradores (G-XXX)
  - Painéis elétricos (PNL-XXX, MCC-XXX)
  - Disjuntores (CB-XXX, DJ-XXX)
  - Relés de proteção (REL-XXX)
  - Instrumentação elétrica (amperímetros, voltímetros, etc.)

**Benefício**: A IA recebe instruções específicas sobre qual tipo de diagrama está analisando, evitando confusão.

#### Atualização da Função `build_generation_prompt()`

Adicionado parâmetro `diagram_type` e avisos explícitos:

```python
def build_generation_prompt(process_description: str, width_mm: float = 1189.0, 
                           height_mm: float = 841.0, diagram_type: str = "pid") -> str:
```

**Avisos CRÍTICOS adicionados ao prompt**:

```
CRITICAL: You MUST generate a {DIAGRAM_TYPE}, NOT any other type of diagram. 
Focus exclusively on {electrical components OR process equipment}.
```

**Benefício**: Instrui explicitamente a IA para gerar o tipo correto de diagrama, prevenindo alucinações.

#### Atualização da Função `process_quadrant()`

Adicionado parâmetro `diagram_type` para passar o tipo através da cadeia de processamento:

```python
async def process_quadrant(gx, gy, rect, page, W_mm, H_mm, dpi, diagram_type="pid"):
```

**Benefício**: Mantém a consistência do tipo de diagrama através de todo o pipeline de processamento.

## Como Usar

### No Frontend (app.py)

O frontend já está preparado com seletor de tipo de diagrama:

```python
diagram_type_analyze = st.selectbox(
    "Tipo de Diagrama:",
    options=[("P&ID", "pid"), ("Diagrama Elétrico", "electrical")],
    ...
)
```

O valor selecionado é passado automaticamente para o backend:

```python
params = {"diagram_type": diagram_type_value}
response = requests.post(API_URL, files=files, params=params, timeout=3600)
```

### Fluxo Completo

1. **Usuário seleciona tipo de diagrama** no frontend
2. **Frontend envia `diagram_type`** para o backend
3. **Backend usa prompts específicos** baseado no `diagram_type`
4. **IA gera ou analisa** com contexto correto
5. **System Matcher usa embeddings corretos** (P&ID ou Electrical)

## Exemplo de Uso

### Analisando um Diagrama Elétrico

1. No frontend, selecione: **"Diagrama Elétrico"**
2. Faça upload do PDF
3. O backend irá:
   - Usar prompt focado em componentes elétricos
   - Procurar por: transformadores, motores, disjuntores, etc.
   - Usar embeddings de referência elétrica para matching

### Gerando um Diagrama Elétrico

1. No frontend, aba "Gerar a partir de Prompt"
2. Selecione: **"Diagrama Elétrico"**
3. Digite: "Gere um diagrama elétrico de distribuição de energia"
4. O backend irá:
   - Usar prompt de geração focado em equipamentos elétricos
   - Gerar transformadores, painéis, disjuntores, etc.
   - **NÃO** gerar bombas, tanques ou instrumentação ISA

## Testes Realizados

✅ Código compila sem erros
✅ Assinaturas de função verificadas
✅ Lógica de tipo de diagrama funciona para "pid" e "electrical"
✅ Conteúdo dos prompts verificado para cada tipo
✅ Todos os testes unitários passam

## Arquivos Modificados

- `backend/system_matcher.py`: Adicionada função `ensure_embeddings_exist()`
- `backend/backend.py`: 
  - Startup event atualizado
  - `build_prompt()` atualizado com `diagram_type`
  - `build_generation_prompt()` atualizado com `diagram_type`
  - `process_quadrant()` atualizado com `diagram_type`
  - Todas as chamadas atualizadas para passar `diagram_type`

## Próximos Passos (Opcional)

Para melhorias futuras, considere:

1. Adicionar mais tipos de diagramas (instrumentação, hidráulico, etc.)
2. Criar prompts ainda mais específicos por subtipos
3. Adicionar validação de tipo de diagrama baseada no conteúdo detectado
4. Criar embeddings especializados por tipo de equipamento
