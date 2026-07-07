"""Asistente de voz: activa la grabación con la combinación de teclas
COMBO_ACTIVACION (graba hasta detectar silencio) o manteniendo presionada F9
(graba mientras se mantiene presionada). Transcribe con Whisper local,
pregunta a Claude con el contexto de las notas (con fallback a Ollama local
si Claude no está disponible), y responde en voz alta con Piper/Mireya.

La wake word "oye dipi" está desactivada por defecto (USAR_WAKEWORD = False)
por falsos positivos al estar siempre escuchando; el código se deja intacto
para reactivarla poniendo esa constante en True. Se entrena aparte en Colab,
ver `entrenamiento_wakeword/README.md`.
"""

import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Habilitar las DLL de CUDA (pip install nvidia-cublas-cu12 nvidia-cudnn-cu12)
# para que faster-whisper pueda usar la GPU. Debe ir antes de importar
# faster_whisper/ctranslate2.
_site_packages = next(p for p in sys.path if p.endswith("site-packages"))
for _paquete in ("cublas", "cudnn"):
    _dll_dir = os.path.join(_site_packages, "nvidia", _paquete, "bin")
    if os.path.isdir(_dll_dir):
        os.environ["PATH"] = _dll_dir + os.pathsep + os.environ["PATH"]

import keyboard
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

try:
    from config import NOMBRE_USUARIO
except ImportError:
    raise SystemExit(
        "Falta voz_local/config.py — copia config.example.py a config.py y completa tus datos."
    )

import bandeja
import overlay
import volumen
from leer_notas import ORGANIZADO_PATH, hablar

TECLA = "f9"  # mantener presionada mientras se habla
COMBO_ACTIVACION = "ctrl+alt+d"  # presionar una vez: graba hasta detectar silencio
SAMPLE_RATE = 16000
FRAME_SIZE = 1280  # 80 ms a 16kHz, tamaño de frame que espera openWakeWord

USAR_WAKEWORD = False  # ponytail: "oye dipi" desactivado (falsos positivos); True para reactivar
WAKEWORD_PATH = Path(__file__).parent / "voces" / "wakeword" / "oye_deepy.onnx"
UMBRAL = 0.6  # ajustar en la práctica: sube si dispara con ruido, baja si no detecta la voz

SILENCIO_RMS = 300  # nivel de audio (int16) por debajo del cual se considera silencio
SILENCIO_SEG = 1.5  # segundos de silencio seguido para cortar la grabación
MAX_GRAB_SEG = 10  # tope máximo de grabación aunque no se detecte silencio

_whisper_model: WhisperModel | None = None


def obtener_modelo_whisper() -> WhisperModel:
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    print("Cargando modelo de transcripción (una sola vez)...")
    try:
        _whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
    except Exception as exc:
        print(f"No se pudo usar GPU ({exc}), usando CPU en su lugar.")
        _whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _whisper_model


def grabar_mientras_tecla_presionada(tecla: str) -> np.ndarray:
    frames: list[np.ndarray] = []

    def callback(indata, frames_count, time_info, status):
        frames.append(indata.copy())

    # ya se sabe que "tecla" está presionada (esperar_disparador lo confirmó);
    # no repetir keyboard.wait aquí, se queda colgado si se soltó justo antes.
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=1600, callback=callback
    ):
        while keyboard.is_pressed(tecla):
            sd.sleep(50)

    if not frames:
        return np.array([], dtype="int16")
    return np.concatenate(frames, axis=0).flatten()


def esperar_disparador(oww_model) -> str:
    """Bloquea hasta detectar la wake word, F9 o COMBO_ACTIVACION.

    Devuelve "wakeword", "tecla" o "combo" según qué haya disparado.
    """
    if oww_model is None:
        while True:
            if keyboard.is_pressed(TECLA):
                return "tecla"
            if keyboard.is_pressed(COMBO_ACTIVACION):
                return "combo"
            sd.sleep(50)

    disparado = False

    def callback(indata, frames_count, time_info, status):
        nonlocal disparado
        if disparado:
            return
        prediccion = oww_model.predict(indata.flatten())
        if prediccion["oye_deepy"] > UMBRAL:
            disparado = True

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16",
        blocksize=FRAME_SIZE, callback=callback,
    ):
        while not disparado and not keyboard.is_pressed(TECLA) and not keyboard.is_pressed(COMBO_ACTIVACION):
            sd.sleep(50)
    oww_model.reset()
    if disparado:
        return "wakeword"
    return "tecla" if keyboard.is_pressed(TECLA) else "combo"


def grabar_hasta_silencio() -> np.ndarray:
    frames: list[np.ndarray] = []
    silencio_frames = 0
    frames_silencio_necesarios = int(SILENCIO_SEG / 0.1)
    max_bloques = int(MAX_GRAB_SEG / 0.1)

    def callback(indata, frames_count, time_info, status):
        frames.append(indata.copy())

    # blocksize=1600 = 100ms exactos a 16kHz; frames_silencio_necesarios y
    # max_bloques de arriba asumen ese tamaño de frame (sin esto, el dispositivo
    # real entrega bloques de ~26ms y el tope de MAX_GRAB_SEG se cumple 4x antes).
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=1600, callback=callback
    ):
        while len(frames) < max_bloques:
            sd.sleep(100)
            if not frames:
                continue
            ultimo = frames[-1]
            rms = np.sqrt(np.mean(ultimo.astype(np.float64) ** 2))
            silencio_frames = silencio_frames + 1 if rms < SILENCIO_RMS else 0
            if len(frames) > 3 and silencio_frames >= frames_silencio_necesarios:
                break

    if not frames:
        return np.array([], dtype="int16")
    return np.concatenate(frames, axis=0).flatten()


def transcribir(audio: np.ndarray) -> str:
    if audio.size == 0:
        return ""
    audio_float = audio.astype(np.float32) / 32768.0
    modelo = obtener_modelo_whisper()
    segmentos, _ = modelo.transcribe(audio_float, language="es")
    return " ".join(segmento.text for segmento in segmentos).strip()


OLLAMA_MODEL = "qwen3:8b"
OLLAMA_URL = "http://localhost:11434/api/generate"


def construir_prompt(pregunta: str) -> str:
    contexto = ORGANIZADO_PATH.read_text(encoding="utf-8")
    return (
        f"Eres Deepy, el asistente de voz personal de {NOMBRE_USUARIO}. Este es el "
        "archivo de notas organizadas (pendientes, recordatorios, completadas) que "
        "tienes disponible como contexto:\n\n"
        f"{contexto}\n\n"
        f"Pregunta de {NOMBRE_USUARIO}: {pregunta}\n\n"
        "Respóndele específicamente a lo que preguntó, ni más ni menos: si pide "
        "una tarea puntual o la más urgente, dale solo esa, no recites todo el "
        "archivo de memoria; si pide un resumen general, ahí sí cubre lo "
        "relevante. Usa las notas solo como contexto de apoyo, no como un "
        "guion fijo a repetir palabra por palabra. Varía la redacción de forma "
        "natural, como lo haría una persona distinta cada vez, evitando caer "
        "siempre en la misma fórmula de respuesta. "
        "Responde breve y en texto plano, sin markdown ni listas con guiones, "
        "como si se lo estuvieras diciendo en voz alta. "
        "Si el texto original tiene abreviaturas, siglas o códigos (por ejemplo, "
        "códigos de país), expándelos a la palabra completa en tu respuesta, "
        "porque el texto se convierte a voz y las siglas se pronuncian mal. "
        "Usa español neutro con tuteo (tú/tienes/puedes/puedes revisar); nunca "
        "voseo rioplatense (prohibido usar 'vos', 'tenés', 'podés', 'necesitás', "
        "'armá', 'contá', etc.)."
    )


def preguntar_claude(pregunta: str) -> str | None:
    """Devuelve la respuesta de claude -p, o None si falla (sin red, sin cupo, etc.)."""
    prompt = construir_prompt(pregunta)
    try:
        resultado = subprocess.run(
            [
                "claude", "-p", prompt,
                "--model", "haiku",
                "--tools", "",
                "--no-session-persistence",
                "--setting-sources", "",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if resultado.returncode != 0:
        return None
    return resultado.stdout.strip()


def preguntar_ollama(pregunta: str) -> str | None:
    """Fallback local con Ollama cuando claude -p no está disponible (sin internet/cupo)."""
    prompt = construir_prompt(pregunta)
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
    }).encode("utf-8")
    peticion = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
        return datos["response"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return None


def responder(pregunta: str) -> str:
    respuesta = preguntar_claude(pregunta)
    if respuesta is not None:
        return respuesta

    print("claude -p no respondió (¿sin internet o sin cupo?), usando Ollama local...")
    respuesta = preguntar_ollama(pregunta)
    if respuesta is not None:
        return respuesta

    return "Hubo un error al consultar tanto a Claude como al modelo local de respaldo."


def _estado(nombre: str, notificar: str | None = None) -> None:
    bandeja.estado(nombre, notificar=notificar)
    overlay.estado(nombre)


def obtener_modelo_wakeword():
    if not WAKEWORD_PATH.exists():
        print(f"No se encontró {WAKEWORD_PATH.name}, usando solo F9 como disparador.")
        return None
    from openwakeword.model import Model

    return Model(wakeword_models=[str(WAKEWORD_PATH)], inference_framework="onnx")


PUERTO_INSTANCIA_UNICA = 47823  # puerto arbitrario, solo para exclusión mutua local


def main() -> None:
    # evita dos instancias escuchando el micrófono a la vez (ya pasó antes);
    # el SO libera el puerto solo aunque el proceso muera mal.
    _guard = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _guard.bind(("127.0.0.1", PUERTO_INSTANCIA_UNICA))
    except OSError:
        print("Ya hay una instancia de Deepy corriendo, saliendo.")
        return

    obtener_modelo_whisper()
    oww_model = obtener_modelo_wakeword() if USAR_WAKEWORD else None
    bandeja.iniciar()
    overlay.iniciar()
    prefijo = 'Di "oye dipi", ' if oww_model is not None else ""
    print(
        f"Asistente listo. {prefijo}mantén presionada F9 o presiona "
        f"{COMBO_ACTIVACION.upper()} para hablar."
    )

    while True:
        _estado("escuchando")
        disparador = esperar_disparador(oww_model)
        _estado("grabando", notificar="Escuchando tu pregunta...")
        audio = grabar_mientras_tecla_presionada(TECLA) if disparador == "tecla" else grabar_hasta_silencio()
        keyboard.stash_state()  # libera teclas que la librería pudo dejar "pegadas" y re-disparar solas
        if audio.size == 0 or np.sqrt(np.mean(audio.astype(np.float64) ** 2)) < SILENCIO_RMS:
            continue  # no hubo voz real (silencio/ruido); evita que Whisper alucine texto
        _estado("procesando")
        pregunta = transcribir(audio)
        if not pregunta:
            continue

        print(f"Pregunta: {pregunta}")
        respuesta = responder(pregunta)
        print(f"Respuesta: {respuesta}")
        _estado("hablando")
        volumen_original = volumen.agachar()
        try:
            hablar(respuesta)
        finally:
            volumen.restaurar(volumen_original)


if __name__ == "__main__":
    main()
