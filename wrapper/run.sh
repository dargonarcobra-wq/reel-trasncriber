#!/usr/bin/env bash
# wrapper/run.sh
set -euo pipefail

URL="$1"

if [[ -z "$URL" ]]; then
  echo '{"ok":false,"transcript_en":null,"transcript_es":null,"error":"URL no proporcionada"}'
  exit 1
fi

# Asegúrate de que el script Python es ejecutable y tiene permisos
OUTPUT=$(python3 ../reel_transcriber.py "$URL" 2>&1 || true)
STATUS=$?
echo "$OUTPUT"

# Si el script imprime JSON, lo devolvemos tal cual.
# Si no, envolvemos con un JSON básico de error.
if echo "$OUTPUT" | jq -e . >/dev/null 2>&1; then
  # ya es JSON válido
  exit 0
else
  echo '{"ok":false,"transcript_en":null,"transcript_es":null,"error":"Salida no JSON del script"}'
  exit 1
fi
