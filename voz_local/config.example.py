"""Copia este archivo a config.py (mismo directorio) y completa tus datos.
config.py está en .gitignore — nunca se sube al repo, es solo tuyo."""

# Nombre con el que Deepy te habla (ej. "Ana", "jefe", tu nombre real).
NOMBRE_USUARIO = "amigo"

# Ruta al Markdown con tus notas organizadas (secciones "# Dominio" / "## Pendientes"
# / "## Recordatorios" / "## Completadas" / "## Notas sueltas" — ver docs/CONFIGURATION.md).
# Si usas Google Drive for Desktop: la ruta montada, ej. r"G:\Mi unidad\organizado.md".
# Si no: cualquier ruta local, el archivo es texto plano.
ORGANIZADO_PATH = "organizado.md"

# Ruta AL MODELO .onnx de Piper, relativa a voz_local/ (ver docs/VOICES.md antes de
# elegir una — hay recomendaciones con licencia clara y una advertencia sobre voces
# de personajes con derechos de autor, ej. Cortana, que NO vienen con este repo).
VOICE_MODEL = "voces/tu_voz/tu_voz.onnx"

# >1.0 = más lento, <1.0 = más rápido. Calibra a oído con tu propia voz.
VELOCIDAD_VOZ = 1.0

# --- Solo si usas organizar_notas.py (clasificación automática desde un Google Sheet) ---

# ID del Google Sheet "Inbox" (columnas: timestamp, texto, procesado). Ver docs/CONFIGURATION.md.
SHEET_ID = ""

# Ruta al JSON de la cuenta de servicio de Google con permiso de edición sobre ese Sheet.
# Por defecto se espera junto a este archivo (también gitignored).
CREDS_PATH = "credentials.json"

# Dominios de tu vida para clasificar notas (el primero es el default si es ambiguo).
DOMINIOS = ("Personal", "Freelance", "Trabajo")

# Zona horaria para las fechas que se agregan a las notas (nombre de la base tz de IANA).
ZONA_HORARIA = "America/Bogota"
