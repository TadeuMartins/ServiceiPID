# Diagram Type Selection - Visual Summary

## Frontend UI

### Tab 1: Analyze PDF

```
┌─────────────────────────────────────────────────────────────┐
│  📂 Analisar PDF                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tipo de Diagrama:                                          │
│  ┌───────────────────────────────────┐                      │
│  │ P&ID                          ▼ │  <-- NEW SELECTOR!   │
│  └───────────────────────────────────┘                      │
│     Options:                                                │
│     • P&ID                                                  │
│     • Diagrama Elétrico                                     │
│                                                             │
│  📂 Envie um arquivo PDF de P&ID                            │
│  ┌───────────────────────────────────┐                      │
│  │  Choose file...              📁  │                      │
│  └───────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Tab 2: Generate from Prompt

```
┌─────────────────────────────────────────────────────────────┐
│  🎨 Gerar a partir de Prompt                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tipo de Diagrama:                                          │
│  ┌───────────────────────────────────┐                      │
│  │ P&ID                          ▼ │  <-- NEW SELECTOR!   │
│  └───────────────────────────────────┘                      │
│     Options:                                                │
│     • P&ID                                                  │
│     • Diagrama Elétrico                                     │
│                                                             │
│  Descreva o processo:                                       │
│  ┌───────────────────────────────────┐                      │
│  │ Ex: gere um P&ID completo de     │                      │
│  │ um processo de clinquerização    │                      │
│  └───────────────────────────────────┘                      │
│                                                             │
│  [ 🎨 Gerar P&ID ]                                          │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│   Frontend   │
│   (app.py)   │
└──────┬───────┘
       │
       │ 1. User selects diagram type: "P&ID" or "Diagrama Elétrico"
       │ 2. User uploads PDF or enters prompt
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                      API Request                              │
│  POST /analyze?diagram_type=pid                              │
│    or                                                         │
│  POST /generate?prompt=...&diagram_type=electrical           │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Backend    │
│ (backend.py) │
└──────┬───────┘
       │
       │ For each equipment/instrument detected:
       │
       ▼
┌────────────────────────────────────────────────────────────┐
│  match_system_fullname(tag, descricao, tipo, diagram_type) │
└──────┬─────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│   system_matcher.py      │
└──────┬───────────────────┘
       │
       ├─ if diagram_type == "pid":
       │     ├─ Load: referencia_systems.xlsx
       │     ├─ Cache: ref_embeddings_pid.pkl
       │     └─ Use: P&ID embeddings
       │
       └─ if diagram_type == "electrical":
             ├─ Load: Referencia_systems_electrical.xlsx
             ├─ Cache: ref_embeddings_electrical.pkl
             └─ Use: Electrical embeddings
```

## Embedding Cache Files

```
backend/
├── referencia_systems.xlsx           ◄─── P&ID Reference
├── Referencia_systems_electrical.xlsx ◄─── Electrical Reference
├── ref_embeddings_pid.pkl            ◄─── P&ID Embeddings Cache (auto-generated)
└── ref_embeddings_electrical.pkl     ◄─── Electrical Embeddings Cache (auto-generated)
```

## System Matching Process

```
User Input: "Motor M-101"
     │
     ▼
┌─────────────────────────────────┐
│  diagram_type = "electrical"    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 1. Initialize Electrical Reference          │
│    - Load Referencia_systems_electrical.xlsx│
│    - Load/Generate electrical embeddings    │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 2. Create Query Embedding                   │
│    - Text: "Equipment Motor M-101"          │
│    - Generate embedding using OpenAI        │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 3. Calculate Similarity                     │
│    - Compare with all electrical embeddings │
│    - Find best match using cosine similarity│
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 4. Return Result                            │
│    - SystemFullName: @30|M41|A50|A10|...    │
│    - Confidence: 0.8534                     │
│    - diagram_type: "Electrical"             │
└─────────────────────────────────────────────┘
```

## Key Features

✅ **Separate Embeddings**: Each diagram type has its own embedding cache
✅ **Lazy Loading**: Embeddings only generated when first needed
✅ **Persistent Cache**: `.pkl` files prevent regeneration on restart
✅ **User-Friendly**: Frontend shows localized labels
✅ **Type Safety**: Backend validates diagram_type parameter
✅ **Backward Compatible**: Default value is "pid" for existing workflows

## Benefits

1. **Accuracy**: Using specialized reference data improves system matching
2. **Performance**: Cached embeddings speed up subsequent requests
3. **Flexibility**: Easy to add more diagram types in the future
4. **Clarity**: Clear separation between P&ID and electrical diagrams
5. **User Experience**: Simple dropdown selection, no configuration needed
