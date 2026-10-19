# Interfaz del asistente postal

La interfaz toma el azul `#20539a` y el amarillo `#fecc36` de [Correos de Bolivia](https://correos.gob.bo/). El original se conserva en `frontend/public/correos-bolivia.png`; la interfaz usa `correos-bolivia-transparent.png`, una variante sin fondo amarillo. En modo oscuro se aclara mediante CSS para mantener su legibilidad, sin halos ni placas.

- Paneles translúcidos, reflejos y desenfoque de fondo, con superficies legibles sin desenfoque.
- Sobre postal animado con CSS/SVG, sin dependencias nuevas ni recursos externos.
- Selector claro/oscuro disponible antes y después de ingresar. Usa la preferencia del sistema al primer acceso y conserva la selección en `localStorage` bajo `correos-theme`.
- Diseño adaptable, navegación por teclado y respeto de `prefers-reduced-motion`.
- Cartero de la referencia del usuario dentro del mensaje del asistente mientras se genera la respuesta, con una secuencia de 24 poses pensando creada con ImageGen, con transiciones a 24 fps (96 cuadros en cuatro segundos). Se muestra a 240 px (220 px en móvil), con el texto «Construyendo tu respuesta». Desaparece al terminar, fallar o detener la consulta. Usa `frontend/public/cartero-thinking-v2-24fps.webm`, con transparencia y reproducción en bucle. Conserva `cartero-thinking-v2.png` como pose estática al solicitar movimiento reducido o si no puede reproducirse el vídeo.
- Se conservan autenticación, historial, consultas, fuentes y visualización de registros.

Validación: `npm test` y `npm run build` desde `frontend`. Con Vite activo y un navegador de Playwright CLI abierto, ejecutar desde la raíz:

```powershell
npx --yes --package @playwright/cli playwright-cli run-code --filename=scripts/check_frontend_ui.js
```

Esta comprobación visita el acceso, verifica cambio y persistencia de tema, formulario vacío, ausencia de desbordamiento a 320/390/768/1440 px y movimiento reducido. No necesita credenciales. Reinicia la página de prueba; las consultas reales requieren los servicios locales documentados en README.

`playwright-cli --session mascot run-code --filename=scripts/check_mascot_ui.js` verifica el cartero con respuestas simuladas: espera, éxito, error y cancelación, ambos temas, movimiento reducido y ubicación dentro de la respuesta, tamaño mínimo de 200 px y ausencia de solapamiento con el compositor de 320 a 1440 px. Ejecutar en una sesión de navegador de prueba abierta.

## Identidad institucional

La cabecera amarilla, las franjas azules, los títulos de peso 700–800, las tarjetas claras y los botones amarillos siguen la jerarquía del sitio institucional. El acceso conserva la ilustración original del sobre animado y el mensaje «Menos búsquedas. Más respuestas.». El tema oscuro conserva el amarillo y el azul institucionales.
## Navegación lateral

El historial incluye búsqueda local por título, sin distinguir mayúsculas, con estado sin coincidencias y botón para limpiar. Los títulos admiten dos líneas y muestran el texto completo al pasar el cursor. El pie de sesión permanece visible y el historial desplaza por separado.

Con el chat autenticado en Playwright CLI, `playwright-cli run-code --filename=scripts/check_sidebar_ui.js` comprueba el filtrado, su limpieza y el cierre del menú móvil con Escape.

## Fichas y datos relacionados

Las fichas usan secciones planas: datos de la sucursal y bloques separados para personal, empresas y otras relaciones disponibles. No hay desplegables anidados. Los nombres y el contexto de cada bloque sustituyen las referencias internas; se ocultan IDs, claves foráneas y metadatos de transporte. Las listas y categorías vacías no se muestran. Los valores numéricos cero y los booleanos falsos se conservan cuando son datos del registro. Las fechas se presentan en formato legible, respetando la hora guardada cuando no tiene zona horaria. Los avisos de resultados parciales y la paginación se mantienen.

`playwright-cli run-code --filename=scripts/check_details_layout.js` verifica la ficha y sus páginas asociadas con datos sintéticos, en ambos temas y a 320/390/600/768/1440 px. Comprueba que no haya IDs visibles, secciones vacías, desplegables ni desbordamiento. Las pruebas de transformación están incluidas en `npm test`.
