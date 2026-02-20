"""

Reel Transcriber Skill
Propósito

Descargar un Instagram Reel desde una URL, extraer audio y producir dos transcripciones: inglés y español.
Entrada (params)

url: string, URL del Reel (ej. "https://www.instagram.com/reel/DUrhfWOk9cI")
mode (opcional): "local" | "openrouter" (predeterminado "local")
Salida

transcript_en: string (Transcripción en Inglés)
transcript_es: string (Transcripción en Español)
ok: boolean
error: string (si aplica)
Formato de invocación

Entrada: { "command": "reel_trans", "args": { "url": "<URL del Reel>" } }
Salida: JSON con las claves arriba.
Notas de implementación

Mantiene dependencias para ejecución local con faster-whisper.
Soporta extensión futura hacia OpenRouter Whisper si se quiere.
La salida es texto plano dentro del JSON; no se envían adjuntos.
"""
