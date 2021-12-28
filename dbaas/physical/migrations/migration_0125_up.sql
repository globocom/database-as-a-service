INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type)
VALUES (now(), now(), 'STANDARD', 'pd-standard');

INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type)
VALUES (now(), now(), 'BALANCED', 'pd-balanced');

INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type)
VALUES (now(), now(), 'SSD', 'pd-ssd');

INSERT INTO physical_diskofferingtype (created_at, updated_at, name, type)
VALUES (now(), now(), 'DEFAULT', 'default');

INSERT INTO physical_diskofferingtype_environments (diskofferingtype_id, environment_id)
SELECT (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard'), physical_environment.id
FROM physical_environment
WHERE physical_environment.provisioner = 4;

INSERT INTO physical_diskofferingtype_environments (diskofferingtype_id, environment_id)
SELECT (SELECT id FROM physical_diskofferingtype WHERE type = 'default'), physical_environment.id
FROM physical_environment
WHERE physical_environment.provisioner != 4;

UPDATE physical_volume
SET disk_offering_type = (SELECT type FROM physical_diskofferingtype WHERE type = 'pd-standard')
WHERE host_id IN(SELECT id from physical_host where offering_id IN(
SELECT offering_id FROM physical_offering_environments where environment_id IN (
SELECT id FROM physical_environment where physical_environment.provisioner = 4)));

UPDATE physical_volume
SET disk_offering_type = (SELECT type FROM physical_diskofferingtype WHERE type = 'default')
WHERE host_id IN(SELECT id from physical_host where offering_id IN(
SELECT offering_id FROM physical_offering_environments where environment_id IN (
SELECT id FROM physical_environment where physical_environment.provisioner != 4)));

UPDATE physical_plan
SET disk_offering_type_id = (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard')
WHERE id IN (SELECT plan_id FROM physical_plan_environments
WHERE environment_id IN (SELECT id from physical_environment
WHERE physical_environment.provisioner = 4));

UPDATE physical_plan
SET disk_offering_type_id = (SELECT id FROM physical_diskofferingtype WHERE type = 'default')
WHERE id IN (SELECT plan_id FROM physical_plan_environments
WHERE environment_id IN (SELECT id from physical_environment
WHERE physical_environment.provisioner != 4));

UPDATE physical_databaseinfra
SET disk_offering_type_id = (SELECT id FROM physical_diskofferingtype WHERE type = 'pd-standard')
WHERE environment_id IN (SELECT id from physical_environment
WHERE physical_environment.provisioner = 4);

UPDATE physical_databaseinfra
SET disk_offering_type_id = (SELECT id FROM physical_diskofferingtype WHERE type = 'default')
WHERE environment_id IN (SELECT id from physical_environment
WHERE physical_environment.provisioner != 4);

INSERT INTO physical_planattribute (created_at, updated_at, name, value, plan_id)
SELECT now(), now(), 'disk_type', 'pd-standard', physical_plan.id
FROM physical_plan
WHERE id IN (SELECT plan_id FROM physical_plan_environments
WHERE environment_id IN (SELECT id from physical_environment
WHERE physical_environment.provisioner = 4));

INSERT INTO physical_planattribute (created_at, updated_at, name, value, plan_id)
SELECT now(), now(), 'disk_type', 'default', id
FROM physical_plan
WHERE id IN (SELECT plan_id FROM physical_plan_environments
WHERE environment_id IN (SELECT id from physical_environment
WHERE physical_environment.provisioner != 4));


