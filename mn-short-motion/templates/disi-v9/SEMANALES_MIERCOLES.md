# MNShort semanal — miércoles 12:00 (Europa/Madrid)

Regla aprobada: **UN vídeo a la semana**, cada miércoles a las 12:00, seleccionado tras investigar un nuevo micronicho que concentre millones de visualizaciones.

## Ciclo

1. Miércoles 08:15 (Europe/Madrid): GitHub Actions ejecuta el estudio de YouTube sin laptop ni sesión de ChatGPT.
2. En los últimos 7 días exige al menos dos Shorts con más de 1.000.000 de visualizaciones cada uno y de dos canales independientes. Se guardan los IDs, URLs, fechas, vistas, categoría y micronicho exacto; no se inventan resultados.
3. Busca entre los RSS de la categoría ganadora una noticia actual relacionada con ese micronicho. Si no existe o ya se usó, retiene la producción.
4. Prepara guion, nueve traducciones, diez narraciones reales y diez subtítulos. Master un solo vídeo con 10 audio y 10 subtítulos, y corte español.
5. Controla duración inferior a 59 segundos y, aparte, veracidad, licencias, relación imagen-noticia, identidad y plantilla V9 (Canva + cierre V6) antes de publicación. Si falta cualquier evidencia, se archiva el informe pero no se publica.
6. Publicación objetivo: miércoles 12:00, mediante YouTube OAuth y confirmación del canal. El evento debe completarse antes del horario de publicación.
7. La API de YouTube permite añadir diez archivos SRT si el permiso OAuth youtube.force-ssl está concedido; diez cargadas cuestan unas 4.000 unidades de cuota. Los nueve doblajes alternativos no pueden integrarse en un mismo vídeo mediante la API pública disponible: requieren YouTube Studio o una función oficial que se habilite en el futuro.
8. Guardar informe, títulos, fechas, vídeo, pistas y fuentes bajo título + fecha en el NAS, con copia temporal en GitHub Actions.

## Configuración técnica

- Calendario semanal nuevo: .github/workflows/mn-short-weekly-trends.yml, cron 15 8 * * 3, zona Europe/Madrid.
- Calendario anterior de seis franjas: eliminado. El flujo antiguo queda manual y sin disparador de horario.
- Datos de tendencias: scripts/mn_short_weekly_niche.py. Usa secreto opcional YOUTUBE_DATA_API_KEY o OAuth autorizado para consultar estadísticas públicas.
- Comprobación editorial: scripts/mn_short_release_gate.py.
- Control de cuenta: scripts/mn_short_youtube_channel_guard.py, MNSHORT_EXPECTED_CHANNEL_ID.
- Publicación semanal autorizada mediante variable MNSHORT_WEEKLY_PUBLICATION_ENABLED=true, nunca con esa variable sola: hay otros dos controles obligatorios.
- Subtítulos: scripts/mn_short_youtube_captions.py, permisos youtube.force-ssl.

## Estado sin maquillajes

El estudio semanal y la generación de borradores están configurados. **La publicación pública no está habilitada aún:** la ruta actual de borradores no utiliza todavía los recursos privados exactos de la plantilla V9 aprobada ni emite la validación independiente de licencias y fuentes requerida por el control. No debe publicarse automáticamente un vídeo genérico presentándolo como V9.

El OAuth de Google se renovó correctamente en una prueba anterior, pero la identificación del canal de YouTube devolvió HTTP 403. Hay que ajustar el permiso y confirmar el canal antes de permitir subidas autónomas.

El objetivo es un vídeo bueno y comprobable por semana. Si no hay nicho verificable, se retiene la publicación: no se fabrica una noticia para cumplir el calendario.
