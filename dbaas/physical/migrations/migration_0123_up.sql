INSERT INTO physical_diskoffering_environments (diskoffering_id, environment_id)
SELECT d.id, e.id
FROM physical_diskoffering d, physical_environment e;