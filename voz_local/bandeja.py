"""Ícono en la bandeja del sistema para ver de un vistazo el estado del asistente."""

import os
import threading

import pystray
from PIL import Image, ImageDraw

COLORES = {
    "escuchando": "#4a90d9",
    "grabando": "#e74c3c",
    "procesando": "#f1c40f",
    "hablando": "#2ecc71",
}

_icono: pystray.Icon | None = None


def _imagen(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(img)
    dibujo.ellipse((6, 6, 58, 58), fill=color)
    return img


def _salir(icono: pystray.Icon) -> None:
    icono.stop()
    os._exit(0)


def iniciar() -> None:
    global _icono
    menu = pystray.Menu(pystray.MenuItem("Salir", _salir))
    _icono = pystray.Icon("deepy", _imagen(COLORES["escuchando"]), "Deepy", menu)
    threading.Thread(target=_icono.run, daemon=True).start()


def estado(nombre: str, notificar: str | None = None) -> None:
    if _icono is None:
        return
    _icono.icon = _imagen(COLORES[nombre])
    if notificar:
        _icono.notify(notificar, "Deepy")
