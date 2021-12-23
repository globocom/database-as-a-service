INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type) VALUES (now(), now(), 'STANDARD', 'pd-standard');
INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type) VALUES (now(), now(), 'BALANCED', 'pd-balanced');
INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type) VALUES (now(), now(), 'SSD', 'pd-ssd');


INSERT INTO physical_diskofferingtype_environments (diskofferingtype_id, environment_id)
SELECT (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard'), physical_environment.id
FROM physical_environment
WHERE physical_environment.provisioner = 4;

UPDATE physical_volume SET disk_offering_type = (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard');

UPDATE physical_plan SET disk_offering_type_id = (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard')
WHERE id IN (SELECT plan_id FROM physical_plan_environments WHERE environment_id IN (SELECT id from physical_environment where physical_environment.provisioner = 4));

UPDATE physical_databaseinfra SET disk_offering_type_id = (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard')
WHERE environment_id IN (SELECT id from physical_environment where physical_environment.provisioner = 4);