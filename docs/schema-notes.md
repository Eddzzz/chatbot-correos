# Esquema identificado

Inspección mediante `pg_restore 18 --schema-only`, sin conexión a una base, sin ejecutar SQL y sin leer filas. El respaldo de formato custom contiene 122 tablas y 159 claves foráneas. `source-schema.sql` conserva solo definiciones CREATE TABLE y FK: no es una migración ejecutable completa (omite claves únicas, secuencias y demás objetos). No se restauró el respaldo.

## Proyección inicial

- `chatbot.v_tracking`: unión de `paquetes_certi`, `paquetes_ordi`, `paquetes_ems`, `paquetes_contrato`, `paquetes_int`. Columnas: `source`, `shipment_id`, `tracking_code`, `status`, `origin`, `destination`, `registered_at`, `updated_at`, `weight_value`, `amount_value`. Estado por `estados.id`: FK `fk_estado` en certi/ordi, `estado_id` en ems/int y `estados_id` en contrato. `int` tiene campos, pero no FK declarada hacia estados. Se preserva literalmente `cuidad` en certi. Código de seguimiento no implica unicidad entre familias.
- `chatbot.v_offices`: `sucursales.id`, `codigoSucursal`, `municipio`, `departamento`, `telefono`. No existen dirección, horarios ni servicios disponibles en esta tabla. `ventanilla` es un catálogo distinto, sin vínculo declarado a sucursales.
- Analítica: conteo de filas por familia, estado o destino sobre `v_tracking`, en periodo explícito. No inferir significado de entregado/retrasado ni sumar ingresos hasta validar negocio. El identificador compuesto es familia + id; la misma referencia entre familias puede representar duplicación operativa.
- Tarifas detectadas: `tarifario` relaciona `servicio_id`, `origen_id`, `destino_id`, `peso_id` con catálogos, y contiene `precio`. `peso` contiene `peso_inicial`, `peso_final`. No hay vigencia explícita. `tarifa_contrato` contiene condiciones por `empresa_id` y debe permanecer privada. Consulta de tarifa deshabilitada hasta confirmar vigencia, moneda, unidades, inclusión de límites y fórmula.
- Eventos: `eventos_certi`, `eventos_ordi`, `eventos_ems`, `eventos_contrato` relacionan `evento_id` con `eventos`; se asocian por `codigo`, sin FK declarada a paquetes. No habilitar unión automática que duplique conteos. `detalle_evento` y textos libres se excluyen.

## Frontera de seguridad

Solo acceso interno global con permiso explícito: no existe relación homogénea de todas las familias con un cliente/sucursal. `user_id` en ems/contrato y `fk_ventanilla` en certi/ordi no prueban propiedad ni representan una política de acceso. Se requiere matriz real para habilitar clientes o sucursales. Las vistas exigen un GUC establecido por el backend; ese filtro evita errores de configuración, pero no reemplaza la identidad confiable. Un actor con acceso SQL al rol podría cambiarlo: el rol tiene alcance interno global deliberadamente.

Se excluyen nombres, teléfonos de personas, carnets, correos, direcciones, imágenes, mapas, contenido de paquetes, observaciones, usuarios, tokens, sesiones, logs y tablas de integración. El teléfono de oficina es institucional, sujeto a validación.

El rol de lectura no obtiene tablas base. Las vistas usan derechos del propietario y `security_barrier`; deben ser propiedad de una cuenta administradora restringida, sin conceder creación de objetos a la aplicación. Auditar privilegios heredados de PUBLIC y membresías; un REVOKE directo al rol no elimina esos privilegios. No ejecutar migraciones operativas automáticamente.

`peso` y `precio` no documentan unidades: se exponen como weight_value/amount_value y no deben mostrarse como unidades confirmadas. Los timestamps son `without time zone`; confirmar que representan America/La_Paz antes de interpretar periodos. `created_at` es fecha de registro, no fecha probada de envío/entrega.

## Herramientas

`scripts/inspect_backup.py` reproduce la extracción acotada a estructura. `scripts/restoration/restore_selected_data.py` es una herramienta opcional no ejecutada: solo permite destino local `correos_sandbox_*`, requiere tablas previamente preparadas y confirmación explícita de importar datos sensibles. Aunque la proyección excluye PII, restaurar tablas base sí importa PII; proteger ese sandbox. Nunca conecta con producción por configuración remota.
