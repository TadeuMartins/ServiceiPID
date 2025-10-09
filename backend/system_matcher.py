# backend/system_matcher.py
import os
import httpx, certifi
import pandas as pd
import numpy as np
from openai import OpenAI
import pickle


# Config OpenAI
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "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"  # ⚠️ use env var em produção
)
OPENAI_REQUEST_TIMEOUT = int(os.getenv("OPENAI_REQUEST_TIMEOUT", "600"))

def make_client(verify_ssl: bool = True) -> OpenAI:
    http_client = httpx.Client(
        verify=certifi.where() if verify_ssl else False,
        timeout=OPENAI_REQUEST_TIMEOUT,
    )
    return OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

client = make_client(verify_ssl=False)

# Planilha de referência
REF_PATH = os.getenv("REF_XLSX_PATH", "referencia_systems.xlsx")
CACHE_FILE = "ref_embeddings.pkl"

df_ref = pd.read_excel(REF_PATH)

assert all(col in df_ref.columns for col in ["Type", "Descricao", "SystemFullName"]), \
    "Planilha precisa ter colunas: Type, Descricao, SystemFullName"

# Função para criar embeddings
def embed_texts(texts):
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in resp.data]

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

# --- Similaridade ---
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# --- Matcher principal ---
def match_system_fullname(tag: str, descricao: str, tipo: str = "") -> dict:
    try:
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
