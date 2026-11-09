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
Los cron ejecutan la preparación 30 minutos ANTES de cada hora de salida
(07:30, 09:30, 11:30, 15:30, 17:30 y 19:30, Europe/Madrid).
Una vez activado y probado el OAuth, los vídeos se subirán como privados
con publishAt para que YouTube los haga públicos a las 08, 10, 12, 16,
18 y 20 horas. Si la producción llega demasiado tarde, la subida se cancela;
no se publica fuera de horario a escondidas.
GitHub no garantiza comenzar las ejecuciones exactamente al minuto,
y los retrasos pueden causar la omisión segura de una franja.

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


## Publicación automática preparada para cuando el contenido esté listo

El sistema ya dispone del workflow programado, del uploader OAuth y de
un **control automático de salida** previo a cualquier envío público:

- Una noticia nueva y un solo MP4 vertical con audio, título y fuente.
- VERIFICACION_FUENTES.json: comprobación independiente de hechos,
  afirmaciones sin resolver vacías y evidencia de aportación periodística
  original, importante para la elegibilidad de monetización.
- ESCENAS_VERIFICADAS.json: fotografías y escenas con licencia validada,
  personajes identificados, intervalos sincronizados con la narración
  y SHA256 del vídeo final para evitar reutilizar evidencias ajenas.
- CONTROL_PUBLICACION.json/txt: informe APTO_PARA_PROGRAMAR o
  RETENIDO_PARA_REVISION, incluido en el ZIP del Short.

En este momento **el control RETIENE los vídeos**, ya que todavía falta
implementar los verificadores de fuentes y la inserción de imágenes
específicas en el montaje. Pasar la prueba de render no basta.

Con el flujo de validación completo, las ejecuciones programadas podrán
subir los vídeos como privados, con publishAt al horario solicitado,
**sin pasos manuales por vídeo**, siempre que estén presentes:
1. MNSHORT_SCHEDULE_ENABLED=true (variable de GitHub Actions).
2. MNSHORT_PUBLICATION_ENABLED=true (variable de GitHub Actions).
3. Secrets YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET,
   YOUTUBE_REFRESH_TOKEN, obtenidos autorizando el canal MN Short
   con el alcance youtube.upload.
4. Aprobación real del control de salida de esa producción.

La conexión OAuth requiere intervención del titular del canal; no se
puede deducir de la cuenta de GitHub ni de la clave Gemini. No introducir
secretos en el repositorio ni en mensajes. Si el envío se retrasa más allá
de la ventana previa a la publicación, se cancela esa franja.

## Informe automático de visualizaciones e ingresos

Se ha preparado otro workflow:
.github/workflows/mn-short-channel-analytics.yml

Podrá producir cada día, a las 22:10 de Madrid, el paquete:
- INGRESOS_Y_VISUALIZACIONES.txt: cifras legibles desde el móvil
- canal_90_dias.json: datos completos y errores de API
- tendencia_diaria.csv: visualizaciones e ingresos por fecha

Solo se activa al crear MNSHORT_ANALYTICS_ENABLED=true como variable
de Actions, y además requiere YOUTUBE_CLIENT_ID y YOUTUBE_CLIENT_SECRET
y el secret **YOUTUBE_ANALYTICS_REFRESH_TOKEN** (credencial diferente
de la publicación, concedida en lectura con los scopes
youtube.readonly, yt-analytics.readonly y
yt-analytics-monetary.readonly).

El reporte diferencia claramente datos ausentes de 0, muestra cifras
**estimadas** en EUR, no pagos recibidos ni YPP confirmado. Comprende
por defecto todas las estadísticas del canal autorizado, no únicamente
los vídeos producidos por MN Short.

**Ingresos reales por anuncios Shorts:** los requisitos generales de
participación/reparto publicitario incluyen 1000 suscriptores y
10 millones de visualizaciones públicas válidas de Shorts en 90 días,
o la vía correspondiente de vídeo largo, y la aceptación del canal
en YPP. El umbral ampliado de 500 suscriptores / 3 millones de Shorts
permite algunas funciones de financiación de fans, no el reparto
publicitario completo. El titular debe comprobar su elegibilidad y
tramitar la adhesión en YouTube Studio > Ingresos.

La política de YouTube no considera monetizable el contenido genérico
repetitivo producido en masa; es imprescindible aportar contexto y valor
periodístico originales, variedad y tratamiento visual correcto.
Fuente: https://support.google.com/youtube/answer/1311392?hl=es-SP
Umbrales: https://support.google.com/youtube/answer/94522?hl=es-ES

## Pendiente de una segunda fase: vídeos horizontales 16:9

Cuando la parrilla vertical de Shorts esté operativa, estudiar un flujo
**separado** de vídeos 16:9 para YouTube: reportajes y análisis de mayor
duración, composición audiovisual apropiada, producción y costes de
renderizado, estructura editorial, derechos, frecuencia de publicación
y vías de monetización. No cambiar el flujo 9:16 actual ni reutilizar
automáticamente sus guiones cortos para generar vídeos largos.


## Red de distribución priorizada por ingresos (YouTube, Facebook, Instagram, TikTok)

La producción en GitHub sigue creando UN solo MP4 9:16 por franja.
Distribuirlo en varias redes no crea más renders ni publica 6 veces por red.

Orden práctico en 2026:
1. **YouTube Shorts:** integración oficial de publicación programada y panel
   propio de visualizaciones/ingresos; exige admisión YPP, aceptación del
   módulo Shorts y condiciones actuales de acceso al reparto de anuncios.
2. **Facebook Reels:** potencial de monetización de contenido y Reels, sujeto
   a elegibilidad/invitación en el panel profesional de Meta.
3. **Instagram Reels:** descubrimiento, audiencia, colaboración y venta;
   no contabilizar ingresos por visualizaciones como si fueran seguros.
4. **TikTok:** distribución secundaria, NO asumir Creator Rewards: exige
   cuenta elegible en región admitida y vídeos originales de más de un minuto.
   Los Shorts actuales (30–40s) no cumplen esa duración. Upload-Post para
   TikTok requiere plan de pago.

Se ha incorporado scripts/mn_short_crosspost.py al mismo workflow de GitHub.
Usa la API de Upload-Post para programar Reels y, si se autoriza, TikToks.
**No replica YouTube**, evitando duplicar la publicación oficial.
Cada publicación externa utiliza clave de idempotencia (evita programar dos
veces por un reintento) y guarda PROGRAMACION_REDES.json en el ZIP.
Un job_id solo confirma la programación; no prueba publicación completada
ni ingresos.

### Conexión de redes: solo cuando estén validadas

En la cuenta de Upload-Post:
- Vincular la **Página de Facebook** correcta y la cuenta Instagram
  profesional adecuada; verificar que Meta autoriza publicar Reels.
- Opcionalmente vincular TikTok. Evaluar coste y elegibilidad real.
- Crear API key; guardarla como GitHub Actions SECRET llamado
  UPLOAD_POST_API_KEY. No introducir credenciales en este documento.
- Crear GitHub Actions VARIABLE UPLOAD_POST_PROFILE con el perfil autorizado.
- Crear GitHub Actions VARIABLE MNSHORT_CROSSPOST_PLATFORMS con
  facebook,instagram (o solo facebook para limitar costes).
- Opcional: incluir tiktok y variable MNSHORT_TIKTOK_ENABLED=true.
  No se activa solo por tener la cuenta conectada.
- Tras comprobar derechos, exactitud e integración visual de cada vídeo,
  establecer MNSHORT_CROSSPOST_ENABLED=true.

MNSHORT_CROSSPOST_ENABLED está ausente/false por defecto. Además, el
workflow exige el mismo control de publicación APTO_PARA_PROGRAMAR, un
evento programado (no una prueba manual), una sola pieza y un MP4
criptográficamente idéntico al validado. Si no hay pruebas suficientes,
**ninguna red recibe vídeos nuevos**.

El servicio Upload-Post anuncia 10 subidas gratuitas al mes, pero TikTok
requiere plan de pago. Seis Shorts diarios implicarían aprox. 180 piezas
mensuales (y varios destinos por pieza); comparar tarifas y retorno real
antes de contratar algo. Consultar precios actuales directamente en
https://upload-post.com/pricing

No tenemos conexión confirmada ni estados de monetización de las cuentas
de Facebook, Instagram o TikTok. La prioridad final dependerá de sus
paneles de monetización y de ingresos efectivos; nunca atribuir ingresos
a visualizaciones simples si la plataforma no informa de ellos.

Fuentes:
- https://docs.upload-post.com/api/upload-video
- https://docs.upload-post.com/guides/github-action/
- https://about.fb.com/news/2026/03/creator-fast-track-grow-your-audience-earn-money-on-facebook/
- https://support.tiktok.com/es/business-and-creator/creator-rewards-program/how-is-the-creator-rewards-program-different-from-the-tiktok-creator-fund
