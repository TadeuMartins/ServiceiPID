# Grid Validation for Electrical Diagrams

## Problema Resolvido

O grid do output dos diagramas elétricos agora é sempre um número inteiro múltiplo ou divisível por 4, conforme requisitado. Esta restrição se aplica **somente a diagramas elétricos**, não afetando diagramas P&ID.

## Implementação

### Valores Válidos do Grid

Para **diagramas elétricos**, os valores válidos são:
- `1` - 4 é divisível por 1 ✓
- `2` - 4 é divisível por 2 ✓  
- `4` - 4 é múltiplo de 4 (4 × 1) ✓

Valores **inválidos** para diagramas elétricos:
- `3` - 4 NÃO é divisível por 3 ✗
- `5` - 4 NÃO é divisível por 5 ✗
- `6` - 4 NÃO é divisível por 6 ✗

Para **diagramas P&ID**, todos os valores de 1 a 6 continuam válidos (sem mudanças).

## Mudanças no Código

### 1. Nova Função de Validação (`backend/backend.py`)

```python
def validate_grid_for_diagram_type(grid: int, diagram_type: str) -> None:
    """
    Validate that the grid parameter is appropriate for the diagram type.
    
    For electrical diagrams, grid must be a value that is a multiple or divisible by 4.
    Valid values for electrical diagrams: 1, 2, 4
    
    For P&ID diagrams, grid can be any value from 1 to 6.
    """
    if diagram_type.lower() == "electrical":
        valid_grid_values = [1, 2, 4]
        if grid not in valid_grid_values:
            raise HTTPException(
                status_code=400,
                detail=f"Para diagramas elétricos, o parâmetro 'grid' deve ser 1, 2 ou 4 (múltiplo ou divisível por 4). Valor fornecido: {grid}"
            )
```

### 2. Validação no Endpoint (`backend/backend.py`)

A validação é executada logo no início do processamento:

```python
@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile,
    dpi: int = Query(400, ge=100, le=600),
    grid: int = Query(3, ge=1, le=6),
    ...
    diagram_type: str = Query("pid", description="Diagram type: 'pid' for P&ID or 'electrical' for Electrical Diagram")
):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY não definida. Configure a chave no arquivo .env")

    # Validate grid parameter for diagram type
    validate_grid_for_diagram_type(grid, diagram_type)
    
    # ... resto do processamento
```

## Uso

### Exemplos de Requisições Válidas

```bash
# Diagrama elétrico com grid=4
POST /analyze?diagram_type=electrical&grid=4

# Diagrama elétrico com grid=2
POST /analyze?diagram_type=electrical&grid=2

# Diagrama elétrico com grid=1
POST /analyze?diagram_type=electrical&grid=1

# Diagrama P&ID com qualquer grid de 1 a 6
POST /analyze?diagram_type=pid&grid=3
POST /analyze?diagram_type=pid&grid=5
```

### Exemplos de Requisições Inválidas

```bash
# Diagrama elétrico com grid=3 (ERRO!)
POST /analyze?diagram_type=electrical&grid=3
# Retorna: HTTP 400
# "Para diagramas elétricos, o parâmetro 'grid' deve ser 1, 2 ou 4 (múltiplo ou divisível por 4). Valor fornecido: 3"

# Diagrama elétrico com grid=5 (ERRO!)
POST /analyze?diagram_type=electrical&grid=5
# Retorna: HTTP 400
# "Para diagramas elétricos, o parâmetro 'grid' deve ser 1, 2 ou 4 (múltiplo ou divisível por 4). Valor fornecido: 5"
```

## Testes

Foram criados testes abrangentes em `test_grid_validation.py`:

- ✅ Validação de valores válidos para diagramas elétricos (1, 2, 4)
- ✅ Validação de valores inválidos para diagramas elétricos (3, 5, 6)
- ✅ Validação de todos os valores para P&ID (1-6)
- ✅ Verificação de case-insensitive no tipo de diagrama
- ✅ Qualidade das mensagens de erro

### Executar os Testes

```bash
python test_grid_validation.py
```

## Impacto

### ✅ Benefícios
- Garante consistência nos diagramas elétricos
- Grid sempre compatível com a grade de 4mm usada nas coordenadas
- Mensagens de erro claras em português
- Sem impacto em diagramas P&ID

### ✅ Sem Quebras
- Diagramas P&ID não são afetados
- Testes existentes continuam passando
- Nenhuma vulnerabilidade de segurança introduzida

## Arquivos Modificados

1. `backend/backend.py` - Adicionada função de validação e chamada no endpoint
2. `test_grid_validation.py` - Novo arquivo com testes abrangentes

Total: 28 linhas adicionadas, 0 linhas removidas
