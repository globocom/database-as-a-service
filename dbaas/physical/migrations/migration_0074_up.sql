INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
'init_connect', 1, null,
'A string to be executed by the server for each client that connects. The string consists of one or more SQL statements, separated by semicolon characters.',
'', 'string'
from physical_enginetype where name = 'mysql' limit 1;

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 36) = 'drivers.replication_topologies.mysql'
AND physical_parameter.name in ('init_connect')
AND physical_parameter.engine_type_id = (select id from physical_enginetype where name = 'mysql' limit 1);