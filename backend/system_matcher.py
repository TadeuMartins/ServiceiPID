# backend/system_matcher.py
import os
import httpx, certifi
import pandas as pd
import numpy as np
from openai import OpenAI
import pickle
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Config OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REQUEST_TIMEOUT = int(os.getenv("OPENAI_REQUEST_TIMEOUT", "600"))

def make_client(verify_ssl: bool = True) -> OpenAI:
    http_client = httpx.Client(
        verify=certifi.where() if verify_ssl else False,
        timeout=OPENAI_REQUEST_TIMEOUT,
    )
    return OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

# Planilha de referência
REF_PATH = os.getenv("REF_XLSX_PATH", "referencia_systems.xlsx")
CACHE_FILE = "ref_embeddings.pkl"

# Global variables for lazy initialization
client = None
df_ref = None
ref_embeddings = None
ref_texts = None

def _initialize():
    """Initialize client and load/create embeddings lazily."""
    global client, df_ref, ref_embeddings, ref_texts
    
    if client is not None:
        return  # Already initialized
    
    # Check if API key is valid
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY não definido. Configure a chave no arquivo .env")
    
    client = make_client(verify_ssl=False)
    
    df_ref = pd.read_excel(REF_PATH)
    
    assert all(col in df_ref.columns for col in ["Type", "Descricao", "SystemFullName"]), \
        "Planilha precisa ter colunas: Type, Descricao, SystemFullName"
    
    # Carrega cache se existir, senão gera e salva
    ref_texts = (df_ref["Type"].fillna("") + " " + df_ref["Descricao"].fillna("")).tolist()
    
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            ref_embeddings = pickle.load(f)
        print(f"📂 Embeddings carregados do cache: {len(ref_embeddings)} itens")
    else:
        ref_embeddings = embed_texts(ref_texts)
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(ref_embeddings, f)
        print(f"✅ Embeddings gerados e salvos em cache: {len(ref_embeddings)} itens")
    
    ref_embeddings = np.array(ref_embeddings)

# Função para criar embeddings
def embed_texts(texts):
    if client is None:
        _initialize()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in resp.data]

# --- Similaridade ---
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Handle edge cases: zero vectors or invalid norms
    if norm_a == 0 or norm_b == 0 or not np.isfinite(norm_a) or not np.isfinite(norm_b):
        return 0.0
    
    similarity = np.dot(a, b) / (norm_a * norm_b)
    
    # Ensure the result is finite and within valid range
    if not np.isfinite(similarity):
        return 0.0
    
    return float(similarity)

# --- Matcher principal ---
def match_system_fullname(tag: str, descricao: str, tipo: str = "") -> dict:
    try:
        # Initialize on first use
        if client is None:
            _initialize()
        
        query_text = f"{tipo} {tag} {descricao}".strip()
        emb_q = client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text
        ).data[0].embedding

        sims = [cosine_similarity(emb_q, emb_ref) for emb_ref in ref_embeddings]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        
        # Ensure best_score is JSON-compliant (not NaN or Infinity)
        if not np.isfinite(best_score):
            best_score = 0.0

        ref_row = df_ref.iloc[best_idx]

        return {
            "SystemFullName": ref_row["SystemFullName"],
            "Confiança": round(best_score, 4),
            "Tipo_ref": ref_row["Type"],
            "Descricao_ref": ref_row["Descricao"]
        }
    except Exception as e:
        return {
            "SystemFullName": None,
            "Confiança": 0.0,
            "Tipo_ref": tipo or "N/A",
            "Descricao_ref": descricao or "N/A",
            "matcher_error": str(e)
        }

