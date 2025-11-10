# ValueError Fix: Invalid Format Specifier

## Problem

The application was experiencing `ValueError` exceptions when processing electrical diagrams. The error appeared in the logs as:

```
⚠️ Global falhou na página 1: ValueError('Invalid format specifier \' "CB-101",\n    "descricao": "Disjuntor Principal", ...')
❌ Erro Quadrant 1-1: ValueError(...)
❌ Erro Quadrant 1-2: ValueError(...)
❌ Erro Quadrant 1-3: ValueError(...)
... (all quadrants failing)
```

## Root Cause

The issue was in the `build_prompt` function in `backend/backend.py`. The function uses Python f-strings to generate prompts for the AI model. Within these f-strings, there were JSON examples meant to show the AI the expected output format.

The problem: **Curly braces `{}` inside f-strings have special meaning in Python** - they're used for variable interpolation. When the f-string encountered the JSON examples like:

```python
f"""
Example:
[
  {
    "tag": "CB-101",
    "descricao": "Disjuntor Principal"
  }
]
"""
```

Python tried to interpret `{"tag": "CB-101", ...}` as a format specification, which is invalid, causing the ValueError.

## Solution

The fix was simple but critical: **escape the curly braces by doubling them**:

```python
f"""
Example:
[
  {{
    "tag": "CB-101",
    "descricao": "Disjuntor Principal"
  }}
]
"""
```

When Python processes `{{` in an f-string, it produces a literal `{` in the output. Similarly, `}}` produces `}`.

## Changes Made

Two sections in `backend/backend.py` were updated:

### 1. Electrical Diagram JSON Example (lines 1717-1742)
**Before:**
```python
[
  {
    "tag": "CB-101",
    "descricao": "Disjuntor Principal",
    ...
  }
]
```

**After:**
```python
[
  {{
    "tag": "CB-101",
    "descricao": "Disjuntor Principal",
    ...
  }}
]
```

### 2. P&ID Diagram JSON Example (lines 1779-1796)
**Before:**
```python
[
  {
    "tag": "P-101",
    "descricao": "Bomba Centrífuga",
    ...
  }
]
```

**After:**
```python
[
  {{
    "tag": "P-101",
    "descricao": "Bomba Centrífuga",
    ...
  }}
]
```

## Result

After the fix:
- ✅ No more `ValueError` exceptions
- ✅ The JSON examples render correctly in the prompt with single braces
- ✅ The AI receives properly formatted examples
- ✅ Both electrical diagrams and P&IDs process successfully

## Testing

Multiple test suites confirm the fix:

1. **test_electrical_diagram_prompts.py**: 50/50 checks passed
2. **test_valueerror_fix.py**: 4/4 scenarios passed
   - Electrical Diagram - Global mode ✅
   - Electrical Diagram - Quadrant mode ✅
   - P&ID - Global mode ✅
   - P&ID - Quadrant mode ✅

## How to Verify

Run the test:
```bash
python3 test_valueerror_fix.py
```

Expected output:
```
✅ ALL TESTS PASSED

📝 What was fixed:
   - JSON examples in f-strings now use escaped braces {{...}}
   - This produces literal braces {...} in the output
   - No more ValueError: Invalid format specifier errors
```

## Lessons Learned

When using JSON or any content with curly braces inside Python f-strings, always remember to escape them:
- Use `{{` for literal `{`
- Use `}}` for literal `}`

This is a common gotcha in Python f-string formatting.
