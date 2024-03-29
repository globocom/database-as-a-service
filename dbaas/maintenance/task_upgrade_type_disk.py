from models import DatabaseUpgradeDiskType
from util.providers import get_upgrade_disk_type_settings
from workflow.workflow import steps_for_instances
from physical.models import DiskOfferingType


def task_upgrade_disk_type(database, new_disk_type_upgrade, task, retry_from=None):
    try:
        upgrade_disk_type = DatabaseUpgradeDiskType()
        upgrade_disk_type.task = task
        upgrade_disk_type.database = database
        upgrade_disk_type.disk_offering_type = DiskOfferingType.objects.get(id=new_disk_type_upgrade)
        upgrade_disk_type.origin_disk_offering_type = database.databaseinfra.disk_offering_type

        topology_path = database.plan.replication_topology.class_path
        steps = get_upgrade_disk_type_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances_to_upgrade_disk = database.infra.get_driver().get_database_instances()
        if steps_for_instances(
                steps, instances_to_upgrade_disk, task, upgrade_disk_type.update_step, since_step=since_step
        ):
            infra = database.infra
            infra.disk_offering_type = upgrade_disk_type.disk_offering_type
            infra.save()
            upgrade_disk_type.set_success()
            task.set_status_success('Upgrade Disk Type is done')
        else:
            upgrade_disk_type.set_error()
            task.set_status_error(
                'Could not do upgrade disk type\n'
                'Please check error message and do retry'
            )
    except Exception as erro:
        task.set_status_error('Error: {erro}.\n'
                              'To create task task_upgrade_disk_type!\n'
                              'Please check error message and start new task.'.format(erro=erro))
