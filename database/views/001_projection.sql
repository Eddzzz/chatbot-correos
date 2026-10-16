-- Apply only with a reviewed administrative account to an approved restored DB.
-- No source tables are altered. Internal global access only; no customer RLS is implied.
BEGIN;
CREATE SCHEMA IF NOT EXISTS chatbot;
REVOKE ALL ON SCHEMA chatbot FROM PUBLIC;

CREATE OR REPLACE VIEW chatbot.v_tracking WITH (security_barrier = true) AS
SELECT p.source, p.shipment_id, p.tracking_code, e.nombre_estado::text AS status,
       p.origin, p.destination, p.registered_at, p.updated_at, p.weight_value, p.amount_value
FROM (
    SELECT 'certi'::text AS source, id AS shipment_id, codigo::text AS tracking_code,
           fk_estado AS state_id, NULL::text AS origin, cuidad::text AS destination,
           created_at AS registered_at, updated_at, peso AS weight_value, precio AS amount_value
    FROM public.paquetes_certi
    UNION ALL
    SELECT 'ordi', id, codigo::text, fk_estado, NULL::text, ciudad::text,
           created_at, updated_at, peso, precio FROM public.paquetes_ordi
    UNION ALL
    SELECT 'ems', id, codigo::text, estado_id, origen::text, ciudad::text,
           created_at, updated_at, peso, precio FROM public.paquetes_ems
    UNION ALL
    SELECT 'contrato', id, codigo::text, estados_id, origen::text, destino::text,
           created_at, updated_at, peso, precio FROM public.paquetes_contrato
    UNION ALL
    SELECT 'int', id, codigo::text, estado_id, origen::text, destino::text,
           created_at, updated_at, peso, precio FROM public.paquetes_int
) AS p
LEFT JOIN public.estados AS e ON e.id = p.state_id
WHERE current_setting('chatbot.access_scope', true) = 'global_internal';

CREATE OR REPLACE VIEW chatbot.v_offices WITH (security_barrier = true) AS
SELECT id AS office_id, "codigoSucursal" AS codigo_sucursal,
       municipio::text AS municipality, departamento::text AS department,
       telefono::text AS phone
FROM public.sucursales
WHERE current_setting('chatbot.access_scope', true) = 'global_internal';

COMMENT ON VIEW chatbot.v_tracking IS
'Internal-only minimal projection. Source peso/precio units require business confirmation. Source created_at timestamps lack timezone. No proof of delivery inferred.';
COMMENT ON VIEW chatbot.v_offices IS
'Internal-only branch directory. Source contains no address, office hours or service availability.';
COMMIT;
