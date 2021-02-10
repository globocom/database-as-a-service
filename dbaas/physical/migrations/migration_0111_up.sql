INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
    'save', 1, null,
    "Will save the DB if both the given number of seconds and the given number of write operations against the DB occurred.",
    '', 'string'
from physical_enginetype where name = 'redis';

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 36) = 'drivers.replication_topologies.redis'
AND physical_parameter.name = 'save'
AND physical_parameter.engine_type_id IN (select id from physical_enginetype where name = "redis");

