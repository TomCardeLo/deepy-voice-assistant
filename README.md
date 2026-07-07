# Deepy

![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.14%2B-blue) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

Asistente de voz personal para Windows, 100 % local salvo el razonamiento de lenguaje: escucha un atajo de teclado, transcribe con Whisper en tu propia máquina, responde con la CLI de Claude Code y contesta en voz con Piper. También organiza notas sueltas (por ejemplo, las que envías por WhatsApp a un Google Sheet) en un Markdown estructurado por pendientes, recordatorios y completadas.

Proyecto de hobby, para un único usuario y su propio flujo. No es una librería ni un producto.

## Qué hace

- Presiona un atajo (`Ctrl+Alt+D`, configurable) o mantén `F9`: graba tu pregunta hasta detectar silencio.
- Transcribe el audio localmente con `faster-whisper` (CPU o GPU con CUDA).
- Arma un prompt con tus notas organizadas (`organizado.md`) y se lo pasa a `claude -p` (Claude Code CLI, sin herramientas, sin red de sesión) para obtener una respuesta. Si Claude no responde (sin red o sin cupo), cae en Ollama local (por ejemplo `qwen3:8b`).
- Sintetiza la respuesta con Piper TTS (modelos `.onnx` locales) y la reproduce, bajando el volumen de otras apps mientras habla y restaurándolo después.
- Muestra un overlay flotante (siempre encima, oculto en reposo) con una animación distinta por estado: grabando, procesando, hablando — al estilo del indicador de Siri.
- Un ícono en la bandeja del sistema refleja el mismo estado.
- `organizar_notas.py` lee filas nuevas de un Google Sheet "Inbox" (pensado para recibir notas reenviadas desde WhatsApp u otra fuente que armes por tu cuenta — este repo no incluye ningún bot de WhatsApp), las clasifica con `claude -p` por dominio de vida y tipo (Pendiente / Recordatorio / Completada / Nota suelta), poda completadas viejas y reescribe `organizado.md`. Pensado para correr cada 2 horas vía el Programador de Tareas de Windows.
- `saludo_matutino.py`: si inicias sesión en Windows antes de las 9am, lee tus pendientes del día y te saluda en voz alta.
- Existe una wake word entrenable ("oye dipi", vía `openWakeWord`), pero está **desactivada por defecto** por falsos positivos — el atajo de teclado es el disparador principal.

## Cómo funciona

```
Atajo de teclado / F9 mantenida
        │
        ▼
Grabación (sounddevice) hasta detectar silencio
        │
        ▼
Transcripción local (faster-whisper, CPU o GPU)
        │
        ▼
Prompt + organizado.md → claude -p  (fallback: Ollama local)
        │
        ▼
Síntesis de voz (Piper TTS, modelo .onnx local)
        │
        ▼
Reproducción (baja volumen de otras apps y lo restaura)
```

En paralelo, `organizar_notas.py` corre por su cuenta (Programador de Tareas) leyendo un Google Sheet y reescribiendo `organizado.md`, que es el archivo que el flujo de arriba consulta.

## Requisitos

- Windows (usa `pycaw`, `keyboard`, rutas y Programador de Tareas de Windows — no probado en Linux/Mac).
- Python 3.14+.
- [CLI de Claude Code](https://docs.claude.com/claude-code) instalada y autenticada en el `PATH`, con suscripción activa.
- Micrófono.
- GPU NVIDIA + CUDA opcional (acelera la transcripción; sin ella corre en CPU, más lento).

## Instalación

```powershell
git clone <url-de-este-repo>
cd <carpeta-del-repo-clonado>/voz_local
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

La wake word (`openwakeword`) es opcional y solo hace falta si activas `USAR_WAKEWORD`. Si ya tienes `onnxruntime-gpu` instalado, instálala con `--no-deps` para no arrastrar el `onnxruntime` de CPU (mismo nombre de import, conflicto de archivos):

```powershell
pip install --no-deps openwakeword==0.6.0
```

## Configuración

```powershell
Copy-Item voz_local\config.example.py voz_local\config.py
```

Edita `voz_local/config.py`: tu nombre, ruta a `organizado.md`, modelo de voz de Piper, velocidad, ID del Google Sheet y ruta a las credenciales (solo si usas `organizar_notas.py`). El detalle de cada campo, el formato de `organizado.md` y cómo automatizar con el Programador de Tareas de Windows está en [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md).

`config.py` está en `.gitignore` — nunca se sube al repo.

## Uso

```powershell
python asistente.py
```

Deja la ventana corriendo (o lánzala oculta con `lanzar_oculto.vbs` / `lanzar_oculto.bat`). Mantén `F9` o usa el atajo configurado para hablar con Deepy.

## Voces

Piper necesita un modelo `.onnx` de voz, que no viene incluido en este repo (`voz_local/voces/` está en `.gitignore`). Cómo elegir uno y dónde conseguirlo está en [`docs/VOICES.md`](docs/VOICES.md).

**Aviso sobre derechos de autor:** existen modelos de voz entrenados por la comunidad que imitan voces de personajes con copyright (por ejemplo, Cortana). Este repo no distribuye ninguno y no recomienda ese camino — usa como default las voces oficiales de Piper, con licencia clara (catálogo [`rhasspy/piper-voices`](https://huggingface.co/rhasspy/piper-voices)). Ver `docs/VOICES.md` para el detalle.

## Limitaciones

- **Solo Windows.** Usa `pycaw`, `keyboard` y rutas de Windows; no hay soporte planeado para Linux/Mac.
- **Requiere la CLI de Claude Code con suscripción activa.** Deepy delega el razonamiento a Claude Code; sin eso, solo responde el fallback de Ollama local si está configurado.
- **Necesita micrófono.**
- **GPU opcional.** Corre en CPU con `faster-whisper`, pero la transcripción es notablemente más lenta. Con GPU NVIDIA + CUDA es prácticamente en tiempo real.
- **Proyecto personal, no una librería.** Está pensado para mi propio flujo (mis notas, mi Sheet, mi voz); adaptarlo a otro uso implica tocar `config.py` y probablemente el código.

## Estructura del repo

```
voz_local/
├── asistente.py              # Loop principal: atajo/wake word → STT → Claude/Ollama → TTS
├── leer_notas.py             # Lee y formatea organizado.md para el prompt
├── organizar_notas.py        # Clasifica notas del Google Sheet y reescribe organizado.md
├── saludo_matutino.py        # Saludo hablado con pendientes del día al iniciar sesión
├── bandeja.py                # Ícono de estado en la bandeja del sistema
├── overlay.py                # Overlay flotante con animación por estado
├── volumen.py                # Baja/restaura el volumen de otras apps (pycaw)
├── lanzar_oculto.vbs         # Lanza asistente.py oculto (sin consola visible)
├── lanzar_oculto.bat         # Variante .bat del lanzador oculto
├── config.example.py         # Plantilla de configuración (copiar a config.py)
├── config.py                 # Tu configuración personal (gitignored, no se sube)
├── requirements.txt          # Dependencias
├── test_asistente.py         # Self-checks de asistente.py (pytest, sin hardware real)
├── test_saludo.py            # Self-checks de saludo_matutino.py
├── animaciones/               # 3 GIFs del overlay (grabando/procesando/hablando), reemplazables
├── voces/                     # Modelos de voz Piper (gitignored, vacío en un clone fresco)
└── entrenamiento_wakeword/    # Notebook de Colab para entrenar la wake word (GPU T4, 1-2h)
```

## Licencia

MIT — ver [`LICENSE`](LICENSE). No cubre modelos de voz de terceros que decidas usar (ver `docs/VOICES.md`).

## Autor

**TommyCardeLo** — [tommycardelo.com](https://tommycardelo.com)
