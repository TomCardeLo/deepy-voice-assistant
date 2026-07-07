"""Self-check del corte por silencio de grabar_hasta_silencio, sin micrófono real."""

import numpy as np

import asistente


def test_corte_por_silencio():
    bloques_voz = [np.full(1600, 5000, dtype="int16") for _ in range(3)]
    bloques_silencio = [np.zeros(1600, dtype="int16") for _ in range(30)]
    cola = iter(bloques_voz + bloques_silencio)
    callback_registrado = []

    class FakeStream:
        def __init__(self, *args, **kwargs):
            callback_registrado.append(kwargs["callback"])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_sleep(_ms):
        bloque = next(cola, np.zeros(1600, dtype="int16"))
        callback_registrado[-1](bloque, None, None, None)

    stream_original, sleep_original = asistente.sd.InputStream, asistente.sd.sleep
    asistente.sd.InputStream, asistente.sd.sleep = FakeStream, fake_sleep
    try:
        audio = asistente.grabar_hasta_silencio()
    finally:
        asistente.sd.InputStream, asistente.sd.sleep = stream_original, sleep_original

    total_bloques_disponibles = 3 + 30
    assert len(audio) < 1600 * total_bloques_disponibles, (
        "no cortó por silencio, grabó hasta agotar todos los bloques disponibles"
    )
    assert len(audio) >= 1600 * 3, "cortó antes de terminar el audio con voz"


def _con_mocks(respuesta_claude, respuesta_ollama, pregunta="cualquier pregunta"):
    original_claude, original_ollama = asistente.preguntar_claude, asistente.preguntar_ollama
    asistente.preguntar_claude = lambda p: respuesta_claude
    asistente.preguntar_ollama = lambda p: respuesta_ollama
    try:
        return asistente.responder(pregunta)
    finally:
        asistente.preguntar_claude, asistente.preguntar_ollama = original_claude, original_ollama


def test_responder_usa_claude_si_funciona():
    resultado = _con_mocks("respuesta de claude", "no debería llamarse a esto")
    assert resultado == "respuesta de claude"


def test_responder_cae_a_ollama_si_claude_falla():
    resultado = _con_mocks(None, "respuesta de respaldo")
    assert resultado == "respuesta de respaldo"


def test_responder_da_error_si_ambos_fallan():
    resultado = _con_mocks(None, None)
    assert "error" in resultado.lower()


if __name__ == "__main__":
    test_corte_por_silencio()
    print("OK: corte por silencio funciona")
    test_responder_usa_claude_si_funciona()
    test_responder_cae_a_ollama_si_claude_falla()
    test_responder_da_error_si_ambos_fallan()
    print("OK: fallback Claude -> Ollama funciona")
