from django.db.models import Q
from physical.models import DatabaseInfra, Instance
from util import slugify, gen_infra_names, get_vm_name
from util.providers import get_deploy_settings, get_deploy_instances
from workflow.workflow import steps_for_instances, rollback_for_instances_full
from models import DatabaseCreate
from logical.forms.database import DatabaseForm


def get_or_create_infra(base_name, plan, environment, backup_hour=None,
                        maintenance_window=None, maintenance_day=None,
                        retry_from=None):
    if retry_from:
        infra = retry_from.infra
        base_name['infra'] = infra.name
        base_name['name_prefix'] = infra.name_prefix
        base_name['name_stamp'] = infra.name_stamp
    else:
        random_backup_hour, random_maintenance_hour, random_maintenance_day = (
            DatabaseForm.randomize_backup_and_maintenance_hour()
        )
        infra = DatabaseInfra()
        infra.name = base_name['infra']
        infra.name_prefix = base_name['name_prefix']
        infra.name_stamp = base_name['name_stamp']
        infra.last_vm_created = 0
        infra.engine = plan.engine
        infra.plan = plan
        infra.disk_offering = plan.disk_offering
        infra.environment = environment
        infra.capacity = 1
        infra.per_database_size_mbytes = plan.max_db_size
        infra.backup_hour = backup_hour or random_backup_hour
        infra.maintenance_window = (
            maintenance_window or random_maintenance_hour
        )
        infra.maintenance_day = maintenance_day or random_maintenance_day
        infra.engine_patch = plan.engine.default_engine_patch
        infra.save()

        driver = infra.get_driver()
        user, password, key = driver.build_new_infra_auth()
        infra.user = user
        infra.password = password
        infra.database_key = key
        infra.save()

    return infra


def get_instances_for(infra, topology_path):
    instances = []
    group_instances = get_deploy_instances(topology_path)
    for count, group in enumerate(group_instances):
        for instance_type in group:
            instance_name = get_vm_name(
                infra.name_prefix, infra.name_stamp, count + 1
            )

            try:
                instance = infra.instances.get(
                    Q(hostname__hostname__startswith=instance_name) |
                    Q(dns__startswith=instance_name),
                    # port=instance_type.port,
                )
            except Instance.DoesNotExist:
                instance = Instance()
                instance.dns = instance_name
                instance.databaseinfra = infra

                instance.port = instance_type.port
                instance.instance_type = instance_type.instance_type

            instance.vm_name = instance.dns
            instances.append(instance)

    return instances


def rollback_create(maintenance, task, user=None, instances=None):
    topology_path = maintenance.plan.replication_topology.class_path
    steps = get_deploy_settings(topology_path)

    if instances is None:
        instances = get_instances_for(maintenance.infra, topology_path)

    maintenance.id = None
    maintenance.user = user.username if user else task.user
    maintenance.task = task
    maintenance.save()

    if rollback_for_instances_full(
        steps, instances, task, maintenance.get_current_step,
        maintenance.update_step,
    ):
        maintenance.set_rollback()
        task.set_status_success('Rollback executed with success')

        infra = maintenance.infra
        infra.delete()
    else:
        maintenance.set_error()
        task.set_status_error(
            'Could not do rollback\n'
            'Please check error message and do retry'
        )
