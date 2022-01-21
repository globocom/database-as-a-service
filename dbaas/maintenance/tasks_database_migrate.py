from maintenance.models import DatabaseMigrate, HostMigrate
from util.providers import get_database_migrate_steps
from workflow.workflow import steps_for_instances, rollback_for_instances_full
from copy import copy
from datetime import datetime
from physical.models import DiskOfferingType


def get_migrate_steps(database, stage):
    class_path = database.infra.plan.replication_topology.class_path
    return get_database_migrate_steps(class_path, stage)


def save_host_migrate(host, zone, snapshot, database_migrate):
    host_migrate = HostMigrate()
    host_migrate.task = database_migrate.task
    host_migrate.host = host
    host_migrate.zone = zone
    host_migrate.snapshot = snapshot
    host_migrate.environment = database_migrate.environment
    host_migrate.database_migrate = database_migrate
    host_migrate.save()


def build_hosts_migrate(hosts_zones, database_migrate):
    instances = []
    for host, zone in hosts_zones.iteritems():
        instance = host.instances.first()
        save_host_migrate(host, zone, None, database_migrate)
        instances.append(instance)
    return instances


def rebuild_hosts_migrate(current_db_migrate, previous_db_migrate):
    instances = []
    previous_hosts_migrate = previous_db_migrate.hosts.all()
    for previous_host_migrate in previous_hosts_migrate:
        host = previous_host_migrate.host
        zone = previous_host_migrate.zone
        snapshot = previous_host_migrate.snapshot
        instance = host.instances.first()
        save_host_migrate(host, zone, snapshot, current_db_migrate)
        instances.append(instance)
    return instances


def build_database_migrate(
    task, database, environment, offering, migration_stage
):
    database_migrate = DatabaseMigrate()
    database_migrate.task = task
    database_migrate.database = database
    database_migrate.environment = environment
    database_migrate.origin_environment = database.environment
    database_migrate.offering = offering
    database_migrate.origin_offering = database.infra.offering
    database_migrate.migration_stage = migration_stage
    database_migrate.save()
    return database_migrate


def rebuild_database_migrate(
    task, previous_db_migrate, 
):
    database_migrate = copy(previous_db_migrate)
    database_migrate.id = None
    database_migrate.created_at = datetime.now()
    database_migrate.started_at = None
    database_migrate.finished_at = None
    database_migrate.status = database_migrate.WAITING
    database_migrate.task = task
    database_migrate.save()
    return database_migrate


def database_environment_migrate(
    database, new_environment, new_offering, task, hosts_zones, since_step=None,
    step_manager=None
):
    infra = database.infra
    database.infra.disk_offering_type = database.infra.disk_offering_type.get_type_to(new_environment)
    database.save()
    if step_manager:
        database_migrate = rebuild_database_migrate(task, step_manager)
        instances = rebuild_hosts_migrate(database_migrate, step_manager)
    else:
        infra.migration_stage += 1
        infra.save()
        database_migrate = build_database_migrate(
            task, database, new_environment, new_offering,
            infra.migration_stage
        )
        if infra.migration_stage == 1:
            instances = build_hosts_migrate(hosts_zones, database_migrate)
        else:
            last_db_migrate = DatabaseMigrate.objects.filter(
                database=database,
                status=DatabaseMigrate.SUCCESS
            ).last()
            instances = rebuild_hosts_migrate(database_migrate, last_db_migrate)
    instances = sorted(instances, key=lambda k: k.id)
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


def rollback_database_environment_migrate(step_manager, task):
    database = step_manager.database
    database.infra.disk_offering_type = database.infra.disk_offering_type.get_type_to(database.environment)
    database.save()
    migration_stage = database.infra.migration_stage

    database_migrate = rebuild_database_migrate(task, step_manager)
    instances = rebuild_hosts_migrate(database_migrate, step_manager)
    instances = sorted(instances, key=lambda k: k.id)
    steps = get_migrate_steps(database, migration_stage)

    result = rollback_for_instances_full(
        steps, instances, task, database_migrate.get_current_step,
        database_migrate.update_step
    )
    database_migrate = DatabaseMigrate.objects.get(id=database_migrate.id)
    if result:
        infra = database_migrate.database.infra
        infra.migration_stage -= 1
        infra.save()

        database_migrate.set_rollback()
        task.set_status_success('Rollback executed with success')
    else:
        database_migrate.set_error()
        task.set_status_error(
            'Could not do rollback\n'
            'Please check error message and do retry'
        )
