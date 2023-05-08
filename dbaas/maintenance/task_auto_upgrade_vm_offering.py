import logging

from django.db.models import Q

from models import DatabaseAutoUpgradeVMOffering
from physical.models import (Plan, DatabaseInfra, Instance, Pool)
from util.providers import get_auto_upgrade_vm_settings
from workflow.workflow import steps_for_instances
from util import get_vm_name

LOG = logging.getLogger(__name__)


def get_base_snapshot(database):
    hosts = database.infra.hosts
    volumes = []

    for host in hosts:
        volumes.extend(host.volumes.all())
    
    snapshots = []

    for volume in volumes:
        snapshots.extend(volume.backups.all())

    base_snapshot = None
    for snapshot in snapshots:
        if (base_snapshot is None or snapshot.created_at > base_snapshot.created_at) and snapshot.end_at is not None and snapshot.purge_at is None:
            base_snapshot = snapshot

    if base_snapshot is None:
        raise AssertionError('Nao foi encontrada nenhuma Snapshot para criacao do novo Volume!')
    
    return base_snapshot


def create_maintenance(database, task, resize_target, retry_from):
    base_snapshot = get_base_snapshot(database)

    number_of_instances_before_task = database.infra.last_vm_created
    number_of_instances = 1

    # se vindo de um retry, traz informacoes de offering da maintenance original
    source_offer = retry_from.source_offer if retry_from else database.infra.offering
    target_offer = retry_from.target_offer if retry_from else database.get_future_offering(resize_target)

    auto_upgrade_vm = DatabaseAutoUpgradeVMOffering()
    auto_upgrade_vm.task = task
    auto_upgrade_vm.database = database
    auto_upgrade_vm.resize_target = resize_target
    auto_upgrade_vm.source_offer = source_offer
    auto_upgrade_vm.target_offer = target_offer  
    auto_upgrade_vm.number_of_instances = number_of_instances
    auto_upgrade_vm.number_of_instances_before = (number_of_instances_before_task)
    auto_upgrade_vm.base_snapshot = base_snapshot
    auto_upgrade_vm.save()

    return auto_upgrade_vm, number_of_instances, number_of_instances_before_task


def task_auto_upgrade_vm_offering(database, task, retry_from=None, resize_target=None):
    auto_upgrade_vm = None
    try:
        infra = database.infra
        driver = infra.get_driver()

        auto_upgrade_vm, number_of_instances, number_of_instances_before_task = create_maintenance(database, task, resize_target, retry_from)

        topology_path = database.plan.replication_topology.class_path
        steps = get_auto_upgrade_vm_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances = infra.get_driver().get_database_instances()  # nao traz a instance do arbitro (mongodb)

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
        if auto_upgrade_vm is not None:
            auto_upgrade_vm.set_error()

        task.set_status_error('Error: {erro}.\n'
                              'To create task task_auto_upgrade_vm!\n'
                              'Please check error message and start new task.'.format(erro=erro))
        LOG.error('Error: {erro}.\n'
                  'To create task task_auto_upgrade_vm!\n'
                  'Please check error message and start new task.'.format(erro=erro))
