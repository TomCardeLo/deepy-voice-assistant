# Contribuir

Deepy es un proyecto personal de un solo desarrollador, hecho en tiempo libre para su propio uso diario.
No hay proceso formal de contribuciones, roadmap público ni SLA de respuesta: las issues y los PRs son
bienvenidos, pero pueden tardar en recibir respuesta (o quedar sin ella) según disponibilidad.

## Supuestos del proyecto

- Windows únicamente (Programador de Tareas, VBScript, pycaw, winsound). No se acepta soporte para
  Linux/macOS salvo que alguien lo mantenga por su cuenta.
- Python 3.14 (versión usada en desarrollo, ver `requirements.txt`).
- Requiere la CLI de Claude Code (`claude`) instalada, autenticada y disponible en el PATH.

## Antes de abrir un PR

- Corre `pytest voz_local/` y verifica que pase antes de proponer el cambio.
- Mantén el estilo de nombres en español que ya usa el código (`asistente.py`, `leer_notas.py`,
  `organizar_notas.py`, etc.) — no mezcles inglés y español en nombres de funciones o variables nuevas.
- Nunca incluyas en un commit `config.py`, credenciales de Google (`credentials.json` o similar), ni
  modelos de voz (`voz_local/voces/`). Los tres están en `.gitignore` a propósito; usa
  `config.example.py` como referencia.
- Si tu cambio toca el manejo de voces de Piper, revisa antes `voz_local/docs/VOICES.md` (incluye la
  sección sobre riesgos legales de voces de personajes con copyright) — ninguna voz de ese tipo debe
  quedar como opción recomendada.

Cambios pequeños y bien explicados (qué rompía, cómo lo probaste) tienen más chance de mergearse rápido
que PRs grandes sin contexto.
