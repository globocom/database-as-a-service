import logging
from models import DatabaseAutoUpgradeVMOffering
from util.providers import get_auto_upgrade_vm_settings
from workflow.workflow import steps_for_instances
LOG = logging.getLogger(__name__)


def task_auto_upgrade_vm_offering(database, task, retry_from=None):
    try:
        auto_upgrade_vm = DatabaseAutoUpgradeVMOffering()
        auto_upgrade_vm.task = task
        auto_upgrade_vm.database = database
        auto_upgrade_vm.save()

        topology_path = database.plan.replication_topology.class_path
        steps = get_auto_upgrade_vm_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances_to_auto_upgrade_vm = database.infra.instances.all()
        if steps_for_instances(
                steps, instances_to_auto_upgrade_vm, task, auto_upgrade_vm.update_step, since_step=since_step
        ):
            database.update_status()
            auto_upgrade_vm.set_success()
            task.set_status_success('Auto Upgrade Database Offering is done')
        else:
            auto_upgrade_vm.set_error()
            task.set_status_error(
                'Could not update database offering\n'
                'Please check error message and do retry'
            )
    except Exception as erro:
        task.set_status_error('Error: {erro}.\n'
                              'To create task task_auto_upgrade_vm!\n'
                              'Please check error message and start new task.'.format(erro=erro))
        LOG.error('Error: {erro}.\n'
                  'To create task task_auto_upgrade_vm!\n'
                  'Please check error message and start new task.'.format(erro=erro))
