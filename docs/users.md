# Usuarios y acceso al chat

Cada usuario tiene una contraseña y un identificador estable de propietario. Sus conversaciones se guardan en el servidor y aparecen al iniciar sesión desde el navegador. El nombre visible y el nombre de acceso no determinan la propiedad: la determina el `user_id` asignado al crear la cuenta.

Las cuentas son administradas localmente. La aplicación no incluye credenciales predeterminadas. El alta interactiva solicita la contraseña y guarda únicamente su hash en la base privada; no crea un archivo con la contraseña en texto plano.

Desde la raíz del proyecto, con las dependencias del backend instaladas:

```powershell
backend/.venv/Scripts/python.exe scripts/manage_users.py create maria --display-name "María"
backend/.venv/Scripts/python.exe scripts/manage_users.py list
backend/.venv/Scripts/python.exe scripts/manage_users.py reset-password maria
```

La herramienta solicita y confirma la contraseña sin mostrarla. Debe tener al menos 12 caracteres. Los permisos predeterminados son `internal_data`, `tracking`, `offices` y `summary`, con alcance `global_internal`. El administrador puede declararlos mediante `--permissions` y `--scope`; el navegador no puede otorgarse permisos. No hay registro público de cuentas.

Para seleccionar otra base de autenticación, colocar `--auth-path RUTA` antes del subcomando. Usar la misma ruta que `CHATBOT_AUTH_PATH` en el servidor. El valor predeterminado es `.runtime/auth.sqlite3`; el servidor en modo ficticio usa `.runtime/auth-fixture.sqlite3`. Para administrar las cuentas del arranque con `-Fixture`, añadir siempre `--auth-path .runtime/auth-fixture.sqlite3` a los ejemplos anteriores. Si se configura `CHATBOT_HISTORY_PATH`, el valor predeterminado de autenticación queda junto a ese archivo, con el sufijo `-auth.sqlite3`.

Para automatización local, `create` y `reset-password` admiten `--password-file RUTA`; ese archivo contiene una contraseña y debe permanecer privado y fuera del repositorio.

Para conservar el historial de un operador que antes usaba Bearer, asignar el mismo identificador, verificando antes la configuración del servidor:

```powershell
$accountName = Read-Host 'Nombre de usuario'
backend/.venv/Scripts/python.exe scripts/manage_users.py create $accountName --user-id operador-local
```

Las nuevas cuentas reciben identificadores independientes si se omite `--user-id`. No reutilizar el identificador de otra persona. La creación de cuentas no altera las bases postales ni copia conversaciones.

Las contraseñas se almacenan con scrypt y sal aleatoria. Las sesiones usan tokens aleatorios; SQLite guarda solamente su hash y vencimiento. La cookie `chatbot_session` es HttpOnly, SameSite=Strict y se limita a `/api`. La sesión dura 12 horas de forma predeterminada. Cerrar sesión revoca el token en el servidor; cambiar la contraseña revoca todas las sesiones de esa cuenta. Los tokens Bearer configurados siguen disponibles para las herramientas existentes.

Configuración de autenticación:

| Variable | Uso |
| --- | --- |
| `CHATBOT_AUTH_PATH` | Ruta privada del SQLite de usuarios y sesiones. |
| `CHATBOT_AUTH_SESSION_TTL` | Duración de la sesión en segundos; predeterminado 43200. |
| `CHATBOT_AUTH_COOKIE_SECURE` | Activar en HTTPS; el desarrollo local usa HTTP en loopback. |
| `CHATBOT_AUTH_ALLOWED_ORIGINS` | Lista JSON de orígenes autorizados cuando el proxy presenta un origen distinto al de la API. |
| `CHATBOT_AUTH_LOGIN_MAX_ATTEMPTS` | Máximo de intentos por usuario y dirección durante la ventana; predeterminado 10. |
| `CHATBOT_AUTH_LOGIN_WINDOW` | Ventana en segundos; predeterminado 300. |

Las operaciones que usan cookie verifican el origen. El proxy debe conservar el origen público o declararlo explícitamente; por ejemplo `CHATBOT_AUTH_ALLOWED_ORIGINS=["https://chat.ejemplo.bo"]`. No se habilita CORS abierto. El límite de intentos se conserva al reiniciar el servidor.

API del navegador: `POST /api/auth/login` recibe `{ "username": "maria", "password": "..." }`; `GET /api/auth/me` restaura la sesión; ambos devuelven `{ "user": { "user_id": "...", "username": "maria", "display_name": "María" } }`. `POST /api/auth/logout` revoca la sesión. Todas las respuestas de autenticación impiden almacenamiento en caché. El historial y las operaciones de lectura, edición, borrado y cancelación comprueban el propietario en el servidor.
