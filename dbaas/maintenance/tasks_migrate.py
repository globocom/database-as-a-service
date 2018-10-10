from maintenance.models import HostMigrate
from util.providers import get_host_migrate_steps
from workflow.workflow import steps_for_instances, rollback_for_instances_full


def get_steps(host):
    plan = host.instances.first().databaseinfra.plan
    class_path = plan.replication_topology.class_path
    return get_host_migrate_steps(class_path)


def node_zone_migrate(host, zone, new_environment, task, since_step=None):
    instance = host.instances.first()
    host_migrate = HostMigrate()
    host_migrate.task = task
    host_migrate.host = instance.hostname
    host_migrate.zone = zone
    host_migrate.environment = new_environment
    host_migrate.save()

    steps = get_steps(host)
    result = steps_for_instances(
        steps, [instance], task, host_migrate.update_step, since_step
    )
    host_migrate = HostMigrate.objects.get(id=host_migrate.id)
    if result:
        host_migrate.set_success()
        task.set_status_success('Node migrated with success')
    else:
        host_migrate.set_error()
        task.set_status_error('Could not migrate host')


def rollback_node_zone_migrate(migrate, task):
    instance = migrate.host.instances.first()
    migrate.id = None
    migrate.created_at = None
    migrate.finished_at = None
    migrate.task = task
    migrate.save()

    steps = get_steps(migrate.host)
    result = rollback_for_instances_full(
        steps, [instance], task, migrate.get_current_step, migrate.update_step
    )
    migrate = HostMigrate.objects.get(id=migrate.id)
    if result:
        migrate.set_rollback()
        task.set_status_success('Rollback executed with success')
    else:
        migrate.set_error()
        task.set_status_error(
            'Could not do rollback\n'
            'Please check error message and do retry'
        )
