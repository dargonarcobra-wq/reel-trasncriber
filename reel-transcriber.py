#!/usr/bin/env python3
# reel_transcriber.py
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

# ===== Configuración local (faster-whisper) =====
try:
    import faster_whisper
    import torch
except ImportError:
    # Manejo suave; la wrapper/CLI podrá detectar que falta dependencia
    faster_whisper = None
    torch = None

# ===== Dependencias para la tarea local =====
# Si quieres, puedes adaptar para usar OpenRouter en el futuro
USE_LOCAL = True  # por defecto: flujo local

# Importamos utilidades de transcripción/traducción local
def load_local_whisper_model():
    global _LOCAL_MODEL
    if '_LOCAL_MODEL' in globals() and globals()['_LOCAL_MODEL'] is not None:
        return globals()['_LOCAL_MODEL']
    if not faster_whisper:
        return None
    # Detecta GPU
    device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    model_size = "large-v3"
    print(f"[reel_transcriber] Cargando modelo local faster-whisper: {model_size} en {device} ({compute_type})")
    try:
        model = faster_whisper.WhisperModel(model_size, device=device, compute_type=compute_type)
        globals()['_LOCAL_MODEL'] = model
        return model
    except Exception as e:
        print(f"[reel_transcriber] Error cargando modelo local: {e}", file=sys.stderr)
        globals()['_LOCAL_MODEL'] = None
        return None

def transcribe_audio_local(audio_path, language="en"):
    model = load_local_whisper_model()
    if not model:
        return None
    try:
        segments, info = model.transcribe(audio_path, language=language, task='transcribe')
        return "".join(seg.text for seg in segments)
    except Exception as e:
        print(f"[reel_transcriber] Error en transcripción local: {e}", file=sys.stderr)
        return None

def translate_audio_local(audio_path, target_lang="es"):
    model = load_local_whisper_model()
    if not model:
        return None
    try:
        segments, info = model.transcribe(audio_path, language=target_lang, task='translate')
        return "".join(seg.text for seg in segments)
    except Exception as e:
        print(f"[reel_transcriber] Error en traducción local: {e}", file=sys.stderr)
        return None

def run_reel_pipeline(url, mode="local"):
    """
    Flujo simplificado:
    - Descargar Reel (yt-dlp)
    - Extraer audio (ffmpeg)
    - Transcribir EN (local)
    - Traducir a ES (local)
    - Devolver dict con transcript_en/transcript_es
    """
    import yt_dlp
    import ffmpeg  # opcional; usaremos shell ffmpeg directo

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / "reel.mp4"
        audio_path = tmp / "audio.wav"

        try:
            print(f"[reel_transcriber] Descargando Reel: {url}")
            ytdlp_cmd = [
                "yt-dlp",
                "-o", str(video_path),
                "--quiet",
                "--no-warnings",
                url,
            ]
            subprocess.run(" ".join(ytdlp_cmd), shell=True, check=True)
        except Exception as e:
            return {"ok": False, "transcript_en": None, "transcript_es": None, "error": f"Descarga fallida: {e}"}

        try:
            print(f"[reel_transcriber] Extrayendo audio a {audio_path}")
            ff_cmd = f"ffmpeg -y -i '{video_path}' -vn -acodec pcm_s16le -ar 16000 -ac 1 '{audio_path}'"
            subprocess.run(ff_cmd, shell=True, check=True)
        except Exception as e:
            return {"ok": False, "transcript_en": None, "transcript_es": None, "error": f"Extracción de audio fallida: {e}"}

        eng_text = transcribe_audio_local(str(audio_path), language="en")
        if eng_text is None:
            eng_text = "(No se pudo transcribir en inglés. Ver logs.)"

        es_text = translate_audio_local(str(audio_path), target_lang="es")
        if es_text is None:
            es_text = "(No se pudo traducir al español. Ver logs.)"

        ok = eng_text is not None and es_text is not None
        result = {
            "ok": ok,
            "transcript_en": eng_text,
            "transcript_es": es_text,
            "error": None if ok else "Error en pipeline"
        }
        if not ok:
            # añadir detalle
            result["error"] = result.get("error") or "Fallo en pipeline de transcripción/traducción"
        return result

# Wrapper público para bajar el uso desde main agent
def run_reel_trans(url, mode="local"):
    """
    Firma solicitada por el main agent:
    run_reel_trans(url, mode="local") -> dict
    """
    if not url or not isinstance(url, str):
        return {"ok": False, "transcript_en": None, "transcript_es": None, "error": "URL inválida"}
    if mode not in ("local", "openrouter"):
        mode = "local"
    if mode == "local":
        return run_reel_pipeline(url, mode=mode)
    else:
        # Placeholder para futuro: OpenRouter Whisper
        return {"ok": False, "transcript_en": None, "transcript_es": None, "error": "OpenRouter mode no implementado aún"}

# If run as script for quick test
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python reel_transcriber.py <URL_DEL_REEL>")
        sys.exit(2)
    url = sys.argv[1]
    res = run_reel_trans(url, mode="local")
    print(json.dumps(res, ensure_ascii=False, indent=2))

