"""Self-check del límite de hora de saludo_matutino, sin hablar de verdad."""

from datetime import datetime

import saludo_matutino


class _RelojFalso:
    def __init__(self, hora: int) -> None:
        self._hora = hora

    def now(self):
        return datetime(2026, 7, 7, self._hora, 0)


def _con_reloj(hora: int) -> bool:
    """Devuelve True si main() llegó a llamar a hablar()."""
    llamado = []
    reloj_original, hablar_original = saludo_matutino.datetime, saludo_matutino.hablar
    saludo_matutino.datetime = _RelojFalso(hora)
    saludo_matutino.hablar = lambda texto: llamado.append(texto)
    try:
        saludo_matutino.main()
    finally:
        saludo_matutino.datetime, saludo_matutino.hablar = reloj_original, hablar_original
    return bool(llamado)


def test_saluda_antes_de_las_9():
    assert _con_reloj(8) is True


def test_no_saluda_despues_de_las_9():
    assert _con_reloj(9) is False
    assert _con_reloj(14) is False


if __name__ == "__main__":
    test_saluda_antes_de_las_9()
    test_no_saluda_despues_de_las_9()
    print("OK: límite de hora del saludo matutino funciona")
