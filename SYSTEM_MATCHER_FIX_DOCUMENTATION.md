# System Matcher Fix - Documentation

## Problem Statement

The system matcher was incorrectly matching different equipment types to the same `SystemFullName` (specifically "Motor protection switch, 3-pole") even when they had completely different descriptions:

```
H003A   Ponto de conexão/cabo trifásico (lado de entrada do acionamento)           → Motor protection switch, 3-pole
NO-TAG4 Acionamento eletrônico de motor trifásico (VFD/soft-starter) (3-pole)     → Motor protection switch, 3-pole
H003B   Ponto de conexão/cabo trifásico (saída do acionamento para o motor)       → Motor protection switch, 3-pole
ZMS300  Motor trifásico AC (3-pole) 75,0 cv                                        → Motor protection switch, 3-pole
```

All four completely different equipment types were being matched to the same reference entry.

## Root Cause Analysis

### Issue 1: Over-emphasis on Pole Count
The original filtering logic heavily weighted pole count detection. When "trifásico" (three-phase) was detected, it filtered to all "3-pole" entries (19 items), but then semantic similarity alone determined the match. Since "Motor protection switch" contains the word "motor" and all test cases involve motor-related equipment, it was frequently chosen.

### Issue 2: Inadequate Equipment Type Filtering
The original `extract_equipment_type_keywords` function was too simple:
- It would extract "motor" from both "Motor trifásico AC" AND "Motor protection switch"
- This created ambiguity and confusion in matching
- No priority system for compound terms vs simple terms

### Issue 3: Dual Terminology Not Handled
The reference database uses different terminology:
- **Switches, breakers, fuses**: Use "3-pole" terminology
- **Motors**: Use "three-phase" or "3-phase" terminology

When filtering for "3-pole" only, motors were excluded entirely!

## Solution

### 1. Enhanced Equipment Type Extraction

**Before:**
```python
equipment_types = {
    'motor': ['motor'],
    'switch': ['chave', 'switch', 'interruptor'],
    ...
}
```

**After:**
```python
equipment_types = [
    # Protection devices (check first - compound terms)
    ('protection-switch', ['motor protection switch', 'disjuntor-motor', ...]),
    ('motor-starter', ['motor starter', 'partida', ...]),
    
    # Drives and converters
    ('drive', ['vfd', 'inversor', 'soft-starter', ...]),
    
    # Cables and connections
    ('cable', ['cabo', 'cable', ...]),
    ('connection-point', ['ponto de conexão', ...]),
    
    # Motors (checked AFTER compound terms)
    ('motor', ['motor elétrico', 'three-phase motor', 'ac motor', ...]),
    ...
]
```

Key improvements:
- Priority-based matching (compound terms first)
- Position-based overlap detection to prevent double-matching
- Special handling for "motor" to exclude "motor protection" and "motor starter"

### 2. Combined Pole and Equipment Type Filtering

**Before:**
```python
if detected_pole:
    pole_mask = df_ref['Descricao'].str.contains(detected_pole, ...)
    if pole_mask.sum() > 0:
        df_ref = df_ref[pole_mask]
```

**After:**
```python
# Build masks for both pole count and equipment type
pole_mask = None
type_mask = None

if detected_pole:
    # Handle both "3-pole" and "three-phase" terminology
    if detected_pole == "3-pole":
        pole_patterns = ["3-pole", "three-phase", "3-phase", ...]
    pole_mask = df_ref['Descricao'].str.contains(pole_pattern, ...)

if equipment_types:
    # Build equipment type patterns with negative lookahead
    if eq_type == 'motor':
        pattern = r'(?!.*motor\s+(protection|starter)).*\bmotor\b'
    type_mask = df_ref['Descricao'].str.contains(pattern, ...)

# Combine filters with priority
if pole_mask and type_mask:
    combined_mask = pole_mask & type_mask
    if combined_mask.sum() > 0:
        # Best: both filters match
        df_ref = df_ref[combined_mask]
    elif type_mask.sum() > 0:
        # Prioritize equipment type
        df_ref = df_ref[type_mask]
    elif pole_mask.sum() > 0:
        # Fall back to pole
        df_ref = df_ref[pole_mask]
```

### 3. Dual Terminology Support

The fix now handles both terminologies:
- When detecting "trifásico" → creates patterns for both "3-pole" AND "three-phase"
- Searches for: `"3-pole|three-phase|3-phase|three phase|3 phase"`
- This ensures motors (three-phase) and switches (3-pole) are both found

### 4. Better Query Construction

**Before:**
```python
query_text = f"{tipo} {tag} {descricao}"
```

**After:**
```python
# Weight equipment types heavily by repeating
query_parts = []
if equipment_types:
    query_parts.extend(equipment_types)  # First time
    query_parts.extend(equipment_types)  # Second time (reinforcement)
if detected_pole:
    query_parts.append(detected_pole)
query_parts.append(descricao)
# Don't include tag (often just a code)
```

## Results

### Test 1: Motor (ZMS300 - "Motor trifásico AC (3-pole) 75,0 cv")

**Before:**
- Filtered to: 19 items (all "3-pole" equipment including switches)
- Would match: "Motor protection switch, 3-pole" ❌

**After:**
- Detected: pole="3-pole", type="motor"
- Filtered to: 18 items (three-phase motors only)
- Example matches:
  - Three-phase motor, single speed ✅
  - Three-phase motor, double speed ✅
  - AC motor ✅

### Test 2: Cable/Connection (H003A - "Ponto de conexão/cabo trifásico")

**Before:**
- Filtered to: 19 items (all "3-pole" equipment)
- Would match: "Motor protection switch, 3-pole" ❌

**After:**
- Detected: pole="3-pole", type=["cable", "connection-point"]
- Filtered to: 1 item
- Matches: "General consumer without process connection (AC, 3 phase)" ✅

### Test 3: Drive (NO-TAG4 - "Acionamento eletrônico de motor trifásico (VFD/soft-starter)")

**Before:**
- Filtered to: 19 items (all "3-pole" equipment)
- Would match: "Motor protection switch, 3-pole" ❌

**After:**
- Detected: pole="3-pole", type=["motor-starter", "drive"]
- Filtered to: 2 items
- Example matches:
  - Synchronous rotary converter, 3-phase ✅
  - Frequency converter, 3 phases ✅

## Test Coverage

All tests pass:
- ✅ `test_equipment_type_extraction.py`: 9/9 tests passed
- ✅ `test_filtering_logic.py`: 3/3 tests passed
- ✅ `test_pole_filtering.py`: All tests passed
- ✅ `test_pole_detection.py`: 14/14 tests passed
- ✅ CodeQL security scan: No issues found

## Backward Compatibility

The changes are backward compatible:
- P&ID diagrams continue to work as before (unchanged code path)
- Electrical diagrams without pole counts fall back gracefully
- If equipment type extraction fails, pole filtering still works
- If both fail, uses full reference database (original behavior)

## Performance Impact

Minimal performance impact:
- Equipment type extraction: O(n) where n = number of equipment type patterns (~15)
- Filtering: Same complexity as before (DataFrame masking operations)
- No additional API calls to OpenAI
- Query construction is slightly longer but negligible

## Migration Notes

No migration needed:
- No database changes
- No API changes
- No configuration changes
- Existing embeddings cache remains valid
- Existing reference files unchanged
