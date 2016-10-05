# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.core.exceptions import ObjectDoesNotExist
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from dbaas_zabbix.metrics import ZabbixMetrics
from dbaas_zabbix.errors import ZabbixMetricsError
from account.models import AccountUser
from physical.models import Environment, DiskOffering
from logical.models import Database
from system.models import Configuration
from .models import TaskHistory
from .tasks import database_disk_resize


def zabbix_collect_used_disk(task):
    status = TaskHistory.STATUS_SUCCESS
    threshold_disk_resize = Configuration.get_by_name_as_int(
        "threshold_disk_resize", default=80.0
    )
    collected = 0
    resizes = 0
    problems = 0

    integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
    for environment in Environment.objects.all():
        task.add_detail(
            'Execution for environment: {}'.format(environment.name)
        )
        credentials = Credential.get_credentials(
            environment=environment, integration=integration
        )

        for database in Database.objects.filter(environment=environment):
            task.add_detail(
                message='Database: {}'.format(database.name), level=1
            )

            zabbix_provider = factory_for(
                databaseinfra=database.databaseinfra, credentials=credentials
            )
            metrics = ZabbixMetrics(
                zabbix_provider.api, zabbix_provider.main_clientgroup
            )
            for host in zabbix_provider.hosts:
                collected += 1
                task.add_detail(
                    message='Host: {} ({})'.format(
                        host.hostname, host.address
                    ), level=2
                )

                try:
                    disk_size = metrics.get_current_disk_data_size(host)
                    disk_used = metrics.get_current_disk_data_used(host)
                    usage_percentage = (disk_used * 100)/disk_size
                except ZabbixMetricsError as error:
                    problems += 1
                    task.add_detail(message='Error: {}'.format(error), level=3)
                    status = TaskHistory.STATUS_WARNING
                    continue

                task.add_detail(
                    message='Usage: {}% ({}kb/{}kb)'.format(
                        usage_percentage, disk_used, disk_size
                    ), level=3
                )

                if usage_percentage >= threshold_disk_resize:
                    try:
                        task_resize = disk_auto_resize(
                            database=database, current_size=disk_size
                        )
                    except Exception as e:
                        problems += 1
                        status = TaskHistory.STATUS_WARNING
                        task.add_detail(
                            message='Could not do resize. {}'.format(e),
                            level=4
                        )
                    else:
                        resizes += 1
                        task.add_detail(
                            message='Executing Resize... Task: {}'.format(
                                task_resize.id
                            ), level=4
                        )

                if not update_used_kb(
                        database=database, address=host.address,
                        used_size=disk_used, task=task
                ):
                    problems += 1
                    status = TaskHistory.STATUS_WARNING

            zabbix_provider.logout()

    details = 'Collected: {} | Resize: {} | Problems: {}'.format(
        collected, resizes, problems
    )
    task.update_status_for(status=status, details=details)


def update_used_kb(database, address, used_size, task):
    try:
        nfsaas_host = database.update_host_disk_used_size(
            host_address=address, used_size_kb=used_size
        )
        if not nfsaas_host:
            raise EnvironmentError(
                'Instance {} do not have NFSaaS disk'.format(address)
            )

    except ObjectDoesNotExist:
        task.add_detail(
            message='{} not found for: {}'.format(address, database.name),
            level=3
        )
        return False
    except Exception as error:
        task.add_detail(
            message='Could not update disk size used: {}'.format(error),
            level=3
        )
        return False

    task.add_detail(
        message='Used disk size updated. NFS: {}'.format(
            nfsaas_host.nfsaas_path_host
        ), level=3
    )
    return True


def disk_auto_resize(database, current_size):
    disk = DiskOffering.first_greater_than(current_size + 1024)

    task = TaskHistory()
    task.task_name = "database_disk_auto_resize"
    task.task_status = task.STATUS_WAITING
    task.arguments = "Database name: {}".format(database.name)
    task.save()

    user = AccountUser.objects.get(username='admin')
    database_disk_resize.delay(
        database=database, disk_offering=disk, user=user, task_history=task
    )

    return task
