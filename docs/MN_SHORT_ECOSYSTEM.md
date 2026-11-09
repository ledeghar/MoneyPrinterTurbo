# MN Short — ecosistema audiovisual automático en GitHub

## Componentes conectados

- GitHub Actions programa el trabajo en hora de Madrid.
- RSS por secciones están configurados en config/mn_short_grid.json.
- Gemini redacta un guion a partir del artículo y de su resumen.
- DDGS y los metadatos del artículo recuperan referencias visuales.
- MoneyPrinterTurbo, Pexels, Edge TTS y FFmpeg generan un solo MP4.
- La API oficial de YouTube publica con OAuth SOLO después de habilitar
  expresamente la variable MNSHORT_PUBLICATION_ENABLED.

Se evaluaron Youtube-Atomation-System (agentes, RSS, Playwright),
Remotion, ZeroCost-Shorts y youtube-automation-agent. No se ejecuta
código externo indiscriminadamente: este sistema integra componentes
comprobados. Remotion y Playwright permanecen como posibles adaptadores,
no como dependencias actualmente operativas.

## Horarios: 1 SHORT en español por franja

08:00 — Noticias generales
10:00 — Tecnología e IA
12:00 — Actualidad internacional
16:00 — Sociedad
18:00 — Cine
20:00 — Tecnología o gaming, alternando cada día

Workflow: .github/workflows/mn-short-editorial-grid.yml.
Los cron usan Europe/Madrid, con cambio automático de hora estacional.
GitHub no garantiza comenzar las ejecuciones exactamente al minuto.

## Tres niveles de activación

1. PRUEBA MANUAL (sin publicación):
   GitHub → Actions → MN Short - Six editorial Shorts per day (ES)
   → Run workflow → elegir una franja horaria.
   Esto genera un único MP4 y crea un ZIP para revisión.

2. PRODUCCIÓN PROGRAMADA, sin publicación:
   Settings → Secrets and variables → Actions → Variables →
   crear MNSHORT_SCHEDULE_ENABLED con valor true.
   Las seis franjas producirán MP4 automáticamente siempre que
   haya noticias recientes, servicios disponibles y cuota suficiente.

3. PUBLICACIÓN AUTOMÁTICA (DESACTIVADA POR DEFECTO):
   Antes hay que validar la calidad y los derechos visuales,
   confirmar el canal autorizado y probar OAuth.
   Crear Secrets YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET y
   YOUTUBE_REFRESH_TOKEN, con alcance youtube.upload.
   Luego crear variable MNSHORT_PUBLICATION_ENABLED con valor true.

La autorización de publicación es independiente de la generación.
Nunca compartir claves/tokens en archivos públicos o en el chat.

## Historial y entregables

La rama mnshort-history contiene mnshort-history.json y previene
repetir la misma URL o título en franjas posteriores. Se guarda
después de producir el MP4. La publicación no se reintenta tras
una respuesta ambigua, para evitar duplicados.

Cada ZIP contiene un solo vídeo con título y horario en el nombre,
TITULO_Y_FUENTE.txt, editorial.json y referencias de búsqueda
visual cuando haya resultados.

## Limitaciones pendientes de resolver antes de publicación autónoma

- Las imágenes halladas por el buscador NO están incorporadas todavía
  a la cronología audiovisual; el render usa Pexels.
- Las identidades y licencias de fotografías externas requieren
  comprobación antes de utilizar las imágenes.
- Gemini resume la noticia desde RSS, sin verificación independiente
  de múltiples fuentes en este flujo.
- La calidad de sonido, pausas y montaje precisa pruebas por categoría.
- El OAuth de YouTube aún no está configurado ni verificado.

Mantener MNSHORT_PUBLICATION_ENABLED en false hasta completar
estos controles. No se necesita un portátil encendido para ejecutar
el sistema en GitHub Actions.
