# DISI / Media News — plantilla V9 aprobada

**Referencia congelada: 10-11-2026.** No sobrescribir ningún original aprobado.

## Referencia y SHA-256

- Máster: MASTER_10_AUDIO_10_SUBTITULOS.mp4. Dura 54,773 s, 720×1280, 1 vídeo H.264, **10 voces AAC reales y 10 subtítulos mov_text**, idiomas es/en/fr/de/it/pt/ru/zh/ja/ar.
- SHA-256 máster: 3b2817d6b5461f2ddcd76062c4315074f6faed64fceac2b434f83fdba45b59de.
- Cierre: OUTRO_V6_ORIGINAL.mp4, transformación M → DISI, **sonido original OK! News**, 7,666 s.
- SHA-256 cierre: 67536b800ba211d52e364489c6c1418459e9e3c5c256a2df92669ad054c6e926.
- VIDEO_APROBADO_ES.mp4: locución original de Pelayo y karaoke de palabras.
- Logos requeridos: LOGO_MEDIA_NEWS_CANVA.png, LOGO_DISI_CANVA.png, MEDIA_CANVA_WORDMARK.png. No sustituir por iniciales ni recreaciones tipográficas.
- Mantener archivos fuente, narraciones y SRT en NAS. No publicar archivos de fuentes tipográficas.

Los masters y activos originales están archivados en el paquete **DISI_V9_MAESTRA_CONGELADA_2026-11-10.zip** (almacenamiento privado del proyecto). No publicar material de marca ni vídeos privados en este repositorio público sin autorización.

## Contrato audiovisual para nuevos MNShort

1. **Menos de 59 s incluyendo el V6 de 7,666 s**. Mantener intacta la pista sonora del cierre.
2. Vídeos reales estables, sin zoom artificial ni metraje que atribuya identidades inventadas.
3. Cabecera con los originales MEDIA/Media News/DISI; tipografía editorial serif en titulares, pies y colores originales; no sustituir el arte de Canva por texto.
4. Banda oscura reservada abajo, subtítulos de máximo dos líneas, claros y con color por palabra sincronizado con la voz.
5. Audio inteligible sin ambiente molesto, sin cortar ni estirar la locución, y sin presentar canales mudos como «idiomas».
6. Comprobar 10 pistas de voz y 10 pistas de subtítulos con FFprobe; revisar todas las traducciones antes de publicar.
7. Identidad visual de cierre y Media News by DISI. Guardar originales en NAS bajo titular + fecha.

## Generador Remotion

La composición **DISIV9Approved** vive en mn-short-motion/src/DisiV9.jsx y está registrada de forma independiente de MNShortEditorial. Produce un Short a 720×1280 y 25 fps mediante el storyboard del vídeo.

Copiar desde el archivo maestro privado los siguientes recursos a **mn-short-motion/public/disi-v9/**:

- LOGO_MEDIA_NEWS_CANVA.png
- LOGO_DISI_CANVA.png
- MEDIA_CANVA_WORDMARK.png
- OUTRO_V6_ORIGINAL.mp4
- Audio correspondiente y clips licenciados para cada nueva noticia.

No se emplearán logotipos sustitutos si falta un original.

Propiedades de la composición:
- totalFrames y bodyFrames, siempre reservando la duración completa del V6.
- scenes: objetos con file, headline, startFrame, durationFrames, sourceStartFrame.
- captions: objetos con startFrame, endFrame, text y opcionalmente words (text, start, end en segundos).
- audio: archivo de narración dentro de public/disi-v9.

Comando (tras importar recursos y preparar props/nueva_noticia.json):

    cd mn-short-motion
    npm install
    npx remotion render src/index.jsx DISIV9Approved ../salida/MNShort_NUEVO_ES.mp4 --props=./props/nueva_noticia.json

## Verificación y preparación de YouTube

Verificar el máster APROBADO:

    python scripts/mnshort_v9_template.py verify --master /NAS/DISI/V9/MASTER_10_AUDIO_10_SUBTITULOS.mp4 --approved

Exportar el MP4 español y diez paquetes de idiomas SIN modificar el máster:

    python scripts/mnshort_v9_template.py youtube --master /NAS/DISI/V9/MASTER_10_AUDIO_10_SUBTITULOS.mp4 --approved --reviewed --title "DISI: periodismo y fuentes" --output /NAS/DISI/YOUTUBE

Exporta MNShort_YOUTUBE_ES.mp4 y, por separado, los nueve audios .m4a y diez subtítulos .srt. **Esta acción no publica ningún vídeo.** La API de YouTube puede publicar el MP4 con OAuth y cargar subtítulos, pero las pistas de doblaje se agregan por idioma desde YouTube Studio en canales elegibles. No basta subir el MP4 de diez audios.

Existe un publicador unlisted de prueba, scripts/mn_short_youtube_direct.py; requiere secretos YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET y YOUTUBE_REFRESH_TOKEN configurados y confirmación manual. Verificar el canal de destino, ya que existen varios posibles canales. Ningún disparo automático se habilita con esta plantilla.

Para TikTok, Facebook, Instagram y LinkedIn, usar un corte por idioma revisado, no el máster diez pistas.

## CI y archivo seguro

El workflow disi-v9-template-qa.yml valida sintaxis y reglas; NO publica y NO requiere credenciales. El empaquetado de archivo conserva SHA-256; no reemplazar el original. La automatización de publicación requiere validación HUMINT, derechos de cada clip, audio, subtítulos y autorización de la cuenta.
