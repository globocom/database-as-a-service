from maintenance.models import DatabaseMigrate, HostMigrate
from util.providers import get_database_migrate_steps
from workflow.workflow import steps_for_instances, rollback_for_instances_full
from copy import copy
from datetime import datetime


def get_migrate_steps(database, stage):
    class_path = database.infra.plan.replication_topology.class_path
    return get_database_migrate_steps(class_path, stage)

def build_migrate_hosts(hosts_zones, migrate, step_manager=None):
    instances = []
    for host, zone in hosts_zones.iteritems():
        instance = host.instances.first()
        if step_manager:
            host_migrate = step_manager.hosts.get(host=instance.hostname)
            host_migrate.id = None
            host_migrate.finished_at = None
            host_migrate.created_at = datetime.now()
        else:
            host_migrate = HostMigrate()
        host_migrate.task = migrate.task
        host_migrate.host = instance.hostname
        host_migrate.zone = zone
        host_migrate.environment = migrate.environment
        host_migrate.database_migrate = migrate
        host_migrate.save()
        instances.append(instance)
    return instances


def database_environment_migrate(

    database, new_environment, new_offering, task, hosts_zones, since_step=None,
    step_manager=None
):
    infra = database.infra
    if step_manager:
        database_migrate = copy(step_manager)
        database_migrate.id = None
        database_migrate.created_at = datetime.now()
        database_migrate.started_at = None
        database_migrate.finished_at = None
    else:
        database_migrate = DatabaseMigrate()
        infra.migration_stage += 1
        infra.save()
    database_migrate.task = task
    database_migrate.database = database
    database_migrate.environment = new_environment
    database_migrate.origin_environment = database.environment
    database_migrate.offering = new_offering
    database_migrate.origin_offering = database.infra.offering
    database_migrate.migration_stage = infra.migration_stage
    database_migrate.save()
    
    instances = build_migrate_hosts(hosts_zones, database_migrate, step_manager=step_manager)
    instances = sorted(instances, key=lambda k: k.dns)
    steps = get_migrate_steps(database, infra.migration_stage)
    result = steps_for_instances(
        steps, instances, task, database_migrate.update_step, since_step,
        step_manager=step_manager
    )
    database_migrate = DatabaseMigrate.objects.get(id=database_migrate.id)
    if result:
        database = database_migrate.database
        infra = database.infra
        is_ha = infra.plan.is_ha
        migration_stage = infra.migration_stage
        if ((is_ha and migration_stage == infra.STAGE_3) or
           (not is_ha and migration_stage == infra.STAGE_2)):
        
            database.environment = database_migrate.environment
            database.save()
        
            infra.environment = database_migrate.environment
            infra.plan = infra.plan.get_equivalent_plan_for_env(
                database_migrate.environment
            )
            infra.migration_stage = infra.NOT_STARTED
            infra.save()
        database_migrate.set_success()
        task.set_status_success('Database migrated with success')
    else:
        database_migrate.set_error()
        task.set_status_error('Could not migrate database')


def rollback_database_environment_migrate(migrate, task):
    hosts_zones = migrate.hosts_zones
    migrate.id = None
    migrate.created_at = datetime.now()
    migrate.started_at = None
    migrate.finished_at = None
    migrate.task = task
    migrate.migration_stage = migrate.database.infra.migration_stage
    migrate.save()

    instances = build_migrate_hosts(hosts_zones, migrate)
    instances = sorted(instances, key=lambda k: k.dns)
    steps = get_migrate_steps(migrate.database, 1)
    result = rollback_for_instances_full(
        steps, instances, task, migrate.get_current_step, migrate.update_step
    )
    migrate = DatabaseMigrate.objects.get(id=migrate.id)
    if result:
        infra = migrate.database.infra
        infra.migration_stage -= 1
        infra.save()

        migrate.set_rollback()
        task.set_status_success('Rollback executed with success')
    else:
        migrate.set_error()
        task.set_status_error(
            'Could not do rollback\n'
            'Please check error message and do retry'
        )
