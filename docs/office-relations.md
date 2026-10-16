# Datos asociados a una sucursal

En la misma conversación, consultar «Dame los datos de la sucursal de Santa Cruz» y después «todos los datos». Además de la ficha, aparece información de las 65 categorías de negocio conectadas por claves foráneas declaradas en el respaldo. La interfaz usa nombres en español y frases con los conteos y el significado de la asociación, sin mostrar rutas técnicas. Incluye categorías vacías y registros consultables mediante el botón de cada categoría, «Siguiente» y «Anterior». La interfaz muestra diez registros por página. La búsqueda acepta palabras sin tildes.

La ampliación recorre todas las claves entrantes desde `sucursales`, pasando por los usuarios asignados y sus registros relacionados. Une todos los caminos y elimina duplicados. Después incorpora las referencias salientes necesarias, sin expandir nuevamente sus registros dependientes: una referencia a un usuario de otra sucursal no incorpora todas las operaciones de esa otra sucursal.

Los conteos separan registros alcanzados mediante usuarios asignados y referencias. En Santa Cruz, `users` contiene 42 registros vinculados: dos usuarios asignados y cuarenta referencias. Esto no significa que haya 42 empleados asignados. Los conteos entre tablas tampoco representan envíos únicos ni prueban dónde se realizó una operación.

En el respaldo local del 8 de octubre de 2026, Santa Cruz tiene 21 tablas con filas vinculadas, de las 65 del catálogo. Las 122 tablas del respaldo no están todas relacionadas con una sucursal. No se inventan relaciones sin claves declaradas ni direcciones u horarios ausentes del origen.

Se incluyen los campos personales autorizados. Se excluyen contraseñas, tokens, identificadores de sesión/dispositivo, archivos binarios y cinco tablas de seguridad: `activity_logs`, `external_api_tokens`, `mobile_db_snapshots`, `user_ips_links`, `user_login_logs`. Los campos excluidos o convertidos en indicadores de presencia están definidos en `config/office_relations_catalog.json`. El respaldo original permanece intacto.

## Implementación y permisos

La copia privada conserva nodos, vínculos, pertenencias y conteos. El lector accede únicamente a dos vistas protegidas, con alcance `global_internal` y permiso de datos personales. La API autentica al operador y aplica consultas SQL cerradas:

- `GET /api/offices/{office_id}/relations`: inventario, máximo 128 tablas y 64 KiB.
- `GET /api/offices/{office_id}/relations/{table_name}?offset=0&limit=10`: registros, límite de 1 a 20; conserva los límites configurados de filas y bytes. `next_offset` indica la página siguiente.

El inventario tiene un límite independiente del límite de filas de registros. Las páginas no se mezclan en la respuesta del chat, para evitar que un resultado grande oculte tablas. Cada registro indica si es una referencia o un vínculo mediante usuarios asignados.

## Preparación y comprobación

Esta instalación ya está preparada; no repetir la importación. Para una nueva copia institucional previamente configurada, ejecutar desde la raíz con el Python del backend:

```powershell
& .\backend\.venv\Scripts\python.exe scripts/upgrade_office_relations.py 'D:\edwin\Downloads\backapsiop\backapsiop.sql'
& .\backend\.venv\Scripts\python.exe scripts/office_relation_paths.py
```

El importador crea un esquema nuevo de forma atómica y rehúsa sobrescribirlo. `database/views/004_office_relations.sql` documenta las vistas y permisos aplicados. Los informes locales de importación y validación quedan en `.runtime`, sin versionar datos personales.

Con la API activa, comprobar inventario y paginación reales:

```powershell
& .\backend\.venv\Scripts\python.exe scripts/check_office_relations.py
```

Las pruebas `scripts/test_office_relations.py` comprueban el catálogo y todos los caminos con datos sintéticos y rollback. La prueba PostgreSQL se omite si no existe el entorno local preparado.
