DELETE FROM physical_replicationtopology_parameter
WHERE parameter_id in (SELECT id FROM physical_parameter WHERE name = 'slave_net_timeout'
AND engine_type_id IN (SELECT id FROM physical_enginetype WHERE name = "mysql"));

DELETE FROM physical_parameter
WHERE name = 'slave_net_timeout'
AND engine_type_id IN (SELECT id FROM physical_enginetype WHERE name = "mysql");
