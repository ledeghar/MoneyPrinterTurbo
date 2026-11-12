# DISI Book Marketing v0.1 — 11 de noviembre de 2026

Marketing editorial automatizado sin cuotas ni servidor permanente para promocionar los libros **ALEPO** y **JARTUM** desde la infraestructura MNShort.

**Esta fase prepara campañas y una web estática; NO publica en redes, no aloja la web, no paga anuncios, no recopila datos privados ni envía mensajes sin consentimiento.** Mantiene intactos DISI V9, las 10 pistas y el cierre corporativo V6.

## Enlaces y ediciones

- **ALEPO: Los cristianos olvidados**, subtítulo editorial «El día que Roma dejó caer la cruz». Amazon KDP ISBN 9798167321427, ASIN B0HQ58WM3Y; URL por ASIN: https://www.amazon.es/dp/B0HQ58WM3Y . Publicación comunicada por el autor; **pendiente de comprobar el enlace comercial en vivo**.
- **JARTUM: Los que quedaron atrás**. Edición Amazon KDP ISBN 9798165874536, ASIN B0HPRHJNJ1, URL por ASIN https://www.amazon.es/dp/B0HPRHJNJ1 (pendiente de comprobar); **edición Lulu diferente**, ISBN 9781326492946, ficha comercial pública comprobada: https://www.lulu.com/es/shop/juan-manuel-ledesma/jartum-los-que-quedaron-atras/paperback/product-m2rdqz7.html .

No mezclar ISBN de ediciones distintas ni inventar precio, reseñas, stock, descuentos o ventas.

## Qué hace en GitHub

1. Validación del catálogo de obras, ISBN y librerías de destino en HTTPS.
2. Generación de una página estática responsiva con enlaces de compra, sin cookies ni rastreadores, en disi-book-marketing/output/site.
3. Calendario editable de **28 borradores en 4 semanas**, alternando ALEPO y JARTUM: lunes (LinkedIn y Facebook), miércoles (YouTube, Instagram, TikTok), viernes (X, Pinterest).
4. Exportación de campaigns.json, campaign-calendar.csv y copy-to-review.txt, sin publicar.
5. Ejecución manual y semanal mediante GitHub Actions los lunes 07:15 UTC después de fusionar. El resultado permanece como artefacto temporal durante 30 días.
6. Tests sin red que bloquean enlaces externos no reconocidos, campañas sin aprobación, supuestos ingresos y publicaciones sin vídeo completo.

No se ha conectado ningún servicio de terceros, comprado publicidad ni desplegado página pública.

## Requisitos obligatorios de cualquier vídeo

- DISIV9Approved con originales Canva de Media News/DISI.
- Cierre corporativo original V6 (~3,5 s) M→DISI.
- Máster MP4 con **10 voces reales y 10 pistas de subtítulos sincronizadas**, idiomas es, en, fr, de, it, pt, ru, zh, ja y ar. QA FFprobe y control editorial, duración total inferior a 59 s.
- Imágenes/música con derechos, aprobación editorial, cuenta autorizada y antifraude/deduplicación.
- El planificador no genera ni publica automáticamente vídeos; no se salta el flujo MNShort.

## Ejecutar con Python estándar

    python -m unittest discover -s tests -p test_disi_book_marketing.py -v
    python disi-book-marketing/marketing.py --start 2026-11-16

Después de publicar realmente la página, se puede generar una nueva campaña con URLs UTM:

    python disi-book-marketing/marketing.py --landing-url https://TU-DOMINIO-REAL/ --start 2026-11-16

El parámetro landing-url no verifica dominio ni despliega nada. Las métricas de clics y las ventas reales siguen siendo **desconocidas** hasta conectar analítica y consultar informes KDP/Lulu.

## Alojamiento gratuito, fase posterior

Cloudflare Pages (plan gratuito) puede conectar GitHub: https://developers.cloudflare.com/pages/get-started/git-integration/

Configuración futura:
- Repo: ledeghar/MoneyPrinterTurbo
- Rama: main **tras revisar y fusionar el borrador**
- Build command: python3 disi-book-marketing/marketing.py --site-dir disi-book-marketing/output/site --campaign-dir disi-book-marketing/output/campaigns
- Output directory: disi-book-marketing/output/site

Verificar enlaces Amazon y portadas auténticas antes de publicar. No hay imágenes falsas de portadas: la web usa tratamiento tipográfico provisional.

## Integraciones existentes que reutilizar (NO activadas)

- scripts/mn_short_crosspost.py: FB/IG y TikTok opcional, servicio Upload-Post posiblemente de pago, **excluido por presupuesto**.
- scripts/mn_short_publish_scheduled.py: YouTube, depende de OAuth y control editorial, no usar antes de autorización.
- scripts/mn_short_channel_analytics.py: lectura de rendimiento de YouTube con autorización, no de KDP/Lulu.
- El sistema de noticias semanal es independiente y no debe cambiarse.

## Pendientes concretos

1. Comprobar URLs Amazon y obtener portadas oficiales autorizadas del autor.
2. Aprobar los copies y conectar gratuitamente una web.
3. Preparar vídeo V9 de promoción con diez pistas, subtítulos y cierre original.
4. Conectar cuentas de redes mediante APIs autorizadas y resolver OAuth YouTube.
5. Medir enlaces clicados y conciliar con ventas KDP/Lulu sin inventar atribución.

El código queda abierto para revisión en una PR independiente, sin alterar producción.
