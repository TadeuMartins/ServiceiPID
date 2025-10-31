# Before & After: Diagram Type Selection Feature

## Problem Statement (Portuguese)

> Eu adicionei um novo arquivo no backend com o nome de Referencia_systems_electrical.xlsx, ele é exclusivo para encontrar o system full name quando trata-se de um diagrama elétrico, então preciso que você coloque uma seleção no front end para o usuario escolher entre P&ID e Diagrama elétrico, se for P&ID no final ele vai fazer o system matcher com o Referencia_systems, se for diagrama no final ele precisa fazer o system matcher com o Referencia_systems_electrical.xlsx, portanto é necessário garantir que existam 2 embeddings diferentes dependendo da aplicação.

## Translation

> I added a new file in the backend named Referencia_systems_electrical.xlsx, it is exclusive for finding the system full name when dealing with an electrical diagram, so I need you to add a selection in the front end for the user to choose between P&ID and Electrical Diagram. If it's P&ID, in the end it will do the system matcher with Referencia_systems, if it's a diagram in the end it needs to do the system matcher with Referencia_systems_electrical.xlsx, therefore it is necessary to ensure that there are 2 different embeddings depending on the application.

---

## Before

### System Matcher (backend/system_matcher.py)

```python
# OLD - Single reference file
REF_PATH = os.getenv("REF_XLSX_PATH", "referencia_systems.xlsx")
CACHE_FILE = "ref_embeddings.pkl"

# OLD - Single set of global variables
client = None
df_ref = None
ref_embeddings = None
ref_texts = None

def _initialize():
    """Initialize client and load/create embeddings lazily."""
    global client, df_ref, ref_embeddings, ref_texts
    # ... loads only one reference file

def match_system_fullname(tag: str, descricao: str, tipo: str = "") -> dict:
    """OLD - No diagram type parameter"""
    # ... uses single reference
```

### Backend API (backend/backend.py)

```python
# OLD - No diagram type selection
@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile,
    dpi: int = Query(400, ge=100, le=600),
    grid: int = Query(3, ge=1, le=6),
    # ... no diagram_type parameter
):
    # ...
    match = match_system_fullname(item["tag"], item["descricao"], tipo)
    # ^^^^^^^^^ No diagram_type passed
```

### Frontend (frontend/app.py)

```python
# OLD - No diagram type selector
with tab1:
    st.markdown("### Analise um P&ID existente")
    uploaded_file = st.file_uploader("📂 Envie um arquivo PDF de P&ID", type=["pdf"])
    # ^^^^^^^^^ No selector for diagram type

# OLD - API call without diagram_type
files = {"file": uploaded_file.getvalue()}
response = requests.post(API_URL, files=files, timeout=3600)
# ^^^^^^^^^ No diagram_type parameter
```

---

## After

### System Matcher (backend/system_matcher.py)

```python
# NEW - Separate reference files for each diagram type
REF_PATH_PID = os.getenv("REF_XLSX_PATH_PID", "referencia_systems.xlsx")
REF_PATH_ELECTRICAL = os.getenv("REF_XLSX_PATH_ELECTRICAL", "Referencia_systems_electrical.xlsx")
CACHE_FILE_PID = "ref_embeddings_pid.pkl"
CACHE_FILE_ELECTRICAL = "ref_embeddings_electrical.pkl"

# NEW - Separate global variables for each diagram type
client = None

# P&ID reference data
df_ref_pid = None
ref_embeddings_pid = None
ref_texts_pid = None

# Electrical diagram reference data
df_ref_electrical = None
ref_embeddings_electrical = None
ref_texts_electrical = None

def _initialize_client():
    """Initialize OpenAI client."""
    # ... client initialization

def _initialize_pid():
    """Initialize P&ID reference data and embeddings lazily."""
    # ... loads referencia_systems.xlsx and pid embeddings

def _initialize_electrical():
    """Initialize Electrical diagram reference data and embeddings lazily."""
    # ... loads Referencia_systems_electrical.xlsx and electrical embeddings

def match_system_fullname(tag: str, descricao: str, tipo: str = "", diagram_type: str = "pid") -> dict:
    """NEW - With diagram_type parameter"""
    # Initialize appropriate reference data based on diagram type
    if diagram_type.lower() == "electrical":
        _initialize_electrical()
        df_ref = df_ref_electrical
        ref_embeddings = ref_embeddings_electrical
        diagram_label = "Electrical"
    else:
        _initialize_pid()
        df_ref = df_ref_pid
        ref_embeddings = ref_embeddings_pid
        diagram_label = "P&ID"
    
    # ... uses selected reference
```

### Backend API (backend/backend.py)

```python
# NEW - With diagram type selection
@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile,
    dpi: int = Query(400, ge=100, le=600),
    grid: int = Query(3, ge=1, le=6),
    # ... other parameters
    diagram_type: str = Query("pid", description="Diagram type: 'pid' for P&ID or 'electrical' for Electrical Diagram")
    # ^^^^^^^^^ NEW parameter
):
    # ...
    match = match_system_fullname(item["tag"], item["descricao"], tipo, diagram_type)
    # ^^^^^^^^^ diagram_type now passed to matcher
```

### Frontend (frontend/app.py)

```python
# NEW - With diagram type selector
with tab1:
    st.markdown("### Analise um P&ID existente")
    
    # NEW - Diagram type selector
    diagram_type_analyze = st.selectbox(
        "Tipo de Diagrama:",
        options=[("P&ID", "pid"), ("Diagrama Elétrico", "electrical")],
        format_func=lambda x: x[0],
        key="diagram_type_analyze",
        help="Selecione o tipo de diagrama para usar a referência apropriada no system matcher"
    )
    # ^^^^^^^^^ NEW selector for diagram type
    
    uploaded_file = st.file_uploader("📂 Envie um arquivo PDF de P&ID", type=["pdf"])

# NEW - API call with diagram_type
files = {"file": uploaded_file.getvalue()}
diagram_type_value = diagram_type_analyze[1]  # Extract the value from tuple
params = {"diagram_type": diagram_type_value}
response = requests.post(API_URL, files=files, params=params, timeout=3600)
# ^^^^^^^^^ diagram_type parameter now sent to backend
```

---

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Reference Files** | Single file (referencia_systems.xlsx) | Two files (referencia_systems.xlsx + Referencia_systems_electrical.xlsx) |
| **Embeddings** | Single embedding cache | Two separate embedding caches (pid + electrical) |
| **User Selection** | No choice - always uses P&ID | Dropdown to select P&ID or Electrical |
| **Backend API** | No diagram_type parameter | diagram_type parameter in both /analyze and /generate |
| **System Matching** | Always matches against P&ID reference | Matches against selected reference type |
| **Initialization** | Single initialization function | Three functions: client, pid, electrical |
| **Cache Files** | ref_embeddings.pkl | ref_embeddings_pid.pkl + ref_embeddings_electrical.pkl |

---

## User Experience Flow

### Before
```
User → Upload PDF → System uses P&ID reference → Results
                    (no choice, always P&ID)
```

### After
```
User → Select "P&ID" or "Diagrama Elétrico" → Upload PDF → System uses selected reference → Results
       ↓                                                     ↓
   P&ID selected                                    Uses referencia_systems.xlsx
       ↓                                                     +
   Electrical selected                               ref_embeddings_pid.pkl
                                                            OR
                                                    Uses Referencia_systems_electrical.xlsx
                                                            +
                                                    ref_embeddings_electrical.pkl
```

---

## Files Modified

1. ✅ `backend/system_matcher.py` - Core matching logic with dual references
2. ✅ `backend/backend.py` - API endpoints with diagram_type parameter
3. ✅ `frontend/app.py` - UI with diagram type selectors

## Files Created

1. ✅ `DIAGRAM_TYPE_SELECTION.md` - Technical documentation
2. ✅ `DIAGRAM_TYPE_VISUAL_SUMMARY.md` - Visual diagrams and flows
3. ✅ `test_diagram_type.py` - Structure verification tests
4. ✅ `BEFORE_AFTER_COMPARISON.md` - This file

## Files Updated

1. ✅ `.gitignore` - Added cache files and test file exclusions

---

## Testing

All structure verification tests passed:
- ✅ Reference files exist in backend/
- ✅ All Python files compile successfully
- ✅ Code structure includes all required variables and functions
- ✅ API parameters correctly configured
- ✅ Frontend selectors present and functional

---

## Result

✅ **Task completed successfully!**

The application now supports both P&ID and Electrical diagrams with:
- Separate reference files for each type
- Independent embeddings for accurate matching
- User-friendly selection in the frontend
- Clean separation of concerns in the code
- Comprehensive documentation for future maintenance
