# Periodos naturales y registros de cobros/facturación

El chat interpreta «todo octubre», «octubre de 2025», «este mes», «el mes pasado», «hoy», «ayer» y «del 1 al 31 de octubre de 2026». Resuelve los límites del calendario mediante código, independientemente de las fechas propuestas por el modelo. El día final expresado en lenguaje natural se incluye; internamente se consulta un intervalo con extremo final exclusivo. Los intervalos ISO existentes conservan su contrato de fecha final exclusiva.

Si falta el año se utiliza el actual según UTC−4 (La Paz) y siempre se muestra el periodo interpretado. Una continuación que solo cambia el mes conserva el año del periodo confirmado. Un año explícito, «este año» o «año pasado» prevalece sobre ese contexto. Los meses múltiples o días ambiguos generan una pregunta de precisión, sin declararse interrupciones. Se siguen rechazando fechas generadas por el modelo sin respaldo en el texto, calendario o contexto confirmado.

«Dame el registro contable del mes de octubre» consulta tres categorías separadas: movimientos, cobros y registros de facturación. «De todo el mes de octubre» conserva esa consulta. «Solo cobros» conserva el periodo y limita la categoría. Las conversaciones guardadas conservan la intención y sus filtros; las continuaciones de chats antiguos que fallaron pueden recuperar el tema contable de la última pregunta explícita guardada.

## Fuentes y significado

| Categoría | Fuente privada | Fecha usada |
| --- | --- | --- |
| Movimientos de cuentas por cobrar | `chatbot_relations_source.cashier_flow_receivable_movements` | `cobrado_at` |
| Cobros de cuentas por cobrar | `chatbot_relations_source.cashier_flow_receivable_collections` | `cobrado_at` |
| Registros de facturación | `chatbot_accounting_source.facturas` | `created_at` |

Estos son registros operativos de esas fuentes, no un libro mayor validado. No se calcula balance, ingresos, impuestos ni total monetario de la unión. Movimientos y cobros pueden describir el mismo pago. Los importes conservados se muestran como texto decimal exacto, sin inferir moneda. La tabla `facturas` solo contiene identificador y fechas; no acredita emisión fiscal ni contiene detalle de importes. Los indicadores activos/devueltos se conservan como datos registrados, sin deducir saldos.

**Resultado verificado en este respaldo del 8 de octubre de 2026:** las tres tablas tienen cero filas, también fuera de octubre. La API informa cero por categoría y ausencia de registros en estas fuentes. Esto no prueba ausencia de actividad contable en otros sistemas o tablas. Si el periodo solicitado supera la fecha del respaldo, la respuesta señala que no puede confirmar los días posteriores.

## Implementación

La vista `chatbot.v_accounting_records` exige alcance global interno y acceso a datos personales. El operador requiere `internal_data`, `summary` y `personal_data`; no se concede ningún permiso adicional automáticamente. El lector PostgreSQL sigue sin escritura ni acceso a tablas originales. Dos consultas parametrizadas del catálogo obtienen conteos por categoría y registros limitados. Los conteos tienen un máximo independiente de tres categorías, para que el límite de filas de detalle no los oculte. La respuesta indica si la lista es parcial.

La migración local ya está aplicada. En otra copia institucional previamente preparada:

```powershell
& .\backend\.venv\Scripts\python.exe scripts/upgrade_accounting.py 'D:\edwin\Downloads\backapsiop\backapsiop.sql'
```

Rehúsa sobrescribir el esquema privado y comprueba los conteos COPY/importación antes de confirmar. No altera el respaldo. El informe local está en `.runtime/accounting-import.json`, fuera de Git.

Pruebas: `backend/tests/test_natural_periods.py` cubre calendario, cambios de año, febrero bisiesto, continuaciones, permisos y separación respecto al conteo postal. `scripts/test_accounting.py` inserta datos sintéticos en una transacción con rollback, verifica categorías, fechas de octubre frente al 1 de noviembre, precisión decimal y permisos de las vistas. Se omite sin la credencial del entorno local.
