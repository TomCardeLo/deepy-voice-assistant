# Voces de Piper TTS

Deepy usa [Piper](https://github.com/rhasspy/piper) para sintetizar voz, de forma
100% local. Piper necesita dos archivos por voz: un modelo `.onnx` y su archivo de
configuración `.onnx.json` (contiene el mapeo de fonemas, el idioma, etc.). Ninguno
de los dos se incluye en este repositorio — `voz_local/voces/` está en `.gitignore` —
así que cada quien descarga la voz que prefiera.

## Cómo cambiar de voz

1. Crea una carpeta dentro de `voz_local/voces/` con el nombre de la voz, por ejemplo:

   ```
   voz_local/voces/davefx/
     es_ES-davefx-medium.onnx
     es_ES-davefx-medium.onnx.json
   ```

2. En `config.py`, apunta `VOICE_MODEL` al archivo `.onnx` (el `.onnx.json` se busca
   automáticamente junto a él, con el mismo nombre):

   ```python
   VOICE_MODEL = "voces/davefx/es_ES-davefx-medium.onnx"
   ```

   La ruta es relativa a `voz_local/`.

3. Reinicia `asistente.py`. No hace falta ningún otro cambio de configuración.

## Voces oficiales recomendadas (licencia clara)

El catálogo oficial es [`rhasspy/piper-voices` en Hugging Face](https://huggingface.co/rhasspy/piper-voices).
El repositorio en sí es MIT, pero cada voz trae su propia licencia en su `MODEL_CARD`
(varía de CC0 a CC BY con atribución obligatoria) — conviene revisarla antes de usar
esa voz en un proyecto que se vaya a distribuir.

Tres opciones ya verificadas para español:

- **`es_ES-davefx`** (medium) — español de España, licencia **CC0** (dominio público,
  sin condiciones). Recomendada como opción por defecto.
  [MODEL_CARD](https://huggingface.co/rhasspy/piper-voices/blob/main/es/es_ES/davefx/medium/MODEL_CARD)
- **`es_MX-ald`** (medium) — español de México, licencia **Unlicense** (también
  dominio público). Buena alternativa si prefieres acento mexicano.
  [MODEL_CARD](https://huggingface.co/rhasspy/piper-voices/blob/main/es/es_MX/ald/medium/MODEL_CARD)
- **`es_ES-sharvard`** (medium) — español de España, licencia **CC BY 3.0**: libre de
  usar, pero exige dar atribución visible (por ejemplo, en el README de tu propio
  proyecto o fork).
  [MODEL_CARD](https://huggingface.co/rhasspy/piper-voices/blob/main/es/es_ES/sharvard/medium/MODEL_CARD)

## Catálogos comunitarios

También circulan voces entrenadas por usuarios individuales fuera del catálogo
oficial, en distintos Spaces de Hugging Face. Suelen no tener licencia declarada ni
documentar de dónde salió el audio de entrenamiento. Trátalas como "uso personal, sin
garantía de licencia": sirven para probar en tu propia máquina, pero no son una buena
elección para un proyecto que se vaya a distribuir o publicar, salvo que su propio
README aclare fuente y licencia.

## ⚠️ Sobre voces de personajes con derechos de autor

Existen modelos de Piper entrenados para imitar voces de personajes con copyright
(Jarvis, Cortana, etc.), generalmente entrenados con audio extraído de películas o
videojuegos. El personaje y las grabaciones originales tienen dueño (por ejemplo,
Marvel/Disney o Microsoft/343 Industries, según el caso), y entrenar un modelo que
los imita no cambia eso. Alojar ese tipo de modelo en una plataforma pública expone
tanto al autor del modelo como a la plataforma a un reclamo de derechos de autor.

En honor a la transparencia: el autor de este proyecto usa, en su configuración
personal, una voz comunitaria de "Cortana" encontrada en un Space de terceros en
Hugging Face, para uso propio en su propia máquina. Es zona gris — no hay garantía
legal de que esté permitido — pero el riesgo de un uso personal a pequeña escala es
distinto al de redistribuirlo. Por eso:

- Ese modelo **no se distribuye en este repositorio** (`voz_local/voces/` está en `.gitignore`).
- **No se recomienda como opción por defecto** ni se documenta cómo conseguirlo.
- Si quieres una voz así por gusto propio, consíguela y úsala bajo tu propia
  responsabilidad, fuera de este repositorio — nunca como parte instalada o
  referenciada del proyecto.

Si buscas una voz "con personalidad" para tu asistente sin este problema, las
opciones oficiales de la sección anterior (`davefx`, `ald`, `sharvard`) cumplen esa
función sin depender de un personaje con dueño.
