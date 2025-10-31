# Quick Start: Diagram Type Selection Feature

## What's New?

The ServiceiPID application now supports **two types of diagrams**:
1. **P&ID** (Piping and Instrumentation Diagram)
2. **Diagrama Elétrico** (Electrical Diagram)

Each type uses its own reference file for accurate system matching.

## How to Use

### For End Users

#### Analyzing a PDF

1. Open the application
2. Go to "📂 Analisar PDF" tab
3. **Select diagram type** from the dropdown:
   - Choose "P&ID" for traditional P&ID diagrams
   - Choose "Diagrama Elétrico" for electrical diagrams
4. Upload your PDF file
5. Results will use the appropriate reference database

#### Generating from Prompt

1. Open the application  
2. Go to "🎨 Gerar a partir de Prompt" tab
3. **Select diagram type** from the dropdown:
   - Choose "P&ID" for traditional P&ID diagrams
   - Choose "Diagrama Elétrico" for electrical diagrams
4. Enter your process description
5. Click "Gerar P&ID"
6. Results will use the appropriate reference database

### For Developers

#### Quick Test

Run structure verification:
```bash
cd /path/to/ServiceiPID
python3 test_diagram_type.py
```

Expected output:
```
✅ ALL STRUCTURE TESTS PASSED
```

#### First Run

The application will automatically:
1. Detect which diagram type is selected
2. Load the appropriate reference file:
   - `backend/referencia_systems.xlsx` for P&ID
   - `backend/Referencia_systems_electrical.xlsx` for Electrical
3. Generate embeddings (only on first use)
4. Save embeddings to cache:
   - `backend/ref_embeddings_pid.pkl`
   - `backend/ref_embeddings_electrical.pkl`

#### Subsequent Runs

The application will:
1. Load embeddings from cache (faster startup)
2. Use cached embeddings for matching
3. Only regenerate if cache files are missing

## Files Structure

```
ServiceiPID/
├── backend/
│   ├── backend.py                          ✓ Modified - Added diagram_type parameter
│   ├── system_matcher.py                   ✓ Modified - Dual reference support
│   ├── referencia_systems.xlsx             ✓ Existing - P&ID reference
│   ├── Referencia_systems_electrical.xlsx  ✓ New - Electrical reference
│   ├── ref_embeddings_pid.pkl             ⚡ Auto-generated - P&ID cache
│   └── ref_embeddings_electrical.pkl      ⚡ Auto-generated - Electrical cache
├── frontend/
│   └── app.py                              ✓ Modified - Added selectors
└── Documentation/
    ├── DIAGRAM_TYPE_SELECTION.md           📚 Technical documentation
    ├── DIAGRAM_TYPE_VISUAL_SUMMARY.md      📊 Visual diagrams
    └── BEFORE_AFTER_COMPARISON.md          🔍 Before/after comparison
```

## API Changes

### Backward Compatibility

✅ **Existing code continues to work** - `diagram_type` defaults to "pid"

### New Parameters

Both endpoints now accept `diagram_type`:

**POST /analyze**
```python
POST /analyze?diagram_type=pid          # Default
POST /analyze?diagram_type=electrical   # New option
```

**POST /generate**
```python
POST /generate?prompt=...&diagram_type=pid         # Default
POST /generate?prompt=...&diagram_type=electrical  # New option
```

## Configuration

### Environment Variables (Optional)

Create a `.env` file to customize reference file paths:

```bash
# P&ID reference file path
REF_XLSX_PATH_PID=referencia_systems.xlsx

# Electrical reference file path  
REF_XLSX_PATH_ELECTRICAL=Referencia_systems_electrical.xlsx

# OpenAI API key (required)
OPENAI_API_KEY=your-api-key-here
```

## Troubleshooting

### Cache Issues

If embeddings seem incorrect, delete cache files:
```bash
cd backend
rm ref_embeddings_pid.pkl
rm ref_embeddings_electrical.pkl
```

They will regenerate on next run.

### Reference Files

Both reference files must have these columns:
- `Type` - Equipment/instrument type
- `Descricao` - Description  
- `SystemFullName` - Full system name

### Import Errors

If you see "No module named 'httpx'", install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

## Learn More

- **Technical Details**: See `DIAGRAM_TYPE_SELECTION.md`
- **Visual Diagrams**: See `DIAGRAM_TYPE_VISUAL_SUMMARY.md`
- **Code Changes**: See `BEFORE_AFTER_COMPARISON.md`

## Support

For issues or questions:
1. Check the documentation files listed above
2. Run `python3 test_diagram_type.py` to verify structure
3. Check that both reference files exist in `backend/`
4. Verify `OPENAI_API_KEY` is set in `.env`

---

**Status**: ✅ Complete and ready for production use
**Version**: 1.0 - Diagram Type Selection Feature
**Last Updated**: 2025-10-31
