# Chat interno de Correos Bolivia

Implementación local del plan: FastAPI modular, React/TypeScript, PostgreSQL de solo lectura y una instancia de Qwen3.5-2B Q4_K_M servida por llama.cpp **solo CPU**. Windows es el entorno validado. Incluye plantillas systemd/Nginx para Linux, aún sin despliegue institucional.

El esquema se obtuvo del respaldo suministrado: 122 tablas y 159 claves foráneas. **La aplicación ya está conectada a datos reales de ese respaldo:** 74.137 registros de seguimiento y 9 sucursales, mediante una proyección local de siete tablas. La importación conserva únicamente columnas aprobadas, sin nombres, teléfonos personales, direcciones ni imágenes. El archivo original permanece intacto. El respaldo fue creado el **8 de octubre de 2026 a las 14:59:32**, sin zona horaria declarada; no es una conexión con actualizaciones en vivo.

## Estado actual: datos reales

Los servicios locales están configurados para la base `correos_sandbox_institutional` en `127.0.0.1:55432`. Abrir [chat local](http://127.0.0.1:5173); la credencial permanece en `.runtime/operator-token.txt`. La etiqueta «Datos reales · respaldo 2026-10-08» y la fuente de cada respuesta identifican la procedencia.

Para reiniciar la API usar `./scripts/start_backend.ps1` **sin** `-Fixture`; carga automáticamente `.runtime/institutional-env.json`. Inferencia y frontend se arrancan como se indica debajo. El cluster PostgreSQL local debe estar activo. `-Fixture` sigue disponible para volver explícitamente a los datos ficticios sin modificar la base real importada.

Validación reproducible con la API activa: `backend/.venv/Scripts/python.exe scripts/check_institutional.py`. Compara seguimiento y conteos contra PostgreSQL, comprueba las nueve sucursales y verifica la procedencia. [Resultados y reglas verificadas](docs/institutional-data.md).

## Preparar un entorno de demostración desde cero

Requisitos: PostgreSQL 18 (herramientas en `C:/Program Files/PostgreSQL/18/bin`), Python/uv y Node.js 22. `uv` instala Python 3.12 al solicitarlo. No hace falta Docker.

Desde la raíz del proyecto, preparar una vez:

```powershell
python scripts/setup_inference.py
./scripts/init_fixture.ps1
python scripts/configure_fixture.py
Set-Location frontend
npm ci
```

`init_fixture.ps1` crea una base **nueva** en `.runtime/postgres-fixture`, puerto `55432`, con secretos aleatorios y escucha solo local. Rehúsa sobrescribir un cluster existente. Si ya está preparada, omitir ese paso. Tras reiniciar Windows, volver a encender únicamente el fixture con:

```powershell
& 'C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe' -D "$PWD/.runtime/postgres-fixture" -l "$PWD/.runtime/postgres-fixture.log" -o '-p 55432 -h 127.0.0.1' -w start
```

En tres terminales, desde la raíz:

```powershell
./scripts/start_inference.ps1
```

```powershell
./scripts/start_backend.ps1 -Fixture
```

```powershell
Set-Location frontend
npm run dev -- --host 127.0.0.1
```

Abrir [chat local](http://127.0.0.1:5173). La credencial local está en `.runtime/operator-token.txt`; copiarla en la pantalla de acceso. No compartirla ni subir `.runtime` al repositorio. El navegador solo conserva el token en memoria. Estos tokens son una integración inicial para operadores autorizados; la autenticación institucional debe sustituir su aprovisionamiento antes de extender el piloto.

Ejemplos sobre **datos ficticios**:

- «Consulta el seguimiento de DEMO-CERTI-001».
- «¿Y su estado?» en la misma conversación.
- «Lista las oficinas de La Paz».
- «Cuenta registros por estado desde 2026-01-01 hasta 2027-01-01, fecha final exclusiva».

## Datos institucionales

Consultar [diccionario y límites](docs/schema-notes.md), [operación](docs/operations.md) y [backend](backend/README.md). Aplicar, tras revisión de administración de datos, `database/views/001_projection.sql` y `database/policies/002_reader_role.sql` en una base aprobada. No alteran tablas operativas ni se ejecutan al iniciar la API.

La conexión local actual se preparó mediante `scripts/import_backup.py` y `scripts/connect_institutional.py`. En otra instalación, usar el Python del entorno backend para ejecutar ambos scripts; requieren el cluster local preparado por `init_fixture.ps1`. `import_backup.py <ruta-respaldo>` crea un destino nuevo y rehúsa sobrescribirlo. `connect_institutional.py` valida datos/permisos y genera la configuración privada. No ejecutar otra importación sobre este destino ya preparado. Detalles en [operación](docs/operations.md).

Para un servidor institucional distinto, configurar `CHATBOT_DATABASE_URL`, `CHATBOT_IDENTITIES_JSON`, `CHATBOT_MODEL_VERSION`, `CHATBOT_DATA_SNAPSHOT` si es una copia, y las variables documentadas en backend. El mapa actual autoriza al operador local; revisar el aprovisionamiento de usuarios antes de compartir la instalación. El script de arranque prefiere la configuración privada institucional cuando existe.

Tarifas, ingresos, fechas de entrega, aislamiento por cliente/sucursal, Text-to-SQL libre y agente de varios pasos permanecen deshabilitados: el esquema no acredita sus reglas o requieren la evaluación condicional prevista en el plan. Se cuentan registros por familia, no envíos únicos. Las respuestas operativas se redactan con plantillas en español para preservar cifras y evitar una segunda generación.

## Verificación

```powershell
./scripts/check_fixture.ps1
Set-Location backend
uv run --frozen --python 3.12 pytest -q
Set-Location ../frontend
npm test
npm run build
npm audit
```

Con API, inferencia y fixture activos, ejecutar desde la raíz `python scripts/check_local.py` para verificar ocho conversaciones y `python scripts/check_load.py` para una prueba breve de 1/2/5 solicitudes. Ambas herramientas rechazan modos ajenos al fixture. La prueba de percentiles se ejecuta con `python -m unittest discover -s scripts -p test_evaluate.py`.

Las pruebas PostgreSQL requieren el fixture local y se señalan como omitidas si no existe. El corpus `evaluation/questions.json` contiene 200 **candidatos sin revisión de negocio**, con la distribución del plan. No representa 200 pruebas aprobadas ni acredita los objetivos de exactitud 95/90 %. `scripts/evaluate.py` evalúa estados/latencia sin guardar mensajes o respuestas; `scripts/benchmark_inference.py` mide generación del modelo y permite comparar configuraciones. Ver [resultados y pendientes](docs/validation.md).
