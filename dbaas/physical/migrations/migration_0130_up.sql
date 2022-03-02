INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
    'cluster-node-timeout', 1, null,
    "The amount of milliseconds a node must be unreachable for it to be considered in failure state.",
    '1:', 'integer'
from physical_enginetype where name = 'redis';

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 49) = 'drivers.replication_topologies.redis.RedisCluster'
AND physical_parameter.name = 'cluster-node-timeout'
AND physical_parameter.engine_type_id IN (select id from physical_enginetype where name = "redis");
