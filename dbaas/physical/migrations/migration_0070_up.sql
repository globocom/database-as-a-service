INSERT INTO physical_parameter (created_at, updated_at,
    engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
VALUES ( now(), now(),
    (select id from physical_enginetype where name = 'mysql' limit 1),
    'wait_timeout', 1, null,
    'The number of seconds the server waits for activity on a noninteractive connection before closing it.',
    '1:31536000', 'string' );

INSERT INTO physical_parameter (created_at, updated_at,
    engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
VALUES ( now(), now(),
    (select id from physical_enginetype where name = 'mysql' limit 1),
    'interactive_timeout', 1, null,
    'The number of seconds the server waits for activity on an interactive connection before closing it.',
    '1:31536000', 'string' );

INSERT INTO physical_parameter (created_at, updated_at,
    engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
VALUES ( now(), now(),
    (select id from physical_enginetype where name = 'mysql' limit 1),
    'log_bin_trust_function_creators', 1, null,
    'It controls whether stored function creators can be trusted not to create stored functions that will cause unsafe events to be written to the binary log.',
    '', 'boolean' );

INSERT INTO physical_replicationtopology_parameter (replicationtopology_id, parameter_id)
SELECT physical_replicationtopology.id, physical_parameter.id
FROM physical_replicationtopology, physical_parameter
WHERE substr(physical_replicationtopology.class_path, 1, 36) = 'drivers.replication_topologies.mysql'
AND physical_parameter.name in ('wait_timeout', 'interactive_timeout', 'log_bin_trust_function_creators')
AND physical_parameter.engine_type_id = (select id from physical_enginetype where name = 'mysql' limit 1);