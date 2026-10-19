# Fichas completas y datos asociados

El usuario autorizó expresamente incluir tanto datos institucionales como personales. La ficha completa es una operación distinta del resumen y exige `personal_data`, además del permiso de seguimiento u oficinas y el alcance `global_internal`. La consulta normal sigue devolviendo solo los campos resumidos.

## Comportamiento

Después de «dame los datos de la sucursal de La Paz», escribir «dame los datos completos» reutiliza la sucursal confirmada. También se reconoce el ejemplo «dame compelto lo datos completos». Después de consultar un código, la misma continuación amplía la ficha del envío. Se conserva solo la intención y sus filtros; se vuelven a consultar datos y permisos. Las fichas personales se conservan en el historial privado solicitado por el usuario, con permisos vigentes al abrirlo; sus resultados no se envían al modelo. Ver [conversaciones guardadas](saved-chats.md).

Sin contexto, «datos completos» pide sucursal o código. «Dame el último dato guardado» pide precisar tabla/tipo; no se trata como tema ajeno ni se interpreta como un último registro global entre tablas sin relación. Una petición con otro departamento o código se interpreta por separado y no reutiliza silenciosamente el anterior.

Las peticiones con un recurso explícito, como «dame todos los datos de la oficina de La Paz» o «toda la información de la sucursal de La Paz», también activan la ficha completa, aunque el modelo clasifique inicialmente una consulta resumida. Se mantienen los filtros explícitos y los permisos de acceso a detalles.

Las continuaciones toleran pequeñas erratas en palabras de presentación, como «datos compeltos», y referencias como «más detalles» o «muéstrame toda su información». No se corrigen códigos, fechas ni nombres de lugares. Una solicitud incompleta «sucursales y envíos» recibe una aclaración que conserva el departamento ya confirmado y solicita el código del envío. La aclaración no borra el último recurso confirmado; «más detalles» puede retomarlo. Estas reglas no unen envíos a sucursales por coincidencia de ciudad.

La interfaz muestra campos y relaciones en secciones desplegables, con valores ausentes explícitos. Cuando una relación contiene más de 50 registros se indica `truncado=true`, con límite 50; no se afirma que la lista sea exhaustiva. Si una ficha supera el límite total de bytes, se pide reducir la información y no se informa falsamente que no hay registros.

## Cobertura

Las continuaciones que solo cambian el departamento («ahorita las de Santa Cruz», «ahorta las de santa cruz», «y de Pando») conservan la consulta anterior de sucursales: si se estaba consultando personal, mantienen la tabla de personal. El contexto se recupera del historial al reabrir el chat y se mantiene aunque un departamento no tenga resultados. Una petición explícita de otro recurso cambia el tema. Los chats guardados afectados por el clasificador anterior recuperan el tema de personal desde la última petición explícita, sin reescribir respuestas antiguas.

«Dame qué personal hay en la sucursal de Beni en tablas» consulta directamente el personal asignado, sin tratarlo como un tema ajeno ni devolver toda la ficha de la oficina. También se reconocen empleados, funcionarios, trabajadores y usuarios. La tabla muestra nombre, correo, documento de identidad, ciudad, sucursal y departamento disponibles, sin IDs internos. Usa la relación directa `users.sucursal_id` de la ficha autorizada y exige `offices`, `internal_data`, `personal_data` y alcance interno. Si falta el departamento se solicita; «y el personal en tablas» conserva el departamento previamente confirmado. Un departamento nuevo sustituye al anterior. Las listas parciales se identifican como tales y los resultados quedan en el historial privado con sus permisos.

Las tablas y columnas admitidas están en `config/details_catalog.json`. La ampliación comprende las sucursales, cinco familias de paquetes y los catálogos/registros relacionados revisados: usuarios, empresas, estados, servicios, ventanillas, referencias tarifarias, eventos, carteros, bitácoras, malencaminados, formularios y preregistros. No se habilita un explorador SQL arbitrario de las 122 tablas del respaldo.

La sucursal muestra sus ocho columnas originales, incluidos `puntoVenta`, creación y actualización, y sus usuarios asignados mediante `users.sucursal_id`. No se asocia un paquete a una sucursal por coincidir su texto de ciudad. Los paquetes incorporan campos institucionales y personales autorizados y relaciones del catálogo, usando las FK declaradas. Los eventos asociados por código indican expresamente que la coincidencia es textual y no una FK. Los IDs sin una relación declarada se muestran sin inventar una asociación.

Contraseñas, tokens de sesión y campos de autenticación quedan excluidos del esquema importado. Para imágenes, mapas y archivos adjuntos se informa si existe contenido mediante campos `*_presente`; no se importa el binario ni se navega a enlaces del respaldo. Las referencias tarifarias se muestran como datos guardados, sin declarar vigencia, moneda o fórmula que no hayan sido confirmadas.

## Acceso y operación

`scripts/upgrade_details.py <respaldo>` crea `chatbot_details_source` y las vistas en una transacción en la base local del proyecto. No altera tablas operativas ni sobrescribe un esquema de detalles existente. Los campos personales quedan en esa proyección privada, aparte de las tablas resumidas; el rol API no puede leer sus tablas directamente.

`scripts/authorize_local_details.py` concede el nuevo permiso únicamente al operador local ya autorizado. `--revoke` permite retirarlo; reiniciar la API para aplicar el cambio. No se conceden automáticamente permisos a otros usuarios. Los secretos continúan fuera de Git.

Las vistas de detalles exigen simultáneamente alcance interno y `chatbot.personal_access=allowed` dentro de la transacción. El backend establece ese segundo contexto solo desde la identidad autorizada, y comprueba el permiso en operaciones y acceso a datos. La auditoría identifica `offices_details` o `tracking_details`, sin registrar las fichas, códigos o mensajes. Las respuestas se renderizan de forma determinista y React escapa los valores, incluidos textos almacenados no confiables.

Después de aplicar esta actualización, reiniciar backend y recargar el navegador. Las sesiones anteriores eran efímeras; iniciar una conversación nueva para establecer de nuevo el contexto de sucursal o envío.

## Verificación de esta actualización

31 pruebas backend, 6 pruebas de scripts y 2 pruebas SSE aprobadas; build frontend aprobado. `python scripts/check_details.py` verificó seis conversaciones de extremo a extremo con datos reales y modelo CPU: petición ambigua del último dato, sucursal con errores de escritura, ficha completa con el texto exacto del usuario, repetición de detalles asociados, seguimiento y ficha completa del envío. La comprobación actual del historial verifica que conserve la respuesta y sus filas autorizadas.

PostgreSQL verificó ambas condiciones de contexto, ausencia de privilegios directos sobre `chatbot_details_source`, ocho campos por oficina, igualdad de conteos de las cinco familias y ausencia recursiva de credenciales/adjuntos en los JSON de muestra. En el navegador se verificaron los campos adicionales y secciones asociadas, continuación de sucursal, anchos 320/768/1440, token solo en memoria y cero errores JavaScript. Las pruebas imprimen solo estados/contadores; no generan capturas de datos personales. Los informes locales `.runtime/details-import.json`, `details-validation.json` y `details-api-validation.json` no incluyen fichas personales.
