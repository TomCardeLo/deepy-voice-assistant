# Entrenar la wake word "oye deepy"

1. Sube `entrenar_oye_deepy.ipynb` a [Google Colab](https://colab.research.google.com/) (Archivo → Subir notebook).
2. Entorno de ejecución → Cambiar tipo de entorno de ejecución → **GPU (T4)**.
3. Ejecuta las celdas en orden. Tarda entre 1 y 2 horas (mayormente descargas y entrenamiento en la celda 12).
4. En el paso 6 puedes (opcional, recomendado) subir ~20-30 grabaciones propias diciendo "oye deepy" — mejora mucho la detección de la voz real.
5. Al final se descarga `oye_deepy.onnx` automáticamente. Guárdalo en:
   ```
   voz_local/voces/wakeword/oye_deepy.onnx
   ```

## Si algo falla

El ecosistema de openWakeWord/piper-sample-generator cambia con el tiempo; si una celda
falla por una librería que cambió de nombre o versión, copia el error y continúa la
sesión de Claude para ajustarlo.

## Calibración después de entrenar

El umbral de detección (`UMBRAL` en `asistente.py`) se ajusta probando en la práctica:
- Se dispara con ruido o conversación normal → subir el umbral.
- No detecta la frase al decirla → bajar el umbral.
