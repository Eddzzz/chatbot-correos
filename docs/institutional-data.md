# Datos reales conectados

Actualización del 16 de octubre de 2026, solicitada expresamente para utilizar los datos del respaldo. La API activa carga `.runtime/institutional-env.json`; el frontend distingue esta conexión de la demostración. El token del operador local se mantiene en `.runtime/operator-token.txt`, sin incluirlo en el repositorio ni en el navegador de forma persistente.

**Ampliación autorizada posterior:** las fichas completas cuentan ahora con una proyección privada adicional con datos personales y registros asociados. Las cifras y exclusiones descritas debajo corresponden a la proyección resumida inicial. Consultar [fichas completas y permisos](full-details.md) para el alcance actual; el resumen permanece sin columnas personales.

## Procedencia y alcance

Origen: respaldo PostgreSQL custom `backapsiop.sql`, 15.396.364.706 bytes. Su cabecera declara creación el **8 de octubre de 2026 a las 14:59:32**, sin zona horaria. Es una copia local estática, no una conexión de actualización continua. El archivo original y los PostgreSQL preexistentes se conservaron.

`scripts/import_backup.py` transmitió los datos COPY de siete tablas mediante `pg_restore 18`, sin ejecutar SQL, funciones, triggers, ACL o propietarios del archivo. Cada fila se proyectó antes de escribirla: se retienen identificadores internos, códigos, estado, origen/destino, fecha de registro/actualización y valores sin unidades confirmadas. Se omiten las columnas explícitas de nombres, carnets, teléfonos personales, direcciones, observaciones, contenido e imágenes. El teléfono de sucursal corresponde al directorio institucional. Usuarios y credenciales del respaldo no se importan.

Destino: `correos_sandbox_institutional` en el cluster propiedad del proyecto, `127.0.0.1:55432`. El nombre del directorio del cluster sigue siendo `.runtime/postgres-fixture`; **las bases real y ficticia son distintas**, con logins y permisos separados. Se usa el mismo servidor local para evitar un tercer proceso PostgreSQL. La aplicación solo recibe el login de lectura de las vistas `chatbot.v_tracking` y `chatbot.v_offices`.

| Familia o catálogo | Filas importadas |
| --- | ---: |
| Certificados | 5.231 |
| Contratos | 58.752 |
| EMS | 6.679 |
| Internacionales | 2.396 |
| Ordinarios | 1.079 |
| **Total de registros de seguimiento** | **74.137** |
| Estados | 26 |
| Sucursales | 9 |

Hay índices únicos por `id` de cada tabla e índices de código y fecha en las cinco familias, más estadísticas ANALYZE. No se añaden ni alteran índices en las bases originales.

## Reglas comprobadas y límites

- Los conteos de importación, tablas proyectadas y vistas coinciden por familia; sucursales devuelve nueve filas.
- Todos los registros de seguimiento resuelven su estado en el catálogo de estados importado. No se deduce que un nombre de estado equivalga a una entrega o retraso.
- Existe **un registro sin fecha de registro**. El resumen de `[2026-01-01, 2027-01-01)` devuelve **74.136**, mientras que el total sin filtro temporal es **74.137**. No se inventó una fecha ni se excluyó del seguimiento por código.
- Hay **197 repeticiones adicionales de códigos** respecto a los códigos distintos. Se permite que un código devuelva más de un registro y familia; no se presenta el conteo de filas como envíos únicos.
- Las sucursales almacenan departamentos en mayúsculas sin tildes. La consulta parametrizada normaliza mayúsculas y vocales acentuadas, por lo que «La Paz» y «LA PAZ» consultan el mismo departamento; no utiliza coincidencia parcial ni comodines del usuario.
- `created_at` significa registro y `updated_at` actualización. Sus timestamps no incluyen zona. La fecha del respaldo se muestra tal como figura en su cabecera; la fecha de consulta sí se muestra en America/La_Paz.
- Las tarifas, vigencias, unidades de peso/importes, ingresos y causas de cambios continúan sin confirmación de negocio. No se habilitan ni se inventan. Los valores de peso/precio no se muestran en las herramientas actuales.

Esta validación acredita coherencia estructural, referencias, filtros y resultados contra la copia importada. No sustituye la confirmación institucional del significado de los estados, unidades, tarifas o permisos de cada empleado.

## Verificación ejecutada

`scripts/connect_institutional.py` verificó la lista exacta de columnas retenidas, igualdad de conteos con la importación, ausencia de privilegios elevados, cero filas sin alcance transaccional, limpieza tras COMMIT, denegación de tablas originales y bloqueo de escrituras. Configuró timeout de bloqueos e inactividad en el login, ya que los parámetros de roles de grupo no se heredan al iniciar sesión.

`scripts/check_institutional.py` pasó **7/7 casos** usando el modelo CPU real y la API activa: seguimiento de un código existente, continuación, oficinas de La Paz, todas las oficinas, resumen de estados contra consulta independiente de PostgreSQL, periodo ambiguo y tarifas no habilitadas. Informes privados `.runtime/institutional-import.json`, `institutional-validation.json` e `institutional-api-validation.json` guardan conteos/resultados de comprobaciones sin respuestas operativas ni datos personales. El código de referencia permanece en un archivo privado independiente y no se imprime en las pruebas.

Además: **24 pruebas backend aprobadas**, **4 pruebas de scripts aprobadas**, **2 pruebas SSE aprobadas** y build del frontend aprobado. El navegador real verifica la etiqueta del respaldo, seguimiento SSE con evidencia, ausencia de almacenamiento persistente del token y diseño móvil. Persisten los dos avisos de deprecación de dependencias documentados en la validación inicial.

## Arranque, recuperación y reversión

Desde la raíz del proyecto:

```powershell
./scripts/start_inference.ps1
./scripts/start_backend.ps1
```

En otra terminal: `Set-Location frontend` y `npm run dev`. La API prefiere automáticamente la configuración real si existe. `./scripts/start_backend.ps1 -Fixture` elige explícitamente la base ficticia y limpia la etiqueta de fecha; no borra ni modifica datos reales. Si el cluster está detenido, arrancarlo como documenta README; no crear otro sobre su directorio.

Para reproducir la importación en otra instalación: preparar el cluster local, ejecutar `backend/.venv/Scripts/python.exe scripts/import_backup.py <archivo>` y luego `backend/.venv/Scripts/python.exe scripts/connect_institutional.py`. El importador crea un destino nuevo y se niega a sobrescribir uno existente. Las nuevas importaciones conservan datos, índices, vistas y rol en una transacción. Si falla, queda un destino local vacío que debe revisar la administración antes de reintentar; no se elimina automáticamente. Una actualización del respaldo requiere preparar otro destino revisado o retirar expresamente el anterior, nunca sobrescribir por defecto.

Cambiar los datos no requiere descargar de nuevo el modelo. Para revertir la conexión, parar la API real y reiniciarla con `-Fixture`; las dos bases y el respaldo quedan conservados. El login real solo tiene acceso interno global explícito; no se debe reutilizar para clientes públicos ni para fingir aislamiento por sucursal.
