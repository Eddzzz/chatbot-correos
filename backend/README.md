# API interna de Correos Bolivia

Python 3.12, FastAPI, Psycopg asíncrono, SQLGlot, llama.cpp vía HTTP. Un proceso API y una generación de modelo concurrente. No cargar pesos en Python.

Desde esta carpeta:

```powershell
uv sync --frozen
uv run pytest -q
uv run python -m app.run
```

El lanzador escucha solo `127.0.0.1:8000` y configura SelectorEventLoop en Windows (requerido por Psycopg). Un proxy local proporciona frontend/API del mismo origen. El API no habilita CORS abierto.

Configuración mediante variables `CHATBOT_` o archivo `.env` local ignorado por git:

```dotenv
CHATBOT_DEMO_MODE=false
CHATBOT_FIXTURE_DATA=false
CHATBOT_DATABASE_URL=postgresql://CUENTA_LECTURA:SECRETO@127.0.0.1:5432/BASE
CHATBOT_LLAMA_URL=http://127.0.0.1:8081/v1
CHATBOT_LLAMA_MODEL=local
CHATBOT_MODEL_VERSION=SHA256_DEL_MODELO_VERIFICADO
CHATBOT_IDENTITIES_JSON={"TOKEN_ALEATORIO_LARGO":{"user_id":"operador1","permissions":["internal_data","tracking","offices","summary"],"scope":["global_internal"]}}
```

El navegador usa cuentas de usuario y contraseña administradas con `scripts/manage_users.py`; ver [usuarios](../docs/users.md). Las sesiones usan cookies HttpOnly y los chats se vinculan al identificador estable de cada cuenta. Identidad y permisos proceden del servidor, nunca del cuerpo de chat.

Para scripts sigue disponible el mapa Bearer. Genera tokens con `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Tokens de ejemplo no son credenciales. Sin cuenta válida ni token configurado, las rutas de datos rechazan acceso. Agregar `diagnostics` permite `/api/health` y `/api/metrics`; `/health` solo verifica vida del proceso, no conectividad.

`CHATBOT_DEMO_MODE=true` habilita únicamente fixtures identificados como ficticios e interpretación por reglas; código disponible `DEMO123BO`. `CHATBOT_FIXTURE_DATA=true` identifica una base PostgreSQL de prueba con datos ficticios y permite usar el modelo real sin confundirla con el respaldo. Ambos están desactivados de forma predeterminada. Configurar DSN no restaura ni altera bases existentes. Aplicar la proyección SQL y un rol restringido mediante los scripts del directorio raíz, tras revisar sus instrucciones. No usar administrador, dueño de objetos ni cuenta con SELECT sobre tablas de `public`. Las vistas deben exigir `chatbot.access_scope=global_internal`; acceso interno global explícito, sin aislamiento ficticio por cliente/oficina.

Rutas autenticadas con la cookie de sesión o `Authorization: Bearer ...`:

* `POST /api/chat` y `POST /api/chat/stream`: `{ "message":"...", "session_id": null }`.
* SSE: `request_started`, `status`, `answer_chunk`, `completed`, `error`; todos con `request_id`. Primer evento incluye `session_id`; completed incluye respuesta y evidencia. Texto se fragmenta después de comprobar los resultados, nunca durante generación no verificada.
* `GET /api/sessions`, `GET /api/sessions/{id}` y alias `/history`: exclusivamente sesiones propias.
* `GET /api/postal-records`: registros mínimos por periodo/familia, autenticados con permisos de resumen; paginación de 1 a 20 filas y límites de bytes. Ver [continuaciones por familia](../docs/postal-followups.md).
* `POST /api/requests/{request_id}/cancel`: exclusivamente solicitud propia en curso. Cancela tarea, HTTP de inferencia y ejecución PostgreSQL asíncrona.
* `GET /api/config` público indica modo; no revela DSN, tokens ni esquema.

Catálogo cerrado: seguimiento exacto, oficinas por departamento, conteos por estado/familia/destino entre fechas (final exclusiva, hasta 366 días). SQL fijo parametrizado, comparación exacta con catálogo y validación AST; nunca SQL procedente del modelo. Transacción read-only, timeout SQL 3 s, máximo 100 filas/64 KiB, pool máximo 3 conexiones. Consultas sin autorización fallan antes de SQL y vuelven a comprobar autorización en el acceso a datos. Tarifas no habilitadas; el resumen de seguimiento no calcula pesos ni importes. `registered_at` significa fecha de registro. Los conteos representan registros de familias, no envíos únicos ni entregas.

Ampliación: los periodos naturales se resuelven en el servidor. La operación `accounting` consulta movimientos, cobros y registros de facturas con permisos `summary` y `personal_data`, mediante la vista protegida `v_accounting_records`. Los importes operativos, si existen, se conservan como texto decimal sin asumir moneda ni calcular balances. Ver [periodos y fuentes contables](../docs/natural-periods-accounting.md).

Interpretación local: una llamada JSON estructurada, temperatura 0, máximo 256 tokens, pensamiento desactivado; hasta 4 esperas, cola 15 s, llamada 60 s. Errores de inferencia fallan sin inventar resultados. Respuestas deterministas sobre filas autorizadas preservan fechas/códigos. El servidor llama.cpp se instala y arranca por separado. No se afirma disponibilidad por tener URL configurada.

Conversaciones persistentes en SQLite privado: preguntas, respuestas, resultados, fuentes y contexto confirmado. Cada chat tiene UUID y URL `/c/{id}`. La caché conserva TTL de 30 min; el historial sobrevive a recargas y reinicios y no se recorta a 40 mensajes. Se comprueban propietario, alcance y permisos vigentes al abrirlo. El límite de 100 chats por operador (configurable) rechaza creaciones nuevas sin borrar chats existentes. Ruta configurable con `CHATBOT_HISTORY_PATH`. Ver [conversaciones guardadas](../docs/saved-chats.md).

Logs JSON: request_id, identificador interno confiable del operador, operación, versión del modelo, estado y duración; sin prompts ni filas. No hay agente analítico multi-paso ni SQL libre.

Pruebas ejecutables: contratos JSON/SSE, autorización, aislamiento de sesiones, propiedad y permisos del historial persistente, fechas y procedencia de filtros, límites de cola, cancelación, catálogo SQL y arquitectura. Si existe `.runtime/fixture-dsn.txt` en la raíz, se prueba además contra PostgreSQL aislado con filas ficticias y rol restringido; de otro modo esa prueba se omite explícitamente. Si existe también la credencial del administrador del fixture, se bloquea temporalmente una tabla exclusivamente en `127.0.0.1:55432/correos_sandbox_fixture`, se cancela una consulta real bloqueada y se verifica reutilización del pool. Esto no sustituye validar sobre la base real antes de producción.
