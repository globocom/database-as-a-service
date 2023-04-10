import logging

from django.db.models import Q

from models import DatabaseAutoUpgradeVMOffering
from physical.models import (Plan, DatabaseInfra, Instance, Pool)
from util.providers import get_auto_upgrade_vm_settings
from workflow.workflow import steps_for_instances
from util import get_vm_name

LOG = logging.getLogger(__name__)


def task_auto_upgrade_vm_offering(database, task, retry_from=None, resize_target=None):
    try:
        number_of_instances_before_task = database.infra.last_vm_created
        number_of_instances = 1

        auto_upgrade_vm = DatabaseAutoUpgradeVMOffering()
        auto_upgrade_vm.task = task
        auto_upgrade_vm.database = database
        auto_upgrade_vm.resize_target = resize_target
        auto_upgrade_vm.source_offer = database.infra.offering
        auto_upgrade_vm.target_offer = database.get_future_offering(resize_target)  
        auto_upgrade_vm.number_of_instances = number_of_instances
        auto_upgrade_vm.number_of_instances_before = (number_of_instances_before_task)
        auto_upgrade_vm.save()

        infra = database.infra
        plan = infra.plan
        driver = infra.get_driver()

        topology_path = database.plan.replication_topology.class_path
        steps = get_auto_upgrade_vm_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances = list(database.infra.instances.all())

        last_vm_created = number_of_instances_before_task

        if not retry_from:
            for i in range(number_of_instances):
                instance = None
                last_vm_created += 1
                vm_name = get_vm_name(
                    prefix=infra.name_prefix,
                    sufix=infra.name_stamp,
                    vm_number=last_vm_created
                )

                try:
                    instance = infra.instances.get(
                        Q(hostname__hostname__startswith=vm_name) |
                        Q(dns__startswith=vm_name)
                    )
                except Instance.DoesNotExist:
                    instance = Instance(
                        databaseinfra=infra,
                        dns=vm_name,
                        port=driver.get_default_database_port(),
                        instance_type=driver.get_default_instance_type(),
                        temporary=True
                    )

                instance.vm_name = instance.dns
                instances.append(instance)

        if steps_for_instances(
                steps, instances, task, auto_upgrade_vm.update_step, since_step=since_step
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
