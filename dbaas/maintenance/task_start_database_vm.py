import logging
from models import DatabaseStartDatabaseVM
from util.providers import get_start_database_vm_settings
from workflow.workflow import steps_for_instances
LOG = logging.getLogger(__name__)


def task_start_database_vm(database, task, retry_from=None):
    try:
        start_database_vm = DatabaseStartDatabaseVM()
        start_database_vm.task = task
        start_database_vm.database = database
        start_database_vm.save()

        topology_path = database.plan.replication_topology.class_path
        steps = get_start_database_vm_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances_to_start_database_vm = database.infra.instances.all()
        if steps_for_instances(
                steps, instances_to_start_database_vm, task, start_database_vm.update_step, since_step=since_step
        ):
            database.was_manually_stopped = False
            database.save()

            database.update_status()
            start_database_vm.set_success()
            task.set_status_success('Starting Database is done')
        else:
            start_database_vm.set_error()
            task.set_status_error(
                'Could not start database\n'
                'Please check error message and do retry'
            )
    except Exception as erro:
        task.set_status_error('Error: {erro}.\n'
                              'To create task task_start_database_vm!\n'
                              'Please check error message and start new task.'.format(erro=erro))
        LOG.error('Error: {erro}.\n'
                  'To create task task_start_database_vm!\n'
                  'Please check error message and start new task.'.format(erro=erro))
