import logging
from models import DatabaseStopDatabaseVM, DatabaseStopVMInstanceMaster
from util.providers import get_stop_database_vm_settings
from workflow.workflow import steps_for_instances
LOG = logging.getLogger(__name__)


def task_stop_database_vm(database, task, retry_from=None):
    try:
        stop_database_vm = DatabaseStopDatabaseVM()
        stop_database_vm.task = task
        stop_database_vm.database = database
        stop_database_vm.save()
        if 'mysql' in database.infra.engine.name.lower():
            database_instance_master = DatabaseStopVMInstanceMaster()
            database_instance_master.database_stop = stop_database_vm
            database_instance_master.master = database.infra.get_driver().get_master_instance()
            database_instance_master.save()

        topology_path = database.plan.replication_topology.class_path
        steps = get_stop_database_vm_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances_to_stop_database_vm = database.infra.instances.all()
        if steps_for_instances(
                steps, instances_to_stop_database_vm, task, stop_database_vm.update_step, since_step=since_step
        ):
            database.update_status()
            stop_database_vm.set_success()
            task.set_status_success('Stopping Database is done')
        else:
            stop_database_vm.set_error()
            task.set_status_error(
                'Could not stop database\n'
                'Please check error message and do retry'
            )
    except Exception as erro:
        task.set_status_error('Error: {erro}.\n'
                              'To create task task_stop_database_vm!\n'
                              'Please check error message and start new task.'.format(erro=erro))
        LOG.error('Error: {erro}.\n'
                  'To create task task_stop_database_vm!\n'
                  'Please check error message and start new task.'.format(erro=erro))
