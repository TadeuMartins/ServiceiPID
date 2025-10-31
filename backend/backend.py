import os
import re
import json
import math
import base64
import traceback
import time
import asyncio
from typing import List, Any, Dict, Tuple, Optional
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import numpy as np

# Try to import cv2 for advanced preprocessing - gracefully handle if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None  # Placeholder

import fitz  # PyMuPDF
import httpx, certifi
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, Query
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import OpenAI
from system_matcher import match_system_fullname, ensure_embeddings_exist

# Load environment variables from .env file
load_dotenv()

# =================================================
# 🔑 COORDINATE CONVERSION CONSTANTS
# =================================================
# PDF uses PostScript points: 1 point = 1/72 inch
# 1 inch = 25.4 mm
# Therefore: 1 point = 25.4/72 mm (exact conversion)
PT_TO_MM = 25.4 / 72  # Exact: 0.3527777... mm per point
MM_TO_PT = 72 / 25.4  # Exact: 2.8346456... points per mm

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
    
    # Check and ensure embeddings exist
    log_to_front("🔍 Verificando embeddings...")
    ensure_embeddings_exist()
    
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
    """
    Convert PDF points to millimeters with exact precision.
    
    Uses the exact conversion factor: 1 point = 25.4/72 mm
    This ensures coordinates are identical to the PDF.
    
    Args:
        points: Coordinate value in PostScript points
        
    Returns:
        Coordinate value in millimeters (rounded to 3 decimal places for precision)
    """
    return round(points * PT_TO_MM, 3)


def mm_to_points(mm: float) -> float:
    """
    Convert millimeters to PDF points with exact precision.
    
    Uses the exact conversion factor: 1 mm = 72/25.4 points
    This is the inverse of points_to_mm and ensures perfect round-trip conversion.
    
    Args:
        mm: Coordinate value in millimeters
        
    Returns:
        Coordinate value in PostScript points
    """
    return mm * MM_TO_PT


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


def assign_no_tag_identifiers(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign sequential NO-TAG identifiers to equipment without valid tags.
    Equipment with tag "N/A" will be renamed based on instrument type:
    - PT-notag1, PT-notag2 for Transmissor de Pressão
    - PI-notag1, PI-notag2 for Indicador de Pressão
    - etc.
    """
    # Mapping from description keywords to instrument prefixes
    instrument_type_mapping = {
        # Pressure instruments
        "transmissor de pressão": "PT",
        "pressure transmitter": "PT",
        "indicador de pressão": "PI",
        "pressure indicator": "PI",
        "chave de pressão alta": "PSH",
        "pressure switch high": "PSH",
        "chave de pressão baixa": "PSL",
        "pressure switch low": "PSL",
        
        # Temperature instruments
        "controlador indicativo de temperatura": "TIC",
        "temperature indicating controller": "TIC",
        "indicador de temperatura": "TI",
        "temperature indicator": "TI",
        "transmissor de temperatura": "TT",
        "temperature transmitter": "TT",
        
        # Level instruments
        "transmissor de nível": "LT",
        "level transmitter": "LT",
        "controlador indicação de nível": "LIC",
        "controlador de nível": "LIC",
        "level indicating controller": "LIC",
        "level controller": "LIC",
        
        # Flow instruments
        "indicador de vazão": "FI",
        "flow indicator": "FI",
        "transmissor de vazão": "FT",
        "flow transmitter": "FT",
        "controlador de vazão": "FIC",
        "flow indicating controller": "FIC",
        "flow controller": "FIC",
        "válvula de controle de vazão": "FV",
        "flow control valve": "FV",
    }
    
    # Track counters for each instrument prefix
    prefix_counters = {}
    
    for item in items:
        if item.get("tag") == "N/A":
            descricao = item.get("descricao", "").lower()
            
            # Detect instrument type from description
            prefix = None
            for keyword, instrument_prefix in instrument_type_mapping.items():
                if keyword in descricao:
                    prefix = instrument_prefix
                    break
            
            # If no specific instrument type is detected, use generic NO-TAG
            if prefix is None:
                prefix = "NO-TAG"
            
            # Get or initialize counter for this prefix
            if prefix not in prefix_counters:
                prefix_counters[prefix] = 1
            
            # Assign tag based on prefix
            if prefix == "NO-TAG":
                item["tag"] = f"NO-TAG{prefix_counters[prefix]}"
            else:
                item["tag"] = f"{prefix}-notag{prefix_counters[prefix]}"
            
            prefix_counters[prefix] += 1
    
    return items


def estimate_symbol_size(tag: str, descricao: str) -> float:
    """
    Estimate typical symbol size in mm based on equipment type.
    Used for dynamic deduplication tolerance.
    
    Returns:
        Estimated symbol size in mm (for tolerance calculation)
    """
    tag_upper = tag.upper()
    desc_lower = descricao.lower()
    
    # Large equipment - bigger symbols, larger tolerance
    large_equipment_keywords = [
        "tank", "tanque", "vessel", "vaso", "tower", "torre", "column", "coluna",
        "reactor", "reator", "furnace", "forno", "boiler", "caldeira", "heat exchanger",
        "trocador", "exchanger", "compressor", "compressor"
    ]
    
    # Medium equipment
    medium_equipment_keywords = [
        "pump", "bomba", "filter", "filtro", "separator", "separador",
        "drum", "tambor", "accumulator", "acumulador"
    ]
    
    # Small instruments and valves
    small_instrument_prefixes = ["PT", "TT", "FT", "LT", "PI", "TI", "FI", "LI", 
                                  "PSV", "PCV", "FCV", "TCV", "LCV", "VALVE", "VÁLVULA"]
    
    # Check for large equipment
    for keyword in large_equipment_keywords:
        if keyword in desc_lower:
            return 50.0  # Large symbols, use larger tolerance
    
    # Check for small instruments
    for prefix in small_instrument_prefixes:
        if tag_upper.startswith(prefix) or prefix.lower() in desc_lower:
            return 10.0  # Small symbols, use smaller tolerance
    
    # Check for medium equipment
    for keyword in medium_equipment_keywords:
        if keyword in desc_lower:
            return 25.0
    
    # Default medium size
    return 20.0


def calculate_dynamic_tolerance(item: Dict[str, Any], base_tol_mm: float = 10.0) -> float:
    """
    Calculate dynamic tolerance for deduplication based on symbol characteristics.
    
    Args:
        item: Equipment/instrument item with tag and description
        base_tol_mm: Base tolerance in mm
    
    Returns:
        Adjusted tolerance in mm
    """
    tag = item.get("tag", "N/A")
    descricao = item.get("descricao", "")
    
    # Estimate symbol size
    estimated_size = estimate_symbol_size(tag, descricao)
    
    # Scale tolerance based on estimated size
    # Larger symbols get proportionally larger tolerance
    size_factor = estimated_size / 20.0  # Normalize to medium size
    
    # Apply factor with reasonable bounds
    dynamic_tol = base_tol_mm * size_factor
    
    # Clamp to reasonable range (5mm to 100mm)
    dynamic_tol = max(5.0, min(100.0, dynamic_tol))
    
    return dynamic_tol


def dist_mm(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dedup_items(items: List[Dict[str, Any]], page_num: int, tol_mm: float = 10.0, 
                use_dynamic_tolerance: bool = True, log_metadata: bool = False) -> List[Dict[str, Any]]:
    """
    Remove duplicatas com base em TAG e proximidade espacial.
    
    Args:
        items: List of items to deduplicate
        page_num: Page number
        tol_mm: Base tolerance in mm
        use_dynamic_tolerance: Use dynamic tolerance based on symbol size
        log_metadata: Log deduplication metadata for auditing
    
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
    dedup_metadata = []  # Track deduplication decisions
    
    for it in items:
        tag = it.get("tag", "").strip().upper()
        pos = (it["x_mm"], it["y_mm"])
        page = it["pagina"]
        
        # Calculate dynamic tolerance for this item
        if use_dynamic_tolerance:
            item_tolerance = calculate_dynamic_tolerance(it, tol_mm)
        else:
            item_tolerance = tol_mm
        
        is_duplicate = False
        duplicate_reason = None
        
        # Para itens com TAG válida (não N/A)
        if tag and tag != "N/A":
            tag_key = (tag, page)
            
            # Verifica se já existe esse mesmo TAG
            if tag_key in seen_tags:
                # Verifica se está próximo de alguma posição existente com MESMO TAG
                for existing_pos in seen_tags[tag_key]:
                    distance = dist_mm(pos, existing_pos)
                    if distance <= item_tolerance:
                        is_duplicate = True
                        duplicate_reason = f"Same tag '{tag}' within {distance:.1f}mm (tol={item_tolerance:.1f}mm)"
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
                    distance = dist_mm(pos, existing_pos)
                    if distance <= item_tolerance:
                        # Item sem TAG muito próximo de outro item - provavelmente duplicata
                        is_duplicate = True
                        duplicate_reason = f"No tag, within {distance:.1f}mm of {existing.get('tag', 'N/A')} (tol={item_tolerance:.1f}mm)"
                        break
        
        # Log metadata if requested
        if log_metadata:
            dedup_metadata.append({
                "tag": tag,
                "position": pos,
                "tolerance_used": item_tolerance,
                "is_duplicate": is_duplicate,
                "reason": duplicate_reason,
                "kept": not is_duplicate
            })
        
        # Se não é duplicata, adiciona à lista final
        if not is_duplicate:
            # Add deduplication metadata to item
            if log_metadata:
                it["_dedup_tolerance"] = item_tolerance
            final.append(it)
    
    return final


# ============================================================
# SUBDIVISÃO EM QUADRANTES
# ============================================================
def page_quadrants_with_overlap(page: fitz.Page, grid_x: int = 3, grid_y: int = 3, 
                                 overlap_percent: float = 0.0) -> List[Tuple[int, int, fitz.Rect, str]]:
    """
    Generate quadrants with optional overlap to minimize edge artifacts.
    
    Args:
        page: PyMuPDF page object
        grid_x: Number of columns
        grid_y: Number of rows
        overlap_percent: Percentage of overlap (0.0 to 0.5, where 0.5 = 50% offset)
    
    Returns:
        List of (gx, gy, rect, label) tuples
    """
    # Use page.rect directly (respects rotation metadata)
    rect = page.rect
    W, H = rect.width, rect.height
    
    # Handle landscape/portrait orientation
    if H > W:
        W, H = H, W
    
    quads = []
    
    # Generate base grid
    for gy in range(grid_y):
        for gx in range(grid_x):
            x0 = (W / grid_x) * gx
            y0 = (H / grid_y) * gy
            x1 = x0 + (W / grid_x)
            y1 = y0 + (H / grid_y)
            
            quad_rect = fitz.Rect(x0, y0, x1, y1)
            quad_rect = fitz.Rect(
                max(rect.x0, quad_rect.x0),
                max(rect.y0, quad_rect.y0),
                min(rect.x1, quad_rect.x1),
                min(rect.y1, quad_rect.y1),
            )
            
            if quad_rect.width > 0 and quad_rect.height > 0:
                label = f"{gy+1}-{gx+1}"
                quads.append((gx, gy, quad_rect, label))
    
    # Generate overlapped quadrants with offset (if enabled)
    if overlap_percent > 0:
        offset_x = (W / grid_x) * overlap_percent
        offset_y = (H / grid_y) * overlap_percent
        
        for gy in range(grid_y - 1):  # Don't create offset beyond last row
            for gx in range(grid_x - 1):  # Don't create offset beyond last column
                x0 = (W / grid_x) * gx + offset_x
                y0 = (H / grid_y) * gy + offset_y
                x1 = x0 + (W / grid_x)
                y1 = y0 + (H / grid_y)
                
                quad_rect = fitz.Rect(x0, y0, x1, y1)
                quad_rect = fitz.Rect(
                    max(rect.x0, quad_rect.x0),
                    max(rect.y0, quad_rect.y0),
                    min(rect.x1, quad_rect.x1),
                    min(rect.y1, quad_rect.y1),
                )
                
                if quad_rect.width > 0 and quad_rect.height > 0:
                    label = f"{gy+1}-{gx+1}-overlap"
                    quads.append((gx, gy, quad_rect, label))
    
    return quads


def page_quadrants(page: fitz.Page, grid_x: int = 3, grid_y: int = 3):
    """Legacy quadrant generation - kept for backward compatibility"""
    quads_with_labels = page_quadrants_with_overlap(page, grid_x, grid_y, overlap_percent=0.0)
    # Return in old format (without label)
    return [(gx, gy, rect) for gx, gy, rect, label in quads_with_labels]
    return quads


def preprocess_image_adaptive(img_bytes: bytes, method: str = "hybrid") -> bytes:
    """
    Adaptive image preprocessing with multiple methods.
    
    Args:
        img_bytes: Raw image bytes
        method: Preprocessing method - "hybrid" (grayscale + enhanced + adaptive), 
                "binary" (old fixed threshold), "grayscale" (contrast enhanced only)
    
    Returns:
        Preprocessed image bytes
    """
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    
    # Normalize scale before upscaling for consistency
    # Target standard DPI equivalent
    target_width = max(img.width, 2000)
    if img.width < target_width:
        scale_factor = target_width / img.width
        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        img = img.resize(new_size, Image.LANCZOS)
    
    if method == "binary":
        # Old fixed threshold method (for backward compatibility)
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.point(lambda p: 255 if p > 180 else 0)
        if img.getpixel((0, 0)) < 128:
            img = ImageOps.invert(img)
            
    elif method == "grayscale":
        # Enhanced grayscale only
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        
    elif method == "hybrid":
        # Hybrid approach: adaptive thresholding with morphology
        if not CV2_AVAILABLE:
            # Fallback to grayscale if OpenCV not available
            log_to_front("⚠️ OpenCV not available, falling back to grayscale preprocessing")
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Sharpness(img).enhance(1.2)
        else:
            # Convert to numpy for OpenCV operations
            img_np = np.array(img)
            
            # Enhance contrast
            img_enhanced = ImageEnhance.Contrast(img).enhance(1.5)
            img_np = np.array(img_enhanced)
            
            # Apply adaptive thresholding (block-based)
            # Use Gaussian adaptive threshold for better handling of varying lighting
            binary = cv2.adaptiveThreshold(
                img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 2
            )
            
            # Light morphological operations to preserve thin lines
            # Use smaller kernel to avoid losing small symbols
            kernel = np.ones((2, 2), np.uint8)
            
            # Opening to remove small noise
            opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Closing to connect nearby components (only if it helps)
            # Use very conservative closing to avoid merging separate symbols
            kernel_close = np.ones((2, 2), np.uint8)
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close, iterations=1)
            
            # Check if background is dark (invert if needed)
            if np.mean(closed) < 128:
                closed = cv2.bitwise_not(closed)
            
            # Convert back to PIL
            img = Image.fromarray(closed)
    
    else:
        raise ValueError(f"Unknown preprocessing method: {method}")
    
    # Final upscale to 2x for better detail
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


def preprocess_image(img_bytes: bytes) -> bytes:
    """Legacy preprocessing function - uses hybrid method by default"""
    return preprocess_image_adaptive(img_bytes, method="hybrid")


def render_quadrant_png(page: fitz.Page, rect: fitz.Rect, dpi: int = 400, 
                        handle_rotation: bool = True) -> bytes:
    """
    Render a quadrant of a PDF page to PNG with preprocessing.
    
    Args:
        page: PyMuPDF page object
        rect: Rectangle to render
        dpi: Resolution
        handle_rotation: Apply rotation correction based on page.rotation metadata
    
    Returns:
        Preprocessed PNG bytes
    """
    try:
        # Get page rotation metadata
        rotation = page.rotation if handle_rotation else 0
        
        # Render with automatic rotation handling by PyMuPDF
        # PyMuPDF's get_pixmap handles rotation automatically if we use matrix
        if rotation != 0:
            # Create rotation matrix
            mat = fitz.Matrix(1, 1).prerotate(rotation)
            pix = page.get_pixmap(dpi=dpi, clip=rect, matrix=mat)
        else:
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
# ITEM 6: POST-LLM VALIDATION WITH OCR
# ============================================================
def validate_tag_with_ocr(page: fitz.Page, item: Dict[str, Any], dpi: int = 300, 
                          search_radius_mm: float = 50.0) -> Dict[str, Any]:
    """
    Validate equipment TAG using OCR on nearby region.
    
    Args:
        page: PyMuPDF page object
        item: Equipment item with x_mm, y_mm coordinates and tag
        dpi: Resolution for OCR
        search_radius_mm: Radius in mm to search for TAG text
    
    Returns:
        Validation result with OCR text, confidence, and match status
    """
    try:
        import pytesseract
        from PIL import Image
        
        # Convert coordinates to points
        x_pts = mm_to_points(item["x_mm"])
        y_pts = mm_to_points(item["y_mm"])
        search_radius_pts = mm_to_points(search_radius_mm)
        
        # Create search rectangle around the item
        rect = fitz.Rect(
            x_pts - search_radius_pts,
            y_pts - search_radius_pts,
            x_pts + search_radius_pts,
            y_pts + search_radius_pts
        )
        
        # Clip to page bounds
        rect = rect & page.rect
        
        # Render region
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        img_bytes = pix.tobytes("png")
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(img_bytes))
        
        # Perform OCR
        ocr_text = pytesseract.image_to_string(img, config='--psm 6')
        ocr_text_clean = ocr_text.strip().upper()
        
        # Clean and normalize TAG
        expected_tag = str(item.get("tag", "")).strip().upper()
        expected_tag_clean = re.sub(r'[^A-Z0-9]', '', expected_tag)
        
        # Check if TAG appears in OCR text
        ocr_text_normalized = re.sub(r'[^A-Z0-9]', '', ocr_text_clean)
        tag_found = expected_tag_clean in ocr_text_normalized if expected_tag_clean else False
        
        # Calculate confidence score (0-100)
        if tag_found:
            confidence = min(100, int(80 + 20 * (len(expected_tag_clean) / max(1, len(ocr_text_normalized)))))
        else:
            # Check for partial match
            if expected_tag_clean and any(c in ocr_text_normalized for c in expected_tag_clean):
                confidence = 30
            else:
                confidence = 0
        
        return {
            "ocr_text": ocr_text.strip(),
            "ocr_text_normalized": ocr_text_normalized,
            "expected_tag": expected_tag,
            "tag_found": tag_found,
            "confidence": confidence,
            "validation_passed": confidence >= 50,
            "search_region": {
                "x0": rect.x0,
                "y0": rect.y0,
                "x1": rect.x1,
                "y1": rect.y1
            }
        }
    except ImportError:
        return {
            "error": "pytesseract not installed",
            "validation_passed": True,  # Skip validation if OCR not available
            "confidence": 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "validation_passed": True,  # Don't fail on OCR errors
            "confidence": 0
        }


def validate_symbol_type(item: Dict[str, Any], description: str) -> Dict[str, Any]:
    """
    Validate equipment type based on TAG prefix and description.
    Uses pattern matching to verify consistency.
    
    Args:
        item: Equipment item with tag
        description: Equipment description
    
    Returns:
        Validation result with matched type and confidence
    """
    tag = str(item.get("tag", "")).strip().upper()
    desc_lower = description.lower()
    
    # ISA S5.1 standard instrument tags
    instrument_types = {
        "PT": ["pressure", "transmitter", "transmissor de pressão", "pressão"],
        "TT": ["temperature", "transmitter", "transmissor de temperatura", "temperatura"],
        "FT": ["flow", "transmitter", "transmissor de vazão", "vazão"],
        "LT": ["level", "transmitter", "transmissor de nível", "nível"],
        "PI": ["pressure", "indicator", "indicador de pressão"],
        "TI": ["temperature", "indicator", "indicador de temperatura"],
        "FI": ["flow", "indicator", "indicador de vazão"],
        "LI": ["level", "indicator", "indicador de nível"],
        "PSV": ["pressure", "safety", "valve", "válvula de segurança", "alívio"],
        "FCV": ["flow", "control", "valve", "válvula de controle de vazão"],
        "PCV": ["pressure", "control", "valve", "válvula de controle de pressão"],
        "TCV": ["temperature", "control", "valve", "válvula de controle de temperatura"],
        "LCV": ["level", "control", "valve", "válvula de controle de nível"],
    }
    
    # Equipment tags
    equipment_types = {
        "P": ["pump", "bomba"],
        "T": ["tank", "tanque"],
        "TK": ["tank", "tanque"],
        "V": ["vessel", "vaso", "vasel"],
        "E": ["exchanger", "heat", "trocador"],
        "R": ["reactor", "reator"],
        "C": ["compressor", "column", "tower", "compressor", "coluna", "torre"],
        "K": ["compressor", "compressor"],
        "F": ["furnace", "forno"],
    }
    
    # Extract prefix from TAG
    tag_prefix = ""
    for prefix in sorted(list(instrument_types.keys()) + list(equipment_types.keys()), key=len, reverse=True):
        if tag.startswith(prefix):
            tag_prefix = prefix
            break
    
    if not tag_prefix:
        return {
            "tag_prefix": None,
            "expected_keywords": [],
            "found_keywords": [],
            "type_match": False,
            "confidence": 0,
            "validation_passed": True  # Don't fail on unknown tags
        }
    
    # Get expected keywords
    expected_keywords = instrument_types.get(tag_prefix) or equipment_types.get(tag_prefix) or []
    
    # Check if any keyword appears in description
    found_keywords = [kw for kw in expected_keywords if kw in desc_lower]
    
    # Calculate confidence
    if found_keywords:
        confidence = min(100, int(60 + 40 * (len(found_keywords) / max(1, len(expected_keywords)))))
        type_match = True
    else:
        confidence = 20  # Low confidence but not zero
        type_match = False
    
    return {
        "tag_prefix": tag_prefix,
        "expected_keywords": expected_keywords,
        "found_keywords": found_keywords,
        "type_match": type_match,
        "confidence": confidence,
        "validation_passed": confidence >= 40
    }


# ============================================================
# ITEM 7: GEOMETRIC CENTER REFINEMENT
# ============================================================
def refine_geometric_center(page: fitz.Page, item: Dict[str, Any], 
                            dpi: int = 400, search_radius_mm: float = 30.0) -> Dict[str, Any]:
    """
    Refine equipment coordinates to geometric center using image processing.
    
    Args:
        page: PyMuPDF page object
        item: Equipment item with x_mm, y_mm coordinates
        dpi: Resolution for analysis
        search_radius_mm: Radius in mm to search for symbol
    
    Returns:
        Refined coordinates and metadata
    """
    try:
        from skimage import measure
        
        # Convert coordinates to points
        x_pts = mm_to_points(item["x_mm"])
        y_pts = mm_to_points(item["y_mm"])
        search_radius_pts = mm_to_points(search_radius_mm)
        
        # Create search rectangle around the item
        rect = fitz.Rect(
            x_pts - search_radius_pts,
            y_pts - search_radius_pts,
            x_pts + search_radius_pts,
            y_pts + search_radius_pts
        )
        
        # Clip to page bounds
        rect = rect & page.rect
        
        # Render region
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        img_bytes = pix.tobytes("png")
        
        # Convert to numpy array
        img = Image.open(io.BytesIO(img_bytes)).convert('L')
        img_array = np.array(img)
        
        # Create binary mask using adaptive thresholding
        if not CV2_AVAILABLE:
            # Fallback to simple thresholding if OpenCV not available
            threshold = np.mean(img_array)
            binary = (img_array < threshold).astype(np.uint8) * 255
        else:
            binary = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 2
            )
        
        # Find connected components
        labels = measure.label(binary, connectivity=2)
        
        # Get properties of regions
        regions = measure.regionprops(labels)
        
        if not regions:
            # No regions found, return original coordinates
            return {
                "refined_x_mm": item["x_mm"],
                "refined_y_mm": item["y_mm"],
                "offset_x_mm": 0.0,
                "offset_y_mm": 0.0,
                "refinement_applied": False,
                "reason": "No regions detected",
                "confidence": 0
            }
        
        # Find the largest region (likely the main symbol)
        largest_region = max(regions, key=lambda r: r.area)
        
        # Calculate center of mass
        centroid_y, centroid_x = largest_region.centroid
        
        # Convert centroid from image coordinates to global coordinates
        # Image coordinates are relative to search rectangle
        centroid_x_pts = rect.x0 + (centroid_x / img.width) * rect.width
        centroid_y_pts = rect.y0 + (centroid_y / img.height) * rect.height
        
        # Convert to mm
        refined_x_mm = points_to_mm(centroid_x_pts)
        refined_y_mm = points_to_mm(centroid_y_pts)
        
        # Calculate offset
        offset_x_mm = refined_x_mm - item["x_mm"]
        offset_y_mm = refined_y_mm - item["y_mm"]
        
        # Only apply refinement if offset is reasonable (< search_radius_mm)
        offset_magnitude = math.hypot(offset_x_mm, offset_y_mm)
        apply_refinement = offset_magnitude < search_radius_mm
        
        if apply_refinement:
            # Calculate confidence based on region properties
            # Higher confidence for larger, more compact regions
            compactness = largest_region.area / (largest_region.bbox_area + 1)
            confidence = min(100, int(50 + 50 * compactness))
        else:
            confidence = 0
            refined_x_mm = item["x_mm"]
            refined_y_mm = item["y_mm"]
            offset_x_mm = 0.0
            offset_y_mm = 0.0
        
        return {
            "refined_x_mm": refined_x_mm,
            "refined_y_mm": refined_y_mm,
            "offset_x_mm": offset_x_mm,
            "offset_y_mm": offset_y_mm,
            "offset_magnitude_mm": offset_magnitude,
            "refinement_applied": apply_refinement,
            "confidence": confidence,
            "region_area": largest_region.area,
            "region_bbox": largest_region.bbox,
            "num_regions": len(regions)
        }
        
    except ImportError:
        return {
            "refined_x_mm": item["x_mm"],
            "refined_y_mm": item["y_mm"],
            "offset_x_mm": 0.0,
            "offset_y_mm": 0.0,
            "refinement_applied": False,
            "error": "scikit-image not installed",
            "confidence": 0
        }
    except Exception as e:
        return {
            "refined_x_mm": item["x_mm"],
            "refined_y_mm": item["y_mm"],
            "offset_x_mm": 0.0,
            "offset_y_mm": 0.0,
            "refinement_applied": False,
            "error": str(e),
            "confidence": 0
        }


# ============================================================
# PROMPT BUILDER
# ============================================================
def build_prompt(width_mm: float, height_mm: float, scope: str = "global", origin=(0, 0), quad_label: str = "", diagram_type: str = "pid") -> str:
    if height_mm > width_mm:
        width_mm, height_mm = height_mm, width_mm

    # Determine the type of diagram we're analyzing
    is_electrical = diagram_type.lower() == "electrical"
    
    if is_electrical:
        diagram_name = "Diagrama Elétrico (Electrical Diagram)"
        diagram_description = "diagramas elétricos (Electrical Diagrams) e símbolos elétricos padrão"
        analysis_type = "ANÁLISE DE DIAGRAMA ELÉTRICO - ESPECIFICAÇÕES TÉCNICAS:"
        objective = "Extrair TODOS os elementos do diagrama elétrico com máxima precisão técnica."
    else:
        diagram_name = "P&ID (Piping and Instrumentation Diagram)"
        diagram_description = "diagramas P&ID (Piping and Instrumentation Diagram) e símbolos ISA S5.1/S5.2/S5.3"
        analysis_type = "ANÁLISE DE FLUXOGRAMA DE PROCESSO - ESPECIFICAÇÕES TÉCNICAS:"
        objective = "Extrair TODOS os elementos do fluxograma de processo com máxima precisão técnica."

    base = f"""
Você é um engenheiro especialista em {diagram_description}.

{analysis_type}"""
    
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
OBJETIVO: {objective}

EQUIPAMENTOS A IDENTIFICAR (lista não exaustiva):"""

    if is_electrical:
        base += """
1. Componentes elétricos principais:
   - Transformadores (power transformers, distribution transformers): TR-XXX, T-XXX
   - Motores elétricos (AC/DC motors, synchronous/asynchronous): M-XXX, MOT-XXX
   - Geradores: G-XXX, GEN-XXX
   - Painéis elétricos (switchboards, MCCs): PNL-XXX, MCC-XXX
   - Disjuntores (circuit breakers): CB-XXX, DJ-XXX
   - Fusíveis: F-XXX, FUS-XXX
   - Chaves seccionadoras (disconnectors): DS-XXX, SEC-XXX
   - Relés de proteção: REL-XXX, PROT-XXX
   - Contatores: C-XXX, K-XXX
   - Barramentos (busbars): BB-XXX, BUS-XXX

2. Dispositivos de proteção e controle:
   - Relés de sobrecorrente: 50/51
   - Relés de proteção diferencial: 87
   - Relés de subtensão/sobretensão: 27/59
   - Relés de frequência: 81
   - Dispositivos de proteção contra surtos: SPD, DPS
   - Sistemas de aterramento: GND, PE

3. Instrumentação elétrica:
   - Medidores de energia (energy meters): EM-XXX
   - Amperímetros: A-XXX
   - Voltímetros: V-XXX
   - Wattímetros: W-XXX
   - Indicadores de fator de potência: PF-XXX
   - Transdutores de corrente (CTs): CT-XXX
   - Transdutores de potencial (VTs/PTs): VT-XXX, PT-XXX

4. Cabos e conexões:
   - Linhas de potência (power lines)
   - Cabos de controle
   - Conexões e terminais
   - Eletrodutos e bandejas

5. Outros elementos:
   - Sistemas de backup/UPS
   - Baterias
   - Inversores e conversores
   - Soft-starters e drives de velocidade variável (VFDs)
   - Capacitores para correção de fator de potência
"""
    else:
        base += """
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

1. COORDENADAS (PRECISÃO MÁXIMA - CRÍTICO):
   - Meça as coordenadas com MÁXIMA PRECISÃO ABSOLUTA em relação à imagem que você está vendo
   - As coordenadas devem referenciar o CENTRO GEOMÉTRICO EXATO do equipamento ou instrumento
   - Para símbolos com contorno/borda visível: meça o centro entre as extremidades esquerda-direita e topo-base
   - Para símbolos circulares (bombas, tanques): identifique o centro visual do círculo
   - Para símbolos retangulares (trocadores, vasos): meça o ponto médio da figura
   - Para instrumentos (círculos pequenos com TAG): meça o centro do círculo do símbolo ISA
   - NÃO retorne coordenadas de tubulações, linhas ou elementos auxiliares
   - Precisão OBRIGATÓRIA: até 0.1 mm - cada milímetro conta!
   - Se um equipamento estiver parcialmente visível, estime o centro baseado na parte visível
   - DUPLA VERIFICAÇÃO: Após medir, verifique se a coordenada está no centro visual do símbolo
   
   **MÉTODO DE MEDIÇÃO (PASSO A PASSO):**
   1. Identifique os limites visuais do símbolo (esquerda, direita, topo, base)
   2. Calcule X = (limite_esquerdo + limite_direito) / 2
   3. Calcule Y = (limite_topo + limite_base) / 2
   4. Verifique se o ponto (X,Y) está no centro visual do símbolo
   5. Ajuste se necessário para garantir precisão máxima
   
   **ATENÇÃO ESPECIAL AO EIXO Y:**
   - O eixo Y NÃO está invertido - Y cresce de cima para baixo (padrão de imagem)
   - Y = 0.0 está no TOPO da imagem/quadrante
   - Y = {height_mm} está na BASE da imagem/quadrante
   - NUNCA inverta coordenadas Y - use a posição visual direta
   - Exemplo: Um equipamento no topo da imagem tem Y próximo de 0, não de {height_mm}
   - Exemplo: Um equipamento na base da imagem tem Y próximo de {height_mm}, não de 0

2. VALIDAÇÃO DE COORDENADAS (OBRIGATÓRIA):
   - Antes de retornar coordenadas, SEMPRE verifique se fazem sentido visualmente
   - Compare com conexões adjacentes: equipamentos conectados devem ter coordenadas próximas
   - Se um equipamento está à esquerda de outro, seu X deve ser menor
   - Se um equipamento está acima de outro, seu Y deve ser menor (não maior!)
   - Cruze informações visuais para validar: "from" e "to" devem estar espacialmente coerentes
   - VALIDAÇÃO FINAL: Mentalmente sobreponha as coordenadas na imagem - devem coincidir perfeitamente
   - Se houver dúvida, refaça a medição com mais atenção aos limites do símbolo

3. TAGS E IDENTIFICAÇÃO:
   - Capture TAGs completas mesmo se prefixo e número estiverem separados visualmente
   - Exemplos: "PI 9039", "LT 101", "FV-2001", "P 101 A/B"
   - Se não houver TAG visível, use "tag": "N/A" mas capture o equipamento
   - Inclua sufixos importantes: A/B (redundância), -1/-2 (numeração)

4. DESCRIÇÕES (nomenclatura ISA S5.1):
   - Use terminologia técnica precisa segundo ISA
   - Exemplos: "Transmissor de Pressão", "Válvula de Controle de Vazão", "Bomba Centrífuga"
   - Especifique tipo quando visível: "Trocador de Calor Casco-Tubo", "Válvula Globo"

5. CONEXÕES DE PROCESSO (from/to):
   - Identifique fluxo do processo: equipamento de origem → equipamento de destino
   - Use TAGs dos equipamentos conectados
   - Se não houver conexão clara, use "N/A"
   - Exemplo: "from": "T-101", "to": "P-201"
   - VALIDAÇÃO: As coordenadas dos equipamentos em "from" e "to" devem estar próximas à tubulação que os conecta

6. COMPLETUDE:
   - Extraia TODOS os símbolos visíveis, mesmo sem TAG
   - Não omita instrumentos pequenos ou auxiliares
   - Capture válvulas manuais, drenos, vents, samplers
   - Inclua símbolos parcialmente visíveis (estimando coordenadas do centro)

FORMATO DE SAÍDA (JSON OBRIGATÓRIO):

IMPORTANTE SOBRE COORDENADAS:
- x_mm e y_mm devem ser números com precisão de 0.1 mm (uma casa decimal)
- Use valores como 234.5, 567.8, 1045.3 (NÃO arredonde para inteiros)
- Garanta que as coordenadas referenciam o centro geométrico exato do símbolo
- Exemplo: Para uma bomba centralizada em (234.5, 567.8), NÃO use (234, 567) ou (235, 568)

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
async def process_quadrant(gx, gy, rect, page, W_mm, H_mm, dpi, diagram_type="pid"):
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
        prompt_q = build_prompt(rect_w_mm, rect_h_mm, "quadrant", (ox, oy), label, diagram_type)
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
    tol_mm: float = Query(10.0, ge=1.0, le=50.0),
    use_overlap: bool = Query(False, description="Use overlapping windows for better edge coverage"),
    use_dynamic_tolerance: bool = Query(True, description="Use dynamic tolerance based on symbol size"),
    use_ocr_validation: bool = Query(False, description="Validate TAGs using OCR (requires pytesseract)"),
    use_geometric_refinement: bool = Query(True, description="Refine coordinates to geometric center (enabled by default for better accuracy)"),
    diagram_type: str = Query("pid", description="Diagram type: 'pid' for P&ID or 'electrical' for Electrical Diagram")
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
            prompt_global = build_prompt(W_mm, H_mm, "global", diagram_type=diagram_type)
            model_used, resp = llm_call(page_b64, prompt_global)
            raw = resp.choices[0].message.content if resp and resp.choices else ""
            log_to_front(f"🌐 RAW GLOBAL OUTPUT (page {page_num}): {raw[:500]}")
            global_list = ensure_json_list(raw)
        except Exception as e:
            log_to_front(f"⚠️ Global falhou na página {page_num}: {e}")
            global_list = []

        log_to_front(f"🌐 Global → itens: {len(global_list)}")

        if grid > 1:
            # Use new overlapping quadrants if enabled
            if use_overlap:
                log_to_front(f"📊 Gerando quadrantes com sobreposição de 50%...")
                quads_with_labels = page_quadrants_with_overlap(page, grid_x=grid, grid_y=grid, overlap_percent=0.5)
                tasks = [process_quadrant(gx, gy, rect, page, W_mm, H_mm, dpi, diagram_type) for gx, gy, rect, label in quads_with_labels]
            else:
                quads = page_quadrants(page, grid_x=grid, grid_y=grid)
                tasks = [process_quadrant(gx, gy, rect, page, W_mm, H_mm, dpi, diagram_type) for gx, gy, rect in quads]
            
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

            # Validate coordinates before clamping
            x_was_clamped = x_in < 0.0 or x_in > W_mm
            y_was_clamped = y_in < 0.0 or y_in > H_mm
            
            # clamp to page bounds
            x_in_orig = x_in
            y_in_orig = y_in
            x_in = max(0.0, min(W_mm, x_in))
            y_in = max(0.0, min(H_mm, y_in))
            
            # Log warning if coordinates were out of bounds (may indicate extraction issue)
            if x_was_clamped or y_was_clamped:
                log_to_front(f"   ⚠️ Coordenadas ajustadas para {tag}: ({x_in_orig:.1f}, {y_in_orig:.1f}) → ({x_in:.1f}, {y_in:.1f})")

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
                match = match_system_fullname(item["tag"], item["descricao"], tipo, diagram_type)
                item.update(match)
            except Exception as e:
                item.update({
                    "SystemFullName": None,
                    "Confiança": 0,
                    "matcher_error": str(e),
                    "diagram_type": diagram_type
                })

            combined.append(item)

        # ITEM 6: Post-LLM Validation with OCR and Symbol Type Matching
        if use_ocr_validation:
            log_to_front(f"🔍 Validando itens com OCR e matching de símbolos...")
            for item in combined:
                # OCR validation
                ocr_result = validate_tag_with_ocr(page, item, dpi=dpi)
                item["ocr_validation"] = ocr_result
                
                # Symbol type validation
                type_result = validate_symbol_type(item, item.get("descricao", ""))
                item["type_validation"] = type_result
                
                # Combined validation confidence
                ocr_conf = ocr_result.get("confidence", 0)
                type_conf = type_result.get("confidence", 0)
                item["validation_confidence"] = int((ocr_conf + type_conf) / 2)
                item["validation_passed"] = (
                    ocr_result.get("validation_passed", True) and 
                    type_result.get("validation_passed", True)
                )
            
            validated_count = sum(1 for it in combined if it.get("validation_passed", False))
            log_to_front(f"   ✅ Validados: {validated_count}/{len(combined)} itens")
        
        # ITEM 7: Geometric Center Refinement
        if use_geometric_refinement:
            log_to_front(f"📐 Refinando coordenadas para centro geométrico...")
            refined_count = 0
            total_offset = 0.0
            
            for item in combined:
                refinement = refine_geometric_center(page, item, dpi=dpi)
                item["geometric_refinement"] = refinement
                
                if refinement.get("refinement_applied", False):
                    # Update coordinates with refined values
                    item["x_mm_original"] = item["x_mm"]
                    item["y_mm_original"] = item["y_mm"]
                    item["x_mm"] = refinement["refined_x_mm"]
                    item["y_mm"] = refinement["refined_y_mm"]
                    
                    # Clamp refined coordinates
                    item["x_mm"] = max(0.0, min(W_mm, item["x_mm"]))
                    item["y_mm"] = max(0.0, min(H_mm, item["y_mm"]))
                    
                    refined_count += 1
                    total_offset += refinement.get("offset_magnitude_mm", 0.0)
            
            if refined_count > 0:
                avg_offset = total_offset / refined_count
                log_to_front(f"   ✅ Refinados: {refined_count}/{len(combined)} itens (offset médio: {avg_offset:.2f}mm)")

        unique = dedup_items(combined, page_num=page_num, tol_mm=tol_mm, 
                            use_dynamic_tolerance=use_dynamic_tolerance, log_metadata=False)
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
    
    # Assign NO-TAG identifiers to equipment without valid tags
    if all_items:
        all_items = assign_no_tag_identifiers(all_items)
        # Update pages with the modified items
        item_idx = 0
        for page in all_pages:
            num_items = len(page.get("resultado", []))
            page["resultado"] = all_items[item_idx:item_idx + num_items]
            item_idx += num_items
    
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
def build_generation_prompt(process_description: str, width_mm: float = 1189.0, height_mm: float = 841.0, diagram_type: str = "pid") -> str:
    """
    Constrói prompt técnico e detalhado para gerar P&ID ou diagrama elétrico a partir de descrição do processo.
    A0 sheet dimensions: 1189mm x 841mm (landscape)
    """
    
    is_electrical = diagram_type.lower() == "electrical"
    
    if is_electrical:
        diagram_name = "Electrical Diagram (Diagrama Elétrico)"
        standards = "electrical standards and symbols"
        task_description = "electrical diagram"
        concepts = "electrical diagram concepts and standard electrical symbols"
    else:
        diagram_name = "P&ID (Piping and Instrumentation Diagram)"
        standards = "ISA S5.1, S5.2, S5.3 standards and process engineering best practices"
        task_description = "P&ID"
        concepts = "P&ID concepts and ISA standards"
    
    prompt = f"""
You are an educational tool that helps demonstrate {diagram_name} 
following {standards}.

CRITICAL OUTPUT REQUIREMENT:
You MUST respond with ONLY a valid JSON array. NO additional text, explanations, markdown, or descriptions.
Start your response directly with '[' and end with ']'. Do NOT include any text before or after the JSON.

TASK: Generate a representative {task_description} example for educational purposes based on this process description:
"{process_description}"

NOTE: This is for educational demonstration and learning purposes only, to illustrate {concepts}.

CRITICAL: You MUST generate a {diagram_name.upper()}, NOT any other type of diagram. 
Focus exclusively on {"electrical components, connections, and power distribution" if is_electrical else "process equipment, piping, and instrumentation"}.

TECHNICAL SPECIFICATIONS:
- Sheet: A0 landscape format
- Dimensions: {width_mm} mm (width/X) x {height_mm} mm (height/Y)
- Coordinate system: X increases left to right, Y increases top to bottom
- Origin: Top left corner is point (0, 0)
- Layout: {"Power flow from source (left) to loads (right)" if is_electrical else "Process flow from left (inlet) to right (outlet)"}
- Compatibility: COMOS (Siemens) - absolute coordinates
"""
    
    if is_electrical:
        prompt += """
TYPICAL ELECTRICAL DIAGRAM ELEMENTS - MAIN COMPONENTS:

1. ELECTRICAL EQUIPMENT (include as applicable):
   - Transformers: TR-101, T-101, etc. (power, distribution)
     * Typical specs: kVA rating, voltage ratios, connection type
   - Motors: M-101, M-102, MOT-101 (AC/DC, synchronous/asynchronous)
     * Typical specs: power rating, voltage, speed
   - Generators: G-101, GEN-101
     * Typical items: voltage regulation, frequency control
   - Switchboards/MCCs: PNL-101, MCC-101
     * Typical components: circuit breakers, meters, indicators
   - Circuit Breakers: CB-101, DJ-101
     * Protection ratings and trip characteristics
   - Disconnectors/Switches: DS-101, SEC-101
     * Isolation and switching functions
   - Contactors: C-101, K-101
     * Control and switching applications
   - Protection Relays: REL-101, PROT-101
     * Types: overcurrent (50/51), differential (87), undervoltage (27), overvoltage (59)

2. ELECTRICAL INSTRUMENTATION AND METERS:
   - Energy meters: EM-101
   - Ammeters: A-101
   - Voltmeters: V-101
   - Wattmeters: W-101
   - Power factor indicators: PF-101
   - Current transformers: CT-101
   - Voltage transformers: VT-101, PT-101

3. POWER DISTRIBUTION AND CONNECTIONS:
   - Busbars: BB-101, BUS-101
   - Power cables and lines
   - Control wiring
   - Grounding systems: GND, PE
   - Cable trays and conduits

4. PROTECTION AND CONTROL:
   - Surge protection devices: SPD-101, DPS-101
   - Fuses: F-101, FUS-101
   - Emergency stop systems
   - Interlocking schemes
   - Backup power systems (UPS, batteries)

5. VARIABLE SPEED DRIVES AND POWER ELECTRONICS:
   - VFDs (Variable Frequency Drives): VFD-101
   - Soft-starters: SS-101
   - Inverters/Converters: INV-101, CONV-101
   - Power factor correction capacitors: CAP-101
"""
    else:
        # Original P&ID equipment list
        prompt += """
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
- Use decimal precision: 0.1 mm (one decimal place) - examples: 150.5, 234.8, 567.3
- DO NOT use integer coordinates - add .0 or appropriate decimal: use 150.5 instead of 150
- DO NOT consider piping, process lines, or other auxiliary elements when defining coordinates
- Only equipment (P-XXX, T-XXX, E-XXX, etc.) and instruments (FT-XXX, PT-XXX, etc.) should have coordinates
- Guarantee that coordinates are EXACTLY at the geometric center of symbols

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
"""
    
    # Common OUTPUT FORMAT section for both diagram types
    prompt += """

OUTPUT FORMAT - CRITICAL:

YOU MUST RESPOND WITH ONLY A JSON ARRAY. NO MARKDOWN, NO EXPLANATIONS, NO ADDITIONAL TEXT.
Your entire response must be ONLY the JSON array starting with '[' and ending with ']'.

COORDINATE PRECISION REQUIREMENTS:
- All x_mm and y_mm values MUST have decimal precision (0.1 mm)
- Use format: 150.5, 234.8, 567.3 (NOT 150, 234, 567)
- Coordinates reference the EXACT geometric center of symbols
"""
    
    # Add diagram-type-specific examples
    if is_electrical:
        prompt += """
EXAMPLE OUTPUT FOR ELECTRICAL DIAGRAM (Star-Delta Starter):

[
  {
    "tag": "CB-101",
    "descricao": "Main Circuit Breaker",
    "x_mm": 150.5,
    "y_mm": 400.0,
    "from": "N/A",
    "to": "C-101"
  },
  {
    "tag": "C-101",
    "descricao": "Main Contactor",
    "x_mm": 250.5,
    "y_mm": 400.0,
    "from": "CB-101",
    "to": "C-102"
  },
  {
    "tag": "C-102",
    "descricao": "Star Contactor",
    "x_mm": 350.5,
    "y_mm": 350.0,
    "from": "C-101",
    "to": "M-101"
  },
  {
    "tag": "C-103",
    "descricao": "Delta Contactor",
    "x_mm": 350.5,
    "y_mm": 450.0,
    "from": "C-101",
    "to": "M-101"
  },
  {
    "tag": "M-101",
    "descricao": "Three-Phase Motor",
    "x_mm": 500.5,
    "y_mm": 400.0,
    "from": "C-102",
    "to": "N/A"
  },
  {
    "tag": "REL-101",
    "descricao": "Overload Relay",
    "x_mm": 420.5,
    "y_mm": 400.0,
    "from": "C-101",
    "to": "M-101"
  },
  {
    "tag": "A-101",
    "descricao": "Ammeter",
    "x_mm": 300.5,
    "y_mm": 300.0,
    "from": "C-101",
    "to": "N/A"
  }
]
"""
    else:
        prompt += """
EXAMPLE OUTPUT FOR P&ID:

[
  {{
    "tag": "T-101",
    "descricao": "Feed Tank",
    "x_mm": 150.5,
    "y_mm": 450.8,
    "from": "N/A",
    "to": "P-101"
  }},
  {{
    "tag": "P-101",
    "descricao": "Centrifugal Feed Pump",
    "x_mm": 250.3,
    "y_mm": 400.2,
    "from": "T-101",
    "to": "E-201"
  }},
  {{
    "tag": "FT-101",
    "descricao": "Flow Transmitter",
    "x_mm": 280.7,
    "y_mm": 380.5,
    "from": "P-101",
    "to": "FCV-101"
  }},
  {{
    "tag": "FCV-101",
    "descricao": "Flow Control Valve",
    "x_mm": 320.4,
    "y_mm": 380.5,
    "from": "FT-101",
    "to": "E-201"
  }},
  {{
    "tag": "PT-102",
    "descricao": "Pressure Transmitter",
    "x_mm": 270.6,
    "y_mm": 420.1,
    "from": "P-101",
    "to": "N/A"
  }}
]
"""
    
    prompt += f"""
CRITICAL REMINDERS:
- Return ONLY the JSON array shown above, no other text
- NO explanations, NO markdown formatting (no ```json), NO introductory text
- Start directly with '[' and end with ']'
- Coordinates must be within limits: X: 0-{width_mm}, Y: 0-{height_mm}
- Coordinates MUST use decimal precision (e.g., 150.5, NOT 150)
- Coordinates must reference the CENTER of equipment and instruments (not piping)
- This is an educational example to demonstrate {"electrical diagram concepts" if is_electrical else "P&ID concepts and ISA standards"}
- Include ALL typical essential elements: equipment, instrumentation, {"protection devices, controls" if is_electrical else "valves, controls"}
- Use engineering best practices: redundancy in critical systems, adequate instrumentation
{"- Use standard electrical nomenclature for tags" if is_electrical else "- Strictly follow ISA S5.1 standards for nomenclature"}
"""
    return prompt.strip()


@app.post("/generate")
async def generate_pid(
    prompt: str = Query(..., description="Descrição do processo em linguagem natural"),
    diagram_type: str = Query("pid", description="Diagram type: 'pid' for P&ID or 'electrical' for Electrical Diagram")
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
        generation_prompt = build_generation_prompt(prompt, W_mm, H_mm, diagram_type)
        
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
                match = match_system_fullname(item["tag"], item["descricao"], tipo, diagram_type)
                item.update(match)
                log_to_front(f"  ✓ {item['tag']}: {match.get('SystemFullName', 'N/A')}")
            except Exception as e:
                item.update({
                    "SystemFullName": None,
                    "Confiança": 0,
                    "matcher_error": str(e),
                    "diagram_type": diagram_type
                })
            
            result_items.append(item)
        
        # Remove duplicatas
        unique = dedup_items(result_items, page_num=1, tol_mm=50.0)
        
        # Assign NO-TAG identifiers to equipment without valid tags
        unique = assign_no_tag_identifiers(unique)
        
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
