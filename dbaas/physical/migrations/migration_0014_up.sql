update physical_instance set instance_type = 1 where databaseinfra_id in (select id from physical_databaseinfra where engine_id = 2);

update physical_instance set instance_type = 2 where databaseinfra_id in (select id from physical_databaseinfra where engine_id = 1);

update physical_instance set instance_type = 3 where databaseinfra_id in (select id from physical_databaseinfra where engine_id = 1) and is_arbiter;

update physical_instance set instance_type = 4 where databaseinfra_id in (select id from physical_databaseinfra where engine_id = 3);

