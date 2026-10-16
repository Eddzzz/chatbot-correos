-- Values are source records, not an accounting balance or currency conversion.
-- Collections and movements may describe the same payment; never sum the union.
CREATE OR REPLACE VIEW chatbot.v_accounting_records WITH (security_barrier=true) AS
SELECT 'movimientos'::text AS category, s.id AS record_id,
       s.cobrado_at AS occurred_at, s.servicio AS service,
       s.cobro_activo AS active, s.monto AS amount,
       jsonb_build_object('tabla','cashier_flow_receivable_movements',
         'campos',to_jsonb(s) || jsonb_build_object(
           'monto',s.monto::text,'cantidad_paquetes',s.cantidad_paquetes::text),
         'omitidos','[]'::jsonb) AS record
FROM chatbot_relations_source.cashier_flow_receivable_movements s
WHERE current_setting('chatbot.access_scope',true)='global_internal'
  AND current_setting('chatbot.personal_access',true)='allowed'
UNION ALL
SELECT 'cobros'::text, s.id, s.cobrado_at, s.servicio,
       s.cobro_activo, s.monto_cobrado,
       jsonb_build_object('tabla','cashier_flow_receivable_collections',
         'campos',to_jsonb(s) || jsonb_build_object('monto_cobrado',s.monto_cobrado::text),
         'omitidos','["meses"]'::jsonb)
FROM chatbot_relations_source.cashier_flow_receivable_collections s
WHERE current_setting('chatbot.access_scope',true)='global_internal'
  AND current_setting('chatbot.personal_access',true)='allowed'
UNION ALL
SELECT 'facturacion'::text, s.id, s.created_at, NULL::text,
       NULL::boolean, NULL::numeric,
       jsonb_build_object('tabla','facturas',
         'campos',to_jsonb(s), 'omitidos','[]'::jsonb)
FROM chatbot_accounting_source.facturas s
WHERE current_setting('chatbot.access_scope',true)='global_internal'
  AND current_setting('chatbot.personal_access',true)='allowed';
REVOKE ALL ON chatbot.v_accounting_records FROM PUBLIC,chatbot_reader;
GRANT SELECT ON chatbot.v_accounting_records TO chatbot_institutional;
