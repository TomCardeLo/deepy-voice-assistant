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
DURACION_FRAME_DEFECTO = 80  # ms, por si un frame no trae su propia duración

MARGEN_INFERIOR = 90

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
        cuadros = [ImageTk.PhotoImage(f.convert("RGB")) for f in ImageSequence.Iterator(imagen)]
        tiempos = [f.info.get("duration", DURACION_FRAME_DEFECTO) for f in ImageSequence.Iterator(imagen)]
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


def _animar() -> None:
    global _frame_idx
    if _estado_actual == "escuchando":
        _root.after(DURACION_FRAME_DEFECTO, _animar)
        return

    cuadros = _frames[_estado_actual]
    tiempos = _duraciones[_estado_actual]
    _frame_idx %= len(cuadros)
    _label.configure(image=cuadros[_frame_idx])
    _root.after(tiempos[_frame_idx], _animar)
    _frame_idx += 1


def _run() -> None:
    global _root, _label
    _root = tk.Tk()
    _root.overrideredirect(True)
    _root.attributes("-topmost", True)

    _cargar_animaciones()
    primer_cuadro = next(iter(_frames.values()))[0]
    ancho, alto = primer_cuadro.width(), primer_cuadro.height()
    x = (_root.winfo_screenwidth() - ancho) // 2
    y = _root.winfo_screenheight() - alto - MARGEN_INFERIOR
    _root.geometry(f"{ancho}x{alto}+{x}+{y}")

    _label = tk.Label(_root, bd=0)
    _label.pack()

    _root.withdraw()
    _root.after(50, _procesar_cola)
    _root.after(DURACION_FRAME_DEFECTO, _animar)
    _root.mainloop()


def iniciar() -> None:
    threading.Thread(target=_run, daemon=True).start()


def estado(nombre: str) -> None:
    _cola.put(nombre)
