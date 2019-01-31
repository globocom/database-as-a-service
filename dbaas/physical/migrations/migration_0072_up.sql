delete from physical_databaseinfraparameter where parameter_id in (select id from physical_parameter where name = 'thread_concurrency');
delete from physical_replicationtopology_parameter where parameter_id in (select id from physical_parameter where name = 'thread_concurrency');
delete from physical_parameter where name = 'thread_concurrency';

INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
'audit_log_format', 0, null,
'The audit log file format.',
'NEW, OLD,  JSON', 'string'
from physical_enginetype where name = 'mysql' limit 1;

INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
'audit_log_file', 0, null,
'The base name and suffix of the file to which the audit log plugin writes events.',
'', 'string'
from physical_enginetype where name = 'mysql' limit 1;

INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
'audit_log_rotate_on_size', 1, null,
'If the audit_log_rotate_on_size value is 0, the audit log plugin does not perform automatic log file rotation. Instead, use audit_log_flush to close and reopen the log on demand. In this case, manually rename the file externally to the server before flushing it. If the audit_log_rotate_on_size value is greater than 0, automatic size-based log file rotation occurs. Whenever a write to the log file causes its size to exceed the audit_log_rotate_on_size value, the audit log plugin closes the current log file, renames it, and opens a new log file.',
'0:', 'integer'
from physical_enginetype where name = 'mysql' limit 1;

INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
'audit_log_exclude_accounts', 1, null,
'The accounts for which events should not be logged. The value should be NULL or a string containing a list of one or more comma-separated account names.',
'', 'string'
from physical_enginetype where name = 'mysql' limit 1;

INSERT INTO physical_parameter (created_at, updated_at, engine_type_id,
    name, dynamic, custom_method,
    description,
    allowed_values, parameter_type)
SELECT now(), now(), physical_enginetype.id,
'audit_log_policy', 0, null,
'The policy controlling how the audit log plugin writes events to its log file.',
'ALL, LOGINS, QUERIES, NONE', 'string'
from physical_enginetype where name = 'mysql' limit 1;

