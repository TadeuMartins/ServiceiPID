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


def dist_mm(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dedup_items(items: List[Dict[str, Any]], page_num: int, tol_mm: float = 10.0) -> List[Dict[str, Any]]:
    seen_tag = set()
    kept: List[Dict[str, Any]] = []
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
    for it in items:
        key = (it.get("tag", "").strip().upper(), it["pagina"])
        if key[0] and key[0] != "N/A":
            if key in seen_tag:
                continue
            seen_tag.add(key)
            kept.append(it)
        else:
            kept.append(it)
    final: List[Dict[str, Any]] = []
    for it in kept:
        p = (it["x_mm"], it["y_mm"])
        if not any(dist_mm(p, (jt["x_mm"], jt["y_mm"])) <= tol_mm for jt in final):
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
    img.save(out, format="PNG")
    return out.getvalue()


def render_quadrant_png(page: fitz.Page, rect: fitz.Rect, dpi: int = 400) -> bytes:
    try:
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        raw_bytes = pix.tobytes("png")
        processed_bytes = preprocess_image(raw_bytes)
        return processed_bytes
    except Exception:
        return b""


# ============================================================
# PROMPT BUILDER
# ============================================================
def build_prompt(width_mm: float, height_mm: float, scope: str = "global", origin=(0, 0), quad_label: str = "") -> str:
    if height_mm > width_mm:
        width_mm, height_mm = height_mm, width_mm

    base = f"""
Você é um engenheiro especialista em diagramas P&ID (Piping and Instrumentation Diagram) e símbolos ISA S5.1/S5.2/S5.3.

ANÁLISE DE FLUXOGRAMA DE PROCESSO - ESPECIFICAÇÕES TÉCNICAS:
- Dimensões da página: {width_mm} mm (X - eixo horizontal) x {height_mm} mm (Y - eixo vertical)
- Sistema de coordenadas: ABSOLUTO e GLOBAL da página completa
- Orientação: X crescente da esquerda para direita, Y crescente de baixo para cima
- Compatibilidade: COMOS (Siemens) - coordenadas globais obrigatórias

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

1. COORDENADAS GLOBAIS (CRÍTICO PARA COMOS):
   - SEMPRE retorne coordenadas X e Y em relação ao TOTAL da página ({width_mm} x {height_mm} mm)
   - Mesmo em análise de quadrantes, as coordenadas devem ser GLOBAIS
   - X: 0.0 (extrema esquerda) até {width_mm} (extrema direita)
   - Y: 0.0 (base da página) até {height_mm} (topo da página)
   - Precisão: até 0.1 mm

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
   - Inclua símbolos parcialmente visíveis (estimando coordenadas)

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
"""
    if scope == "quadrant":
        ox, oy = origin
        base += f"""

ATENÇÃO - ANÁLISE DE QUADRANTE {quad_label}:
- Este é o quadrante {quad_label} da página completa
- Origem do quadrante no sistema global: X={ox} mm, Y={oy} mm
- IMPORTANTE: Retorne coordenadas GLOBAIS, NÃO coordenadas locais do quadrante
- Se você calcular coordenadas locais do quadrante, SOME a origem: X_global = X_local + {ox}, Y_global = Y_local + {oy}
- As coordenadas finais devem estar entre X: 0-{width_mm} e Y: 0-{height_mm} (sistema global da página)
"""
    base += "\n\nRETORNE SOMENTE O ARRAY JSON. Não inclua texto adicional, markdown ou explicações."
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

    log_to_front(f"🔹 Quadrant {label} | origem ≈ ({ox}, {oy}) mm")
    try:
        quad_png = render_quadrant_png(page, rect, dpi=dpi)
        quad_b64 = base64.b64encode(quad_png).decode("utf-8")
        prompt_q = build_prompt(W_mm, H_mm, "quadrant", (ox, oy), label)
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

            # corrige quadrantes
            if it.get("_src") == "quadrant":
                ox = float(it.get("_ox_mm", 0.0))
                oy = float(it.get("_oy_mm", 0.0))
                qw = float(it.get("_qw_mm", 0.0))
                qh = float(it.get("_qh_mm", 0.0))
                margin = 5.0
                if (0 - margin) <= x_in <= (qw + margin) and (0 - margin) <= y_in <= (qh + margin):
                    x_in += ox
                    y_in += oy

            # flip Y para COMOS
            y_cad = H_mm - y_in

            # clamp
            x_in = max(0.0, min(W_mm, x_in))
            y_in = max(0.0, min(H_mm, y_in))

            item = {
                "tag": it.get("tag", "N/A"),
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
Você é um engenheiro de processos sênior especializado em elaboração de diagramas P&ID (Piping and Instrumentation Diagram) 
segundo normas ISA S5.1, S5.2, S5.3 e boas práticas de engenharia de processos industriais.

TAREFA: Desenvolver um P&ID COMPLETO e DETALHADO para o seguinte processo:
"{process_description}"

ESPECIFICAÇÕES TÉCNICAS DO DIAGRAMA:
- Folha: A0 formato paisagem (landscape)
- Dimensões: {width_mm} mm (largura/X) x {height_mm} mm (altura/Y)
- Sistema de coordenadas: X crescente da esquerda para direita, Y crescente de baixo para cima
- Layout: Fluxo do processo da esquerda (entrada) para direita (saída)
- Compatibilidade: COMOS (Siemens) - coordenadas absolutas

REQUISITOS DE PROJETO - EQUIPAMENTOS PRINCIPAIS:

1. EQUIPAMENTOS DE PROCESSO (incluir conforme aplicável ao processo):
   - Bombas: P-101, P-102, etc. (centrífugas, alternativas, de vácuo)
     * Especificar: tipo, capacidade nominal, redundância (A/B se aplicável)
   - Tanques de armazenamento: T-101, TK-101, etc.
     * Incluir: indicadores de nível, válvulas de entrada/saída, vents, drenos
   - Vasos de processo: V-101, D-101 (separadores, flash drums, acumuladores)
     * Incluir: controles de pressão, nível, temperatura
   - Trocadores de calor: E-101, E-102, HE-101 (casco-tubo, placas, resfriadores a ar)
     * Incluir: instrumentação em ambos os lados (processo e utilidade)
   - Reatores: R-101, R-102 (CSTR, PFR, batelada)
     * Incluir: agitação, controle de temperatura, pressão, instrumentação analítica
   - Torres: C-101, T-101 (destilação, absorção, stripping)
     * Incluir: condensadores, refervedores, pratos/recheio, refluxo
   - Compressores/Sopradores: K-101, C-101
     * Incluir: sistemas de lubrificação, resfriamento, anti-surge
   - Fornos/Caldeiras: F-101, H-101, B-101
     * Incluir: controles de combustão, temperatura, pressão
   - Filtros/Separadores: FL-101, S-101, CY-101
   - Secadores/Evaporadores: DR-101, EV-101

2. INSTRUMENTAÇÃO COMPLETA (nomenclatura ISA S5.1):

   Pressão:
   - PI: Indicadores de pressão (manômetros locais)
   - PT: Transmissores de pressão (4-20mA para DCS/SDCD)
   - PG: Pressure gauges
   - PS/PSH/PSL: Switches (alarmes alto/baixo)
   - PCV: Válvulas de controle de pressão
   - PSV/PRV: Válvulas de segurança/alívio

   Temperatura:
   - TI: Indicadores de temperatura
   - TT: Transmissores de temperatura (termopares, RTDs)
   - TE: Elementos primários (poços termométricos)
   - TS/TSH/TSL: Switches de temperatura
   - TCV: Válvulas de controle de temperatura

   Vazão:
   - FI: Indicadores de vazão
   - FT: Transmissores de vazão
   - FE: Elementos primários (orifício, venturi, turbina, magnético, Coriolis)
   - FQ: Totalizadores
   - FS: Switches de vazão
   - FCV: Válvulas de controle de vazão

   Nível:
   - LI: Indicadores de nível
   - LT: Transmissores de nível (radar, ultrassônico, pressão diferencial)
   - LG: Visores de nível (gauge glass)
   - LS/LSH/LSL/LSHH/LSLL: Switches de nível (múltiplos níveis)
   - LCV: Válvulas de controle de nível

   Análise e qualidade:
   - AI/AT: Analisadores (pH, condutividade, O2, etc.)
   - QI/QT: Indicadores/transmissores de qualidade
   - Analisadores específicos: pH, condutividade, turbidez, concentração, cromatografia

3. VÁLVULAS E ATUADORES:
   - Válvulas de controle: FCV, PCV, LCV, TCV (com atuadores pneumáticos/elétricos)
   - Válvulas manuais: gate, globe, ball, butterfly, check, plug
   - Válvulas de segurança: PSV, TSV, PRV
   - Válvulas especiais: solenoides, diafragma, pinch
   - Indicar: tipo de atuador (pneumático, elétrico, hidráulico)
   - Indicar: ação na falha (FC - fail close, FO - fail open, FL - fail last)

4. SISTEMAS AUXILIARES E UTILIDADES:
   - Sistemas de vapor: linhas, traps, condensado
   - Água de resfriamento: entrada/retorno
   - Ar de instrumentos: distribuição, FRLs
   - Nitrogen blanketing/inertização
   - Sistemas de drenagem e ventilação
   - Sample points

5. MALHAS DE CONTROLE E AUTOMAÇÃO:
   - Controles regulatórios: PID, cascata
   - Intertravamentos de segurança (SIS)
   - Alarmes: PAH, PAL, TAH, TAL, FAH, FAL, LAH, LAL
   - Indicação local vs. sala de controle (símbolos ISA)

REGRAS PARA TAGS (CRÍTICO):
- Equipamentos principais: P-101, T-201, V-301, E-401, R-501, C-601, K-701, F-801
- Instrumentos seguir ISA: [variável][função]-[loop][sufixo]
  * Exemplos: PT-101, FT-205A, LT-301, TT-401B, PI-9039, FCV-520
- Numeração lógica por área/sistema (centenas: 100s, 200s, 300s, etc.)
- Sufixos: A/B (redundância), -1/-2 (múltiplos), H/L (high/low)

DISTRIBUIÇÃO ESPACIAL E LAYOUT:

1. Coordenadas X (horizontal):
   - Zona de entrada/alimentação: X = 100-300 mm
   - Zona de processamento principal: X = 300-800 mm
   - Zona de separação/purificação: X = 800-1000 mm
   - Zona de saída/produto: X = 1000-1100 mm
   - Margem direita: deixar ~50-100 mm

2. Coordenadas Y (vertical):
   - Equipamentos principais: Y = 300-600 mm (centro)
   - Instrumentos e válvulas: Y = 250-400 mm (próximo aos equipamentos)
   - Linhas auxiliares superiores: Y = 600-750 mm
   - Linhas auxiliares inferiores: Y = 150-250 mm
   - Manter margem superior/inferior: ~50-100 mm

3. Espaçamento:
   - Entre equipamentos principais: mínimo 100-150 mm
   - Entre instrumentos: mínimo 30-50 mm
   - Evitar sobreposições

CONEXÕES DE PROCESSO (from/to):
- Definir fluxo lógico do processo
- "from": equipamento/instrumento de origem
- "to": equipamento/instrumento de destino
- Use TAGs para referências
- Se terminal, use "N/A"

COMPLETUDE E DETALHAMENTO:
- Gere um P&ID COMPLETO com TODOS os equipamentos necessários para o processo
- Inclua TODA instrumentação de controle, monitoramento e segurança
- Não omita equipamentos auxiliares: bombas reserva, filtros, válvulas manuais
- Inclua elementos de segurança: PSVs, alarmes, intertravamentos
- Adicione instrumentação redundante onde crítico
- Considere utilidades necessárias (vapor, água, ar, etc.)
- MÍNIMO ESPERADO: 15-30 equipamentos/instrumentos para processo simples, 30-80 para processo completo

FORMATO DE SAÍDA (JSON):
[
  {{
    "tag": "T-101",
    "tipo": "Tanque",
    "descricao": "Tanque de Alimentação",
    "x_mm": 150.0,
    "y_mm": 450.0,
    "from": "N/A",
    "to": "P-101"
  }},
  {{
    "tag": "P-101",
    "tipo": "Bomba",
    "descricao": "Bomba de Alimentação Centrífuga",
    "x_mm": 250.0,
    "y_mm": 400.0,
    "from": "T-101",
    "to": "E-201"
  }},
  {{
    "tag": "FT-101",
    "tipo": "Instrumento",
    "descricao": "Transmissor de Vazão",
    "x_mm": 280.0,
    "y_mm": 380.0,
    "from": "P-101",
    "to": "FCV-101"
  }},
  {{
    "tag": "FCV-101",
    "tipo": "Válvula",
    "descricao": "Válvula de Controle de Vazão",
    "x_mm": 320.0,
    "y_mm": 380.0,
    "from": "FT-101",
    "to": "E-201"
  }},
  {{
    "tag": "PT-102",
    "tipo": "Instrumento",
    "descricao": "Transmissor de Pressão",
    "x_mm": 270.0,
    "y_mm": 420.0,
    "from": "P-101",
    "to": "N/A"
  }}
]

IMPORTANTE:
- Retorne SOMENTE o array JSON, sem texto adicional, markdown ou explicações
- Coordenadas devem estar dentro dos limites: X: 0-{width_mm}, Y: 0-{height_mm}
- Gere um diagrama COMPLETO e REALISTA para o processo especificado
- Inclua TODOS os elementos essenciais: equipamentos, instrumentação, válvulas, controles
- Use boas práticas de engenharia: redundância em sistemas críticos, instrumentação adequada
- Siga rigorosamente as normas ISA S5.1 para nomenclatura
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
            
            # Flip Y para COMOS
            y_cad = H_mm - y_in
            
            item = {
                "tag": it.get("tag", "N/A"),
                "descricao": it.get("descricao", "Equipamento"),
                "tipo": it.get("tipo", ""),
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
        
        # Retorna no mesmo formato do /analyze
        response_data = [{
            "pagina": 1,
            "modelo": FALLBACK_MODEL,
            "resultado": unique
        }]
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        log_to_front(f"❌ Erro na geração: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar P&ID: {str(e)}")


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
