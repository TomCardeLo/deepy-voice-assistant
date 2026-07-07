# Configuración de Deepy

Esta guía cubre la configuración completa, en el orden en que conviene hacerla: datos personales,
formato del archivo de notas, dependencias, la CLI de Claude Code, el fallback con Ollama, la
integración opcional con Google Sheets y, por último, la programación de las tareas en Windows.

## 1. Archivo de configuración personal

Copia la plantilla y completa tus datos:

```powershell
Copy-Item voz_local\config.example.py voz_local\config.py
```

`config.py` está en `.gitignore` — es solo tuyo, nunca se sube al repositorio. Estos son los campos:

| Campo | Qué es |
|---|---|
| `NOMBRE_USUARIO` | El nombre con el que Deepy te habla (ej. `"Ana"`, `"jefe"`, tu nombre real). |
| `ORGANIZADO_PATH` | Ruta al archivo Markdown con tus notas organizadas. Puede ser una ruta local o una ruta montada por Google Drive for Desktop (ej. `r"G:\Mi unidad\organizado.md"`). Ver el formato en la sección 2. |
| `VOICE_MODEL` | Ruta al modelo `.onnx` de Piper TTS, relativa a `voz_local/`. Ver `docs/VOICES.md` antes de elegir uno: hay recomendaciones con licencia clara y una advertencia sobre voces de personajes con derechos de autor (ej. Cortana), que no vienen incluidas en este repositorio. |
| `VELOCIDAD_VOZ` | Velocidad de habla. `>1.0` = más lento, `<1.0` = más rápido. Se calibra a oído con la voz elegida. |
| `SHEET_ID` | ID del Google Sheet "Inbox" usado por `organizar_notas.py`. Solo hace falta si usas esa integración (sección 6). |
| `CREDS_PATH` | Ruta al JSON de la cuenta de servicio de Google con permiso de edición sobre ese Sheet. También en `.gitignore`. |
| `DOMINIOS` | Tupla con los "dominios" de tu vida para clasificar notas (ej. `("Personal", "Freelance", "Trabajo")`). El primero es el que se usa por defecto cuando la clasificación es ambigua. |
| `ZONA_HORARIA` | Nombre de zona horaria IANA (ej. `"America/Bogota"`) usado para las fechas que `organizar_notas.py` agrega a las notas nuevas. |

## 2. Formato de `organizado.md`

El archivo usa un formato de encabezados fijo: un dominio por sección de nivel 1, y dentro de cada
dominio, cuatro subsecciones de nivel 2 en este orden: `Pendientes`, `Recordatorios`, `Completadas`,
`Notas sueltas`. Cada ítem es una línea con guion; los ítems que llevan fecha (recordatorios,
completadas) la incluyen entre paréntesis al final, en formato `YYYY-MM-DD`.

Ejemplo real:

```markdown
# Personal

## Pendientes
- Renovar el seguro del auto
- Llamar al dentista para sacar turno

## Recordatorios
- Cumpleaños de Marta (2026-07-15)

## Completadas
- Pagar el impuesto municipal (2026-07-02)

## Notas sueltas
- Idea: probar receta de pan sin amasado
```

Tanto `leer_notas.py` (lo que Deepy lee en voz alta) como `organizar_notas.py` (lo que reescribe el
archivo) dependen de que esta estructura de encabezados se respete exactamente, en el mismo orden.

## 3. Instalación de dependencias

```powershell
pip install -r voz_local\requirements.txt
```

El entorno de referencia es Windows con Python 3.14. Notas adicionales:

- Si ya tienes `onnxruntime-gpu` instalado, instala `openwakeword` con `--no-deps` para evitar que
  arrastre el paquete `onnxruntime` (CPU), que tiene archivos en conflicto con la versión GPU:
  ```powershell
  pip install --no-deps openwakeword==0.6.0
  ```
- `nvidia-cublas-cu12` y `nvidia-cudnn-cu12` son opcionales: solo aceleran `faster-whisper` con GPU
  (CUDA). Si no los instalas, `faster-whisper` cae automáticamente a CPU.

## 4. CLI de Claude Code

Deepy invoca `claude -p` para el razonamiento de lenguaje, sin herramientas ni persistencia de sesión.
Necesitas la CLI de [Claude Code](https://docs.claude.com/claude-code) instalada y autenticada,
disponible en el `PATH` del sistema.

## 5. Fallback opcional con Ollama

Si `claude -p` falla (sin red, sin cupo, etc.), Deepy reintenta automáticamente con un modelo local
vía Ollama. Para habilitarlo:

1. Instala [Ollama](https://ollama.com/).
2. Baja un modelo, por ejemplo:
   ```powershell
   ollama pull qwen3:8b
   ```

No hace falta ninguna configuración adicional: el asistente ya intenta este fallback solo cuando
`claude -p` no responde.

## 6. Configurar `organizar_notas.py` (opcional)

Esto solo es necesario si quieres clasificación automática de notas desde un Google Sheet (por
ejemplo, alimentado por un bot de WhatsApp que armes por tu cuenta — este repositorio no incluye
ningún bot de WhatsApp).

1. Crea un Google Sheet con exactamente estas columnas, en este orden: `timestamp`, `texto`, `procesado`.
2. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
3. Habilita la API de Google Sheets para ese proyecto.
4. Crea una cuenta de servicio dentro del proyecto.
5. Descarga el JSON de credenciales de esa cuenta de servicio a `voz_local/credentials.json` (o a la
   ruta que hayas puesto en `CREDS_PATH`).
6. Comparte el Google Sheet con el email de la cuenta de servicio (el que aparece en el JSON, con
   formato `...@...iam.gserviceaccount.com`), con permiso de editor.

## 7. Programar las tareas en el Programador de Tareas de Windows

Son tres tareas independientes. Reemplaza `$repoPath` por la ruta real de tu clon del repositorio
antes de ejecutar cada bloque.

```powershell
$repoPath = "C:\ruta\a\tu\clon\voz_local"
```

Antes de registrar las tareas, abre `lanzar_oculto.bat` y revisa la ruta al ejecutable de Python
(`pythonw.exe`) que tiene escrita de forma fija: edítala para que apunte a tu propia instalación si
difiere. Si no coinciden, las tareas se registran sin error pero no llegan a ejecutar el script.

**Tarea 1 — el asistente de voz, al iniciar sesión:** lanza `asistente.py` oculto en segundo plano
cada vez que inicias sesión en Windows; queda escuchando el atajo de teclado.

```powershell
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"$repoPath\lanzar_oculto.vbs" "asistente.py"' -WorkingDirectory $repoPath
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "Deepy Asistente Voz" -Action $action -Trigger $trigger -Principal (New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited)
```

**Tarea 2 — organizar notas cada 2 horas (opcional, solo si usas `organizar_notas.py`):** revisa el
Google Sheet, clasifica las notas nuevas y reescribe `organizado.md`, de forma repetida e indefinida.

```powershell
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"$repoPath\lanzar_oculto.vbs" "organizar_notas.py"' -WorkingDirectory $repoPath
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 2) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "Deepy Organizar Notas" -Action $action -Trigger $trigger -Settings $settings -Principal (New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited)
```

**Tarea 3 — saludo matutino, al iniciar sesión:** si inicias sesión antes de las 9am, lee
`organizado.md` en voz alta con tus pendientes del día. Tiene 1 minuto de margen (`$trigger.Delay`)
para dar tiempo a que Google Drive for Desktop (u otro sincronizador) monte la carpeta antes de leer
el archivo.

```powershell
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"$repoPath\lanzar_oculto.vbs" "saludo_matutino.py"' -WorkingDirectory $repoPath
$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.Delay = "PT1M"
Register-ScheduledTask -TaskName "Deepy Saludo Matutino" -Action $action -Trigger $trigger -Principal (New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited)
```
