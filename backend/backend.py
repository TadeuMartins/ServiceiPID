import os
import re
import json
import math
import base64
import traceback
import time
import asyncio
from typing import List, Any, Dict, Tuple
from PIL import Image, ImageEnhance, ImageOps
import io

import fitz  # PyMuPDF
import httpx, certifi
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, Query
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import OpenAI
from system_matcher import match_system_fullname

# Load environment variables from .env file
load_dotenv()

# =================================================
# 🔑 CONFIG OPENAI
# =================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-5")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-4o")
OPENAI_REQUEST_TIMEOUT = int(os.getenv("OPENAI_REQUEST_TIMEOUT", "600"))


def make_client(verify_ssl: bool = True) -> OpenAI:
    http_client = httpx.Client(
        verify=certifi.where() if verify_ssl else False,
        timeout=OPENAI_REQUEST_TIMEOUT,
    )
    # Only create client if API key is set
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)


client = make_client(verify_ssl=True)

# ============================================================
# FASTAPI CONFIG
# ============================================================
app = FastAPI(title="P&ID Digitalizer Backend (Quadrants Paralelos + SSE Logs)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================
# LOGS SSE
# ============================================================
progress_messages: List[str] = []

# ============================================================
# KNOWLEDGE BASE - Armazena descrições de P&IDs analisados
# ============================================================
pid_knowledge_base: Dict[str, Dict[str, Any]] = {}

# Configuração do modo do chatbot
# "text" = usa descrição ultra-completa + lista de equipamentos (mais rápido, mais barato)
# "vision" = envia imagem do P&ID com cada pergunta (mais preciso, mais caro)
# "hybrid" = decide automaticamente baseado no tipo de pergunta
CHATBOT_MODE = os.getenv("CHATBOT_MODE", "hybrid")


def log_to_front(msg: str) -> None:
    print(msg, flush=True)
    progress_messages.append(msg)


@app.get("/progress")
def get_progress():
    def event_stream():
        last_index = 0
        while True:
            while last_index < len(progress_messages):
                yield f"data: {progress_messages[last_index]}\n\n"
                last_index += 1
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================
# STARTUP CHECK
# ============================================================
@app.on_event("startup")
async def startup_event():
    if not OPENAI_API_KEY:
        log_to_front("❌ OPENAI_API_KEY não definido. Configure a chave no arquivo .env")
        return
    try:
        models = client.models.list()
        ids = [m.id for m in models.data]
        log_to_front("✅ Conexão OpenAI OK. Modelos detectados: " + ", ".join(ids[:8]))
    except Exception as e:
        log_to_front(f"❌ Erro SSL verificado: {e}")
        try:
            new_client = make_client(verify_ssl=False)
            models = new_client.models.list()
            ids = [m.id for m in models.data]
            log_to_front("⚠️ Conexão sem SSL. Modelos: " + ", ".join(ids[:8]))
            globals()["client"] = new_client
        except Exception as e2:
            log_to_front(f"❌ Falha também sem SSL: {e2}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ping")
def ping():
    return {
        "status": "ok",
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "timeout_s": OPENAI_REQUEST_TIMEOUT,
    }


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def points_to_mm(points: float) -> float:
    return round(points * 0.3528, 3)


def clean_markdown_fences(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned[:4].lower() == "json":
            cleaned = cleaned[4:].strip()
    return cleaned


def extract_first_json_array(text: str) -> str:
    pattern = re.compile(r"\[\s*(?:\{.*?\}\s*,\s*)*\{.*?\}\s*\]|\[\s*\]", re.DOTALL)
    m = pattern.search(text)
    if not m:
        raise ValueError("Nenhum JSON array encontrado.")
    return m.group(0)


def ensure_json_list(content: str) -> List[Any]:
    if not content:
        return []
    cleaned = clean_markdown_fences(content)
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, list):
                    return v
    except Exception:
        pass
    try:
        arr = extract_first_json_array(cleaned)
        obj = json.loads(arr)
        if isinstance(obj, list):
            return obj
    except Exception:
        pass
    return []


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize data structure to ensure all float values are JSON-compliant.
    Replaces NaN and Infinity with 0.0.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    else:
        return obj


def dist_mm(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dedup_items(items: List[Dict[str, Any]], page_num: int, tol_mm: float = 10.0) -> List[Dict[str, Any]]:
    """
    Remove duplicatas com base em TAG e proximidade espacial.
    
    Estratégia:
    1. Normaliza todos os campos
    2. Para cada item, verifica se já existe um item com:
       - Mesma TAG na mesma página (se TAG não for N/A) OU
       - Mesmo TAG E coordenadas muito próximas (dentro de tol_mm)
    3. Se já existe, descarta o novo item (mantém o primeiro)
    4. Se não existe, mantém o item
    
    IMPORTANTE: Itens com TAGs diferentes NÃO são considerados duplicatas,
    mesmo se estiverem próximos espacialmente.
    """
    # Normaliza todos os itens primeiro
    for it in items:
        it["pagina"] = int(round(float(it.get("pagina", page_num)) or page_num))
        try:
            it["x_mm"] = float(it.get("x_mm", 0.0))
            it["y_mm"] = float(it.get("y_mm", 0.0))
        except Exception:
            it["x_mm"], it["y_mm"] = 0.0, 0.0
        if not isinstance(it.get("tag", ""), str):
            it["tag"] = "N/A"
        if not isinstance(it.get("descricao", ""), str):
            it["descricao"] = "Equipamento"
    
    final: List[Dict[str, Any]] = []
    seen_tags = {}  # Maps (tag, page) -> list of positions
    
    for it in items:
        tag = it.get("tag", "").strip().upper()
        pos = (it["x_mm"], it["y_mm"])
        page = it["pagina"]
        
        is_duplicate = False
        
        # Para itens com TAG válida (não N/A)
        if tag and tag != "N/A":
            tag_key = (tag, page)
            
            # Verifica se já existe esse mesmo TAG
            if tag_key in seen_tags:
                # Verifica se está próximo de alguma posição existente com MESMO TAG
                for existing_pos in seen_tags[tag_key]:
                    if dist_mm(pos, existing_pos) <= tol_mm:
                        is_duplicate = True
                        break
                
                # Se não está próximo de nenhuma posição existente com mesmo TAG,
                # pode ser uma segunda ocorrência do mesmo equipamento (ex: P-101A e P-101B)
                # Neste caso, não é duplicata
                if not is_duplicate:
                    seen_tags[tag_key].append(pos)
            else:
                # Primeira ocorrência deste TAG
                seen_tags[tag_key] = [pos]
        
        # Para itens sem TAG (N/A), verifica proximidade com QUALQUER item existente
        else:
            for existing in final:
                if existing["pagina"] == page:
                    existing_pos = (existing["x_mm"], existing["y_mm"])
                    if dist_mm(pos, existing_pos) <= tol_mm:
                        # Item sem TAG muito próximo de outro item - provavelmente duplicata
                        is_duplicate = True
                        break
        
        # Se não é duplicata, adiciona à lista final
        if not is_duplicate:
            final.append(it)
    
    return final


# ============================================================
# SUBDIVISÃO EM QUADRANTES
# ============================================================
def page_quadrants(page: fitz.Page, grid_x: int = 3, grid_y: int = 3):
    W, H = page.rect.width, page.rect.height
    if H > W:
        W, H = H, W
    quads = []
    for gy in range(grid_y):
        for gx in range(grid_x):
            x0 = (W / grid_x) * gx
            y0 = (H / grid_y) * gy
            x1 = x0 + (W / grid_x)
            y1 = y0 + (H / grid_y)
            rect = fitz.Rect(x0, y0, x1, y1)
            rect = fitz.Rect(
                max(page.rect.x0, rect.x0),
                max(page.rect.y0, rect.y0),
                min(page.rect.x1, rect.x1),
                min(page.rect.y1, rect.y1),
            )
            if rect.width > 0 and rect.height > 0:
                quads.append((gx, gy, rect))
    return quads


def preprocess_image(img_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.point(lambda p: 255 if p > 180 else 0)
    if img.getpixel((0, 0)) < 128:
        img = ImageOps.invert(img)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=False)
    result = out.getvalue()
    
    # Validate the PNG can be read back
    try:
        Image.open(io.BytesIO(result))
    except Exception as e:
        raise ValueError(f"Generated invalid PNG: {e}")
    
    return result


def render_quadrant_png(page: fitz.Page, rect: fitz.Rect, dpi: int = 400) -> bytes:
    try:
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        raw_bytes = pix.tobytes("png")
        processed_bytes = preprocess_image(raw_bytes)
        if not processed_bytes or len(processed_bytes) == 0:
            raise ValueError("Processed image is empty")
        return processed_bytes
    except Exception as e:
        log_to_front(f"   ⚠️ Erro ao renderizar quadrante: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise


# ============================================================
# PROMPT BUILDER
# ============================================================
def build_prompt(width_mm: float, height_mm: float, scope: str = "global", origin=(0, 0), quad_label: str = "") -> str:
    if height_mm > width_mm:
        width_mm, height_mm = height_mm, width_mm

    base = f"""
Você é um engenheiro especialista em diagramas P&ID (Piping and Instrumentation Diagram) e símbolos ISA S5.1/S5.2/S5.3.

ANÁLISE DE FLUXOGRAMA DE PROCESSO - ESPECIFICAÇÕES TÉCNICAS:"""
    
    if scope == "global":
        base += f"""
- Dimensões da imagem: {width_mm} mm (largura X) x {height_mm} mm (altura Y)
- Sistema de coordenadas: ABSOLUTO da página completa
- Origem: Topo superior esquerdo é o ponto (0, 0)
- Orientação: X crescente da esquerda para direita, Y crescente de cima para baixo
- X: 0.0 (extrema esquerda) até {width_mm} (extrema direita)
- Y: 0.0 (topo da página) até {height_mm} (base da página)
"""
    else:  # quadrant
        ox, oy = origin
        base += f"""
- VOCÊ ESTÁ ANALISANDO APENAS O QUADRANTE {quad_label} DA PÁGINA COMPLETA
- Dimensões DESTE QUADRANTE: {width_mm} mm (largura X) x {height_mm} mm (altura Y)
- Sistema de coordenadas: LOCAL ao quadrante que você vê
- Origem: Topo superior esquerdo é o ponto (0, 0) DO QUADRANTE
- Orientação: X crescente da esquerda para direita, Y crescente de cima para baixo
- X: 0.0 (extrema esquerda do quadrante) até {width_mm} (extrema direita do quadrante)
- Y: 0.0 (topo do quadrante) até {height_mm} (base do quadrante)
- CRÍTICO: Retorne coordenadas LOCAIS (relativas ao quadrante), NÃO globais
- O sistema converterá automaticamente para coordenadas globais da página completa
"""
    
    base += f"""
OBJETIVO: Extrair TODOS os elementos do fluxograma de processo com máxima precisão técnica.

EQUIPAMENTOS A IDENTIFICAR (lista não exaustiva):
1. Equipamentos principais:
   - Bombas (centrífugas, alternativas, de vácuo): P-XXX
   - Tanques (armazenamento, pulmão, surge): T-XXX, TK-XXX
   - Vasos (separadores, flash drums, acumuladores): V-XXX, D-XXX
   - Trocadores de calor (casco-tubo, placas, ar): E-XXX, HE-XXX
   - Reatores (CSTR, PFR, batelada): R-XXX
   - Fornos e caldeiras: F-XXX, H-XXX, B-XXX
   - Compressores e turboexpansores: C-XXX, K-XXX
   - Torres (destilação, absorção, stripper): C-XXX, T-XXX
   - Ciclones e separadores: CY-XXX, S-XXX
   - Filtros e peneiras: FL-XXX, SC-XXX
   - Secadores, evaporadores, cristalizadores
   - Misturadores, agitadores, homogeneizadores

2. Instrumentos de medição (nomenclatura ISA):
   - Pressão: PI (indicador), PT (transmissor), PG (gauge), PS (switch), PCV (válvula controle)
   - Temperatura: TI, TT, TE (elemento), TW (poço termométrico), TCV
   - Vazão: FI, FT, FE (elemento primário), FQ (totalizador), FCV
   - Nível: LI, LT, LG (visor), LS (switch), LCV
   - Análise: AI, AT (analisador), AQ (qualidade)
   - Densidade/Viscosidade: DI, DT, VI, VT
   - pH/Condutividade: QI, QT, CI, CT
   - Velocidade/Rotação: SI, ST

3. Válvulas e dispositivos de controle:
   - Válvulas de controle: FCV, PCV, LCV, TCV (pneumáticas, motorizadas)
   - Válvulas manuais: gate, globe, ball, butterfly, check, plug
   - Válvulas de segurança/alívio: PSV, PRV, TSV
   - Válvulas solenoides, diafragma
   - Atuadores: pneumáticos, elétricos, hidráulicos

4. Tubulações e conexões:
   - Linhas de processo (principais, auxiliares, utilidades)
   - Conexões: flanges, uniões, derivações
   - Elementos especiais: redutores, expansores, curvas

5. Outros elementos:
   - Instrumentos locais vs. sala de controle (ISA)
   - Malhas de controle (PID, cascata, feedforward)
   - Sistemas de intertravamento e segurança
   - Símbolos auxiliares (drenos, vents, samplers)

REGRAS CRÍTICAS PARA EXTRAÇÃO:

1. COORDENADAS (PRECISÃO MÁXIMA):
   - Meça as coordenadas com MÁXIMA PRECISÃO em relação à imagem que você está vendo
   - As coordenadas devem referenciar o CENTRO/MEIO do equipamento ou instrumento
   - NÃO retorne coordenadas de tubulações, linhas ou elementos auxiliares
   - Precisão requerida: até 0.1 mm
   - Se um equipamento estiver parcialmente visível, estime o centro baseado na parte visível

2. TAGS E IDENTIFICAÇÃO:
   - Capture TAGs completas mesmo se prefixo e número estiverem separados visualmente
   - Exemplos: "PI 9039", "LT 101", "FV-2001", "P 101 A/B"
   - Se não houver TAG visível, use "tag": "N/A" mas capture o equipamento
   - Inclua sufixos importantes: A/B (redundância), -1/-2 (numeração)

3. DESCRIÇÕES (nomenclatura ISA S5.1):
   - Use terminologia técnica precisa segundo ISA
   - Exemplos: "Transmissor de Pressão", "Válvula de Controle de Vazão", "Bomba Centrífuga"
   - Especifique tipo quando visível: "Trocador de Calor Casco-Tubo", "Válvula Globo"

4. CONEXÕES DE PROCESSO (from/to):
   - Identifique fluxo do processo: equipamento de origem → equipamento de destino
   - Use TAGs dos equipamentos conectados
   - Se não houver conexão clara, use "N/A"
   - Exemplo: "from": "T-101", "to": "P-201"

5. COMPLETUDE:
   - Extraia TODOS os símbolos visíveis, mesmo sem TAG
   - Não omita instrumentos pequenos ou auxiliares
   - Capture válvulas manuais, drenos, vents, samplers
   - Inclua símbolos parcialmente visíveis (estimando coordenadas do centro)

FORMATO DE SAÍDA (JSON OBRIGATÓRIO):
[
  {{
    "tag": "P-101",
    "descricao": "Bomba Centrífuga",
    "x_mm": 234.5,
    "y_mm": 567.8,
    "from": "T-101",
    "to": "E-201"
  }},
  {{
    "tag": "PI-9039",
    "descricao": "Indicador de Pressão",
    "x_mm": 245.2,
    "y_mm": 555.3,
    "from": "P-101",
    "to": "N/A"
  }}
]

RETORNE SOMENTE O ARRAY JSON. Não inclua texto adicional, markdown ou explicações."""
    
    return base.strip()


# ============================================================
# LLM CALL
# ============================================================
def llm_call(image_b64: str, prompt: str, prefer_model: str = PRIMARY_MODEL):
    global client
    
    if prefer_model == "gpt-5":
        try:
            resp = client.chat.completions.create(
                model="gpt-5",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                    ]
                }],
                timeout=OPENAI_REQUEST_TIMEOUT
            )
            return "gpt-5", resp
        except Exception as e:
            # Check if it's an SSL error and retry without SSL verification
            if "SSL" in str(e) or "certificate" in str(e).lower():
                log_to_front(f"⚠️ gpt-5 falhou com erro SSL: {e}")
                log_to_front("🔄 Tentando novamente sem verificação SSL...")
                client = make_client(verify_ssl=False)
                try:
                    resp = client.chat.completions.create(
                        model="gpt-5",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                            ]
                        }],
                        timeout=OPENAI_REQUEST_TIMEOUT
                    )
                    return "gpt-5", resp
                except Exception as e2:
                    log_to_front(f"⚠️ gpt-5 falhou novamente: {e2}")
            else:
                log_to_front(f"⚠️ gpt-5 falhou: {e}")
    
    try:
        resp = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }],
            temperature=0,
            timeout=OPENAI_REQUEST_TIMEOUT
        )
        return FALLBACK_MODEL, resp
    except Exception as e:
        # Check if it's an SSL error and retry without SSL verification
        if "SSL" in str(e) or "certificate" in str(e).lower():
            log_to_front(f"❌ Fallback {FALLBACK_MODEL} falhou com erro SSL: {e}")
            log_to_front("🔄 Tentando novamente sem verificação SSL...")
            client = make_client(verify_ssl=False)
            try:
                resp = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                        ]
                    }],
                    temperature=0,
                    timeout=OPENAI_REQUEST_TIMEOUT
                )
                return FALLBACK_MODEL, resp
            except Exception as e2:
                log_to_front(f"❌ Fallback {FALLBACK_MODEL} falhou novamente: {e2}")
                traceback.print_exc()
                raise
        else:
            log_to_front(f"❌ Fallback {FALLBACK_MODEL} falhou: {e}")
            traceback.print_exc()
            raise


# ============================================================
# PROCESSAMENTO QUADRANTE
# ============================================================
async def process_quadrant(gx, gy, rect, page, W_mm, H_mm, dpi):
    label = f"{gy+1}-{gx+1}"
    ox, oy = points_to_mm(rect.x0), points_to_mm(rect.y0)
    rect_w_mm, rect_h_mm = points_to_mm(rect.width), points_to_mm(rect.height)

    log_to_front(f"🔹 Quadrant {label} | origem ≈ ({ox:.1f}, {oy:.1f}) mm | dimensões ≈ ({rect_w_mm:.1f} x {rect_h_mm:.1f}) mm")
    try:
        quad_png = render_quadrant_png(page, rect, dpi=dpi)
        
        # Validate image data exists
        if not quad_png or len(quad_png) == 0:
            raise ValueError(f"Failed to render quadrant {label}: empty image data")
        
        quad_b64 = base64.b64encode(quad_png).decode("utf-8")
        # Passa as dimensões CORRETAS do quadrante (não da página completa)
        prompt_q = build_prompt(rect_w_mm, rect_h_mm, "quadrant", (ox, oy), label)
        model_used, resp_q = await asyncio.to_thread(llm_call, quad_b64, prompt_q)
        raw_q = resp_q.choices[0].message.content if resp_q and resp_q.choices else ""
        log_to_front(f"   🔍 RAW QUADRANT {label}: {raw_q[:500]}")
        items_q = ensure_json_list(raw_q)

        # anota metadados
        for it in items_q:
            if isinstance(it, dict):
                it["_src"] = "quadrant"
                it["_ox_mm"] = ox
                it["_oy_mm"] = oy
                it["_qw_mm"] = rect_w_mm
                it["_qh_mm"] = rect_h_mm

        log_to_front(f"   └─ itens Quadrant {label}: {len(items_q)}")
        return items_q
    except Exception as e:
        log_to_front(f"   ❌ Erro Quadrant {label}: {e}")
        return []


# ============================================================
# ROTA PRINCIPAL
# ============================================================
@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile,
    dpi: int = Query(400, ge=100, le=600),
    grid: int = Query(3, ge=1, le=6),
    tol_mm: float = Query(10.0, ge=1.0, le=50.0)
):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY não definida. Configure a chave no arquivo .env")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    log_to_front(f"📥 Arquivo recebido: {file.filename} ({len(data)} bytes)")

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        log_to_front(f"❌ Erro ao abrir PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Erro PDF: {e}")

    all_pages: List[Dict[str, Any]] = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        log_to_front(f"\n===== Página {page_num} =====")

        W_pts, H_pts = page.rect.width, page.rect.height
        W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
        if H_mm > W_mm:
            W_mm, H_mm = H_mm, W_mm

        log_to_front(f"Dimensões normalizadas (mm): X={W_mm}, Y={H_mm}")

        global_list: List[Dict[str, Any]] = []
        quad_items: List[Dict[str, Any]] = []
        model_used = PRIMARY_MODEL

        try:
            page_png = page.get_pixmap(dpi=dpi).tobytes("png")
            page_b64 = base64.b64encode(page_png).decode("utf-8")
            prompt_global = build_prompt(W_mm, H_mm, "global")
            model_used, resp = llm_call(page_b64, prompt_global)
            raw = resp.choices[0].message.content if resp and resp.choices else ""
            log_to_front(f"🌐 RAW GLOBAL OUTPUT (page {page_num}): {raw[:500]}")
            global_list = ensure_json_list(raw)
        except Exception as e:
            log_to_front(f"⚠️ Global falhou na página {page_num}: {e}")
            global_list = []

        log_to_front(f"🌐 Global → itens: {len(global_list)}")

        if grid > 1:
            quads = page_quadrants(page, grid_x=grid, grid_y=grid)
            tasks = [process_quadrant(gx, gy, rect, page, W_mm, H_mm, dpi) for gx, gy, rect in quads]
            results = await asyncio.gather(*tasks)
            for r in results:
                quad_items.extend(r)

        raw_items = (global_list or []) + (quad_items or [])
        combined = []

        for it in raw_items:
            if not isinstance(it, dict):
                continue

            x_in = float(it.get("x_mm") or 0.0)
            y_in = float(it.get("y_mm") or 0.0)
            tag = it.get("tag", "N/A")
            src = it.get("_src", "global")

            # Converte coordenadas locais de quadrantes para coordenadas globais da página
            if src == "quadrant":
                ox = float(it.get("_ox_mm", 0.0))
                oy = float(it.get("_oy_mm", 0.0))
                qw = float(it.get("_qw_mm", 0.0))
                qh = float(it.get("_qh_mm", 0.0))
                
                # Log detalhado da conversão
                log_to_front(f"   🔄 Convertendo {tag}: local ({x_in:.1f}, {y_in:.1f}) + offset ({ox:.1f}, {oy:.1f}) = global ({x_in+ox:.1f}, {y_in+oy:.1f})")
                
                # Sempre adiciona o offset do quadrante para obter coordenadas globais
                x_in += ox
                y_in += oy

            # No Y flip - top-left origin (0,0) for both y_mm and y_mm_cad
            y_cad = y_in

            # clamp
            x_in = max(0.0, min(W_mm, x_in))
            y_in = max(0.0, min(H_mm, y_in))

            item = {
                "tag": tag,
                "descricao": it.get("descricao", "Equipamento"),
                "x_mm": x_in,
                "y_mm": y_in,
                "y_mm_cad": y_cad,
                "pagina": page_num,
                "from": it.get("from", "N/A"),
                "to": it.get("to", "N/A"),
                "page_width_mm": W_mm,
                "page_height_mm": H_mm,
            }

            try:
                tipo = it.get("tipo", "")
                match = match_system_fullname(item["tag"], item["descricao"], tipo)
                item.update(match)
            except Exception as e:
                item.update({
                    "SystemFullName": None,
                    "Confiança": 0,
                    "matcher_error": str(e)
                })

            combined.append(item)

        unique = dedup_items(combined, page_num=page_num, tol_mm=tol_mm)
        log_to_front(f"📄 Página {page_num} | Global: {len(global_list)} | Quadrants: {len(quad_items)} | Únicos: {len(unique)}")

        all_pages.append({
            "pagina": page_num,
            "modelo": model_used,
            "resultado": unique
        })

    log_to_front("✅ Análise concluída.")
    
    # Auto-armazena na base de conhecimento
    from datetime import datetime
    all_items = []
    for page in all_pages:
        all_items.extend(page.get("resultado", []))
    
    if all_items:
        pid_id = f"analyzed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pid_knowledge_base[pid_id] = {
            "data": all_items,
            "timestamp": datetime.now().isoformat(),
            "description": "",
            "source": "analyze",
            "filename": file.filename if hasattr(file, 'filename') else "unknown",
            "pdf_data": data,  # Armazena PDF original para modo vision
            "page_count": len(all_pages)
        }
        log_to_front(f"💾 P&ID armazenado como '{pid_id}' ({len(all_items)} itens)")
        
        # Gera descrição automática ULTRA-COMPLETA
        try:
            description = generate_process_description(all_items, ultra_complete=True)
            pid_knowledge_base[pid_id]["description"] = description
            log_to_front(f"📝 Descrição ultra-completa do processo gerada automaticamente")
        except Exception as e:
            log_to_front(f"⚠️ Não foi possível gerar descrição: {e}")
        
        # Adiciona pid_id ao response
        for page in all_pages:
            page["pid_id"] = pid_id
    
    # Sanitize all float values to ensure JSON compliance
    all_pages = sanitize_for_json(all_pages)
    
    return JSONResponse(content=all_pages)


# ============================================================
# GERAÇÃO DE P&ID A PARTIR DE PROMPT
# ============================================================
def build_generation_prompt(process_description: str, width_mm: float = 1189.0, height_mm: float = 841.0) -> str:
    """
    Constrói prompt técnico e detalhado para gerar P&ID completo a partir de descrição do processo.
    A0 sheet dimensions: 1189mm x 841mm (landscape)
    """
    prompt = f"""
You are an educational tool that helps demonstrate P&ID (Piping and Instrumentation Diagram) concepts 
following ISA S5.1, S5.2, S5.3 standards and process engineering best practices.

TASK: Generate a representative P&ID example for educational purposes based on this process description:
"{process_description}"

NOTE: This is for educational demonstration and learning purposes only, to illustrate P&ID concepts and ISA standards.

TECHNICAL SPECIFICATIONS:
- Sheet: A0 landscape format
- Dimensions: {width_mm} mm (width/X) x {height_mm} mm (height/Y)
- Coordinate system: X increases left to right, Y increases top to bottom
- Origin: Top left corner is point (0, 0)
- Layout: Process flow from left (inlet) to right (outlet)
- Compatibility: COMOS (Siemens) - absolute coordinates

TYPICAL P&ID ELEMENTS - MAIN EQUIPMENT:

1. PROCESS EQUIPMENT (include as applicable):
   - Pumps: P-101, P-102, etc. (centrifugal, reciprocating, vacuum)
     * Typical specs: type, capacity, redundancy (A/B if applicable)
   - Storage tanks: T-101, TK-101, etc.
     * Typical items: level indicators, inlet/outlet valves, vents, drains
   - Process vessels: V-101, D-101 (separators, flash drums, accumulators)
     * Typical controls: pressure, level, temperature
   - Heat exchangers: E-101, E-102, HE-101 (shell-tube, plate, air coolers)
     * Typical instrumentation: both sides (process and utility)
   - Reactors: R-101, R-102 (CSTR, PFR, batch)
     * Typical features: agitation, temperature control, pressure, analytical instrumentation
   - Towers: C-101, T-101 (distillation, absorption, stripping)
     * Typical components: condensers, reboilers, trays/packing, reflux
   - Compressors/Blowers: K-101, C-101
     * Typical systems: lubrication, cooling, anti-surge
   - Furnaces/Boilers: F-101, H-101, B-101
     * Typical controls: combustion, temperature, pressure
   - Filters/Separators: FL-101, S-101, CY-101
   - Dryers/Evaporators: DR-101, EV-101

2. COMPLETE INSTRUMENTATION (ISA S5.1 nomenclature):

   Pressure:
   - PI: Pressure indicators (local gauges)
   - PT: Pressure transmitters (4-20mA to DCS/SCADA)
   - PG: Pressure gauges
   - PS/PSH/PSL: Switches (high/low alarms)
   - PCV: Pressure control valves
   - PSV/PRV: Safety/relief valves

   Temperature:
   - TI: Temperature indicators
   - TT: Temperature transmitters (thermocouples, RTDs)
   - TE: Primary elements (thermowells)
   - TS/TSH/TSL: Temperature switches
   - TCV: Temperature control valves

   Flow:
   - FI: Flow indicators
   - FT: Flow transmitters
   - FE: Primary elements (orifice, venturi, turbine, magnetic, Coriolis)
   - FQ: Flow totalizers
   - FS: Flow switches
   - FCV: Flow control valves

   Level:
   - LI: Level indicators
   - LT: Level transmitters (radar, ultrasonic, differential pressure)
   - LG: Level gauge glass
   - LS/LSH/LSL/LSHH/LSLL: Level switches (multiple levels)
   - LCV: Level control valves

   Analysis and quality:
   - AI/AT: Analyzers (pH, conductivity, O2, etc.)
   - QI/QT: Quality indicators/transmitters
   - Specific analyzers: pH, conductivity, turbidity, concentration, chromatography

3. VALVES AND ACTUATORS:
   - Control valves: FCV, PCV, LCV, TCV (with pneumatic/electric actuators)
   - Manual valves: gate, globe, ball, butterfly, check, plug
   - Safety valves: PSV, TSV, PRV
   - Special valves: solenoid, diaphragm, pinch
   - Indicate: actuator type (pneumatic, electric, hydraulic)
   - Indicate: fail action (FC - fail close, FO - fail open, FL - fail last)

4. AUXILIARY SYSTEMS AND UTILITIES:
   - Steam systems: lines, traps, condensate
   - Cooling water: supply/return
   - Instrument air: distribution, FRLs
   - Nitrogen blanketing/inerting
   - Drainage and venting systems
   - Sample points

5. CONTROL LOOPS AND AUTOMATION:
   - Regulatory controls: PID, cascade
   - Safety interlocks (SIS)
   - Alarms: PAH, PAL, TAH, TAL, FAH, FAL, LAH, LAL
   - Local indication vs. control room (ISA symbols)

TAG RULES (CRITICAL):
- Main equipment: P-101, T-201, V-301, E-401, R-501, C-601, K-701, F-801
- Instruments follow ISA: [variable][function]-[loop][suffix]
  * Examples: PT-101, FT-205A, LT-301, TT-401B, PI-9039, FCV-520
- Logical numbering by area/system (hundreds: 100s, 200s, 300s, etc.)
- Suffixes: A/B (redundancy), -1/-2 (multiples), H/L (high/low)

SPATIAL DISTRIBUTION AND LAYOUT:

1. X Coordinates (horizontal):
   - Feed/inlet zone: X = 100-300 mm
   - Main processing zone: X = 300-800 mm
   - Separation/purification zone: X = 800-1000 mm
   - Product/outlet zone: X = 1000-1100 mm
   - Right margin: leave ~50-100 mm

2. Y Coordinates (vertical):
   - Main equipment: Y = 300-600 mm (center)
   - Instruments and valves: Y = 250-400 mm (near equipment)
   - Upper auxiliary lines: Y = 600-750 mm
   - Lower auxiliary lines: Y = 150-250 mm
   - Maintain top/bottom margins: ~50-100 mm

3. Spacing:
   - Between main equipment: minimum 100-150 mm
   - Between instruments: minimum 30-50 mm
   - Avoid overlaps

**CRITICAL RULE FOR COORDINATES:**
- Coordinates (x_mm, y_mm) must ALWAYS reference the CENTER/MIDDLE of the equipment or instrument
- DO NOT consider piping, process lines, or other auxiliary elements when defining coordinates
- Only equipment (P-XXX, T-XXX, E-XXX, etc.) and instruments (FT-XXX, PT-XXX, etc.) should have coordinates

PROCESS CONNECTIONS (from/to):
- Define logical process flow
- "from": source equipment/instrument
- "to": destination equipment/instrument
- Use TAGs for references
- If terminal, use "N/A"
- Remember: coordinates should be at equipment/instrument centers, not piping

COMPLETENESS AND DETAIL:
- Generate a COMPLETE P&ID with ALL necessary equipment for the process
- Include ALL control, monitoring, and safety instrumentation
- Do not omit auxiliary equipment: spare pumps, filters, manual valves
- Include safety elements: PSVs, alarms, interlocks
- Add redundant instrumentation where critical
- Consider necessary utilities (steam, water, air, etc.)


OUTPUT FORMAT (JSON):
[
  {{
    "tag": "T-101",
    "descricao": "Feed Tank",
    "x_mm": 150.0,
    "y_mm": 450.0,
    "from": "N/A",
    "to": "P-101"
  }},
  {{
    "tag": "P-101",
    "descricao": "Centrifugal Feed Pump",
    "x_mm": 250.0,
    "y_mm": 400.0,
    "from": "T-101",
    "to": "E-201"
  }},
  {{
    "tag": "FT-101",
    "descricao": "Flow Transmitter",
    "x_mm": 280.0,
    "y_mm": 380.0,
    "from": "P-101",
    "to": "FCV-101"
  }},
  {{
    "tag": "FCV-101",
    "descricao": "Flow Control Valve",
    "x_mm": 320.0,
    "y_mm": 380.0,
    "from": "FT-101",
    "to": "E-201"
  }},
  {{
    "tag": "PT-102",
    "descricao": "Pressure Transmitter",
    "x_mm": 270.0,
    "y_mm": 420.0,
    "from": "P-101",
    "to": "N/A"
  }}
]

IMPORTANT:
- Return ONLY the JSON array, without additional text, markdown, or explanations
- Coordinates must be within limits: X: 0-{width_mm}, Y: 0-{height_mm}
- Coordinates must reference the CENTER of equipment and instruments (not piping)
- This is an educational example to demonstrate P&ID concepts and ISA standards
- Include ALL typical essential elements: equipment, instrumentation, valves, controls
- Use engineering best practices: redundancy in critical systems, adequate instrumentation
- Strictly follow ISA S5.1 standards for nomenclature
"""
    return prompt.strip()


@app.post("/generate")
async def generate_pid(
    prompt: str = Query(..., description="Descrição do processo em linguagem natural")
):
    """
    Gera P&ID a partir de descrição em linguagem natural.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY não definida. Configure a chave no arquivo .env")
    
    if not prompt or len(prompt.strip()) < 10:
        raise HTTPException(status_code=400, detail="Prompt muito curto. Descreva o processo com mais detalhes.")
    
    log_to_front(f"🎨 Gerando P&ID para: {prompt}")
    
    # Dimensões folha A0 (landscape)
    W_mm = 1189.0
    H_mm = 841.0
    
    try:
        # Gera o prompt de geração
        generation_prompt = build_generation_prompt(prompt, W_mm, H_mm)
        
        # Chama LLM sem imagem (apenas texto)
        log_to_front("🤖 Chamando LLM para gerar equipamentos...")
        
        global client
        try:
            resp = client.chat.completions.create(
                model=FALLBACK_MODEL,  # usa gpt-4o para geração de texto
                messages=[{
                    "role": "user",
                    "content": generation_prompt
                }],
                temperature=0.7,  # um pouco de criatividade
                timeout=OPENAI_REQUEST_TIMEOUT
            )
        except Exception as e:
            # Check if it's an SSL error and retry without SSL verification
            if "SSL" in str(e) or "certificate" in str(e).lower():
                log_to_front(f"⚠️ Erro SSL detectado: {e}")
                log_to_front("🔄 Tentando novamente sem verificação SSL...")
                client = make_client(verify_ssl=False)
                resp = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[{
                        "role": "user",
                        "content": generation_prompt
                    }],
                    temperature=0.7,
                    timeout=OPENAI_REQUEST_TIMEOUT
                )
            else:
                raise
        
        raw = resp.choices[0].message.content if resp and resp.choices else ""
        log_to_front(f"📝 RAW GENERATION OUTPUT: {raw[:500]}")
        
        # Parseia JSON
        items = ensure_json_list(raw)
        
        if not items:
            raise ValueError("LLM não retornou equipamentos válidos")
        
        log_to_front(f"✅ Gerados {len(items)} equipamentos/instrumentos")
        
        # Processa cada item
        result_items = []
        for it in items:
            if not isinstance(it, dict):
                continue
            
            x_in = float(it.get("x_mm", 0.0))
            y_in = float(it.get("y_mm", 0.0))
            
            # Clamp nas dimensões A0
            x_in = max(0.0, min(W_mm, x_in))
            y_in = max(0.0, min(H_mm, y_in))
            
            # No Y flip - top-left origin (0,0) for both y_mm and y_mm_cad
            y_cad = y_in
            
            item = {
                "tag": it.get("tag", "N/A"),
                "descricao": it.get("descricao", "Equipamento"),
                "x_mm": x_in,
                "y_mm": y_in,
                "y_mm_cad": y_cad,
                "pagina": 1,  # gerado = página 1
                "from": it.get("from", "N/A"),
                "to": it.get("to", "N/A"),
                "page_width_mm": W_mm,
                "page_height_mm": H_mm,
            }
            
            # Aplica matcher para SystemFullName
            try:
                tipo = it.get("tipo", "")
                match = match_system_fullname(item["tag"], item["descricao"], tipo)
                item.update(match)
                log_to_front(f"  ✓ {item['tag']}: {match.get('SystemFullName', 'N/A')}")
            except Exception as e:
                item.update({
                    "SystemFullName": None,
                    "Confiança": 0,
                    "matcher_error": str(e)
                })
            
            result_items.append(item)
        
        # Remove duplicatas
        unique = dedup_items(result_items, page_num=1, tol_mm=50.0)
        
        log_to_front(f"✅ Geração concluída: {len(unique)} itens únicos")
        
        # Auto-armazena na base de conhecimento
        from datetime import datetime
        pid_id = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pid_knowledge_base[pid_id] = {
            "data": unique,
            "timestamp": datetime.now().isoformat(),
            "description": "",
            "source": "generate",
            "original_prompt": prompt,
            "pdf_data": None,  # P&IDs gerados não têm PDF original
            "page_count": 1
        }
        log_to_front(f"💾 P&ID armazenado como '{pid_id}' ({len(unique)} itens)")
        
        # Gera descrição automática ULTRA-COMPLETA
        try:
            description = generate_process_description(unique, ultra_complete=True)
            pid_knowledge_base[pid_id]["description"] = description
            log_to_front(f"📝 Descrição ultra-completa do processo gerada automaticamente")
        except Exception as e:
            log_to_front(f"⚠️ Não foi possível gerar descrição: {e}")
        
        # Retorna no mesmo formato do /analyze
        response_data = [{
            "pagina": 1,
            "modelo": FALLBACK_MODEL,
            "resultado": unique,
            "pid_id": pid_id
        }]
        
        # Sanitize all float values to ensure JSON compliance
        response_data = sanitize_for_json(response_data)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        log_to_front(f"❌ Erro na geração: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar P&ID: {str(e)}")


# ============================================================
# GERAÇÃO DE DESCRIÇÃO DO PROCESSO
# ============================================================
def generate_process_description(pid_data: List[Dict[str, Any]], ultra_complete: bool = False) -> str:
    """
    Gera uma descrição completa do P&ID baseada nos equipamentos identificados.
    
    Args:
        pid_data: Lista de equipamentos e instrumentos do P&ID
        ultra_complete: Se True, gera descrição MUITO mais detalhada incluindo TODOS os equipamentos
    """
    if not pid_data:
        return "Nenhum equipamento identificado."
    
    # Agrupa por tipo de equipamento
    equipamentos = []
    instrumentos = []
    
    for item in pid_data:
        tag = item.get("tag", "N/A")
        descricao = item.get("descricao", "")
        tipo = item.get("tipo", "")
        
        if any(prefix in tag for prefix in ["FT", "PT", "TT", "LT", "FIC", "PIC", "TIC", "LIC", "PSV", "FE", "PE", "TE", "LE"]):
            instrumentos.append(item)
        else:
            equipamentos.append(item)
    
    # Monta o prompt para gerar descrição
    if ultra_complete:
        # Modo ULTRA-COMPLETO: inclui TODOS os equipamentos com coordenadas e conexões
        # Primeiro, analisa os dados para criar informações estruturadas
        
        # Mapeia instrumentos por equipamento associado
        instruments_by_equipment = {}
        for inst in instrumentos:
            from_tag = inst.get('from', 'N/A')
            if from_tag != 'N/A':
                if from_tag not in instruments_by_equipment:
                    instruments_by_equipment[from_tag] = []
                instruments_by_equipment[from_tag].append(inst)
        
        # Identifica equipamentos reserva (A/B, -1/-2, etc.)
        backup_pairs = {}
        for eq in equipamentos:
            tag = eq.get('tag', '').strip()
            # Remove sufixos A/B, -1/-2, etc. para agrupar
            base_tag = tag.rstrip('AB12').rstrip('-').rstrip('/')
            if base_tag and base_tag != tag:
                if base_tag not in backup_pairs:
                    backup_pairs[base_tag] = []
                backup_pairs[base_tag].append(tag)
        
        # Monta mapa de fluxo (from → to)
        flow_map = {}
        for item in pid_data:
            tag = item.get('tag', 'N/A')
            from_tag = item.get('from', 'N/A')
            to_tag = item.get('to', 'N/A')
            if tag != 'N/A':
                flow_map[tag] = {'from': from_tag, 'to': to_tag}
        
        prompt = f"""Com base nos seguintes equipamentos e instrumentos identificados em um P&ID, gere uma descrição técnica ULTRA-COMPLETA e EXTREMAMENTE DETALHADA do processo industrial.

INSTRUÇÕES CRÍTICAS:
Esta descrição será a ÚNICA fonte de informação para um chatbot responder perguntas sobre o P&ID.
Você DEVE incluir TODOS os detalhes específicos abaixo para cada equipamento e instrumento.

DETALHES OBRIGATÓRIOS A INCLUIR:
1. Para CADA equipamento principal:
   - TAG completa e descrição
   - Função específica no processo
   - De onde recebe material (FROM) e para onde envia (TO)
   - Coordenadas exatas (x_mm, y_mm)
   - TODOS os instrumentos associados (pressão, temperatura, vazão, nível)
   - Se é equipamento reserva/backup de outro (identificar pares A/B, -1/-2)

2. Para CADA instrumento:
   - TAG completa e tipo (PT, TT, FT, LT, etc.)
   - Qual equipamento ele monitora/controla
   - Tipo de medição (pressão, temperatura, vazão, nível, etc.)
   - Se faz parte de malha de controle (identificar FCV, PCV, LCV, TCV)

3. Fluxo do Processo:
   - Caminho COMPLETO do material usando TAGs
   - Ex: "O processo inicia em T-101 → P-101A (com P-101B como reserva) → FT-101 → FCV-101 → E-201"
   - Derivações, by-passes, reciclos

4. Instrumentação por Equipamento:
   - Para cada equipamento, liste EXATAMENTE quais instrumentos estão associados
   - Ex: "P-101A é monitorado por: PT-101 (pressão descarga), FT-101 (vazão), TT-101 (temperatura)"

DADOS FORNECIDOS:

EQUIPAMENTOS PRINCIPAIS ({len(equipamentos)} itens):
"""
        # Inclui TODOS os equipamentos com detalhes completos
        for eq in equipamentos:
            tag = eq.get('tag', 'N/A')
            desc = eq.get('descricao', 'N/A')
            from_tag = eq.get('from', 'N/A')
            to_tag = eq.get('to', 'N/A')
            x = eq.get('x_mm', 'N/A')
            y = eq.get('y_mm', 'N/A')
            
            prompt += f"\n• {tag}: {desc}"
            if from_tag != 'N/A' or to_tag != 'N/A':
                prompt += f"\n  → Fluxo: {from_tag} ➜ {to_tag}"
            if x != 'N/A' and y != 'N/A':
                prompt += f"\n  → Posição: ({x}, {y}) mm"
            
            # Lista instrumentos associados a este equipamento
            if tag in instruments_by_equipment:
                insts = instruments_by_equipment[tag]
                prompt += f"\n  → Instrumentos associados: {', '.join([i.get('tag', 'N/A') for i in insts])}"
        
        # Informação sobre equipamentos reserva
        if backup_pairs:
            prompt += f"\n\nEQUIPAMENTOS RESERVA/BACKUP identificados:"
            for base, variants in backup_pairs.items():
                if len(variants) > 1:
                    prompt += f"\n• {base}: {' e '.join(variants)} (equipamentos redundantes)"
        
        prompt += f"""

INSTRUMENTAÇÃO COMPLETA ({len(instrumentos)} itens):
"""
        # Agrupa instrumentos por tipo
        inst_by_type = {}
        for inst in instrumentos:
            tag = inst.get('tag', 'N/A')
            # Extrai tipo do instrumento (PT, TT, FT, etc.)
            inst_type = tag.split('-')[0] if '-' in tag else tag[:2]
            if inst_type not in inst_by_type:
                inst_by_type[inst_type] = []
            inst_by_type[inst_type].append(inst)
        
        # Lista por tipo para facilitar compreensão
        for inst_type, insts in sorted(inst_by_type.items()):
            type_name = {
                'PT': 'Transmissores de Pressão',
                'TT': 'Transmissores de Temperatura',
                'FT': 'Transmissores de Vazão',
                'LT': 'Transmissores de Nível',
                'PI': 'Indicadores de Pressão',
                'TI': 'Indicadores de Temperatura',
                'FI': 'Indicadores de Vazão',
                'LI': 'Indicadores de Nível',
                'PSV': 'Válvulas de Segurança (Pressão)',
                'FCV': 'Válvulas de Controle de Vazão',
                'PCV': 'Válvulas de Controle de Pressão',
                'TCV': 'Válvulas de Controle de Temperatura',
                'LCV': 'Válvulas de Controle de Nível',
            }.get(inst_type, f'Instrumentos tipo {inst_type}')
            
            prompt += f"\n{type_name}:"
            for inst in insts:
                tag = inst.get('tag', 'N/A')
                desc = inst.get('descricao', 'N/A')
                from_tag = inst.get('from', 'N/A')
                x = inst.get('x_mm', 'N/A')
                y = inst.get('y_mm', 'N/A')
                
                prompt += f"\n• {tag}: {desc}"
                if from_tag != 'N/A':
                    prompt += f" → Associado ao equipamento: {from_tag}"
                if x != 'N/A' and y != 'N/A':
                    prompt += f" [Pos: ({x}, {y}) mm]"
        
        prompt += """

REQUISITOS PARA A DESCRIÇÃO ULTRA-COMPLETA:

1. **Objetivo do Processo**: 
   - Propósito principal desta planta/sistema
   - Produto final ou objetivo operacional

2. **Descrição Geral do Sistema**: 
   - Visão overview do processo completo
   - Principais seções/áreas do P&ID

3. **Inventário Completo de Equipamentos**: 
   - Liste TODOS os equipamentos por categoria (bombas, tanques, trocadores, etc.)
   - Para CADA equipamento mencione:
     * Função específica
     * Conexões (de onde vem e para onde vai o material)
     * Se tem equipamento reserva (ex: P-101A e P-101B são redundantes)
     * Posição aproximada no diagrama (use coordenadas)

4. **Instrumentação Detalhada por Equipamento**: 
   - Para CADA equipamento principal, liste TODOS os instrumentos:
     * Ex: "Bomba P-101A é instrumentada com:"
       - PT-101: mede pressão de descarga
       - FT-102: mede vazão na saída
       - TT-103: monitora temperatura do fluido
   - Identifique malhas de controle completas:
     * Ex: "Malha de controle de vazão: FT-101 → FIC-101 → FCV-101"

5. **Fluxo Detalhado do Processo (Passo-a-Passo)**:
   - Descreva o caminho COMPLETO usando TAGs:
     * Ex: "Material armazenado em T-101 é bombeado por P-101A (ou P-101B em standby) através de FCV-101 (controlada por FIC-101) para o trocador E-201..."
   - Mencione todos os pontos de medição no caminho
   - Indique by-passes, reciclos, derivações

6. **Sistemas de Controle e Automação**:
   - Liste todas as malhas de controle identificadas
   - Para cada malha: sensor → controlador → atuador
   - Alarmes e intertravamentos (switches de alta/baixa)

7. **Elementos de Segurança**:
   - Todas as PSVs (válvulas de segurança) e onde estão instaladas
   - Switches de segurança (PSH, PSL, TSH, TSL, etc.)
   - Sistemas de proteção

8. **Layout e Distribuição Espacial**:
   - Descreva onde estão os equipamentos usando coordenadas
   - Agrupe equipamentos por região/área
   - Ex: "Na região esquerda (X: 100-300mm) encontram-se os tanques de alimentação..."

9. **Relações e Dependências**:
   - Equipamentos reserva e sua relação (A/B, standby)
   - Instrumentos compartilhados entre equipamentos
   - Interdependências operacionais

IMPORTANTE: 
- Use as TAGs EXATAS fornecidas acima
- Seja EXTREMAMENTE específico sobre qual instrumento monitora qual equipamento
- Descreva o fluxo usando as conexões FROM/TO fornecidas
- Mencione TODOS os equipamentos e instrumentos, não omita nenhum
- Esta descrição precisa ser tão completa que o chatbot possa responder perguntas como:
  * "Qual instrumento mede a pressão da bomba P-101?"
  * "Qual equipamento é reserva do P-101A?"
  * "Qual é o fluxo do material desde T-101 até E-201?"
  * "Onde está localizado o instrumento FT-101?"
"""
    else:
        # Modo normal (mais resumido)
        prompt = f"""Com base nos seguintes equipamentos e instrumentos identificados em um P&ID, gere uma descrição técnica completa e detalhada do processo industrial:

EQUIPAMENTOS PRINCIPAIS ({len(equipamentos)} itens):
"""
        for eq in equipamentos[:20]:  # Limita para não exceder token limit
            prompt += f"- {eq.get('tag', 'N/A')}: {eq.get('descricao', 'N/A')}\n"
        
        if len(equipamentos) > 20:
            prompt += f"... e mais {len(equipamentos) - 20} equipamentos\n"
        
        prompt += f"""
INSTRUMENTAÇÃO ({len(instrumentos)} itens):
"""
        for inst in instrumentos[:30]:
            prompt += f"- {inst.get('tag', 'N/A')}: {inst.get('descricao', 'N/A')}\n"
        
        if len(instrumentos) > 30:
            prompt += f"... e mais {len(instrumentos) - 30} instrumentos\n"
        
        prompt += """
Por favor, forneça uma descrição estruturada incluindo:
1. **Objetivo do Processo**: Qual é o propósito principal desta planta/sistema
2. **Etapas do Processo**: Descreva as principais etapas em sequência lógica
3. **Equipamentos Principais**: Função de cada equipamento principal identificado
4. **Instrumentação e Controle**: Quais variáveis são monitoradas e controladas
5. **Segurança**: Elementos de segurança presentes (PSVs, alarmes, intertravamentos)
6. **Fluxo do Processo**: Descreva o fluxo de materiais através do sistema

Seja técnico e específico, usando terminologia da engenharia de processos."""
    
    try:
        log_to_front(f"🤖 Gerando descrição {'ULTRA-COMPLETA' if ultra_complete else 'do processo'}...")
        
        global client
        resp = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.7,
            timeout=OPENAI_REQUEST_TIMEOUT
        )
        
        description = resp.choices[0].message.content if resp and resp.choices else "Erro ao gerar descrição"
        log_to_front(f"✅ Descrição {'ULTRA-COMPLETA' if ultra_complete else ''} do processo gerada")
        
        return description
        
    except Exception as e:
        log_to_front(f"❌ Erro ao gerar descrição: {e}")
        return f"Erro ao gerar descrição: {str(e)}"


@app.get("/describe")
async def describe_pid(
    pid_id: str = Query(..., description="ID do P&ID a ser descrito"),
    regenerate: bool = Query(False, description="Forçar regeneração da descrição (padrão: False)")
):
    """
    Retorna a descrição completa do P&ID baseada na base de conhecimento.
    Por padrão, retorna a descrição ultra-completa que já foi gerada.
    Use regenerate=true apenas se quiser forçar regeneração.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY não definida")
    
    if pid_id not in pid_knowledge_base:
        raise HTTPException(status_code=404, detail=f"P&ID '{pid_id}' não encontrado na base de conhecimento")
    
    pid_info = pid_knowledge_base[pid_id]
    description = pid_info.get("description", "")
    
    # Só regenera se forçado OU se não existe descrição
    if regenerate or not description:
        log_to_front(f"🔄 {'Regenerando' if regenerate else 'Gerando'} descrição ultra-completa...")
        description = generate_process_description(pid_info.get("data", []), ultra_complete=True)
        # Atualiza a base de conhecimento com a descrição
        pid_knowledge_base[pid_id]["description"] = description
    else:
        log_to_front(f"📖 Retornando descrição ultra-completa existente (já foi gerada)")
    
    return JSONResponse(content={
        "pid_id": pid_id,
        "description": description,
        "equipment_count": len(pid_info.get("data", [])),
        "timestamp": pid_info.get("timestamp", ""),
        "regenerated": regenerate
    })


# ============================================================
# CHATBOT Q&A - MODO HÍBRIDO COM SUPORTE A VISION
# ============================================================
def should_use_vision_mode(question: str) -> bool:
    """
    Determina se a pergunta requer modo vision (análise visual do P&ID).
    
    Perguntas sobre layout, posicionamento, visual, símbolos, etc. se beneficiam de vision.
    Perguntas sobre função, fluxo, lista de equipamentos funcionam bem com texto.
    """
    vision_keywords = [
        "onde", "posição", "localiz", "coordenada", "layout", "espaço", "distribuição",
        "visual", "símbol", "diagrama", "desenho", "aparência", "próxim", "distân",
        "esquerda", "direita", "acima", "abaixo", "topo", "base", "centro",
        "região", "área", "zona", "quadrante"
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in vision_keywords)


async def chat_with_vision(pid_id: str, question: str, pid_info: Dict[str, Any]) -> str:
    """
    Responde pergunta usando o modo VISION - envia imagem(ns) do P&ID para GPT-4V.
    """
    pdf_data = pid_info.get("pdf_data")
    
    if not pdf_data:
        # Fallback para modo texto se não houver PDF
        log_to_front(f"⚠️ PDF não disponível para {pid_id}, usando modo texto")
        return await chat_with_text(pid_id, question, pid_info)
    
    try:
        log_to_front(f"🖼️ Usando MODO VISION para responder pergunta")
        
        # Abre o PDF e renderiza páginas
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Para perguntas gerais, usa a primeira página
        # Para P&IDs multipáginas, poderia processar todas
        page = doc[0]
        pix = page.get_pixmap(dpi=200)  # Resolução menor para economizar tokens
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # Prepara contexto com descrição + imagem
        pid_data = pid_info.get("data", [])
        description = pid_info.get("description", "")
        
        prompt = f"""Você é um assistente especializado em P&ID (Piping and Instrumentation Diagram).

Você tem acesso a:
1. A IMAGEM do P&ID (anexada)
2. Descrição do processo: {description[:500]}...
3. {len(pid_data)} equipamentos/instrumentos identificados

PERGUNTA DO USUÁRIO:
{question}

Por favor, analise a IMAGEM do P&ID junto com a descrição e responda de forma clara, técnica e específica.
Se a informação visual for relevante, use-a. Referencie equipamentos por suas TAGs quando possível."""
        
        global client
        resp = client.chat.completions.create(
            model=FALLBACK_MODEL,  # gpt-4o suporta vision
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }],
            temperature=0.5,
            timeout=OPENAI_REQUEST_TIMEOUT
        )
        
        answer = resp.choices[0].message.content if resp and resp.choices else "Erro ao gerar resposta"
        log_to_front("✅ Resposta gerada usando VISION")
        
        doc.close()
        return answer
        
    except Exception as e:
        log_to_front(f"❌ Erro no modo vision: {e}")
        # Fallback para modo texto
        log_to_front("🔄 Tentando modo texto como fallback")
        return await chat_with_text(pid_id, question, pid_info)


async def chat_with_text(pid_id: str, question: str, pid_info: Dict[str, Any]) -> str:
    """
    Responde pergunta usando o modo TEXTO - usa descrição ultra-completa que já foi gerada.
    A descrição ultra-completa contém TODOS os detalhes: equipamentos, instrumentos, conexões, coordenadas.
    """
    description = pid_info.get("description", "")
    
    if not description:
        log_to_front(f"⚠️ Descrição ultra-completa não encontrada para {pid_id}")
        # Fallback: gera agora se não existir
        pid_data = pid_info.get("data", [])
        description = generate_process_description(pid_data, ultra_complete=True)
        pid_knowledge_base[pid_id]["description"] = description
        log_to_front(f"📝 Descrição ultra-completa gerada agora como fallback")
    
    # Monta contexto usando APENAS a descrição ultra-completa
    # (que já contém todos os equipamentos, instrumentos, coordenadas e conexões)
    context = f"""Você é um assistente especializado em P&ID (Piping and Instrumentation Diagram). 
Você tem acesso à descrição ultra-completa do P&ID '{pid_id}':

{description}

PERGUNTA DO USUÁRIO:
{question}

Por favor, responda de forma clara, técnica e específica baseando-se nas informações fornecidas acima. 
Use as TAGs dos equipamentos para contextualizar sua resposta.
Se a informação solicitada não estiver disponível, indique isso claramente."""
    
    try:
        log_to_front(f"📝 Usando MODO TEXTO (descrição ultra-completa pré-gerada)")
        
        global client
        resp = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[{
                "role": "user",
                "content": context
            }],
            temperature=0.5,
            timeout=OPENAI_REQUEST_TIMEOUT
        )
        
        answer = resp.choices[0].message.content if resp and resp.choices else "Erro ao gerar resposta"
        log_to_front("✅ Resposta gerada usando descrição ultra-completa (sem reprocessamento)")
        
        return answer
        
    except Exception as e:
        log_to_front(f"❌ Erro no modo texto: {e}")
        raise


@app.post("/chat")
async def chat_about_pid(
    pid_id: str = Query(..., description="ID do P&ID"),
    question: str = Query(..., description="Pergunta sobre o P&ID"),
    mode: str = Query(None, description="Modo: 'text', 'vision' ou None para automático (hybrid)")
):
    """
    Responde perguntas sobre um P&ID específico usando a base de conhecimento.
    
    Modos disponíveis:
    - 'text': Usa descrição ultra-completa + lista completa de equipamentos (mais rápido, mais barato)
    - 'vision': Envia imagem do P&ID para análise visual (mais preciso para perguntas visuais, mais caro)
    - None (padrão): Modo híbrido - decide automaticamente baseado na pergunta
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY não definida")
    
    if not question or len(question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Pergunta muito curta")
    
    if pid_id not in pid_knowledge_base:
        raise HTTPException(status_code=404, detail=f"P&ID '{pid_id}' não encontrado. Execute análise ou geração primeiro.")
    
    pid_info = pid_knowledge_base[pid_id]
    
    try:
        # Decide o modo
        if mode is None:
            # Modo híbrido - decide automaticamente
            mode = CHATBOT_MODE
            if mode == "hybrid":
                use_vision = should_use_vision_mode(question)
                actual_mode = "vision" if use_vision else "text"
                log_to_front(f"🤖 Modo HÍBRIDO: detectou pergunta {'VISUAL' if use_vision else 'TEXTUAL'}")
            else:
                actual_mode = mode
        else:
            actual_mode = mode
        
        # Executa no modo escolhido
        if actual_mode == "vision":
            answer = await chat_with_vision(pid_id, question, pid_info)
            mode_used = "vision"
        else:
            answer = await chat_with_text(pid_id, question, pid_info)
            mode_used = "text"
        
        return JSONResponse(content={
            "pid_id": pid_id,
            "question": question,
            "answer": answer,
            "mode_used": mode_used
        })
        
    except Exception as e:
        log_to_front(f"❌ Erro no chatbot: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")


# ============================================================
# ARMAZENAR P&ID NA BASE DE CONHECIMENTO
# ============================================================
@app.post("/store")
async def store_pid_knowledge(
    pid_id: str = Query(..., description="ID único para o P&ID"),
    data: List[Dict[str, Any]] = None
):
    """
    Armazena dados de P&ID na base de conhecimento para uso posterior no chatbot.
    """
    from datetime import datetime
    
    if not data:
        raise HTTPException(status_code=400, detail="Dados do P&ID não fornecidos")
    
    # Sanitize data to prevent NaN/Infinity values
    data = sanitize_for_json(data)
    
    pid_knowledge_base[pid_id] = {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "description": ""  # Será preenchido quando /describe for chamado
    }
    
    log_to_front(f"💾 P&ID '{pid_id}' armazenado na base de conhecimento ({len(data)} itens)")
    
    return JSONResponse(content={
        "status": "success",
        "pid_id": pid_id,
        "items_stored": len(data),
        "message": "P&ID armazenado com sucesso. Use /describe para gerar descrição."
    })


# ============================================================
# LISTAR P&IDs NA BASE DE CONHECIMENTO
# ============================================================
@app.get("/knowledge-base")
def list_knowledge_base():
    """
    Lista todos os P&IDs armazenados na base de conhecimento.
    """
    summary = []
    for pid_id, info in pid_knowledge_base.items():
        summary.append({
            "pid_id": pid_id,
            "item_count": len(info.get("data", [])),
            "timestamp": info.get("timestamp", ""),
            "has_description": bool(info.get("description", ""))
        })
    
    return JSONResponse(content={
        "total_pids": len(pid_knowledge_base),
        "pids": summary
    })


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Try to get port from environment, default to 8000
    default_port = int(os.getenv("PORT", "8000"))
    
    # List of ports to try if the default fails
    ports_to_try = [default_port, 8001, 8002, 8003, 8080, 5000]
    
    # Remove duplicates while preserving order
    ports_to_try = list(dict.fromkeys(ports_to_try))
    
    selected_port = None
    for port in ports_to_try:
        try:
            # Try to bind to the port to check if it's available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                selected_port = port
                break
        except OSError as e:
            if port == ports_to_try[-1]:
                # This was the last port to try
                print(f"❌ Não foi possível vincular a nenhuma porta. Último erro: {e}")
                print(f"💡 Portas tentadas: {', '.join(map(str, ports_to_try))}")
                print(f"💡 Solução: Especifique uma porta disponível usando PORT=<porta>")
                print(f"   Exemplo Windows: set PORT=9000 && uvicorn backend:app --reload --port 9000")
                print(f"   Exemplo Linux/Mac: PORT=9000 uvicorn backend:app --reload --port 9000")
                raise
            else:
                print(f"⚠️  Porta {port} não disponível, tentando porta {ports_to_try[ports_to_try.index(port) + 1]}...")
    
    if selected_port:
        print(f"✅ Iniciando servidor na porta {selected_port}")
        uvicorn.run("backend:app", host="0.0.0.0", port=selected_port, reload=True)
