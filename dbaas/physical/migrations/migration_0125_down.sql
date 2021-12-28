UPDATE physical_volume SET disk_offering_type = NULL;
UPDATE physical_plan SET disk_offering_type_id = NULL WHERE id IN (SELECT plan_id FROM physical_plan_environments WHERE environment_id IN (SELECT id from physical_environment where physical_environment.provisioner = 4));
UPDATE physical_databaseinfra SET disk_offering_type_id = NULL WHERE environment_id IN (SELECT id from physical_environment where physical_environment.provisioner = 4);

DELETE FROM physical_diskofferingtype_environments;

DELETE FROM physical_diskofferingtype;

