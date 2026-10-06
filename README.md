# Mi FICValdivia 2026

Agenda personal para el 33 Festival Internacional de Cine de Valdivia (12–18 oct. 2026).
Eliges funciones con tu nombre (sin cuenta), se guardan en tu navegador y las descargas como `.ics`
para Google Calendar, Apple Calendar u Outlook.

Sitio estático: `index.html` + `data.js` (programación) + `ics.js` (genera el calendario).
Prueba del generador: `node ics.test.js`.

Para actualizar la programación (horarios, duraciones, estado de cada función e imágenes nuevas): `python3 actualizar.py`, luego `python3 programa_pdf.py` (regenera `programacion-ficv2026.pdf`, la programación completa; necesita Google Chrome), y commit y push.

Datos e imágenes: [33.ficvaldivia.cl/programacion](https://33.ficvaldivia.cl/programacion), al 5 de octubre de 2026. Sitio no oficial.

## Actualización automática

`.github/workflows/actualizar.yml` corre `actualizar.py` (y `programa_pdf.py` si hubo cambios) todos los días a las 07:00 de Chile, y publica solo si cambió algo. Se detiene sola después del 19 de octubre de 2026. Para correrla a mano: pestaña **Actions → Actualizar programación → Run workflow**.

## Tarjeta al compartir

`og.png` (1200×630) es la imagen que muestran X, WhatsApp, etc. al pegar el enlace.

