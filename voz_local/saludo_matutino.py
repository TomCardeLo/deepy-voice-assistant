"""Si el inicio de sesión ocurre antes de HORA_LIMITE, saluda y dice los
pendientes/recordatorios del día en voz alta. Pensado para una tarea del
Programador de Tareas disparada "al iniciar sesión"."""

import time
from datetime import datetime

from config import NOMBRE_USUARIO
from leer_notas import ORGANIZADO_PATH, construir_resumen, extraer_items, hablar

HORA_LIMITE = 9
REINTENTOS_DRIVE = 24  # 24 x 5s = 2min, por si Google Drive for Desktop no montó G: todavía
ESPERA_REINTENTO_SEG = 5


def _leer_organizado_con_reintento() -> str:
    for intento in range(REINTENTOS_DRIVE):
        try:
            return ORGANIZADO_PATH.read_text(encoding="utf-8")
        except OSError:
            if intento == REINTENTOS_DRIVE - 1:
                raise
            time.sleep(ESPERA_REINTENTO_SEG)


def main() -> None:
    if datetime.now().hour >= HORA_LIMITE:
        return

    texto = _leer_organizado_con_reintento()
    dominios = extraer_items(texto)
    saludo = f"Buenos días {NOMBRE_USUARIO}. " + construir_resumen(dominios)
    print(saludo)
    hablar(saludo)


if __name__ == "__main__":
    main()
