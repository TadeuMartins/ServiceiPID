# Guia Rápido - Novo Sistema de Coordenadas

## O Que Mudou?

### Problema Resolvido ✅

O sistema anterior tinha **contradições** que confundiam a IA:
- Prompt dizia: "coordenadas devem ser GLOBAIS" E "coordenadas devem ser LOCAIS"
- Dimensões erradas passadas (página completa em vez de quadrante)
- Resultado: coordenadas inconsistentes e incorretas

### Solução Implementada ✅

Agora o sistema é **claro e preciso**:
- Cada contexto tem instruções específicas (global OU local, nunca ambos)
- Dimensões corretas sempre passadas
- Conversão automática e consistente
- Resultado: coordenadas **exatamente** como no PDF

---

## Como Funciona Agora

### 1. Análise Global (Página Completa)

```
A IA vê: Página completa (1189 x 841 mm)
Recebe: "Retorne coordenadas absolutas da página"
Retorna: Coordenadas globais (ex: 594, 420)
Sistema: Usa direto (já são globais)
```

### 2. Análise por Quadrante (Subdivisão)

```
A IA vê: Quadrante (396 x 280 mm)
Recebe: "Retorne coordenadas locais deste quadrante de 396x280mm"
Retorna: Coordenadas locais ao quadrante (ex: 198, 140)
Sistema: Converte para global (198+396=594, 140+280=420)
```

**Importante:** A conversão é SEMPRE automática e rastreável nos logs!

---

## Validação das Coordenadas

### Como Verificar se Está Funcionando

1. **Verifique os logs** durante a análise:
   ```
   🔹 Quadrant 2-3 | origem ≈ (396.3, 280.3) mm | dimensões ≈ (396.3 x 280.3) mm
   🔄 Convertendo P-101: local (198.0, 140.0) + offset (396.3, 280.3) = global (594.3, 420.3)
   ```

2. **Compare com posições visuais** no PDF:
   - Abra o PDF em um visualizador
   - Identifique a posição de um equipamento (ex: centro da página)
   - Verifique se as coordenadas retornadas correspondem (centro ≈ 594, 420)

3. **Execute os testes automatizados**:
   ```bash
   python test_coordinate_system.py
   python test_quadrant_coordinates.py
   ```

---

## Sistema de Coordenadas - Referência Rápida

### Página A0 (Paisagem)

```
     0                           1189 (mm)
   0 ┌──────────────────────────────┐
     │                              │
     │   X → (cresce para direita)  │
     │   Y ↓ (cresce para baixo)    │
     │                              │
 841 └──────────────────────────────┘
```

- **Origem:** Topo superior esquerdo (0, 0)
- **Largura:** 0 a 1189 mm
- **Altura:** 0 a 841 mm

### Quadrantes (3x3)

```
┌─────┬─────┬─────┐
│ 1-1 │ 1-2 │ 1-3 │  Cada: ~396 x 280 mm
├─────┼─────┼─────┤
│ 2-1 │ 2-2 │ 2-3 │  Origem local: (0,0)
├─────┼─────┼─────┤  no canto superior
│ 3-1 │ 3-2 │ 3-3 │  esquerdo do quadrante
└─────┴─────┴─────┘
```

---

## Parâmetros Ajustáveis

### Via API `/analyze`

```python
POST /analyze
{
  "file": <PDF>,
  "dpi": 400,      # Resolução (300-600, padrão: 400)
  "grid": 3,       # Subdivisão (1-6, padrão: 3)
  "tol_mm": 10.0   # Tolerância deduplicação (1-50, padrão: 10)
}
```

**Recomendações:**
- `dpi=400`: Bom equilíbrio entre qualidade e velocidade
- `grid=3`: Ideal para a maioria dos P&IDs A0
- `tol_mm=10`: Remove duplicatas reais, mantém instrumentos próximos

---

## Deduplicação Inteligente

### Como Funciona

1. **Mesma TAG + proximidade < 10mm:** Remove duplicata
   ```
   P-101 at (500, 400) + P-101 at (502, 398) → Mantém apenas primeiro
   ```

2. **TAGs diferentes mesmo se próximos:** Mantém ambos
   ```
   P-101 at (500, 400) + PT-101 at (505, 395) → Mantém ambos ✅
   ```

3. **Sem TAG + proximidade:** Remove se perto de item identificado
   ```
   P-101 at (500, 400) + N/A at (503, 399) → Remove N/A
   ```

---

## Compatibilidade COMOS

### Conversão Automática

O sistema gera **dois campos** de coordenada Y:

1. **y_mm:** Sistema PDF (Y=0 no topo)
   ```
   Topo:   y_mm = 0
   Centro: y_mm = 420
   Base:   y_mm = 841
   ```

2. **y_mm_cad:** Sistema COMOS (Y=0 na base)
   ```
   Topo:   y_mm_cad = 841
   Centro: y_mm_cad = 421
   Base:   y_mm_cad = 0
   ```

**Fórmula:** `y_mm_cad = altura_total - y_mm`

---

## Troubleshooting

### Coordenadas Parecem Erradas?

1. **Verifique os logs** para ver a conversão:
   ```
   🔄 Convertendo <TAG>: local (...) + offset (...) = global (...)
   ```

2. **Confirme as dimensões** do quadrante nos logs:
   ```
   🔹 Quadrant X-Y | origem ≈ (...) mm | dimensões ≈ (... x ...) mm
   ```

3. **Execute os testes**:
   ```bash
   python test_coordinate_system.py
   python test_quadrant_coordinates.py
   ```

### Duplicatas Sendo Removidas Incorretamente?

1. **Verifique a tolerância** (padrão: 10mm)
2. **Ajuste via parâmetro** `tol_mm` na API
3. **Verifique TAGs** - itens sem TAG próximos são removidos

### IA Retornando Coordenadas Estranhas?

1. **Verifique o DPI** (padrão: 400) - imagens muito pequenas dificultam análise
2. **Tente grid menor** (ex: 2x2) - quadrantes maiores podem ser mais fáceis de analisar
3. **Verifique qualidade do PDF** - PDFs de baixa qualidade dificultam detecção

---

## Arquivos da Solução

### Código

- **backend/backend.py:** Lógica principal (prompt + conversão)

### Documentação

- **COORDINATE_SYSTEM_FINAL.md:** Documentação completa da solução
- **COMPARISON_BEFORE_AFTER.md:** Comparação detalhada antes vs depois
- **Este arquivo:** Guia rápido de referência

### Testes

- **test_coordinate_system.py:** Valida sistema nos prompts
- **test_quadrant_coordinates.py:** Valida conversão e deduplicação

---

## Resumo Executivo

### O Que Foi Corrigido

| Problema | Solução |
|----------|---------|
| Instruções contraditórias no prompt | Prompts específicos para cada contexto |
| Dimensões erradas passadas | Dimensões corretas do quadrante |
| Conversão ambígua | Sempre local → global |
| Falta de rastreabilidade | Logging detalhado de cada conversão |

### Garantias

✅ Coordenadas **exatamente** como no PDF  
✅ Sistema **100% consistente**  
✅ **Fácil validação** via logs  
✅ **Todos os testes** passando  

---

**Pronto para uso em produção!** 🚀
