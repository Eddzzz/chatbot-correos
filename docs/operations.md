# Operación y conexión institucional

**Estado actual:** datos reales del respaldo ya importados y conectados. Consultar [datos institucionales locales](institutional-data.md) para procedencia, conteos, validaciones y arranque. Las instrucciones originales de fixture siguen aplicando a la base ficticia independiente.

## Separación de entornos

El respaldo original y los PostgreSQL preexistentes no se modificaron. La base ficticia usa exclusivamente `127.0.0.1:55432/correos_sandbox_fixture`. Las credenciales generadas están en `.runtime`, fuera de Git. Los scripts de prueba nunca toman un DSN institucional para administrar bases o bloquear tablas.

`scripts/inspect_backup.py` reconoce formato custom y usa pg_restore 18 solo para generar estructura, sin ejecutarla. `docs/source-schema.sql` contiene CREATE TABLE/FK y sirve de referencia, **no es una migración completa**. Las definiciones omiten secuencias, PK, funciones y permisos. `scripts/restoration/restore_selected_data.py` es una herramienta opcional de administración que no se ejecutó; importa PII de tablas base y exige destino local nuevo/preparado y confirmación explícita. Revisar su ayuda y las definiciones antes de usarla. No restaurar el respaldo completo sobre una base existente.

## Cuenta de lectura y vistas

1. Administración prepara una base restaurada o de solo lectura en una red privada y valida semántica/volumen.
2. Revisa y aplica vistas y rol de `database/`. No usar el rol de la aplicación como propietario de vistas/tablas.
3. Crea un login exclusivo sin membresías amplias y le concede `chatbot_reader`. Configura su secreto mediante herramienta administrativa/secret store, sin pegarlo en chats ni en comandos que queden en historial.
4. Audita privilegios heredados de PUBLIC: REVOKE directo no elimina herencia por PUBLIC o membresías. La aplicación rechaza roles privilegiados y accesos directos a relaciones de `public`, pero la revisión administrativa sigue siendo necesaria.
5. Configura API con `CHATBOT_DATABASE_URL`, mapa de identidades autorizado y `CHATBOT_FIXTURE_DATA=false`. Mantener solo permisos necesarios: `internal_data` más `tracking`, `offices` o `summary`; `diagnostics` queda restringido a operación.
6. Contrasta conteos/fechas contra consultas revisadas antes de habilitar operadores reales. Confirmar zona horaria de timestamps sin zona, valores de estado y duplicación entre familias. Añadir índices de código/fecha si el EXPLAIN y la carga lo requieren; no ejecutar índices automáticamente sobre tablas ajenas.

El catálogo inicial ofrece seguimiento por código exacto, oficinas por departamento y conteos por estado/familia/destino para rango `[inicio,fin)`, máximo 366 días. Tarifas y métricas monetarias no se habilitan por falta de vigencia/unidades confirmadas.

## Despliegue

Windows local: usar los scripts de README. No se necesita Docker. Linux institucional: las unidades en `deploy/` son plantillas y requieren usuario dedicado `correos-chat`, Python 3.12/venv, build del frontend y compilación CPU de llama.cpp `b11696`. Seguir la [compilación oficial](https://github.com/ggml-org/llama.cpp/blob/b11696/docs/build.md), fijar opciones CPU y verificar logs antes de usar el GGUF del manifiesto.

`deploy/nginx.conf` sirve frontend y proxy SSE por HTTPS; reemplazar hostname/certificados internos y comprobar `nginx -t`. API e inferencia escuchan solo loopback. No exponer 8000/8081/55432 a la red. Para PostgreSQL remoto utilizar red privada y TLS validado. Restringir acceso al chat desde la red institucional. Los archivos de entorno y certificados deben tener permisos exclusivos del usuario de servicio/administración.

Liveness `/health` no acredita dependencias. `/api/health` y `/api/metrics` requieren `diagnostics` y distinguen configuración de verificación. Probar una consulta autorizada controlada para readiness operacional, sin publicar resultados. Si no hay modelo, DB o autorización, el sistema falla con estado explícito y no devuelve un resultado inventado.

## Mantenimiento, recuperación y reversión

- Mantener un worker API y una instancia de inferencia. La cola y las solicitudes en curso viven en memoria. El historial SQLite sobrevive al reinicio; ver [conversaciones guardadas](saved-chats.md).
- Medir RAM y p50/p95 con carga 1/2/5, además de tokens/s. El límite de systemd es un presupuesto inicial, no consumo medido ni garantía de ausencia de swap.
- Conservar copias de manifiestos, configuración y políticas con secretos protegidos. Respaldar también el historial SQLite privado con la API detenida. Definir retención y controles de acceso de los logs en la infraestructura institucional.
- Para revertir, detener API, restaurar el checkout/versiones anteriores y su lockfile, reconstruir frontend y reiniciar. Las vistas deben mantener compatibilidad o restaurar su definición previa mediante DBA. No borrar tablas del sistema postal.
- Para detener la prueba, cerrar frontend/API/modelo y ejecutar `pg_ctl -D <raíz>/.runtime/postgres-fixture -m fast stop`. No borrar recursivamente el directorio de un cluster activo.
- Volver a evaluar tras cambios de modelo, prompt, esquema, permisos o catálogo. Probar caída/reinicio y recuperación antes de declarar el piloto apto para producción.

## Fuentes utilizadas

[pg_restore](https://www.postgresql.org/docs/current/app-pgrestore.html), [Psycopg asíncrono](https://www.psycopg.org/psycopg3/docs/advanced/async.html), [servidor llama.cpp](https://github.com/ggml-org/llama.cpp/blob/b11696/tools/server/README.md). Se consultaron fuentes oficiales para formato de respaldo, cancelación asíncrona y flags del servidor; las decisiones locales y resultados se documentan por separado.
