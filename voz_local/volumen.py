"""Baja el volumen de las demás apps mientras Deepy habla, y lo restaura después."""

import os

from pycaw.pycaw import AudioUtilities

NIVEL_AGACHADO = 0.15


def agachar() -> dict[int, float]:
    """Baja el volumen de todas las apps menos la de este proceso. Devuelve los valores originales."""
    originales: dict[int, float] = {}
    pid_propio = os.getpid()
    for sesion in AudioUtilities.GetAllSessions():
        if sesion.ProcessId == pid_propio or sesion.SimpleAudioVolume is None:
            continue
        try:
            originales[sesion.ProcessId] = sesion.SimpleAudioVolume.GetMasterVolume()
            sesion.SimpleAudioVolume.SetMasterVolume(NIVEL_AGACHADO, None)
        except Exception:
            continue
    return originales


def restaurar(originales: dict[int, float]) -> None:
    for sesion in AudioUtilities.GetAllSessions():
        volumen_original = originales.get(sesion.ProcessId)
        if volumen_original is None or sesion.SimpleAudioVolume is None:
            continue
        try:
            sesion.SimpleAudioVolume.SetMasterVolume(volumen_original, None)
        except Exception:
            continue
