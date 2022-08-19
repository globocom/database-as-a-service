# -*- coding: utf-8 -*-
from __future__ import absolute_import

from account.models import AccountUser
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from dbaas_zabbix.errors import ZabbixMetricsError
from dbaas_zabbix.metrics import ZabbixMetrics
from logical.errors import BusyDatabaseError
from logical.models import Database
from physical.errors import DiskOfferingMaxAutoResize
from physical.models import Environment, DiskOffering
from physical.ssh import ScriptFailedException
from system.models import Configuration
from util import email_notifications
from notification.tasks_disk_resize import update_disk

from .models import TaskHistory


def zabbix_collect_used_disk(task):
    status = TaskHistory.STATUS_SUCCESS
    threshold_disk_resize = Configuration.get_by_name_as_int(
        "threshold_disk_resize", default=80.0
    )
    collected = 0
    resizes = 0
    problems = 0
    integration = CredentialType.objects.get(type=CredentialType.ZABBIX_READ_ONLY)
    environments = Environment.objects.all()

    # run validations for every environment
    collected, problems, resizes, status = execute_for_environments(
        environments, task, integration, collected, problems, resizes, status, threshold_disk_resize
    )

    details = "Collected: {} | Resize: {} | Problems: {}".format(
        collected, resizes, problems
    )
    task.update_status_for(status=status, details=details)


def execute_for_environments(environments, task, integration, collected, problems, resizes, status,
                             threshold_disk_resize):
    for environment in environments:
        task.add_detail("Execution for environment: {}".format(environment.name))

        # get credentials
        zabbix_credential, grafana_credential = find_credentials_for_environment(environment, integration, task)
        if zabbix_credential is None and grafana_credential is None:
            return

        project_domain = grafana_credential.get_parameter_by_name('project_domain')
        databases = Database.objects.filter(environment=environment)

        # execute for databases of this specific environment
        collected, problems, resizes, status = execute_for_databases(databases, task, zabbix_credential,
                                                                     project_domain, collected, problems, resizes,
                                                                     status, threshold_disk_resize)

    return collected, problems, resizes, status


def execute_for_databases(databases, task, zabbix_credential, project_domain, collected, problems, resizes, status,
                          threshold_disk_resize):
    if databases is not None:
        for database in databases:
            database_resized = False
            task.add_detail(message="Database: {}".format(database.name), level=1)

            # check if database is locked
            if check_locked_database(database, task):
                continue  # goes to next database because this is locked

            # get zabbix provider and metrics
            zabbix_provider, metrics = get_provider_and_metrics(database, zabbix_credential)

            driver = database.databaseinfra.get_driver()
            non_database_instances = driver.get_non_database_instances()

            # get hosts either from zabbix or infra
            hosts = get_hosts(zabbix_provider, database)

            # execute for hosts
            collected, problems, resizes, status, database_resized = execute_for_hosts(hosts, database,
                                                                                       non_database_instances, collected,
                                                                                       task, zabbix_provider,
                                                                                       project_domain, metrics, problems,
                                                                                       status, threshold_disk_resize,
                                                                                       resizes, database_resized)

            zabbix_provider.logout()
        return collected, problems, resizes, status


def execute_for_hosts(hosts, database, non_database_instances, collected, task, zabbix_provider, project_domain,
                      metrics, problems, status, threshold_disk_resize, resizes, database_resized):
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
        zabbix_size, zabbix_used, zabbix_percentage = get_zabbix_metrics_value(metrics, zabbix_host, host, task)
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

        current_percentage, current_used, current_size = check_treshold_for_data(
            current_percentage, current_used, current_size, zabbix_percentage, threshold_disk_resize, host, task
        )

        if zabbix_percentage > current_percentage:
            problems += 1
            status = TaskHistory.STATUS_WARNING
            task.add_detail(
                message="Error: Zabbix metrics not updated", level=4
            )

        problems, resizes, status, database_resized = check_size_differences(database, current_size, current_percentage,
                                                                             threshold_disk_resize, database_resized,
                                                                             problems, task, status, resizes)
        # update disk size info in DBaaS DB
        if not update_disk(
                database=database,
                address=host.address,
                task=task,
                total_size=current_size,
                used_size=current_used,
        ):
            problems += 1
            status = TaskHistory.STATUS_WARNING

    return collected, problems, resizes, status, database_resized


def check_size_differences(database, current_size, current_percentage, threshold_disk_resize, database_resized,
                           problems, task, status, resizes):
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
            # create the actual disk resize task
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

    return problems, resizes, status, database_resized


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


def find_credentials_for_environment(environment, integration, task):
    zabbix_credential = None
    grafana_credential = None
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


def get_provider_and_metrics(database, zabbix_credential):
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


def get_zabbix_metrics_value(metrics, zabbix_host, host, task):
    zabbix_size = None
    zabbix_used = None
    zabbix_percentage = None
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


def check_treshold_for_data(current_percentage, current_used, current_size, zabbix_percentage, threshold_disk_resize,
                            host, task):
    if zabbix_percentage >= threshold_disk_resize:
        (
            current_percentage,
            current_used,
            current_size,
        ) = host_mount_data_percentage(host=host, task=task)

    return current_percentage, current_used, current_size
