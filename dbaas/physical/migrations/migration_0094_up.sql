INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
    'collation_server', 1, null,
    "The server's default collation.",
    '', 'string'
from physical_enginetype where name = 'mysql';

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 36) = 'drivers.replication_topologies.mysql'
AND physical_parameter.name = 'collation_server'
AND physical_parameter.engine_type_id IN (select id from physical_enginetype where name = "mysql");
