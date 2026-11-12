# DISI Agnes Video — generador auxiliar controlado

Integración de prueba para **Media News by DISI**, 12 de noviembre de 2026.

## Qué hace

- Claude Code descubre `.claude/skills/disi-agnes-video/SKILL.md`.
- El puente `agnes_video.py` usa el endpoint de Agnes `POST https://apihub.agnes-ai.com/v1/videos` y consulta `GET /agnesapi?video_id=...&model_name=...`.
- Restringido a `agnes-video-2.5-flash`, que la documentación pública anuncia **gratuito temporalmente** (cola y disponibilidad variables). No cambia a un modelo de pago.
- Produce **un clip IA de 4–12 segundos**, 720P, 9:16, con archivo JSON de procedencia. No es el short final.
- No instala otros repositorios ni modifica `mn-short-motion`, plantilla V9, Remotion, los diez doblajes o DISIM.
- **Nunca publica** en YouTube, Facebook u otras redes.

## Pasos para el propietario

1. Crea una cuenta y obtiene una clave en <https://platform.agnes-ai.com/>. No pegarla en chats ni archivos.
2. En el repositorio `ledeghar/MoneyPrinterTurbo`, abre **Settings → Secrets and variables → Actions → New repository secret** y guarda la clave como `AGNES_API_KEY`.
3. Abre **Actions → DISI Agnes - optional AI video clip → Run workflow**.
4. Introduce un **prompt público o ficticio** (nunca HUMINT privado), escoge los segundos y deja **execute = false** para el test local sin consumo de API.
5. Para solicitar un clip real, repite con **execute = true**. El MP4 y JSON, si Agnes termina, estarán en el artefacto `disi-agnes-draft` del run (retención 7 días).
6. Claude o un editor debe comprobar el vídeo y su procedencia antes de incorporarlo **como recurso** al montaje V9 de DISI. Se requiere el outro original M→DISI y la verificación de diez idiomas al finalizar el montaje en la fábrica principal.

**En repositorios fork puede ser necesario habilitar GitHub Actions en Settings → Actions.** La existencia de un archivo workflow no demuestra que un run haya ejecutado.

## Ejecución local para Claude Code

Sin clave, sin red y sin facturación:

```bash
VIDEO_PROMPT="A fictional sunrise above a Swiss mountain village in cinematic light" python disi-agnes/agnes_video.py --dry-run --seconds 5
python -m unittest discover -s disi-agnes -p 'test_*.py' -v
```

Generación real (la variable AGNES_API_KEY debe establecerse de forma segura en tu máquina):

```bash
VIDEO_PROMPT="A fictional sunrise above a Swiss mountain village in cinematic light" python disi-agnes/agnes_video.py --execute --seconds 5 --output-dir disi-agnes-output
```

**Privacidad**: ningún documento de fuentes, teléfono, dato sensible, rostro privado o material con derechos sin permiso se envía a Agnes. El prompt enviado por Actions se almacena en los parámetros del workflow: usa material público y autorizado. El JSON de salida marca `AI_GENERATED_RECONSTRUCTION` y `published: false`.

## Límites verificados

- El servicio de generación se ejecuta en infraestructura externa; **no es local ni offline** (el test sí).
- La modalidad Flash gratuita es **una promoción**. Puede cambiar o saturarse y responder 429/503. No hay garantía de gratuidad perpetua ni de disponibilidad inmediata.
- La salida no incluye por sí misma ni Pelayo, ni diez pistas, ni el outro corporativo. Todo eso pertenece al pipeline Remotion V9.
- Si falla la prueba con la clave ausente, **no se considera una instalación totalmente operativa**. Primero verificar secrets y completar un run real.

## Fuentes y licencia

- [Agnes Video Generator](https://github.com/lcy362/agnes-video-generator), MIT.
- [Agnes Video Generator skill](https://github.com/lcy362/agnes-video-generator-skills), MIT.
- [Agnes AI model API docs](https://agnes-ai.com/en/docs/overview).
- Este puente DISI es una **integración escrita para el proyecto**, no una copia ni distribución del servidor de Agnes. No se ejecutan scripts remotos.

La publicación en redes sigue siendo una tarea independiente con aprobación editorial DISI.
