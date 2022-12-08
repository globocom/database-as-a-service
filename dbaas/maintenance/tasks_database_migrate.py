from maintenance.models import DatabaseMigrate, HostMigrate
from util.providers import get_database_migrate_steps
from workflow.workflow import (
    steps_for_instances, rollback_for_instances_full, get_current_step_for_instances, lock_databases_for
)
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


def rebuild_hosts_migrate(current_db_migrate, previous_db_migrate, validate_hosts=False):
    instances = []
    previous_hosts_migrate = previous_db_migrate.hosts.all()

    for previous_host_migrate in previous_hosts_migrate:
        if validate_hosts and previous_host_migrate.host.first_instance_dns != previous_host_migrate.host.address:
            continue
        host = previous_host_migrate.host
        zone = previous_host_migrate.zone
        snapshot = previous_host_migrate.snapshot
        instance = host.instances.first()
        save_host_migrate(host, zone, snapshot, current_db_migrate)
        instances.append(instance)
    return instances


def build_database_migrate(task, database, environment, offering, migration_stage):
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


def rebuild_database_migrate(task, previous_db_migrate):
    database_migrate = copy(previous_db_migrate)
    database_migrate.id = None
    database_migrate.created_at = datetime.now()
    database_migrate.started_at = None
    database_migrate.finished_at = None
    database_migrate.status = database_migrate.WAITING
    database_migrate.task = task
    database_migrate.save()
    return database_migrate


def can_migrate(database, task, migration_stage, rollback):

    last_mig = DatabaseMigrate.objects.filter(database=database).last()
    if not last_mig:
        return True

    if last_mig.status == DatabaseMigrate.WAITING:
        task.set_status_error(
            "Could not run migration. Found a 'Waiting' database migration: '{}'".format(last_mig)
        )
        return False
    elif last_mig.status == DatabaseMigrate.RUNNING:
        task.set_status_error(
            "Could not run migration. Found a 'Running' database migration: '{}'".format(last_mig)
        )
        return False
    elif last_mig.status == DatabaseMigrate.SUCCESS:
        completed_migration_stage = last_mig.migration_stage
    elif last_mig.status == DatabaseMigrate.ERROR:
        completed_migration_stage = last_mig.migration_stage - 1
    elif last_mig.status == DatabaseMigrate.ROLLBACK:
        completed_migration_stage = last_mig.migration_stage - 1
    else:
        task.set_status_error(
            "Unknown database migration status: '{}'. For migration: '{}'".format(last_mig.status, last_mig)
        )
        return False

    '''
    TODO: REVIEW
    if not rollback and migration_stage == completed_migration_stage:
        task.set_status_error(
            "Could not run migration. The migration stage " \
            "'{}' for database '{}' is already completed." \
            "".format(migration_stage, database)
        )
        return False
    if rollback and migration_stage != completed_migration_stage:
        task.set_status_error(
            "Could not run rollback migration. The rollback stage should be " \
            "{}, but it is {}" \
            "".format(completed_migration_stage, migration_stage)
        )
        return False
    '''

    return True


def database_environment_migrate(
    database, new_environment, new_offering, task, hosts_zones, since_step=None, step_manager=None
):

    infra = database.infra
    #database.infra.disk_offering_type = database.infra.disk_offering_type.get_type_to(new_environment)
    #database.save()
    if step_manager:
        migration_stage = step_manager.migration_stage
        if not can_migrate(database, task, migration_stage, False):
            return
        database_migrate = rebuild_database_migrate(task, step_manager)
        instances = rebuild_hosts_migrate(database_migrate, step_manager, infra.in_last_migration_stage)
    else:
        infra.migration_stage += 1
        if not can_migrate(database, task, infra.migration_stage, False):
            return

        infra.save()
        database_migrate = build_database_migrate(task, database, new_environment, new_offering, infra.migration_stage)
        if infra.migration_stage == 1:
            instances = build_hosts_migrate(hosts_zones, database_migrate)
        else:
            last_db_migrate = DatabaseMigrate.objects.filter(database=database, status=DatabaseMigrate.SUCCESS).last()
            instances = rebuild_hosts_migrate(database_migrate, last_db_migrate, infra.in_last_migration_stage)
    instances = sorted(instances, key=lambda k: k.id)
    steps = get_migrate_steps(database, infra.migration_stage)
    if not can_migrate_check_steps(steps, instances, since_step, database_migrate, task, False):
        return

    result = steps_for_instances(
        steps, instances, task, database_migrate.update_step, since_step, step_manager=step_manager
    )
    database_migrate = DatabaseMigrate.objects.get(id=database_migrate.id)
    if result:
        database = database_migrate.database
        infra = database.infra
        migration_stage = infra.migration_stage
        if infra.in_last_migration_stage:
            database.environment = database_migrate.environment
            database.save()

            infra.environment = database_migrate.environment
            infra.plan = infra.plan.get_equivalent_plan_for_env(database_migrate.environment)
            infra.disk_offering_type = infra.disk_offering_type.get_type_to(new_environment)
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

    if not can_migrate(database, task, migration_stage, True):
        return

    database_migrate = rebuild_database_migrate(task, step_manager)
    instances = rebuild_hosts_migrate(database_migrate, step_manager)
    instances = sorted(instances, key=lambda k: k.id)
    steps = get_migrate_steps(database, migration_stage)

    if not can_migrate_check_steps(steps, instances, database_migrate.get_current_step(), database_migrate, task, True):
        return

    result = rollback_for_instances_full(
        steps, instances, task, database_migrate.get_current_step, database_migrate.update_step
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


def can_migrate_check_steps(steps, instances, since_step, database_migrate, task, rollback):

    if not since_step:
        return True
    if not database_migrate.current_step_class:
        return True

    current_step = get_current_step_for_instances(steps, instances, since_step, rollback)

    if current_step != database_migrate.current_step_class:
        lock_databases_for(instances, task, True)
        database_migrate.set_error()
        task.set_status_error(
            "Could not migrate database. \n" \
            "Last step in last migration was '{}'\n" \
            "It is trying to execute '{}'.\n" \
            "Probably there was a deploy after last migration.\n" \
            "Try to fix the 'Current Step' and 'Current Step Class' " \
            "on migration admin." \
            "".format(database_migrate.current_step_class, current_step)
        )
        return False

    return True
