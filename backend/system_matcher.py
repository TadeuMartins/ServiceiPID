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

# Get the directory where this file is located
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Planilhas de referência - resolve paths relative to backend directory
REF_PATH_PID = os.getenv("REF_XLSX_PATH_PID", os.path.join(BACKEND_DIR, "referencia_systems.xlsx"))
REF_PATH_ELECTRICAL = os.getenv("REF_XLSX_PATH_ELECTRICAL", os.path.join(BACKEND_DIR, "Referencia_systems_electrical.xlsx"))
CACHE_FILE_PID = os.path.join(BACKEND_DIR, "ref_embeddings_pid.pkl")
CACHE_FILE_ELECTRICAL = os.path.join(BACKEND_DIR, "ref_embeddings_electrical.pkl")

# Global variables for lazy initialization
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
    global client
    
    if client is not None:
        return  # Already initialized
    
    # Check if API key is valid
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY não definido. Configure a chave no arquivo .env")
    
    client = make_client(verify_ssl=False)


def _initialize_pid():
    """Initialize P&ID reference data and embeddings lazily."""
    global df_ref_pid, ref_embeddings_pid, ref_texts_pid
    
    if df_ref_pid is not None:
        return  # Already initialized
    
    _initialize_client()
    
    df_ref_pid = pd.read_excel(REF_PATH_PID)
    
    assert all(col in df_ref_pid.columns for col in ["Type", "Descricao", "SystemFullName"]), \
        "Planilha P&ID precisa ter colunas: Type, Descricao, SystemFullName"
    
    # Carrega cache se existir, senão gera e salva
    ref_texts_pid = (df_ref_pid["Type"].fillna("") + " " + df_ref_pid["Descricao"].fillna("")).tolist()
    
    # Validate that we have non-empty texts
    valid_texts = [text.strip() for text in ref_texts_pid if text.strip()]
    if not valid_texts:
        raise ValueError(f"Planilha P&ID ({REF_PATH_PID}) não contém textos válidos para criar embeddings")
    
    if os.path.exists(CACHE_FILE_PID):
        with open(CACHE_FILE_PID, "rb") as f:
            ref_embeddings_pid = pickle.load(f)
        print(f"📂 Embeddings P&ID carregados do cache: {len(ref_embeddings_pid)} itens")
    else:
        ref_embeddings_pid = embed_texts(ref_texts_pid)
        with open(CACHE_FILE_PID, "wb") as f:
            pickle.dump(ref_embeddings_pid, f)
        print(f"✅ Embeddings P&ID gerados e salvos em cache: {len(ref_embeddings_pid)} itens")
    
    ref_embeddings_pid = np.array(ref_embeddings_pid)


def _initialize_electrical():
    """Initialize Electrical diagram reference data and embeddings lazily."""
    global df_ref_electrical, ref_embeddings_electrical, ref_texts_electrical
    
    if df_ref_electrical is not None:
        return  # Already initialized
    
    _initialize_client()
    
    df_ref_electrical = pd.read_excel(REF_PATH_ELECTRICAL)
    
    assert all(col in df_ref_electrical.columns for col in ["Type", "Descricao", "SystemFullName"]), \
        "Planilha Electrical precisa ter colunas: Type, Descricao, SystemFullName"
    
    # Carrega cache se existir, senão gera e salva
    ref_texts_electrical = (df_ref_electrical["Type"].fillna("") + " " + df_ref_electrical["Descricao"].fillna("")).tolist()
    
    # Validate that we have non-empty texts
    valid_texts = [text.strip() for text in ref_texts_electrical if text.strip()]
    if not valid_texts:
        raise ValueError(f"Planilha Electrical ({REF_PATH_ELECTRICAL}) não contém textos válidos para criar embeddings")
    
    if os.path.exists(CACHE_FILE_ELECTRICAL):
        with open(CACHE_FILE_ELECTRICAL, "rb") as f:
            ref_embeddings_electrical = pickle.load(f)
        print(f"📂 Embeddings Electrical carregados do cache: {len(ref_embeddings_electrical)} itens")
    else:
        ref_embeddings_electrical = embed_texts(ref_texts_electrical)
        with open(CACHE_FILE_ELECTRICAL, "wb") as f:
            pickle.dump(ref_embeddings_electrical, f)
        print(f"✅ Embeddings Electrical gerados e salvos em cache: {len(ref_embeddings_electrical)} itens")
    
    ref_embeddings_electrical = np.array(ref_embeddings_electrical)


def ensure_embeddings_exist():
    """
    Ensure embeddings exist for both P&ID and Electrical diagrams.
    Called on backend startup to initialize embeddings if they don't exist.
    """
    try:
        print("🔍 Verificando embeddings...")
        
        # Check and initialize P&ID embeddings
        if not os.path.exists(CACHE_FILE_PID):
            print(f"⚠️  Cache de embeddings P&ID não encontrado. Criando...")
            try:
                _initialize_pid()
            except Exception as e:
                print(f"❌ Erro ao criar embeddings P&ID: {e}, por favor verifique.")
                raise
        else:
            print(f"✅ Cache de embeddings P&ID encontrado: {CACHE_FILE_PID}")
        
        # Check and initialize Electrical embeddings
        if not os.path.exists(CACHE_FILE_ELECTRICAL):
            print(f"⚠️  Cache de embeddings Electrical não encontrado. Criando...")
            try:
                _initialize_electrical()
            except Exception as e:
                print(f"❌ Erro ao criar embeddings Electrical: {e}, por favor verifique.")
                raise
        else:
            print(f"✅ Cache de embeddings Electrical encontrado: {CACHE_FILE_ELECTRICAL}")
        
        print("✅ Verificação de embeddings concluída")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar embeddings: {e}, por favor verifique.")
        return False

# Função para criar embeddings
def embed_texts(texts):
    """
    Create embeddings for a list of texts.
    
    Args:
        texts: List of strings to embed
        
    Returns:
        List of embeddings (list of floats)
        
    Raises:
        ValueError: If texts is empty or contains only empty strings
    """
    _initialize_client()
    
    # Validate input
    if not texts:
        raise ValueError("Cannot create embeddings for empty text list")
    
    # Convert to strings and filter out empty entries
    valid_texts = []
    for text in texts:
        text_str = str(text).strip()
        if text_str:
            valid_texts.append(text_str)
    
    if not valid_texts:
        raise ValueError("Cannot create embeddings: all texts are empty after filtering")
    
    # Log if we filtered out some texts
    if len(valid_texts) != len(texts):
        print(f"⚠️  Filtered {len(texts) - len(valid_texts)} empty texts from embedding input")
    
    # Batch the requests to avoid API limits (max 2048 inputs per request)
    batch_size = 2000  # Conservative batch size
    all_embeddings = []
    
    for i in range(0, len(valid_texts), batch_size):
        batch = valid_texts[i:i + batch_size]
        print(f"🔄 Criando embeddings para batch {i//batch_size + 1}/{(len(valid_texts) + batch_size - 1)//batch_size} ({len(batch)} textos)...")
        
        try:
            resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            batch_embeddings = [d.embedding for d in resp.data]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"❌ Erro ao criar embeddings para batch {i//batch_size + 1}: {e}")
            raise
    
    return all_embeddings

# --- Similaridade ---
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Handle edge cases: zero vectors or invalid norms
    # Use a small epsilon for robust zero detection with floating-point numbers
    eps = np.finfo(float).eps
    if norm_a < eps or norm_b < eps or not np.isfinite(norm_a) or not np.isfinite(norm_b):
        return 0.0
    
    similarity = np.dot(a, b) / (norm_a * norm_b)
    
    # Ensure the result is finite and within valid range
    if not np.isfinite(similarity):
        return 0.0
    
    return float(similarity)

# --- Matcher principal ---
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
    try:
        # Initialize appropriate reference data based on diagram type
        if diagram_type.lower() == "electrical":
            _initialize_electrical()
            df_ref = df_ref_electrical
            ref_embeddings = ref_embeddings_electrical
            diagram_label = "Electrical"
        else:
            # Default to P&ID
            _initialize_pid()
            df_ref = df_ref_pid
            ref_embeddings = ref_embeddings_pid
            diagram_label = "P&ID"
        
        query_text = f"{tipo} {tag} {descricao}".strip()
        emb_q = client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text
        ).data[0].embedding

        sims = [cosine_similarity(emb_q, emb_ref) for emb_ref in ref_embeddings]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])

        ref_row = df_ref.iloc[best_idx]

        return {
            "SystemFullName": ref_row["SystemFullName"],
            "Confiança": round(best_score, 4),
            "Tipo_ref": ref_row["Type"],
            "Descricao_ref": ref_row["Descricao"],
            "diagram_type": diagram_label
        }
    except Exception as e:
        return {
            "SystemFullName": None,
            "Confiança": 0.0,
            "Tipo_ref": tipo or "N/A",
            "Descricao_ref": descricao or "N/A",
            "matcher_error": str(e),
            "diagram_type": diagram_type
        }

