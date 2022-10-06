from maintenance.models import HostMigrate
from util.providers import get_region_migrate_steps
from workflow.workflow import steps_for_instances, rollback_for_instances_full
import logging

LOG = logging.getLogger(__name__)


def get_steps(host):
    plan = host.instances.first().databaseinfra.plan
    class_path = plan.replication_topology.class_path
    return get_region_migrate_steps(class_path)


def node_region_migrate(host, new_zone, environment, task,
                      since_step=None, step_manager=None, 
                      zone_origin=None):
    instance = host.instances.first()
    if step_manager:
        region_migrate = step_manager
        region_migrate.id = None
    else:
        region_migrate = HostMigrate()
    region_migrate.task = task
    region_migrate.host = instance.hostname
    region_migrate.zone = new_zone
    region_migrate.zone_origin = zone_origin
    region_migrate.environment = environment
    region_migrate.save()

    steps = get_steps(host)
    result = steps_for_instances(
        steps, [instance], task, region_migrate.update_step, since_step,
        step_manager=region_migrate
    )
    host_migrate = HostMigrate.objects.get(id=region_migrate.id)
    if result:
        host_migrate.set_success()
        task.set_status_success('Node migrated with success')
    else:
        host_migrate.set_error()
        task.set_status_error('Could not migrate host')


def rollback_node_region_migrate(migrate, task):
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
