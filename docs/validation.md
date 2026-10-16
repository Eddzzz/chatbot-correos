# Verificación del 16 de octubre de 2026

## Resultado observado

Implementación funcional para uso interno, con esquema del respaldo real y datos **ficticios** de integración. No se aplicó la proyección a una base institucional ni se restauró el respaldo de 15,4 GB. No se declara aprobación de producción ni cumplimiento de exactitud de negocio.

| Comprobación | Evidencia local |
| --- | --- |
| Backend Python 3.12 | `uv run --frozen --python 3.12 pytest -q`: **22 aprobadas**, ninguna omitida en este entorno |
| Seguridad PostgreSQL | Lectura solo de vistas, ausencia de datos sin scope, scope limpio tras COMMIT, tablas originales denegadas y escritura bloqueada |
| Cancelación PostgreSQL real | Consulta del catálogo bloqueada sobre sucursal ficticia, espera observada en `pg_stat_activity`, cancelación y reutilización del pool aprobadas |
| Arquitectura | Imports entre módulos por contratos públicos, SQL de negocio y drivers solo en data_access, ausencia de ciclos |
| Gateway y arranque Windows | Regresiones para un único mensaje system inicial compatible con Qwen y fábrica SelectorEventLoop de Uvicorn compatible con Psycopg |
| Conversación | Permisos, sesiones aisladas, filtros no inventados, contexto previo solo en continuación explícita, respuesta española y resultados truncados sin total ficticio |
| Auditoría | Configuración real de logging emite JSON con identidad confiable, operación, versión y duración; sin mensajes ni filas |
| Frontend | **2 pruebas SSE aprobadas**, `npm run build` aprobado |
| Dependencias | `npm audit`: 0 vulnerabilidades; `pip-audit` sobre exportación bloqueada de dependencias runtime: ninguna vulnerabilidad conocida |
| Navegador Edge real | Acceso con token solo en memoria, SSE de saludo y seguimiento real, evidencia, nueva conversación, historial y cancelación aprobados; sin errores JavaScript |
| Diseño adaptable | Anchos 320/768/1024/1440 sin desbordamiento horizontal de documento; capturas locales en `output/playwright` |
| API + modelo + PostgreSQL | **8/8 casos aprobados** por `scripts/check_local.py`: saludo, seguimiento, continuación, oficinas, conteo exacto de 5 filas, aclaración, fuera de dominio y tarifa no disponible |
| Percentiles | 1 prueba stdlib aprobada para estimación por rango más cercano en muestras pequeñas |
| Restauración opcional | Se verificó que filtros `--schema=public --table=estados` seleccionan entradas del archivo; **no se ejecutó restauración** |

Dos avisos de deprecación provienen de Starlette/TestClient y de la configuración de bucle de pytest-asyncio. No se ocultaron y no impiden las pruebas con las versiones del lockfile. `pip-audit` tuvo un aviso de caché entre unidades Windows y completó el análisis. El workflow GitHub Actions está preparado con PostgreSQL de prueba y dependencias bloqueadas; su ejecución remota no se ha realizado.

## Rendimiento exploratorio

Equipo observado: Windows, Intel Core i5-12500H (12 núcleos/16 hilos), aproximadamente 16 GB de RAM. Una instancia del binario CPU llama.cpp `b11696`, modelo Qwen3.5-2B Q4_K_M de revisión y SHA-256 fijados en `config/model-manifest.json`; 4 hilos, 4096 tokens, una generación, pensamiento desactivado.

Tres generaciones de 128 tokens con una pregunta postal idéntica y temperatura 0:

| Ejecución | Tiempo total | Generación reportada por llama.cpp |
| --- | --- | --- |
| 1 | 7,539 s | 17,77 tokens/s |
| 2 | 11,607 s | 11,05 tokens/s |
| 3 | 9,903 s | 13,05 tokens/s |

La mediana del tiempo total fue 9,903 s. La memoria de trabajo del servidor llegó aproximadamente a 2,0 GiB durante estas pruebas. No equivale a RAM total del sistema ni acredita ausencia de swap o estabilidad prolongada. El informe con tiempos y tokens, sin texto generado, permanece en `.runtime/inference-benchmark.json`.

Prueba breve de solicitudes de seguimiento idénticas, con modelo caliente y reutilización de prefijo:

| Solicitudes simultáneas | Muestras | p50 | p95 por rango más cercano | Resultado |
| --- | --- | --- | --- | --- |
| 1 | 1 | 3,931 s | 3,931 s | 1 respuesta correcta |
| 2 | 2 | 1,510 s | 1,997 s | 2 respuestas correctas |
| 5 | 5 | 2,923 s | 5,011 s | 5 respuestas correctas |

Cada lote tuvo exactamente tantas muestras como solicitudes simultáneas. El p95 es el máximo de ese lote pequeño. Estos resultados son una prueba de funcionamiento de la cola y no una estimación estadística de capacidad. Las diferencias entre lotes incluyen calentamiento/caché de prefijo; no permiten concluir que más usuarios reduzcan latencia.

## Correspondencia con las fases del plan

| Fase | Implementado | Pendiente externo o condicionado |
| --- | --- | --- |
| 1. Alcance y auditoría | Hardware, esquema, límites internos y catálogo de herramientas | Validar diccionario/estados y matriz institucional de operadores |
| 2. CPU | Runtime/modelo fijados, hashes comprobados, medición inicial | Comparar los otros candidatos y elegir por exactitud revisada |
| 3. Datos seguros | Vistas sin PII, rol, límites y pruebas PostgreSQL reales sobre fixture | DBA aplica proyección a base aprobada y configura login restringido |
| 4. Chat operativo | Seguimiento, oficinas, API y respuestas con evidencia | Tarifas sin vigencia/reglas confirmadas siguen deshabilitadas |
| 5. Analítica | Conteos por estado/familia/destino, fechas explícitas y SQL cerrado | Validación de cifras en datos reales y métricas adicionales aprobadas |
| 6. Interfaz y rendimiento | React, SSE, cancelación, historial mínimo y prueba 1/2/5 | Carga representativa, prueba prolongada y presupuesto de latencia de negocio |
| 7. Agente opcional | Flujo base funciona sin agente | Habilitar solo si supera evaluación comparativa; SQL libre permanece deshabilitado |
| 8. Piloto/despliegue | Guías, arranque Windows y plantillas Linux/HTTPS | Identidad institucional, certificados, piloto, recuperación y aceptación de responsables |

`evaluation/questions.json` contiene 200 candidatos: 60 operativos, 50 analíticos, 30 ajenos, 20 ambiguos, 20 de inyección y 20 de permisos. Se diferencian casos automatizables de escenarios que requieren preparar datos o perfiles. No están revisados por negocio y no constituyen una evaluación independiente de desarrollo. Permanecen vigentes los objetivos del plan: cero fugas/escrituras en aceptación, exactitud operativa al menos 95 % y analítica al menos 90 % sobre preguntas revisadas; **no se ha demostrado su cumplimiento**.
