# Diagram Type Selection Feature

## Overview

This feature allows users to select between two types of diagrams when analyzing or generating P&IDs:
1. **P&ID (Piping and Instrumentation Diagram)** - Uses `referencia_systems.xlsx`
2. **Electrical Diagram** - Uses `Referencia_systems_electrical.xlsx`

Each diagram type has its own:
- Reference Excel file with system definitions
- Separate embeddings cache file
- Independent system matching logic

## Implementation Details

### Backend Changes

#### 1. `system_matcher.py`

**Key Changes:**
- Split reference data into two separate sets (P&ID and Electrical)
- Created separate cache files for embeddings:
  - `ref_embeddings_pid.pkl` - for P&ID diagrams
  - `ref_embeddings_electrical.pkl` - for electrical diagrams
- Added initialization functions:
  - `_initialize_client()` - Initializes OpenAI client
  - `_initialize_pid()` - Loads P&ID reference data and embeddings
  - `_initialize_electrical()` - Loads Electrical reference data and embeddings
- Updated `match_system_fullname()` to accept `diagram_type` parameter

**Function Signature:**
```python
def match_system_fullname(tag: str, descricao: str, tipo: str = "", diagram_type: str = "pid") -> dict:
    """
    Match system full name based on tag, description, and type.
    
    Args:
        tag: Equipment tag
        descricao: Equipment description
        tipo: Equipment type
        diagram_type: Type of diagram - "pid" for P&ID or "electrical" for Electrical Diagram
    
    Returns:
        Dictionary with SystemFullName, confidence, and reference data
    """
```

**Lazy Initialization:**
- Embeddings are only generated when first needed
- Each diagram type initializes independently
- Cache files prevent re-generation on subsequent runs

#### 2. `backend.py`

**API Endpoints Updated:**

**POST /analyze**
- Added `diagram_type` query parameter (default: "pid")
- Parameter is passed to `match_system_fullname()` for each detected item
- Added `diagram_type` to error responses

**POST /generate**
- Added `diagram_type` query parameter (default: "pid")
- Parameter is passed to `match_system_fullname()` for each generated item
- Added `diagram_type` to error responses

### Frontend Changes

#### `app.py`

**Tab 1 - Analyze PDF:**
- Added selectbox for diagram type selection
- Options: "P&ID" (value: "pid"), "Diagrama Elétrico" (value: "electrical")
- Selected value is sent to `/analyze` endpoint

**Tab 2 - Generate from Prompt:**
- Added selectbox for diagram type selection
- Options: "P&ID" (value: "pid"), "Diagrama Elétrico" (value: "electrical")
- Selected value is sent to `/generate` endpoint

## User Flow

### Analyzing a PDF

1. User uploads a PDF file
2. User selects diagram type from dropdown:
   - "P&ID" - for traditional P&ID diagrams
   - "Diagrama Elétrico" - for electrical diagrams
3. System processes the PDF and uses the appropriate reference file for system matching
4. Results show `SystemFullName` matched against the correct reference database

### Generating from Prompt

1. User enters process description
2. User selects diagram type from dropdown:
   - "P&ID" - for traditional P&ID diagrams
   - "Diagrama Elétrico" - for electrical diagrams
3. System generates equipment list and matches against the appropriate reference file
4. Results show `SystemFullName` matched against the correct reference database

## Technical Details

### Embeddings Cache

**P&ID Cache:** `backend/ref_embeddings_pid.pkl`
- Generated from `referencia_systems.xlsx`
- Lazily initialized on first use
- Persists across application restarts

**Electrical Cache:** `backend/ref_embeddings_electrical.pkl`
- Generated from `Referencia_systems_electrical.xlsx`
- Lazily initialized on first use
- Persists across application restarts

### Reference Files

Both files must have the following columns:
- `Type` - Equipment/instrument type
- `Descricao` - Description
- `SystemFullName` - Full system name (COMOS format)

**Location:**
- `backend/referencia_systems.xlsx` - P&ID reference
- `backend/Referencia_systems_electrical.xlsx` - Electrical reference

## Testing

Run structure verification test:
```bash
python3 test_diagram_type.py
```

This verifies:
- Reference files exist
- Python files compile
- Code structure is correct
- Required variables and functions are defined
- API parameters are correctly configured

Note: Full integration testing requires `OPENAI_API_KEY` environment variable.

## Environment Variables

Optional configuration via `.env`:
- `REF_XLSX_PATH_PID` - Custom path for P&ID reference (default: "referencia_systems.xlsx")
- `REF_XLSX_PATH_ELECTRICAL` - Custom path for Electrical reference (default: "Referencia_systems_electrical.xlsx")

## Troubleshooting

**Problem:** Embeddings not being generated
**Solution:** Ensure `OPENAI_API_KEY` is set in `.env` file

**Problem:** Wrong reference being used
**Solution:** Check that the `diagram_type` parameter is correctly passed from frontend to backend

**Problem:** Cache files growing too large
**Solution:** Delete `.pkl` cache files - they will be regenerated on next use

## Future Enhancements

Potential improvements:
- Add more diagram types (e.g., electrical single-line, instrumentation loop diagrams)
- Allow users to upload custom reference files
- Provide confidence thresholds for system matching
- Add batch processing for multiple diagram types
