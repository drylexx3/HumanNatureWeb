#!/usr/bin/env python3
"""
HumanNature Web Edition - Backend Server & Keystroke Synthesizer
Direct OS typing into any active window/tab via native pynput & xdotool
"""

import os
import sys
import time
import random
import threading
import subprocess
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CORE_DIR = "/home/daniel-sosa/.gemini/antigravity/scratch/HumanNature"
if os.path.exists(CORE_DIR) and CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)

try:
    from humannature import (
        run_humanizer,
        is_spanish_text,
        normalize_whitespace,
        remove_emojis,
        get_typo,
        emit_char,
        emit_key,
    )
except ImportError as e:
    print(f"Warning: Could not import directly from humannature: {e}")
    run_humanizer = None
    is_spanish_text = lambda s: False
    normalize_whitespace = lambda s: " ".join(s.split())
    remove_emojis = lambda s: s
    get_typo = lambda c: 'e'

# Setup fallback keystroke emitter if needed
_pynput_kb = None
PynputKey = None
try:
    from pynput.keyboard import Controller as PynputController, Key as PynputKey
    _pynput_kb = PynputController()
except Exception:
    pass

def safe_emit_char(c: str) -> bool:
    if c in ("\u2019", "\u2018"):
        c = "'"
    elif c in ("\u201c", "\u201d"):
        c = '"'
    elif c in ("\u2013", "\u2014"):
        c = "-"
    elif c == "\u00a0":
        c = " "

    # 1. pynput
    if _pynput_kb is not None:
        try:
            _pynput_kb.type(c)
            return True
        except Exception:
            pass

    # 2. xdotool fallback
    try:
        subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "0", "--", c], check=False, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False

def safe_emit_key(k: str) -> bool:
    if _pynput_kb is not None and PynputKey is not None:
        try:
            if k == "backspace":
                _pynput_kb.press(PynputKey.backspace)
                _pynput_kb.release(PynputKey.backspace)
                return True
            elif k == "enter":
                _pynput_kb.press(PynputKey.enter)
                _pynput_kb.release(PynputKey.enter)
                return True
            elif k == "shift+enter":
                _pynput_kb.press(PynputKey.shift)
                _pynput_kb.press(PynputKey.enter)
                _pynput_kb.release(PynputKey.enter)
                _pynput_kb.release(PynputKey.shift)
                return True
        except Exception:
            pass

    try:
        if k == "backspace":
            subprocess.run(["xdotool", "key", "BackSpace"], check=False, stderr=subprocess.DEVNULL)
        elif k == "enter":
            subprocess.run(["xdotool", "key", "Return"], check=False, stderr=subprocess.DEVNULL)
        elif k == "shift+enter":
            subprocess.run(["xdotool", "key", "Shift+Return"], check=False, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False


# Initialize FastAPI
app = FastAPI(
    title="HumanNature Web Edition",
    description="Full-featured Web App for AI Humanization & OS Keystroke Simulation",
    version="3.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ---------------------------------------------------------------------
# Global System Typing State
# ---------------------------------------------------------------------
typing_lock = threading.Lock()
is_system_typing = False
is_system_paused = False

typing_state = {
    "is_typing": False,
    "is_paused": False,
    "status": "● Ensayo listo",
    "telemetry": "> status: standing by",
    "wpm_measured": 72,
    "last_key_ms": 0,
    "keystrokes": 0,
    "typos_fixed": 0,
    "current_char": 0,
    "total_chars": 0,
    "recent_latencies": [160] * 65,
    "new_terminal_logs": []
}

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------
class HumanizeRequest(BaseModel):
    text: str
    engine: str = "⚡ HumanizeAI Pro"
    casual_mode: bool = False
    remove_emojis: bool = False
    remove_asterisks: bool = False
    remove_lines: bool = False

class AnalyzeRequest(BaseModel):
    text: str

class StartTypingRequest(BaseModel):
    text: str
    wpm: int = 72
    accuracy: float = 96.4
    start_delay: int = 5
    use_burst: bool = True
    use_fragments: bool = True
    use_shift_enter: bool = False
    remove_asterisks: bool = True
    remove_emojis: bool = False

class CleanMarkdownRequest(BaseModel):
    text: str


# ---------------------------------------------------------------------
# Text Metrics
# ---------------------------------------------------------------------
AI_BUZZWORDS_ES = [
    "crucial", "fundamental", "es menester", "cabe destacar", "cabe señalar",
    "sumergirse", "sinfín", "desentrañar", "tapiz", "vital", "panorama",
    "innovación constante", "paradigma", "revolucionario", "intrincado", "multifacético",
    "fomentar", "interconectado", "de vital importancia", "en resumen", "en conclusión"
]

def analyze_text_metrics(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        return {
            "words": 0, "chars": 0, "sentences": 0, "avg_sentence_len": 0,
            "sentence_variance": 0, "buzzwords_found": [], "ai_probability": 0,
            "verdict": "Empty", "lang": "es"
        }

    is_es = is_spanish_text(text)
    words = text.split()
    word_count = len(words)
    char_count = len(text)

    import re
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = max(1, len(sentences))
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_len = sum(sentence_lengths) / sentence_count

    if sentence_count > 1:
        variance = sum((l - avg_sentence_len) ** 2 for l in sentence_lengths) / sentence_count
        std_dev = variance ** 0.5
    else:
        std_dev = 0

    lower_text = text.lower()
    found_buzzwords = [bw for bw in AI_BUZZWORDS_ES if bw in lower_text]

    buzzword_density = (len(found_buzzwords) / max(1, word_count)) * 100
    score = 15.0 + min(50.0, buzzword_density * 18.0)
    if std_dev < 3.5:
        score += 30.0
    elif std_dev > 7.0:
        score -= 15.0

    score = max(0.0, min(100.0, score))
    verdict = "100% Human Score" if score < 35 else ("Mixed Signals" if score < 70 else "Likely AI-Generated")

    return {
        "words": word_count,
        "chars": char_count,
        "sentences": sentence_count,
        "avg_sentence_len": round(avg_sentence_len, 1),
        "sentence_variance": round(std_dev, 2),
        "buzzwords_found": found_buzzwords,
        "ai_probability": round(score, 1),
        "verdict": verdict,
        "lang": "es" if is_es else "en"
    }


def smart_clean_markdown(text: str) -> str:
    import re
    if not text:
        return ""

    # 1. Typography & smart quotes
    quote_map = {
        '’': "'", '‘': "'", '“': '"', '”': '"',
        '–': '-', '—': ', ', '…': '...', '\u00a0': ' ', '\u200b': ''
    }
    for o, r in quote_map.items():
        text = text.replace(o, r)

    # 2. Fenced code blocks: remove ```lang ... ```
    text = re.sub(r'```[a-zA-Z0-9_-]*\n?', '', text)
    text = text.replace("```", "")

    # 3. Inline code backticks: `code` -> code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = text.replace("`", "")

    # 4. Markdown links: [Title](url) -> Title, images ![alt](url) -> alt
    text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    # 5. Strikethrough: ~~text~~ -> text
    text = re.sub(r'~~(.*?)~~', r'\1', text)

    # 6. Headers: ### Title -> Title
    text = re.sub(r'(?m)^#{1,6}\s+', '', text)

    # 7. Blockquotes: > Quote -> Quote
    text = re.sub(r'(?m)^>\s+', '', text)

    # 8. Unordered lists: convert * and + to clean dashes - so asterisks never reach Google Docs
    text = re.sub(r'(?m)^[ \t]*\*[ \t]+', '- ', text)
    text = re.sub(r'(?m)^[ \t]*\+[ \t]+', '- ', text)

    # 9. Bold and Italics: ***text***, **text**, *text*
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'(?<!\d)\*([^*\n]+?)\*(?!\d)', r'\1', text)
    # Remaining stray asterisks
    text = text.replace("*", "")

    # 10. Horizontal rules (---, ***, ___)
    text = re.sub(r'(?m)^[-*_]{3,}\s*$', '', text)

    # 11. Normalize commas and em-dashes
    text = text.replace("—", ", ").replace("--", ", ")

    # 12. Fix missing spaces after punctuation commonly created by AI copy-paste
    # e.g. "país,sin" -> "país, sin", "mismos.Expresar" -> "mismos. Expresar"
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]),([a-zA-ZáéíóúñÁÉÍÓÚÑ])', r'\1, \2', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ])\.([A-ZÁÉÍÓÚÑ])', r'\1. \2', text)

    # 13. Clean redundant whitespace
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

strip_all_markdown = smart_clean_markdown

# ---------------------------------------------------------------------
# Full Keystroke Simulation Worker (Background Thread)
# ---------------------------------------------------------------------
def background_type_worker(req: StartTypingRequest):
    global is_system_typing, is_system_paused, typing_state

    with typing_lock:
        is_system_typing = True
        is_system_paused = False

    text = req.text
    # Completely strip any markdown syntax and polish punctuation for natural human writing
    if getattr(req, "remove_asterisks", True):
        text = smart_clean_markdown(text)
    else:
        text = normalize_whitespace(text)

    if getattr(req, "remove_emojis", False) and remove_emojis:
        text = remove_emojis(text)

    typing_state["is_typing"] = True
    typing_state["is_paused"] = False
    typing_state["current_char"] = 0
    typing_state["total_chars"] = len(text)
    typing_state["keystrokes"] = 0
    typing_state["typos_fixed"] = 0
    typing_state["recent_latencies"] = [160] * 65
    typing_state["new_terminal_logs"] = [
        f"[Control] ▶ Iniciando tipeo en el sistema ({len(text)} caracteres, {req.wpm} WPM)..."
    ]

    # Countdown phase
    start_delay = max(0, req.start_delay)
    if start_delay > 0:
        steps = int(start_delay * 10)
        for i in range(steps, 0, -1):
            if not is_system_typing:
                typing_state["is_typing"] = False
                typing_state["status"] = "● Cancelado"
                return
            c_sec = i / 10.0
            typing_state["status"] = f"⏳ {c_sec:.1f}s — ¡Haz clic en tu destino!"
            typing_state["telemetry"] = f"> seq launch: t-minus {c_sec:.1f}s (haz clic en tu destino)"
            time.sleep(0.1)

    typing_state["status"] = "● Status: Typing active... (F8 Pausa, F10 Detener)"
    typing_state["new_terminal_logs"].append("[Control] ▶ Cuenta atrás terminada. Escribiendo en ventana activa...")

    cpm = max(1, req.wpm * 5)
    base_delay = 60.0 / cpm
    typo_chance = max(0.0, (100.0 - req.accuracy) / 100.0)

    is_es = is_spanish_text(text)
    connectors = [
        " y ", " pero ", " porque ", " además ", " entonces ", " aunque ",
        " así que ", " es decir ", " sin embargo ", " por lo tanto ", " en cambio "
    ] if is_es else [" and ", " but ", " because ", " so ", " also ", " however "]

    is_new_sentence = True
    smoothed_wpm = float(req.wpm)

    try:
        for idx, char in enumerate(text):
            if not is_system_typing:
                break

            while is_system_paused:
                if not is_system_typing:
                    break
                typing_state["status"] = "● Status: ⏸ En Pausa (F8 para seguir)"
                typing_state["telemetry"] = "> status: paused"
                time.sleep(0.1)

            # Jitter
            actual_delay = base_delay * random.uniform(0.72, 1.28)

            # False-start fragment mode (at sentence start)
            if is_new_sentence and char.isalpha() and req.use_fragments and random.random() < 0.14:
                fragment = random.choice(["Bueno, ", "O sea, ", "Es decir, ", "A ver, "]) if is_es else random.choice(["Well, ", "I mean, ", "Basically, "])
                for f_char in fragment:
                    safe_emit_char(f_char)
                    time.sleep(base_delay * random.uniform(0.75, 1.25))
                    typing_state["keystrokes"] += 1
                time.sleep(random.uniform(0.2, 0.4))
                for _ in range(len(fragment)):
                    safe_emit_key("backspace")
                    time.sleep(base_delay * 0.6)
                    typing_state["keystrokes"] += 1
                time.sleep(random.uniform(0.1, 0.2))

            # Typo injection
            triggers_typo = char.isalpha() and random.random() < typo_chance
            if triggers_typo:
                wrong_char = get_typo(char)
                safe_emit_char(wrong_char)
                typing_state["keystrokes"] += 1
                typing_state["typos_fixed"] += 1
                time.sleep(random.uniform(0.12, 0.25))
                safe_emit_key("backspace")
                typing_state["keystrokes"] += 1
                time.sleep(random.uniform(0.06, 0.12))

            # Emit actual character
            if char == "\n":
                if req.use_shift_enter:
                    safe_emit_key("shift+enter")
                else:
                    safe_emit_key("enter")
                is_new_sentence = True
                actual_delay += random.uniform(0.35, 0.55)
            else:
                safe_emit_char(char)
                if char in (".", "!", "?"):
                    is_new_sentence = True
                    actual_delay += random.uniform(0.28, 0.48)
                elif char in (",", ";", ":"):
                    actual_delay += random.uniform(0.12, 0.22)
                else:
                    is_new_sentence = False

            typing_state["keystrokes"] += 1
            typing_state["current_char"] = idx + 1

            # Update latency oscilloscope
            flight_ms = int(actual_delay * 1000)
            typing_state["last_key_ms"] = flight_ms
            typing_state["recent_latencies"].pop(0)
            typing_state["recent_latencies"].append(min(450, flight_ms))

            # Speedometer smoothing
            inst_wpm = (60.0 / actual_delay) / 5.0
            smoothed_wpm = smoothed_wpm * 0.85 + inst_wpm * 0.15
            typing_state["wpm_measured"] = int(round(smoothed_wpm))
            typing_state["telemetry"] = f"> char {idx + 1}/{len(text)} | latency {flight_ms}ms"

            time.sleep(actual_delay)

    finally:
        is_system_typing = False
        typing_state["is_typing"] = False
        words = len(text.split())
        typing_state["status"] = f"● Ensayo listo: {words} palabras"
        typing_state["telemetry"] = f"> total: {typing_state['keystrokes']} strokes, {typing_state['typos_fixed']} typos corrected"
        typing_state["new_terminal_logs"].append(f"[Done] Tipeo completado al 100% ({typing_state['keystrokes']} pulsaciones).")


# ---------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>HumanNature Web Edition is loading...</h1>")


@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "app": "HumanNature Web Edition",
        "version": "3.6.0",
        "core_linked": run_humanizer is not None,
        "is_typing": is_system_typing
    }


@app.post("/api/humanize")
async def api_humanize(req: HumanizeRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    text = req.text
    if req.remove_emojis:
        import re
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    if req.remove_asterisks:
        text = text.replace("*", "")
    if req.remove_lines:
        text = " ".join(text.splitlines())

    try:
        if run_humanizer is not None:
            humanized = run_humanizer(
                text=text,
                engine=req.engine,
                casual_mode=req.casual_mode
            )
        else:
            humanized = text

        analysis_before = analyze_text_metrics(req.text)
        analysis_after = analyze_text_metrics(humanized)

        return {
            "success": True,
            "engine": req.engine,
            "original_text": req.text,
            "humanized_text": humanized,
            "analysis_before": analysis_before,
            "analysis_after": analysis_after,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clean-markdown")
async def api_clean_markdown(req: CleanMarkdownRequest):
    cleaned = smart_clean_markdown(req.text)
    return {
        "success": True,
        "original_text": req.text,
        "cleaned_text": cleaned,
        "chars_diff": len(req.text) - len(cleaned)
    }


@app.post("/api/type/start")
async def api_type_start(req: StartTypingRequest, background_tasks: BackgroundTasks):
    global is_system_typing
    if is_system_typing:
        return {"status": "already_running", "message": "A typing process is already running."}

    background_tasks.add_task(background_type_worker, req)
    return {
        "status": "started",
        "countdown_seconds": req.start_delay,
        "message": f"Switch to your target tab now! Typing starts in {req.start_delay}s."
    }


@app.post("/api/type/pause")
async def api_type_pause():
    global is_system_paused
    if is_system_typing:
        is_system_paused = not is_system_paused
        return {"status": "paused" if is_system_paused else "resumed"}
    return {"status": "idle"}


@app.post("/api/type/stop")
async def api_type_stop():
    global is_system_typing
    is_system_typing = False
    return {"status": "stopped"}


@app.get("/api/type/status")
async def api_type_status():
    global typing_state
    res = dict(typing_state)
    # Drain new logs
    typing_state["new_terminal_logs"] = []
    return res


# Backward compatibility for old endpoint
@app.post("/api/system-type")
async def api_system_type_legacy(req: StartTypingRequest, background_tasks: BackgroundTasks):
    return await api_type_start(req, background_tasks)

@app.post("/api/system-type/stop")
async def api_system_type_stop_legacy():
    return await api_type_stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5050, reload=True)
