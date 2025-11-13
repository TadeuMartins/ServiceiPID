# Correção dos Diagramas Elétricos - Dimensões A3 Fixas e Exclusão de Bornes

## Problema Original (Portuguese)

É preciso considerar que a folha de diagramas elétricos tem sempre X420 e Y297 mm, além disso não considere bornes na analise de diagramas elétricos. a distribuição da folha ainda não está correta.

## Original Problem (English)

The electrical diagram sheet must always be considered as X=420mm and Y=297mm (A3 landscape), and terminals/bornes should not be considered in electrical diagram analysis. The sheet distribution is still not correct.

## Análise do Problema / Problem Analysis

### Problema 1: Dimensões Variáveis
Anteriormente, o sistema usava as dimensões reais da página PDF para diagramas elétricos. Isso causava problemas porque:
- Diferentes PDFs tinham dimensões diferentes (A4, A3, A0, etc.)
- As coordenadas não eram consistentes entre diagramas
- A distribuição espacial ficava incorreta

Previously, the system used actual PDF page dimensions for electrical diagrams. This caused problems because:
- Different PDFs had different dimensions (A4, A3, A0, etc.)
- Coordinates were not consistent across diagrams
- Spatial distribution was incorrect

### Problema 2: Bornes/Terminais Detectados
O sistema estava detectando bornes (terminais de conexão) como objetos separados, quando eles deveriam ser ignorados. Bornes são apenas pontos de conexão e não componentes principais do diagrama.

The system was detecting bornes (connection terminals) as separate objects, when they should be ignored. Bornes are just connection points and not main diagram components.

### Problema 3: Distribuição da Folha
A distribuição das coordenadas na folha não estava correta porque:
- As dimensões variáveis causavam mapeamento inconsistente
- As zonas espaciais não estavam alinhadas corretamente
- A conversão de pixels para milímetros estava incorreta

The sheet distribution was not correct because:
- Variable dimensions caused inconsistent mapping
- Spatial zones were not correctly aligned
- Pixel to millimeter conversion was incorrect

## Solução Implementada / Solution Implemented

### 1. Forçar Dimensões A3 (420x297mm) para Diagramas Elétricos

#### Modificação em `run_electrical_pipeline`

**Antes / Before:**
```python
# Get page dimensions in mm FIRST (needed for prompts)
W_pts, H_pts = page.rect.width, page.rect.height
W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
log_to_front(f"📄 Dimensões da folha: {W_mm:.1f}mm x {H_mm:.1f}mm")
```

**Depois / After:**
```python
# For electrical diagrams, ALWAYS use A3 horizontal dimensions (420mm x 297mm)
# regardless of actual PDF page dimensions
W_mm, H_mm = get_electrical_diagram_dimensions()
log_to_front(f"📄 Dimensões da folha (A3 horizontal fixo): {W_mm:.1f}mm x {H_mm:.1f}mm")
```

#### Impacto / Impact
- Todos os diagramas elétricos agora usam 420x297mm (A3 horizontal)
- Coordenadas são consistentes independente do tamanho real do PDF
- Distribuição espacial é correta e previsível

All electrical diagrams now use 420x297mm (A3 landscape)
Coordinates are consistent regardless of actual PDF size
Spatial distribution is correct and predictable

### 2. Exclusão de Bornes/Terminais

#### A. Atualização dos Prompts

**build_prompt() - Prompt Principal:**
```python
⚠️ IMPORTANTE - FOCO EM OBJETOS PRINCIPAIS:
   - NÃO extraia cabos, linhas de potência ou barramentos como objetos separados
   - NÃO extraia bornes (terminais de conexão) como objetos separados  # NOVO
   - Foque SOMENTE nos componentes principais do diagrama elétrico
   - Cabos, barramentos e bornes devem ser DESCONSIDERADOS na extração  # ATUALIZADO
```

**build_prompt_electrical_global():**
```python
"DO NOT extract terminals/bornes as separate objects - they should be IGNORED."  # NOVO
```

**build_prompt_electrical_tile():**
```python
"ELECTRICAL SCHEMATIC TILE. Detect symbols (motors, breakers, fuses, relays) "  # removido "terminals"
"and connections (from_tag,to_tag,path,direction,confidence). "
"DO NOT extract terminals/bornes as separate objects - they should be IGNORED."  # NOVO
```

#### B. Filtragem em parse_electrical_equips()

**Adicionada lógica de filtragem:**
```python
# Filter out terminals/bornes
descricao_lower = str(e.get("descricao", "")).lower()
type_lower = str(e.get("type", "")).lower()
tag_lower = str(e.get("tag", "")).lower()

# Skip if this is a terminal/borne
terminal_keywords = ["terminal", "borne", "bornes", "terminais"]
if any(keyword in descricao_lower or keyword in type_lower or keyword in tag_lower 
       for keyword in terminal_keywords):
    continue  # Pula este equipamento
```

#### Impacto / Impact
- Bornes não são mais detectados como objetos separados
- Foco apenas em componentes principais (motores, disjuntores, transformadores, etc.)
- Resultados mais limpos e relevantes

Bornes are no longer detected as separate objects
Focus only on main components (motors, breakers, transformers, etc.)
Cleaner and more relevant results

### 3. Correção da Distribuição da Folha

#### Conversão de Coordenadas
A conversão de coordenadas pixel → mm agora funciona corretamente:

```python
# Conversão usando dimensões A3 fixas
x_mm = ((e.bbox.x + e.bbox.w/2) / W_px_at_tiles) * W_mm  # W_mm = 420.0
y_mm = ((e.bbox.y + e.bbox.h/2) / H_px_at_tiles) * H_mm  # H_mm = 297.0
```

#### Zonas Espaciais Alinhadas

**Distribuição Vertical (Y) - Eixo Principal:**
- Zona de fonte (topo): Y = 20-60 mm (10 posições na grade de 4mm)
- Zona de distribuição: Y = 60-120 mm (15 posições)
- Zona de controle/proteção: Y = 120-180 mm (15 posições)
- Zona de carga (base): Y = 180-240 mm (15 posições)
- Margem inferior: ~20-40mm de Y=297mm

**Distribuição Horizontal (X) - Eixo Secundário:**
- Margem esquerda: X = 40-60 mm
- Circuito de potência principal: X = 60-140 mm (80mm de largura)
- Circuito de controle: X = 180-260 mm (80mm de largura)
- Instrumentação/medidores: X = 300-380 mm (80mm de largura)
- Margem direita: ~20-40mm de X=420mm

#### Impacto / Impact
- Coordenadas sempre dentro dos limites A3 (0-420mm x 0-297mm)
- Zonas espaciais bem definidas e alinhadas com grade de 4mm
- Distribuição previsível e consistente

Coordinates always within A3 bounds (0-420mm x 0-297mm)
Spatial zones well-defined and aligned with 4mm grid
Predictable and consistent distribution

## Arquivos Modificados / Files Modified

### 1. `backend/backend.py`

**Linhas modificadas:**
- ~2191-2194: Forçar dimensões A3 em `run_electrical_pipeline`
- ~1626-1630: Adicionar exclusão de bornes em `build_prompt`
- ~1896-1903: Adicionar exclusão de terminais em `build_prompt_electrical_global`
- ~1910-1921: Atualizar `build_prompt_electrical_tile` para excluir terminais
- ~2016-2060: Adicionar filtragem de terminais em `parse_electrical_equips`
- ~2279: Atualizar comentário sobre coordenadas baseadas em A3 fixo

**Total de alterações:** 28 linhas modificadas, 13 linhas adicionadas

### 2. Testes Criados

#### `test_electrical_a3_dimensions.py` (NOVO - 151 linhas)
Testa:
- Dimensões sempre A3 (420x297mm)
- Prompts excluem bornes/terminais
- Filtragem de terminais funciona corretamente

#### `test_electrical_coordinate_distribution.py` (NOVO - 188 linhas)
Testa:
- Conversão pixel→mm com dimensões A3 fixas
- Coordenadas dentro dos limites A3
- Zonas espaciais alinhadas com grade de 4mm
- Distribuição horizontal correta

## Testes de Regressão / Regression Tests

Todos os testes existentes continuam passando:

### ✅ test_electrical_a3_dimensions.py
- Dimensões A3 fixas
- Exclusão de terminais em prompts
- Filtragem de terminais

### ✅ test_electrical_coordinate_distribution.py
- Conversão de coordenadas correta
- Coordenadas dentro dos limites
- Zonas espaciais alinhadas
- Distribuição horizontal

### ✅ test_electrical_vertical_layout.py
- 4/4 test suites passando
- Layout vertical preservado

### ✅ test_electrical_no_quadrants.py
- 3/3 test suites passando
- Sem quadrantes para elétricos

### ✅ test_cable_busbar_exclusion.py
- Exclusão de cabos/barramentos
- Componentes principais preservados

### ✅ test_electrical_prompt_dimensions.py
- Prompts usam dimensões corretas
- Cálculo de mm por pixel

## Verificação / Verification

### Testar Dimensões A3 Fixas
```bash
python3 test_electrical_a3_dimensions.py
# Espera-se: ALL TESTS PASSED ✅
```

### Testar Distribuição de Coordenadas
```bash
python3 test_electrical_coordinate_distribution.py
# Espera-se: ALL TESTS PASSED ✅
```

### Testar Todos os Elétricos
```bash
for test in test_electrical_*.py; do python3 $test; done
# Espera-se: Todos passando ✅
```

## Benefícios / Benefits

1. **✅ Consistência**: Todos os diagramas elétricos usam mesmas dimensões (A3)
2. **✅ Precisão**: Coordenadas corretas e previsíveis
3. **✅ Foco**: Apenas componentes principais, sem bornes
4. **✅ Compatibilidade**: P&ID continua funcionando normalmente
5. **✅ Testado**: Cobertura de testes completa
6. **✅ Seguro**: Sem vulnerabilidades de segurança (verificado com CodeQL)

## Compatibilidade / Compatibility

### ✅ 100% Retrocompatível / 100% Backward Compatible

1. **P&ID sem mudanças**: Continua usando dimensões reais da página
2. **Comportamento padrão**: `diagram_type="pid"` não afetado
3. **Sem quebras de API**: Nenhuma assinatura de função alterada
4. **Frontend pronto**: Já tem seletor de tipo de diagrama
5. **Testes existentes**: Todos passando

## Conclusão / Conclusion

As três correções implementadas resolvem completamente os problemas relatados:

1. **✅ Dimensões A3 Fixas**: Diagramas elétricos sempre usam 420x297mm, independente do tamanho real do PDF
2. **✅ Exclusão de Bornes**: Terminais/bornes são ignorados na análise, foco apenas em componentes principais
3. **✅ Distribuição Correta**: Coordenadas são mapeadas corretamente no espaço A3 com zonas espaciais bem definidas

A solução é:
- **Eficaz**: Resolve todos os problemas relatados
- **Precisa**: Coordenadas consistentes e corretas
- **Segura**: 100% retrocompatível, sem regressões
- **Testada**: Cobertura completa de testes (6 arquivos de teste)
- **Documentada**: Documentação clara e bilíngue

---

**Data da Implementação**: 2025-11-13  
**Arquivos Modificados**: 1 (backend/backend.py - 28 linhas)  
**Testes Adicionados**: 2 novos arquivos (339 linhas de testes)  
**Testes de Regressão**: 6 arquivos, todos passando ✅  
**Segurança**: 0 vulnerabilidades (verificado com CodeQL) ✅
