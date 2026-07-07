"""Overlay flotante (estilo el indicador de Siri): reproduce la animación GIF
de Deepy que corresponde al estado actual (grabando/procesando/hablando),
siempre encima de todo, cerca de la parte inferior de la pantalla. Oculto en
reposo (escuchando)."""

import queue
import threading
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageSequence, ImageTk

CARPETA_ANIMACIONES = Path(__file__).parent / "animaciones"
ANIMACIONES = {
    "grabando": CARPETA_ANIMACIONES / "Deepy - Activacion.gif",
    "procesando": CARPETA_ANIMACIONES / "Deepy - Escuchando.gif",
    "hablando": CARPETA_ANIMACIONES / "Deepy - Hablando.gif",
}
CIERRE_PATH = CARPETA_ANIMACIONES / "Deepy - Cierre.gif"
if CIERRE_PATH.exists():
    ANIMACIONES["cerrando"] = CIERRE_PATH
DURACION_FRAME_DEFECTO = 80  # ms, por si un frame no trae su propia duración

MARGEN_INFERIOR = 90

# ponytail: color chroma-key para simular transparencia (Tk en Windows no soporta
# alfa real en una ventana); verificado que no aparece en ninguno de los 4 gifs.
TRANSPARENTE = "#ff00ff"

_cola: "queue.Queue[str]" = queue.Queue()
_root: tk.Tk | None = None
_label: tk.Label | None = None
_frames: dict[str, list[ImageTk.PhotoImage]] = {}
_duraciones: dict[str, list[int]] = {}
_estado_actual = "escuchando"
_frame_idx = 0


def _cargar_animaciones() -> None:
    for estado, ruta in ANIMACIONES.items():
        imagen = Image.open(ruta)
        cuadros = []
        tiempos = []
        for f in ImageSequence.Iterator(imagen):
            rgba = f.convert("RGBA")
            fondo = Image.new("RGB", rgba.size, TRANSPARENTE)
            fondo.paste(rgba, mask=rgba.getchannel("A"))  # zonas alfa=0 quedan en TRANSPARENTE
            cuadros.append(ImageTk.PhotoImage(fondo))
            tiempos.append(f.info.get("duration", DURACION_FRAME_DEFECTO))
        _frames[estado] = cuadros
        _duraciones[estado] = tiempos


def _procesar_cola() -> None:
    global _estado_actual, _frame_idx
    try:
        while True:
            nuevo = _cola.get_nowait()
            if nuevo != _estado_actual:
                _estado_actual = nuevo
                _frame_idx = 0
    except queue.Empty:
        pass

    if _estado_actual == "escuchando":
        _root.withdraw()
    else:
        _root.deiconify()
    _root.after(50, _procesar_cola)


CONGELA_AL_TERMINAR = {"grabando"}  # se reproduce una vez y se congela en el último cuadro
OCULTA_AL_TERMINAR = {"cerrando"}  # se reproduce una vez y vuelve a "escuchando" (oculto)


def _animar() -> None:
    global _frame_idx, _estado_actual
    if _estado_actual == "escuchando":
        _root.after(DURACION_FRAME_DEFECTO, _animar)
        return

    cuadros = _frames[_estado_actual]
    tiempos = _duraciones[_estado_actual]
    if _frame_idx >= len(cuadros):
        if _estado_actual in OCULTA_AL_TERMINAR:
            _estado_actual = "escuchando"
            _frame_idx = 0
            _root.after(DURACION_FRAME_DEFECTO, _animar)
            return
        # "grabando" dura lo que tarde la grabación real (variable); en vez de
        # repetir el loop entero varias veces, se congela en el último cuadro.
        # El resto de estados (procesando/hablando) sí siguen en loop.
        _frame_idx = len(cuadros) - 1 if _estado_actual in CONGELA_AL_TERMINAR else 0
    _label.configure(image=cuadros[_frame_idx])
    _root.after(tiempos[_frame_idx], _animar)
    _frame_idx += 1


def _run() -> None:
    global _root, _label
    _root = tk.Tk()
    _root.overrideredirect(True)
    _root.attributes("-topmost", True)
    _root.configure(bg=TRANSPARENTE)
    _root.attributes("-transparentcolor", TRANSPARENTE)

    _cargar_animaciones()
    primer_cuadro = next(iter(_frames.values()))[0]
    ancho, alto = primer_cuadro.width(), primer_cuadro.height()
    x = (_root.winfo_screenwidth() - ancho) // 2
    y = _root.winfo_screenheight() - alto - MARGEN_INFERIOR
    _root.geometry(f"{ancho}x{alto}+{x}+{y}")

    _label = tk.Label(_root, bd=0, bg=TRANSPARENTE)
    _label.pack()

    _root.withdraw()
    _root.after(50, _procesar_cola)
    _root.after(DURACION_FRAME_DEFECTO, _animar)
    _root.mainloop()


def iniciar() -> None:
    threading.Thread(target=_run, daemon=True).start()


def estado(nombre: str) -> None:
    if nombre != "escuchando" and nombre not in _frames:
        return  # animación no disponible (p. ej. falta el gif de cierre), ignorar
    _cola.put(nombre)


def duracion_ms(nombre: str) -> int:
    """Duración total (ms) de la animación, para que quien dispare el estado
    espere a que termine antes de seguir. 0 si el estado no tiene animación."""
    return sum(_duraciones.get(nombre, []))
