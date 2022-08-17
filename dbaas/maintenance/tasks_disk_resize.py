# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.core.exceptions import ObjectDoesNotExist
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from dbaas_zabbix.metrics import ZabbixMetrics
from dbaas_zabbix.errors import ZabbixMetricsError
from account.models import AccountUser
from physical.models import Environment, DiskOffering, Host
from physical.errors import DiskOfferingMaxAutoResize
from logical.errors import BusyDatabaseError
from logical.models import Database
from system.models import Configuration
from .models import TaskHistory
from util import email_notifications
from physical.ssh import ScriptFailedException


def zabbix_collect_used_disk(task):
    status = TaskHistory.STATUS_SUCCESS
    threshold_disk_resize = Configuration.get_by_name_as_int(
        "threshold_disk_resize", default=80.0
    )
    collected = 0
    resizes = 0
    problems = 0

    integration = CredentialType.objects.get(type=CredentialType.ZABBIX_READ_ONLY)
    for environment in Environment.objects.all():
        task.add_detail("Execution for environment: {}".format(environment.name))

        # get credentials
        zabbix_credential, grafana_credential = find_credentials_for_environment(environment, integration, task)
        if zabbix_credential is None or grafana_credential is None:
            return

        project_domain = grafana_credential.get_parameter_by_name('project_domain')

        for database in Database.objects.filter(environment=environment):
            database_resized = False
            task.add_detail(message="Database: {}".format(database.name), level=1)

            # check if database is locked
            if check_locked_database(database, task):
                continue

            # get zabbix provider and metrics
            zabbix_provider, metrics = get_provider_and_metrics(database, zabbix_credential)

            driver = database.databaseinfra.get_driver()
            non_database_instances = driver.get_non_database_instances()

            # get hosts either from zabbix or infra
            hosts = get_hosts(zabbix_provider, database)

            for host in hosts:
                # check if host is a database instance
                if not is_database_instance(database, non_database_instances, host):
                    continue

                collected += 1
                task.add_detail(
                    message="Host: {} ({})".format(host.hostname, host.address), level=2
                )

                # get zabbix hostname
                zabbix_host = get_zabbix_host(zabbix_provider, host, project_domain)

                # get zabbix metrics for comparisons
                zabbix_size, zabbix_used, zabbix_percentage = get_zabbix_metrics_values(metrics, zabbix_host, host, task)
                if zabbix_size is None and zabbix_used is None and zabbix_percentage is None:
                    problems += 1
                    status = TaskHistory.STATUS_WARNING
                    continue

                task.add_detail(
                    message="Zabbix /data: {}% ({}kb/{}kb)".format(
                        zabbix_percentage, zabbix_used, zabbix_size
                    ),
                    level=3,
                )

                current_percentage = zabbix_percentage
                current_used = zabbix_used
                current_size = zabbix_size

                current_percentage, current_used, current_size = check_treshhold_limit(
                    current_percentage, current_used, current_size, zabbix_percentage, threshold_disk_resize, host, task
                )

                if zabbix_percentage > current_percentage:
                    problems += 1
                    status = TaskHistory.STATUS_WARNING
                    task.add_detail(
                        message="Error: Zabbix metrics not updated", level=4
                    )

                size_metadata = database.databaseinfra.disk_offering.size_kb
                if has_difference_between(size_metadata, current_size):
                    problems += 1
                    task.add_detail(
                        message="Error: Disk size different: {}kb".format(
                            size_metadata
                        ),
                        level=4,
                    )
                    status = TaskHistory.STATUS_WARNING
                elif (
                    current_percentage >= threshold_disk_resize
                    and database.disk_auto_resize
                    and not database_resized
                ):
                    try:
                        task_resize = disk_auto_resize(
                            database=database,
                            current_size=size_metadata,
                            usage_percentage=current_percentage,
                        )
                        database_resized = True
                    except Exception as e:
                        problems += 1
                        status = TaskHistory.STATUS_WARNING
                        task.add_detail(
                            message="Error: Could not do resize. {}".format(e), level=4
                        )
                    else:
                        resizes += 1
                        task.add_detail(
                            message="Executing Resize... Task: {}".format(
                                task_resize.id
                            ),
                            level=4,
                        )

                if not update_disk(
                    database=database,
                    address=host.address,
                    task=task,
                    total_size=current_size,
                    used_size=current_used,
                ):
                    problems += 1
                    status = TaskHistory.STATUS_WARNING

            zabbix_provider.logout()

    details = "Collected: {} | Resize: {} | Problems: {}".format(
        collected, resizes, problems
    )
    task.update_status_for(status=status, details=details)


def update_disk(database, address, total_size, used_size, task):
    try:
        volume = database.update_host_disk_used_size(
            host_address=address, used_size_kb=used_size, total_size_kb=total_size
        )
        if not volume:
            raise EnvironmentError("Instance {} do not have disk".format(address))
    except ObjectDoesNotExist:
        task.add_detail(
            message="{} not found for: {}".format(address, database.name), level=3
        )
        return False
    except Exception as error:
        task.add_detail(
            message="Could not update disk size used: {}".format(error), level=3
        )
        return False

    task.add_detail(
        message="Used disk size updated. NFS: {}".format(volume.identifier), level=3
    )
    return True


def disk_auto_resize(database, current_size, usage_percentage):
    from notification.tasks import TaskRegister

    disk = DiskOffering.first_greater_than(current_size + 1024, database.environment)

    if disk > DiskOffering.last_offering_available_for_auto_resize(
        environment=database.environment
    ):
        raise DiskOfferingMaxAutoResize()

    if database.is_being_used_elsewhere():
        raise BusyDatabaseError("")

    user = AccountUser.objects.get(username="admin")

    task = TaskRegister.database_disk_resize(
        database=database,
        user=user,
        disk_offering=disk,
        task_name="database_disk_auto_resize",
        register_user=False,
    )

    email_notifications.disk_resize_notification(
        database=database, new_disk=disk, usage_percentage=usage_percentage
    )

    return task


def host_mount_data_percentage(host, task):
    try:
        output = host.ssh.run_script("df -hk | grep /data")
    except ScriptFailedException as err:
        task.add_detail(
            message="Could not load mount size: {}".format(str(err)), level=4
        )
        return None, None, None

    values = output["stdout"][0].strip().split()

    i = 0 if host.is_ol6 else 1

    rvalues = {
        "total": int(values[i]),
        "used": int(values[i + 1]),
        "free": int(values[i + 2]),
        "percentage": int(values[i + 3].replace("%", "")),
    }

    task.add_detail(
        message="Mount /data: {}% ({}kb/{}kb)".format(
            rvalues["percentage"], rvalues["used"], rvalues["total"]
        ),
        level=3,
    )
    return rvalues["percentage"], rvalues["used"], rvalues["total"]


def has_difference_between(metadata, collected):
    threshold = Configuration.get_by_name_as_float(
        "threshold_disk_size_difference", default=1.0
    )

    difference = (metadata * threshold) / 100
    max_value = metadata + difference
    min_value = metadata - difference

    return collected > max_value or collected < min_value


def find_credentials_for_environment(environment, integration, task) -> tuple:
    zabbix_credential, grafana_credential = None
    try:
        zabbix_credential = Credential.get_credentials(
            environment=environment, integration=integration
        )
    except IndexError:
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            "There is no Zabbix credential for {} environment.".format(environment),
        )

    try:
        grafana_credential = Credential.get_credentials(
            environment=environment,
            integration=CredentialType.objects.get(type=CredentialType.GRAFANA)
        )
    except IndexError:
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            "There is no Grafana credential for {} environment.".format(environment),
        )

    return zabbix_credential, grafana_credential


def check_locked_database(database, task):
    if database.is_locked:
        message = ("Skip updating disk used size for database {}. "
                   "It is used by another task."
                   ).format(database)
        task.add_detail(message, level=2)
        return True
    return False


def get_provider_and_metrics(database, zabbix_credential) -> tuple:
    zabbix_provider = factory_for(
        databaseinfra=database.databaseinfra, credentials=zabbix_credential
    )
    metrics = ZabbixMetrics(
        zabbix_provider.api, zabbix_provider.main_clientgroup
    )

    return zabbix_provider, metrics


def get_hosts(zabbix_provider, database):
    if zabbix_provider.using_agent:
        return list({instance.hostname for instance in database.databaseinfra.instances.all()})
    else:
        return zabbix_provider.hosts


def is_database_instance(database, non_database_instances, host):
    instance = database.databaseinfra.instances.filter(
        address=host.address
    ).first()
    return instance not in non_database_instances


def get_zabbix_host(zabbix_provider, host, project_domain):
    if zabbix_provider.using_agent:
        return '{}.{}'.format(host.hostname.split('.')[0], project_domain)
    else:
        return host.hostname


def get_zabbix_metrics_values(metrics, zabbix_host, host, task) -> tuple:
    zabbix_size, zabbix_used, zabbix_percentage = None
    try:
        zabbix_size = metrics.get_current_disk_data_size(zabbix_host)
        zabbix_used = metrics.get_current_disk_data_used(zabbix_host)
        zabbix_percentage = (zabbix_used * 100) / zabbix_size
    except ZabbixMetricsError as error:
        ret = host_mount_data_percentage(host, task)
        if ret != (None, None, None):
            zabbix_percentage, zabbix_used, zabbix_size = ret
        else:
            task.add_detail(message="Error: {}".format(error), level=3)

    return zabbix_size, zabbix_used, zabbix_percentage


def check_treshhold_limit(current_percentage, current_used, current_size, zabbix_percentage, threshold_disk_resize, host, task) -> tuple:
    if zabbix_percentage >= threshold_disk_resize:
        (
            current_percentage,
            current_used,
            current_size,
        ) = host_mount_data_percentage(host=host, task=task)

    return current_percentage, current_used, current_size
