# Conversaciones guardadas

Cada conversación recibe un UUID del servidor y una dirección como `/c/3e40cb2d-7f08-4904-8ab6-bb43cc1d4bf1`. El código aparece bajo el título del centro de consultas. La primera pregunta da nombre al chat en el historial. Los enlaces del historial permiten abrirlo en otra pestaña y funcionan con Atrás/Adelante.

Se guardan preguntas, respuestas, filas devueltas, fuentes, fechas y filtros confirmados. Al recargar o volver a abrir la aplicación, ingresar con la clave del mismo operador y abrir el chat desde su URL o desde el historial. El token sigue únicamente en memoria del navegador; no se guarda en la URL, localStorage ni sessionStorage. Conocer el UUID no concede acceso.

SQLite conserva los chats en `.runtime/chat-history.sqlite3`. El arranque con `-Fixture` usa `.runtime/chat-history-fixture.sqlite3`. `CHATBOT_HISTORY_PATH` permite indicar otra ruta. El archivo es privado del servidor y no se publica ni se versiona. La aplicación usa consultas parametrizadas y verifica propietario, alcance y permisos vigentes antes de devolver mensajes. Una conversación con fichas personales requiere conservar `personal_data`; una que contiene seguimiento requiere `tracking` e `internal_data`. El listado oculta los chats cuyo contenido ya no está autorizado.

La plantilla systemd utiliza su directorio de estado `/var/lib/correos-chat` para permitir persistencia con `ProtectSystem=strict`. La configuración `api.env` puede indicar otra ruta administrada con permisos de escritura adecuados.

Las conversaciones sobreviven al reinicio del backend. El TTL de 30 minutos solo limpia la caché de contexto en memoria. No elimina los chats guardados. No se recortan los mensajes al antiguo límite de 40. El límite configurable `CHATBOT_MAX_SESSIONS` (100 por defecto, máximo 1000) rechaza nuevas conversaciones al alcanzarse y permite continuar las existentes; no elimina silenciosamente las anteriores.

Los errores y cancelaciones conservan la pregunta con una indicación de interrupción. Una sola consulta puede ejecutarse a la vez en cada chat. El despliegue mantiene un worker API; la cola de inferencia y la cancelación siguen en memoria. El historial conserva el resultado original: abrirlo no acredita que esos datos sigan actualizados. Una consulta nueva vuelve a verificar datos y permisos.

El almacenamiento incluye datos operativos y personales presentes en las respuestas autorizadas. Proteger sus permisos de archivo como los demás archivos privados de `.runtime`. Para respaldar el historial local, detener la API y copiar el archivo SQLite; restaurarlo con la API detenida. No hace falta modificar el respaldo postal ni conceder escritura al lector de PostgreSQL. Los chats anteriores a esta actualización eran efímeros y no contenían mensajes originales recuperables.

Verificaciones: recuperación tras reinicio, contexto de seguimiento, resultados completos, aislamiento por operador, revocación de permisos, caché caducada, límite sin borrado, más de 40 mensajes y errores guardados. En navegador: URL, código visible, historial, recarga, Atrás/Adelante y diseño móvil.
