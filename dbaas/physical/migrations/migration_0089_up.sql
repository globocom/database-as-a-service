INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
    'sql_mode', 1, null,
    'Modes affect the SQL syntax MySQL supports and the data validation checks it performs. This makes it easier to use MySQL in different environments and to use MySQL together with other database servers. Use '''' (two single quotes) to set sql_mode to empty.',
    '', 'string'
from physical_enginetype where name = 'mysql' limit 1;

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 36) = 'drivers.replication_topologies.mysql'
AND physical_parameter.name = 'sql_mode'
AND physical_parameter.engine_type_id = (select id from physical_enginetype where name = 'mysql' limit 1);
