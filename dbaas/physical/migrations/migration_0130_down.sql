DELETE FROM physical_replicationtopology_parameter
WHERE parameter_id in (SELECT id FROM physical_parameter WHERE name = 'cluster-node-timeout'
AND engine_type_id IN (SELECT id FROM physical_enginetype WHERE name = "redis"));

DELETE FROM physical_parameter
WHERE name = 'cluster-node-timeout'
AND engine_type_id IN (SELECT id FROM physical_enginetype WHERE name = "redis");