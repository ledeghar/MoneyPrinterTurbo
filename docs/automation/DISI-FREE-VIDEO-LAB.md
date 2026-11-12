# DISI · laboratorio audiovisual gratuito — 11/11/2026

Proyecto: \`ledeghar/MoneyPrinterTurbo\`. Rama aislada; no altera \`main\`, la composición aprobada \`DISIV9Approved\`, los logotipos originales de Canva ni el cierre audiovisual corporativo V6 (~3,5 s).

## Material revisado

- **5310.mp4**: títulos cinéticos, OneTake, collage B-roll, plantillas HTML y estilos de animación. Implementamos prototipos **originales** de tipografía cinética, tarjetas-collage y barras de flujo editorial. No copiamos plantillas ajenas ni usamos servicios comerciales.
- **5305.mp4**: índice de API públicas. No es una licencia universal ni significa acceso comercial gratuito. Se incorporan dos fuentes de señales de uso editorial: NASA EONET y USGS. Se consultan expresamente; nunca publican noticias por sí mismas.
- **5312.mp4**: muestra una curva de trading desde 100.000 USD; no demuestra beneficios reales ni aporta nada verificable a la producción periodística. No integramos operaciones bursátiles ni cifras de rentabilidad.
- **Captura YouTube**: 16 visualizaciones en un momento determinado. No permite deducir retención, elegibilidad de monetización o ingresos.

## Implementación

- \`mn-short-motion/src/DisiMotionLab.jsx\`: tres escenas de 4 s, proporción 9:16, 1080×1920, 30 fps, gráficos procedimentales sin stock, logotipos ni material con derechos externos.
- \`mn-short-motion/src/lab-index.jsx\`: entrada Remotion **separada**, ID \`DISIFreeMotionLab\`. Su salida es un **BORRADOR NO PUBLICAR** de 12 s; no tiene el outro V6 y no está autorizado como vídeo corporativo final.
- \`scripts/disi_public_signals.py\`: dos fuentes, GET solo lectura, JSON con título, fuente y enlace original; modo offline predeterminado, \`--live\` opcional, respuesta limitada a 2 MB y timeout 15 s. Estado editorial \`UNVERIFIED_EDITORIAL_CANDIDATES\`.
- \`tests/test_disi_public_signals.py\`: cinco tests sin red.
- \`.github/workflows/disi-free-motion-lab.yml\`: revisión en GitHub Actions, exporta MP4+JSON+ffprobe como artefacto de siete días, sin cron ni publicación ni secretos.

## Ejecución

\`\`\`bash
python -m unittest discover -s tests -p test_disi_public_signals.py -v
python scripts/disi_public_signals.py --output /tmp/disi-signals.json
python scripts/disi_public_signals.py --live --output /tmp/disi-signals-live.json
cd mn-short-motion
npm install --no-audit --no-fund
npx remotion render src/lab-index.jsx DISIFreeMotionLab ../DISI_Motion_Lab_REVIEW.mp4
\`\`\`

La prueba NO modifica el flujo ya existente de diez pistas de audio y diez subtítulos, la plantilla V9 aprobada, la investigación semanal del miércoles, el cierre M→DISI ni la configuración de publicación (desactivada).

### Fuentes y licencias

- NASA: https://eonet.gsfc.nasa.gov/docs/v3
- USGS: https://earthquake.usgs.gov/earthquakes/feed/v1.0/index.php
- Directorio de descubrimiento: https://github.com/public-apis/public-apis
- Open-Meteo se **excluye** del piloto por sus restricciones del nivel gratuito al uso no comercial.
- Acceso gratuito a datos **no significa** derechos sobre fotografías o vídeos asociados.
- GitHub Actions: los runners estándar son gratis en repositorios públicos bajo las condiciones vigentes.
- Remotion: su licencia gratuita depende del tamaño del equipo/empresa implicado (normalmente hasta tres personas). Verificar elegibilidad antes de la explotación comercial.

### Próximos pasos seguros

Analizar el MP4 y adaptar únicamente los efectos aprobados al cuerpo de V9, conservando logos originales, cierre V6, fuentes, derechos, diez audios, diez subtítulos y **duración total <59 s**. Para ingresos iniciales, medir el clic a páginas de libros y los contactos comerciales; no asumir ingresos publicitarios de Shorts sin requisitos de monetización cumplidos. El OAuth YouTube sigue bloqueado por un HTTP 403 según las pruebas previas.
