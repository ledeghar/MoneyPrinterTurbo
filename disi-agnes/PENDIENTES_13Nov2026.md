# DISI — Pendientes para el viernes 13 de noviembre de 2026

**Objetivo:** desde el portátil prestado, activar y probar la generación real de vídeos de Agnes con Claude Code y GitHub Actions, sin romper la fábrica audiovisual DISI.

## Estado confirmado al 12 de noviembre de 2026

- Repositorio: `ledeghar/MoneyPrinterTurbo`.
- Integración Agnes **fusionada en main**: [PR #34](https://github.com/ledeghar/MoneyPrinterTurbo/pull/34), commit `ca2e3830caab3be4c29a7acb3cf11761558ba493`.
- Skill Claude Code: `.claude/skills/disi-agnes-video/SKILL.md`.
- Adaptador: `disi-agnes/agnes_video.py`; documentación: `disi-agnes/README.md`.
- Workflow: `.github/workflows/disi-agnes-video.yml`.
- Run de GitHub Actions `43289884516`: **pruebas offline y dry-run superados**. No hay un MP4 generado por Agnes todavía.
- Integración opcional, sin publicar automáticamente, y **Remotion V9 + FFmpeg intactos**.

## Prioridad 1 — Crear clave Agnes y activar prueba real

- [ ] Acceder a https://platform.agnes-ai.com/ y crear/verificar la cuenta.
- [ ] Comprobar límites y condiciones vigentes del modelo gratuito `agnes-video-2.5-flash`, incluidos derechos comerciales y capacidad de la cola.
- [ ] Crear una clave API Agnes; **nunca compartirla en el chat ni guardarla en código, archivos, logs o capturas**.
- [ ] En GitHub: `ledeghar/MoneyPrinterTurbo → Settings → Secrets and variables → Actions → New repository secret`, crear `AGNES_API_KEY` con ese valor.
- [ ] En Actions, abrir `DISI Agnes - optional AI video clip`; hacer una ejecución manual con `execute=false` (simulación gratuita).
- [ ] Ejecutar una prueba de **5 segundos**, prompt público o ficticio y `execute=true`; verificar respuesta y consumo real.
- [ ] Descargar el artefacto `disi-agnes-draft`, examinar MP4 y JSON: duración, 9:16, resolución, calidad, marca de agua, errores y procedencia.
- [ ] Si se producen errores 401/429/503, diagnosticar credenciales, límites y saturación; **no pasar automáticamente a servicios de pago**.

## Prioridad 2 — Claude Code y fábrica de reels DISI

- [ ] Acceder a GitHub desde el portátil prestado y comprobar que Claude Code reconoce la skill `disi-agnes-video`.
- [ ] Revisar la conexión actual Claude Code + OpenRouter y el modelo seleccionado sin revelar ni modificar innecesariamente claves existentes.
- [ ] Enlazar el clip generado, tras la revisión editorial, con la plantilla Remotion V9 y el montaje FFmpeg.
- [ ] Validar los requisitos: **<59 s incluyendo outro**, vídeo 9:16, voz Pelayo, música subordinada a la voz, subtítulos sincronizados, diez idiomas (`es,en,fr,de,it,pt,ru,zh,ja,ar`) y outro original Media News M→DISI de ~3,5 s.
- [ ] Comprobar separadamente el proceso efectivo de audios multilingües en YouTube (el MP4 con 10 pistas por sí solo no prueba que YouTube las publique).
- [ ] No activar subidas automáticas sin aprobación editorial. Verificar las integraciones existentes de YouTube y Facebook una vez obtenido un master correcto.
- [ ] Nombrar y archivar los vídeos con **título y fecha**, conservar originales, derechos, fuentes y manifiesto técnico, para su posterior almacenamiento en NAS.

## Prioridad 3 — Herramientas estudiadas en los vídeos enviados

- [ ] Comparar HyperFrames/skill de dirección audiovisual con Remotion y adoptar únicamente mejoras contrastadas, sin rehacer V9.
- [ ] Fortalecer el operador Claude: guion, contraste documental, selección de imágenes con derechos, montaje, validación y registro de errores.
- [ ] Mantener FreeVideo como **opción futura**, pendiente de hardware GPU, licencia y presupuesto; no forzar su instalación en el portátil de pocos recursos.
- [ ] Continuar diseño de **DISI Marketing** para vender *ALEPO* y *JARTUM*; probar llamadas a la acción, enlaces de compra verificados y atribución, sin asumir visitas o ventas garantizadas.
- [ ] Minimizar consumo de tokens, llamadas a APIs y tiempo de render; mantener servicios gratuitos como primera opción y documentar costes antes de contratar nada.

## Seguridad en portátil prestado

- [ ] Preferir Secrets de GitHub y gestor de contraseñas. No almacenar claves en el equipo ni crear archivos `.env` persistentes en él.
- [ ] No copiar documentos HUMINT ni información privada de fuentes a Agnes, GitHub ni al portátil prestado.
- [ ] Al acabar, cerrar sesiones y revocar sesiones temporales de GitHub/Agnes si procede.

## Qué debe quedar demostrado

1. Un workflow de Actions produce un **clip Agnes MP4 real** con su registro técnico, o documenta la razón verificable del bloqueo.
2. Claude Code identifica y utiliza la integración en una prueba.
3. La fábrica Remotion V9 existente sigue intacta, y no se ha hecho ninguna publicación sin autorización.

**Punto de continuación en el próximo chat:** abrir este archivo y comenzar por la clave Agnes en GitHub Secrets. Crear un chat independiente para la jornada 13Nov2026.
