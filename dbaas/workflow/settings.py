

MONGODB_UPGRADE_24_TO_30_SINGLE = (
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_24_to_26_single.UpgradeMongoDB_24_to_26',
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_26_to_30_single.UpgradeMongoDB_26_to_30',
    'workflow.steps.mongodb.upgrade.prereq_change_storage_engine_single.PreReqChangeMongoDBStorageEngine',
    'workflow.steps.mongodb.upgrade.take_instance_snapshot.TakeInstanceBackup',
    'workflow.steps.mongodb.upgrade.change_storage_engine_single.ChangeMongoDBStorageEngine',
    'workflow.steps.mongodb.upgrade.update_plan.UpdatePlan',
    'workflow.steps.mongodb.upgrade.update_engine.UpdateEngine',
    'workflow.steps.mongodb.upgrade.update_dbmonitor_version.UpdateDBMonitorDatabasInfraVersion',
)

MONGODB_UPGRADE_24_TO_30_HA = (
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_24_to_26_ha.UpgradeMongoDB_24_to_26',
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_26_to_30_ha.UpgradeMongoDB_26_to_30',
    'workflow.steps.mongodb.upgrade.take_instance_snapshot.TakeInstanceBackup',
    'workflow.steps.mongodb.upgrade.change_storage_engine_ha.ChangeMongoDBStorageEngine',
    'workflow.steps.mongodb.upgrade.update_plan.UpdatePlan',
    'workflow.steps.mongodb.upgrade.update_engine.UpdateEngine',
    'workflow.steps.mongodb.upgrade.update_dbmonitor_version.UpdateDBMonitorDatabasInfraVersion',
)
