from backup.models import BackupGroup
from util.providers import get_restore_snapshot_settings
from workflow.workflow import steps_for_instances
from models import DatabaseRestore


def restore_snapshot(database, group, task, retry_from=None):
    restore = DatabaseRestore()
    restore.task = task
    restore.database = database
    restore.group = group

    new_group = retry_from.new_group if retry_from else BackupGroup()
    new_group.save()
    restore.new_group = new_group

    restore.save()
    restore.load_instances(retry_from)

    topology_path = database.plan.replication_topology.class_path
    steps = get_restore_snapshot_settings(topology_path)

    since_step = retry_from.current_step if retry_from else None
    if steps_for_instances(
        steps, restore.instances, task, restore.update_step, since_step=since_step
    ):
        restore.set_success()
        task.set_status_success('Restore is done')
    else:
        restore.set_error()
        task.set_status_error(
            'Could not do restore\n'
            'Please check error message and do retry'
        )
