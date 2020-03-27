delete from physical_databaseinfraparameter where parameter_id in (select id from physical_parameter where name ='audit_log_file');

delete from physical_replicationtopology_parameter where parameter_id in (select id from physical_parameter where name ='audit_log_file');

delete from physical_parameter where name ='audit_log_file';