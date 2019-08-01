UPDATE physical_engine
SET major_version = SUBSTRING_INDEX(version, '.', 1),
    minor_version = SUBSTRING_INDEX(SUBSTRING_INDEX(version, '.', 2), '.', -1);

INSERT INTO physical_enginepatch (created_at, updated_at, engine_id, patch_version, is_initial_patch)
SELECT now(), now(), id, SUBSTRING_INDEX(version, '.', -1), true
FROM physical_engine;

UPDATE physical_databaseinfra
JOIN physical_enginepatch ON (physical_enginepatch.engine_id = physical_databaseinfra.engine_id)
SET engine_patch_id = physical_enginepatch.id
WHERE physical_enginepatch.is_initial_patch = true;
