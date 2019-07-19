UPDATE physical_engine
SET major_version = null,
    minor_version = null;

UPDATE physical_databaseinfra SET engine_patch_id = null;

DELETE FROM physical_enginepatch;