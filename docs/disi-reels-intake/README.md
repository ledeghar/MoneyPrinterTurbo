# DISI Reels Intake (piloto, sólo revisión)

Adaptación práctica de tres vídeos recibidos el 11-11-2026:

- 5301: sitio de modelos de vídeo. No se asume «gratis ilimitado» ni se envía contenido a ese proveedor.
- 5282: estilos `/editorial`, `/cinematic`, `/ugc`, etc. Convertidos en nombres de estilos documentados, no «comandos secretos».
- 5251: investigación de tendencias y creación de vídeo. Se aprovecha el flujo existente de `mn-short-weekly-trends.yml`, con pruebas y límites de publicación.

El módulo **no modifica** `mn-short-motion` ni `DisiV9.jsx`. Está aislado, no instala modelos, no llama APIs, no requiere claves, no publica ni compra créditos. El demo es una prueba de movimiento y audio sintético, no una noticia real ni el máster de marca.

~~~bash
python -m unittest discover -s tests -p 'test_disi_reels_intake.py' -v
python scripts/disi_reels_intake.py plan --brief docs/disi-reels-intake/brief.example.json --output /tmp/disi-review.json
python scripts/disi_reels_intake.py demo --output /tmp/disi-reels-demo.mp4
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 /tmp/disi-reels-demo.mp4
~~~

La plantilla editorial definitiva V9, aprobada el 10-11-2026, exige el cierre V6 original de 7,666 segundos y los recursos originales de Canva; estos ficheros privados no se subirán a GitHub público. La duración máxima se mantiene bajo 59 segundos. Archivar guion, fuente, originales, manifest y vídeo por título y fecha.
