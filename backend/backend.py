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

from fastapi import FastAPI, UploadFile, Query
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import OpenAI
from system_matcher import match_system_fullname


# =================================================
# 🔑 CONFIG OPENAI (público)
# =================================================
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "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"  # ⚠️ defina por env var em produção
)
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-5")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-4o")
OPENAI_REQUEST_TIMEOUT = int(os.getenv("OPENAI_REQUEST_TIMEOUT", "600"))


def make_client(verify_ssl: bool = True) -> OpenAI:
    http_client = httpx.Client(
        verify=certifi.where() if verify_ssl else False,
        timeout=OPENAI_REQUEST_TIMEOUT,
    )
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
    if not OPENAI_API_KEY or OPENAI_API_KEY == "COLOQUE_SUA_CHAVE_AQUI":
        log_to_front("❌ OPENAI_API_KEY não definido.")
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
Você é especialista em diagramas P&ID e símbolos ISA.
Analise a imagem com tamanho {width_mm} mm (X) x {height_mm} mm (Y).
Sempre considere:
- Eixo X = {width_mm} mm (maior dimensão).
- Eixo Y = {height_mm} mm (menor dimensão).

Extraia todos os símbolos, instrumentos, válvulas e equipamentos, seguindo estas regras:
- Inclua também símbolos sem TAG (use "tag": "N/A").
- Para instrumentos e válvulas:
  - Sempre junte prefixo + número, mesmo que apareçam separados no símbolo.
  - Exemplos: "PI 9039", "LT 101", "FV-2001".
- Use nomenclatura ISA correta para "descricao".
- Inclua conexões de processo ("from", "to").
- Coordenadas devem estar em **sistema global** da página.
- A saída deve conter somente JSON.

Formato esperado:
[
  {{
    "tag": "PI 9039",
    "descricao": "Indicador de Pressão",
    "x_mm": 120.5,
    "y_mm": 450.7,
    "from": "Bomba P-101",
    "to": "Válvula FV-202"
  }}
]
"""
    if scope == "quadrant":
        ox, oy = origin
        base += f"""
Quadrant {quad_label}: origem global ≈ ({ox}, {oy}) mm.
Se retornar coordenadas locais, **some a origem** e devolva coordenadas globais.
"""
    base += "Regras finais: saída obrigatória em JSON (lista)."
    return base.strip()


# ============================================================
# LLM CALL
# ============================================================
def llm_call(image_b64: str, prompt: str, prefer_model: str = PRIMARY_MODEL):
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
    if not OPENAI_API_KEY or OPENAI_API_KEY == "COLOQUE_SUA_CHAVE_AQUI":
        raise HTTPException(status_code=400, detail="Defina OPENAI_API_KEY.")

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
    Constrói prompt para gerar P&ID completo a partir de descrição do processo.
    A0 sheet dimensions: 1189mm x 841mm (landscape)
    """
    prompt = f"""
Você é um especialista em diagramas P&ID (Piping and Instrumentation Diagram) e símbolos ISA.

Tarefa: Gere um P&ID completo para o seguinte processo:
"{process_description}"

Especificações:
- Folha A0 em formato paisagem: {width_mm} mm (X) x {height_mm} mm (Y)
- Distribua equipamentos e instrumentos de forma lógica e organizada
- Use coordenadas X e Y apropriadas dentro dos limites da folha
- Inclua equipamentos principais (bombas, tanques, vasos, trocadores de calor, etc.)
- Inclua instrumentos de controle e medição (sensores de pressão, temperatura, vazão, nível, válvulas de controle, etc.)
- Use nomenclatura ISA correta para tags e descrições
- Defina conexões lógicas de processo (from/to) entre equipamentos

Regras para TAGs:
- Equipamentos: use prefixos como P (bomba), T (tanque), V (vaso), E (trocador), R (reator), etc. seguido de número (ex: P-101, T-201)
- Instrumentos: use nomenclatura ISA (ex: PI-101 para Indicador de Pressão, TT-201 para Transmissor de Temperatura)
- Válvulas de controle: FV, PV, LV, TV (ex: FV-101 para Válvula de Controle de Vazão)

Formato de saída: JSON com lista de equipamentos e instrumentos

Exemplo de saída esperada:
[
  {{
    "tag": "P-101",
    "tipo": "Bomba",
    "descricao": "Bomba Centrífuga",
    "x_mm": 200.0,
    "y_mm": 400.0,
    "from": "T-101",
    "to": "E-201"
  }},
  {{
    "tag": "PI-101",
    "tipo": "Instrumento",
    "descricao": "Indicador de Pressão",
    "x_mm": 250.0,
    "y_mm": 380.0,
    "from": "P-101",
    "to": "N/A"
  }}
]

Importante:
- Retorne SOMENTE o JSON (lista de objetos)
- Distribua os equipamentos de forma que o fluxo do processo seja claro (entrada à esquerda, saída à direita)
- Posicione instrumentos próximos aos equipamentos que monitoram
- Garanta que todas as coordenadas estejam dentro dos limites: X entre 0 e {width_mm}, Y entre 0 e {height_mm}
"""
    return prompt.strip()


@app.post("/generate")
async def generate_pid(
    prompt: str = Query(..., description="Descrição do processo em linguagem natural")
):
    """
    Gera P&ID a partir de descrição em linguagem natural.
    """
    if not OPENAI_API_KEY or OPENAI_API_KEY == "COLOQUE_SUA_CHAVE_AQUI":
        raise HTTPException(status_code=400, detail="Defina OPENAI_API_KEY.")
    
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
        resp = client.chat.completions.create(
            model=FALLBACK_MODEL,  # usa gpt-4o para geração de texto
            messages=[{
                "role": "user",
                "content": generation_prompt
            }],
            temperature=0.7,  # um pouco de criatividade
            timeout=OPENAI_REQUEST_TIMEOUT
        )
        
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