# Manual Testing Guide - Coordinate Center Fix

## Overview
This guide helps you manually test the coordinate center rule fix and the prompt improvements.

## Prerequisites
1. OpenAI API key configured in `.env` file
2. Backend and frontend dependencies installed

## Test 1: Verify Prompt Generation (No API Call)

This test verifies the prompts are generated correctly without calling OpenAI API.

```bash
# From repository root
cd /home/runner/work/ServiceiPID/ServiceiPID

# Test prompt generation
python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')
from backend import build_generation_prompt, build_prompt

# Test generation prompt
gen_prompt = build_generation_prompt("Generate a P&ID for water treatment")
print("=" * 80)
print("GENERATION PROMPT TEST")
print("=" * 80)
print(f"Length: {len(gen_prompt)} characters")
print(f"Has 'CENTER' rule: {'CENTER' in gen_prompt.upper()}")
print(f"Has 'educational' framing: {'educational' in gen_prompt.lower()}")
print(f"Is in English: {'TASK:' in gen_prompt}")
print(f"Excludes piping: {'piping' in gen_prompt.lower()}")
print()

# Test analysis prompt
analysis_prompt = build_prompt(1189.0, 841.0)
print("=" * 80)
print("ANALYSIS PROMPT TEST")
print("=" * 80)
print(f"Length: {len(analysis_prompt)} characters")
print(f"Has 'CENTRO' rule: {'CENTRO' in analysis_prompt.upper()}")
print(f"Excludes tubulação: {'tubula' in analysis_prompt.lower()}")
print()

print("✅ Both prompts generated successfully!")
EOF
```

Expected output:
```
================================================================================
GENERATION PROMPT TEST
================================================================================
Length: 7XXX characters
Has 'CENTER' rule: True
Has 'educational' framing: True
Is in English: True
Excludes piping: True

================================================================================
ANALYSIS PROMPT TEST
================================================================================
Length: 4XXX characters
Has 'CENTRO' rule: True
Excludes tubulação: True

✅ Both prompts generated successfully!
```

## Test 2: Start Backend (Manual)

```bash
# From repository root
cd backend

# Option 1: Using uvicorn directly
uvicorn backend:app --reload --port 8000

# Option 2: Using python script (auto finds free port)
python backend.py
```

Expected output:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Test 3: Test Generation Endpoint (With API Key)

**⚠️ This test requires a valid OpenAI API key**

In a new terminal:

```bash
# Test the /generate endpoint
curl -X POST "http://localhost:8000/generate?prompt=Generate%20a%20simple%20P%26ID%20for%20water%20pump%20system" \
  -H "Content-Type: application/json" \
  | python -m json.tool | head -50
```

Expected behavior:
- **Before fix**: Would return "I'm sorry, but I can't assist with that request"
- **After fix**: Should return JSON array with equipment and instruments

Look for:
```json
[
  {
    "tag": "T-101",
    "descricao": "...",
    "x_mm": 150.0,  ← Should be at equipment center
    "y_mm": 450.0,  ← Should be at equipment center
    "from": "N/A",
    "to": "P-101"
  },
  ...
]
```

## Test 4: Visual Verification

1. Start both backend and frontend:
   ```bash
   # Terminal 1 - Backend
   cd backend && uvicorn backend:app --reload
   
   # Terminal 2 - Frontend
   cd frontend && streamlit run app.py
   ```

2. In the frontend (usually http://localhost:8501):
   - Go to "🎨 Gerar a partir de Prompt" tab
   - Enter: "Generate a P&ID for a simple water pump system"
   - Click "🎨 Gerar P&ID"

3. Verify:
   - ✅ No error message from OpenAI
   - ✅ Table shows equipment with coordinates
   - ✅ Visualization shows points on the A0 sheet
   - ✅ Export works (Excel/JSON)

## Test 5: Coordinate Center Verification

When reviewing generated coordinates, verify:

```
Equipment: P-101 (Pump)
Coordinates: (250.0, 400.0)  ← Should be at pump CENTER, not pipe connection

Equipment: T-101 (Tank)  
Coordinates: (150.0, 450.0)  ← Should be at tank CENTER, not top/bottom

Instrument: FT-101 (Flow Transmitter)
Coordinates: (280.0, 380.0)  ← Should be at instrument symbol CENTER, not on pipe
```

## Troubleshooting

### OpenAI API Key Error
```
Error: OPENAI_API_KEY não definida
Solution: Create .env file with: OPENAI_API_KEY=your-key-here
```

### Port 8000 Already in Use
```
Error: Address already in use
Solution: Use different port: uvicorn backend:app --port 8001
```

### "I can't assist with that request"
```
If you still see this error after the fix:
1. Verify you're running the updated code (check git log)
2. Try a different prompt (more generic/educational)
3. Check OpenAI API status
```

## Success Criteria

✅ Prompts generate without errors
✅ Backend starts without errors
✅ Generation endpoint returns JSON (not refusal)
✅ Coordinates reference equipment centers
✅ Frontend displays results correctly
✅ Export functions work

## Notes

- The educational framing is key to avoiding OpenAI refusal
- Coordinates are now ALWAYS at equipment/instrument centers
- The system is COMOS-compatible with absolute coordinates
- Both Portuguese (analysis) and English (generation) prompts are supported
