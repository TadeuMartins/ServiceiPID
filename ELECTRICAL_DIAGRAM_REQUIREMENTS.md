# Electrical Diagram Requirements Implementation

## Overview
This document describes the specific requirements for electrical diagrams that have been implemented in the ServiceiPID system.

## Requirements

### 1. A3 Horizontal Sheet Dimensions
**Requirement:** For electrical diagrams, always consider A3 horizontal sheet measurements.

**Implementation:**
- Added `get_electrical_diagram_dimensions()` function that returns A3 horizontal dimensions: 420mm x 297mm
- Updated `build_generation_prompt()` to use A3 dimensions for electrical diagrams
- Modified `/generate` endpoint to automatically use A3 dimensions when `diagram_type="electrical"`
- Updated prompts to explicitly mention A3 horizontal as the reference for electrical diagrams

**Code Location:** `backend/backend.py` lines 217-224

### 2. Unipolar vs Multifilar Detection
**Requirement:** Always verify if diagram is unipolar or multifilar to choose correct system full names.

**Implementation:**
- Added `detect_electrical_diagram_subtype()` function that analyzes equipment descriptions and diagram text to detect:
  - **Unipolar (unifilar/single-line):** Simplified representation, one line per phase group
  - **Multifilar (multi-filar):** All conductors/phases shown explicitly (L1, L2, L3, etc.)
- Detection uses keyword matching for Portuguese and English terms
- Subtype is passed to `match_system_fullname()` for better equipment matching
- Result includes `diagram_subtype` field in the output

**Code Location:** `backend/backend.py` lines 226-272

**Keywords used for detection:**
- Multifilar: "multifilar", "multi-filar", "três fases", "three phase", "trifásico", "l1", "l2", "l3", "r", "s", "t", "cabo", "condutor"
- Unipolar: "unipolar", "uni-polar", "unifilar", "uni-filar", "single line", "single-line", "diagrama simplificado"

### 3. Coordinate Rounding to Multiples of 4mm
**Requirement:** Always use millimeters in multiples of 4. For example, if object is at x:10, y:10, it should be considered as x:12, y:12.

**Implementation:**
- Added `round_to_multiple_of_4()` function that rounds coordinates using "round half up" strategy
- Applied to both `/analyze` and `/generate` endpoints for electrical diagrams
- Rounding is applied AFTER coordinate extraction but BEFORE storage
- Logging shows before/after values for transparency

**Rounding Examples:**
- 10.0 → 12.0 (exactly between 8 and 12, rounds up)
- 10.5 → 12.0 (closer to 12)
- 14.0 → 16.0 (exactly between 12 and 16, rounds up)
- 15.9 → 16.0 (closer to 16)
- 234.5 → 236.0
- 567.8 → 568.0

**Code Location:** `backend/backend.py` lines 196-215

## Prompt Updates

### Analysis Prompt (build_prompt)
For electrical diagrams, the prompt now includes:

1. **Reference Dimensions Section:**
   ```
   A. DIMENSÕES DE REFERÊNCIA (CRÍTICO):
      - Diagramas elétricos SEMPRE usam folha A3 horizontal como referência
      - Dimensões padrão A3 horizontal: 420mm (largura) x 297mm (altura)
   ```

2. **Coordinate Rounding Section:**
   ```
   B. ARREDONDAMENTO DE COORDENADAS (OBRIGATÓRIO PARA DIAGRAMAS ELÉTRICOS):
      - TODAS as coordenadas (x_mm e y_mm) DEVEM ser arredondadas para múltiplos de 4mm
      - Exemplos: 10.0 → 12.0, 14.0 → 16.0, etc.
   ```

3. **Diagram Type Section:**
   ```
   C. TIPO DE DIAGRAMA ELÉTRICO:
      - Identifique se o diagrama é UNIPOLAR ou MULTIFILAR
      - UNIPOLAR: representação simplificada, uma linha por grupo de fases
      - MULTIFILAR: todos os condutores/fases mostrados explicitamente
   ```

### Generation Prompt (build_generation_prompt)
For electrical diagrams, the generation prompt includes:
- A3 landscape format specification
- Coordinate precision requirement: multiples of 4mm only
- Examples using coordinates that are multiples of 4
- Valid coordinate examples: 0.0, 4.0, 8.0, 12.0, 16.0, etc.

## System Matcher Updates

Updated `match_system_fullname()` in `backend/system_matcher.py`:
- Accepts optional `diagram_subtype` parameter
- For electrical diagrams, includes subtype in the query text for better matching
- Returns `diagram_subtype` in the result when applicable

## Testing

Created `test_electrical_diagram_requirements.py` with comprehensive tests:
1. Coordinate rounding to multiples of 4mm
2. A3 horizontal dimensions (420mm x 297mm)
3. Unipolar/Multifilar diagram type detection
4. Electrical prompt includes all requirements
5. Electrical generation prompt uses A3 and coordinate rounding
6. P&ID prompts remain unchanged (no electrical requirements)

## Backward Compatibility

All changes are backward compatible:
- P&ID diagrams continue to use A0 dimensions (1189mm x 841mm)
- P&ID coordinates use decimal precision (0.1mm)
- Electrical requirements only apply when `diagram_type="electrical"`
- Default behavior for `diagram_type="pid"` is unchanged

## Usage Examples

### Analyzing an Electrical Diagram
```python
POST /analyze?diagram_type=electrical
```
Result will include:
- Coordinates rounded to multiples of 4mm
- `diagram_subtype` field (unipolar or multifilar)
- System full names matched with subtype context

### Generating an Electrical Diagram
```python
POST /generate?diagram_type=electrical&prompt="Motor starter circuit"
```
Result will:
- Use A3 horizontal dimensions (420mm x 297mm)
- Generate coordinates as multiples of 4mm
- Include appropriate electrical components

## Files Modified

1. `backend/backend.py`
   - Added 3 new functions
   - Updated 2 prompt building functions
   - Modified 2 endpoints (/analyze, /generate)
   
2. `backend/system_matcher.py`
   - Updated match_system_fullname() signature and logic

3. `test_electrical_diagram_requirements.py`
   - New comprehensive test file

## Summary

All three requirements from the problem statement have been successfully implemented:
1. ✅ A3 horizontal dimensions for electrical diagrams
2. ✅ Unipolar/Multifilar detection for correct system full name matching
3. ✅ Coordinate rounding to multiples of 4mm

The implementation is clean, well-documented, and maintains backward compatibility with existing P&ID functionality.
