INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
    'slave_net_timeout', 0, null,
    "The number of seconds to wait for more data or a heartbeat signal from the source before the replica considers the connection broken.",
    '1:', 'integer'
from physical_enginetype where name = 'mysql';

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 36) = 'drivers.replication_topologies.mysql'
AND physical_parameter.name = 'slave_net_timeout'
AND physical_parameter.engine_type_id IN (select id from physical_enginetype where name = "mysql");
