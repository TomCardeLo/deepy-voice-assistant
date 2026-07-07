"""Organiza notas crudas (de un Google Sheet "Inbox": timestamp, texto, procesado)
dentro de organizado.md: lee filas no procesadas, las clasifica con `claude -p`
(dominio + tipo + poda de completadas), reescribe organizado.md directamente
(si usas Drive for Desktop u otro sync de carpeta, se propaga solo) y marca
esas filas como procesadas en el Sheet.

Pensado para correr cada 2 horas vía el Programador de Tareas de Windows
(ver lanzar_oculto.vbs/.bat). Requiere voz_local/config.py — ver config.example.py
y docs/CONFIGURATION.md para cómo crear el Sheet y la cuenta de servicio de Google.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

try:
    from config import CREDS_PATH, DOMINIOS, SHEET_ID, ZONA_HORARIA as _ZONA_HORARIA
except ImportError:
    raise SystemExit(
        "Falta voz_local/config.py — copia config.example.py a config.py y completa tus datos."
    )

from leer_notas import ORGANIZADO_PATH

CREDS_PATH = Path(__file__).parent / CREDS_PATH
ZONA_HORARIA = ZoneInfo(_ZONA_HORARIA)

SECCIONES = ("Pendientes", "Recordatorios", "Completadas", "Notas sueltas")


def _hoja():
    creds = Credentials.from_service_account_file(
        str(CREDS_PATH), scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID).sheet1


def notas_sin_procesar(ws) -> list[tuple[int, str, str]]:
    """Devuelve [(fila_1indexada, timestamp, texto), ...] de lo aún no procesado."""
    filas = ws.get_all_values()
    pendientes = []
    for i, fila in enumerate(filas[1:], start=2):  # fila 1 es encabezado
        timestamp = fila[0] if len(fila) > 0 else ""
        texto = fila[1] if len(fila) > 1 else ""
        procesado = fila[2].strip().upper() if len(fila) > 2 else ""
        if texto and procesado != "TRUE":
            pendientes.append((i, timestamp, texto))
    return pendientes


def construir_prompt(organizado_actual: str, notas_nuevas: list[tuple[int, str, str]]) -> str:
    hoy = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d")
    lista_notas = "\n".join(f"- ({ts}) {texto}" for _, ts, texto in notas_nuevas)
    lista_dominios = ", ".join(DOMINIOS)
    return f"""Eres un organizador de notas personales. Hoy es {hoy}.

Este es el contenido ACTUAL de organizado.md:

```
{organizado_actual}
```

Estas son las notas NUEVAS a integrar (formato: (timestamp) texto tal cual llegó):

{lista_notas}

Reglas de clasificación (ya acordadas, no las cambies):
- Dominio: uno de {lista_dominios}, según el contexto del mensaje. Si es ambiguo, usa
  "{DOMINIOS[0]}" por defecto.
- Tipo dentro de cada dominio: Pendientes, Recordatorios, Completadas, Notas sueltas.
- Cada ítem nuevo se agrega como "- texto (YYYY-MM-DD)" usando la fecha del timestamp de la nota
  (no la de hoy), igual formato que los ítems ya existentes.
- Si una nota nueva indica que se completó/canceló algo ya existente en Pendientes o Recordatorios,
  moverlo a Completadas (fecha de hoy) en vez de duplicarlo.
- Poda: en Completadas, eliminar los ítems cuya fecha tenga más de 3 días respecto a hoy ({hoy}).
- Mantené la estructura EXACTA de encabezados (# Personal / ## Pendientes / etc.), en el mismo orden,
  incluso las secciones que queden vacías.
- No inventes, no resumas de más, no agregues comentarios tuyos.
- Español neutro con tuteo; nunca voseo rioplatense ('vos', 'tenés', 'podés', etc.) en ningún texto que redactes.

Responde ÚNICAMENTE con el contenido completo y final de organizado.md, sin explicaciones antes ni
después, sin bloque de código markdown alrededor."""


def organizar(prompt: str) -> str | None:
    try:
        resultado = subprocess.run(
            [
                "claude", "-p", prompt,
                "--model", "sonnet",
                "--tools", "",
                "--no-session-persistence",
                "--setting-sources", "",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"claude -p falló al organizar: {exc}")
        return None
    if resultado.returncode != 0:
        print(f"claude -p devolvió error: {resultado.stderr.strip()}")
        return None
    return resultado.stdout.strip()


def es_valido(contenido: str) -> bool:
    return all(f"# {dominio}" in contenido for dominio in DOMINIOS) and all(
        f"## {seccion}" in contenido for seccion in SECCIONES
    )


def main() -> None:
    ws = _hoja()
    pendientes = notas_sin_procesar(ws)
    if not pendientes:
        print("Sin notas nuevas, nada que organizar.")
        return

    print(f"{len(pendientes)} nota(s) nueva(s), organizando...")
    organizado_actual = ORGANIZADO_PATH.read_text(encoding="utf-8")
    prompt = construir_prompt(organizado_actual, pendientes)
    nuevo_contenido = organizar(prompt)

    if nuevo_contenido is None or not es_valido(nuevo_contenido):
        print("Respuesta inválida o vacía, no se modifica organizado.md. Se reintentará en el próximo ciclo.")
        sys.exit(1)

    ORGANIZADO_PATH.write_text(nuevo_contenido, encoding="utf-8")
    filas = [n[0] for n in pendientes]
    ws.batch_update([{"range": f"C{fila}", "values": [["TRUE"]]} for fila in filas])
    print(f"organizado.md actualizado, {len(filas)} fila(s) marcadas como procesadas.")


if __name__ == "__main__":
    main()
