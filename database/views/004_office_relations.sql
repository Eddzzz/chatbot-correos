-- The owner retains all private source tables; the operator can read only guarded views.
CREATE OR REPLACE VIEW chatbot.v_office_related_records WITH (security_barrier=true) AS
SELECT m.office_id,n.table_name,n.record_key,n.record,m.relation_kind
FROM chatbot_relations_source.members m
JOIN chatbot_relations_source.nodes n USING (table_name,record_key)
WHERE current_setting('chatbot.access_scope',true)='global_internal'
  AND current_setting('chatbot.personal_access',true)='allowed';
CREATE OR REPLACE VIEW chatbot.v_office_related_counts WITH (security_barrier=true) AS
SELECT office_id,table_name,total_count,relation_kind,path_info,descendant_count,lookup_count
FROM chatbot_relations_source.counts
WHERE current_setting('chatbot.access_scope',true)='global_internal'
  AND current_setting('chatbot.personal_access',true)='allowed';
REVOKE ALL ON chatbot.v_office_related_records,chatbot.v_office_related_counts FROM PUBLIC,chatbot_reader;
GRANT SELECT ON chatbot.v_office_related_records,chatbot.v_office_related_counts TO chatbot_institutional;
