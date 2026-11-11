---
name: disi-reels-intake
version: "0.1.0"
description: Produce a source-traceable and human-reviewable MNShort brief or a clearly marked offline motion demo, inspired by reusable styles, not viral-automation promises.
---

# DISI / MNShort — brief audiovisual y prueba segura

Activar para transformar un material aportado en storyboard corto de Media News/DISI sin inventar datos, y para ensayar gráficos en vídeo. **No sustituye la plantilla V9 aprobada ni publica.**

## Entradas

`title`, `mode` (`news`, `documentary`, `book`, `promo`), `style`, `hook`, `context`, `evidence`, `cta`.
Para `news`/`documentary` se requieren `sources` con `id`, `title`, `url` y `claims` cuyos `source_ids` existan.
Los datos de tendencias externas deben respaldarse con pruebas de la plataforma, fecha, periodo y metodología. No prometer nichos virales automáticamente.

## Estilos controlados

`editorial`, `documentary`, `cinematic`, `ugc`, `noir`, `archive`, `infographic`, `stickman`.
Las supuestas «32 órdenes secretas» son palabras para orientar el estilo, no funciones especiales de ChatGPT.
En `news`, nunca presentar ilustración, recreación o vídeo sintético como grabación de un hecho.

## Secuencia del trabajo

1. Comprueba autoría, fechas, fuentes, derechos, contexto, declaraciones y contenidos sintéticos.
2. Planifica gancho (0–3 s), contexto (3–7 s), evidencia (7–10 s), CTA (10–12 s) usando texto suministrado.
3. Ejecuta `python scripts/disi_reels_intake.py plan --brief briefing.json --output borrador.json`.
4. Si se pide demostración sin credenciales, `python scripts/disi_reels_intake.py demo --output prueba.mp4`.
5. **Revisar antes de producir/publicar**; conservar originales y fuentes en NAS por título y fecha.
6. El vídeo publicable debe usar la composición `DISIV9Approved` y los logos originales y cierre **V6 de 7,666 s** de `mn-short-motion/templates/disi-v9/README.md`. Ningún placeholder sustituye esos recursos. Para publicación confirmar duración total inferior a 59 s, audio/idiomas, derechos y verificación editorial.

## Proveedores

El vídeo 5301 afirma gratuidad ilimitada sin demostrar el procesamiento. **Nunca enviar materiales propietarios a una web desconocida ni activar proveedores de pago sin autorización expresa.** El modelo Seedance en MoneyPrinterTurbo requiere confirmación de cobro si se configura como tal. El demo local no genera escenas fotorrealistas.

El vídeo 5251 simplifica excesivamente descubrimiento de nicho, guion y edición; reutilizar el workflow existente `mn-short-weekly-trends.yml`, no abrir otro publicador. Las escenas `stickman` son una opción ilustrativa independiente (no suplantar imágenes documentales). El paquete local DISI Reels Skill v0.2 puede incorporarse posteriormente mediante auditoría de dependencias; este skill no instala terceros.
