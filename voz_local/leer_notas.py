"""Lee organizado.md y dice en voz alta los pendientes y recordatorios actuales."""

import re
import wave
import winsound
from pathlib import Path

from piper import PiperVoice
from piper.config import SynthesisConfig

try:
    from config import ORGANIZADO_PATH as _ORGANIZADO_PATH
    from config import VELOCIDAD_VOZ, VOICE_MODEL as _VOICE_MODEL
except ImportError:
    raise SystemExit(
        "Falta voz_local/config.py — copia config.example.py a config.py y completa tus datos."
    )

ORGANIZADO_PATH = Path(_ORGANIZADO_PATH)
VOICE_MODEL = Path(__file__).parent / _VOICE_MODEL
SALIDA_WAV = Path(__file__).parent / "resumen.wav"
VELOCIDAD = SynthesisConfig(length_scale=VELOCIDAD_VOZ)  # >1.0 = más lento; <1.0 = más rápido

_voice: PiperVoice | None = None

SECCIONES_A_LEER = ("Pendientes", "Recordatorios")

RE_DOMINIO = re.compile(r"^# (.+)")
RE_SECCION = re.compile(r"^## (.+)")
RE_ITEM = re.compile(r"^- (.+?)(?:\s*\(\d{4}-\d{2}-\d{2}\))?\s*$")


def extraer_items(texto: str) -> dict[str, dict[str, list[str]]]:
    dominios: dict[str, dict[str, list[str]]] = {}
    dominio_actual = None
    seccion_actual = None

    for linea in texto.splitlines():
        if m := RE_DOMINIO.match(linea):
            dominio_actual = m.group(1).strip()
            dominios[dominio_actual] = {}
            seccion_actual = None
        elif m := RE_SECCION.match(linea):
            seccion_actual = m.group(1).strip()
        elif (m := RE_ITEM.match(linea)) and dominio_actual and seccion_actual in SECCIONES_A_LEER:
            dominios[dominio_actual].setdefault(seccion_actual, []).append(m.group(1).strip())

    return dominios


def construir_resumen(dominios: dict[str, dict[str, list[str]]]) -> str:
    partes = []
    for dominio, secciones in dominios.items():
        items = [item for seccion in SECCIONES_A_LEER for item in secciones.get(seccion, [])]
        if items:
            partes.append(f"En {dominio}: " + "; ".join(items) + ".")

    if not partes:
        return "No tienes pendientes ni recordatorios registrados."

    return "Estos son tus pendientes. " + " ".join(partes)


def obtener_voz() -> PiperVoice:
    global _voice
    if _voice is None:
        _voice = PiperVoice.load(str(VOICE_MODEL))
    return _voice


def hablar(texto: str) -> None:
    voice = obtener_voz()
    with wave.open(str(SALIDA_WAV), "wb") as wav_file:
        voice.synthesize_wav(texto, wav_file, syn_config=VELOCIDAD)
    winsound.PlaySound(str(SALIDA_WAV), winsound.SND_FILENAME)


def main() -> None:
    texto = ORGANIZADO_PATH.read_text(encoding="utf-8")
    dominios = extraer_items(texto)
    resumen = construir_resumen(dominios)
    print(resumen)
    hablar(resumen)


if __name__ == "__main__":
    main()
