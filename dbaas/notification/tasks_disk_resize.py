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
from util import email_notifications, exec_remote_command_host


def zabbix_collect_used_disk(task):
    # TODO: Write tests for this method
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
        try:
            credentials = Credential.get_credentials(
                environment=environment, integration=integration
            )
        except IndexError:
            task.update_status_for(
                TaskHistory.STATUS_ERROR,
                'There is no Zabbix credential for {} environment.'.format(
                    environment
                )
            )
            return

        for database in Database.objects.filter(environment=environment):
            database_resized = False
            task.add_detail(
                message='Database: {}'.format(database.name), level=1
            )

            zabbix_provider = factory_for(
                databaseinfra=database.databaseinfra, credentials=credentials
            )
            metrics = ZabbixMetrics(
                zabbix_provider.api, zabbix_provider.main_clientgroup
            )

            driver = database.databaseinfra.get_driver()
            non_database_instances = driver.get_non_database_instances()

            for host in zabbix_provider.hosts:
                instance = database.databaseinfra.instances.filter(address=host.address).first()
                if instance in non_database_instances:
                    continue

                collected += 1
                task.add_detail(
                    message='Host: {} ({})'.format(
                        host.hostname, host.address
                    ), level=2
                )

                try:
                    zabbix_size = metrics.get_current_disk_data_size(host)
                    zabbix_used = metrics.get_current_disk_data_used(host)
                    zabbix_percentage = (zabbix_used * 100)/zabbix_size
                except ZabbixMetricsError as error:
                    problems += 1
                    task.add_detail(message='Error: {}'.format(error), level=3)
                    status = TaskHistory.STATUS_WARNING
                    continue

                task.add_detail(
                    message='Zabbix /data: {}% ({}kb/{}kb)'.format(
                        zabbix_percentage, zabbix_used, zabbix_size
                    ), level=3
                )

                current_percentage = zabbix_percentage
                current_used = zabbix_used
                current_size = zabbix_size
                if zabbix_percentage >= threshold_disk_resize:
                    current_percentage, current_used, current_size = host_mount_data_percentage(
                        address=host.address, task=task
                    )
                    if zabbix_percentage > current_percentage:
                        problems += 1
                        status = TaskHistory.STATUS_WARNING
                        task.add_detail(
                            message='Error: Zabbix metrics not updated',
                            level=4
                        )

                size_metadata = database.databaseinfra.disk_offering.size_kb
                if has_difference_between(size_metadata, current_size):
                    problems += 1
                    task.add_detail(
                        message='Error: Disk size different: {}kb'.format(
                            size_metadata
                        ),
                        level=4
                    )
                    status = TaskHistory.STATUS_WARNING
                elif current_percentage >= threshold_disk_resize and \
                        database.disk_auto_resize and \
                        not database_resized:
                    try:
                        task_resize = disk_auto_resize(
                            database=database,
                            current_size=current_size,
                            usage_percentage=current_percentage
                        )
                        database_resized = True
                    except Exception as e:
                        problems += 1
                        status = TaskHistory.STATUS_WARNING
                        task.add_detail(
                            message='Error: Could not do resize. {}'.format(e),
                            level=4
                        )
                    else:
                        resizes += 1
                        task.add_detail(
                            message='Executing Resize... Task: {}'.format(
                                task_resize.id
                            ), level=4
                        )

                if not update_disk(
                    database=database, address=host.address, task=task,
                    total_size=current_size, used_size=current_used
                ):
                    problems += 1
                    status = TaskHistory.STATUS_WARNING

            zabbix_provider.logout()

    details = 'Collected: {} | Resize: {} | Problems: {}'.format(
        collected, resizes, problems
    )
    task.update_status_for(status=status, details=details)


def update_disk(database, address, total_size, used_size, task):
    try:
        volume = database.update_host_disk_used_size(
            host_address=address,
            used_size_kb=used_size,
            total_size_kb=total_size
        )
        if not volume:
            raise EnvironmentError(
                'Instance {} do not have disk'.format(address)
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
        message='Used disk size updated. NFS: {}'.format(volume.identifier),
        level=3
    )
    return True


def disk_auto_resize(database, current_size, usage_percentage):
    from notification.tasks import TaskRegister

    disk = DiskOffering.first_greater_than(current_size + 1024)

    if disk > DiskOffering.last_offering_available_for_auto_resize():
        raise DiskOfferingMaxAutoResize()

    if database.is_being_used_elsewhere():
        raise BusyDatabaseError("")

    user = AccountUser.objects.get(username='admin')

    task = TaskRegister.database_disk_resize(
        database=database,
        user=user,
        disk_offering=disk,
        task_name='database_disk_auto_resize',
        register_user=False
    )

    email_notifications.disk_resize_notification(
        database=database, new_disk=disk, usage_percentage=usage_percentage
    )

    return task


def host_mount_data_percentage(address, task):
    host = Host.objects.filter(address=address).first()

    output_message = {}
    command_status = exec_remote_command_host(
        host, 'df -hk | grep /data', output_message
    )

    if command_status != 0:
        task.add_detail(
            message='Could not load mount size: {}'.format(output_message),
            level=4
        )
        return None, None, None

    values = output_message['stdout'][0].strip().split()
    values = {
        'total': int(values[0]),
        'used': int(values[1]),
        'free': int(values[2]),
        'percentage': int(values[3].replace('%', ''))
    }

    task.add_detail(
        message='Mount /data: {}% ({}kb/{}kb)'.format(
            values['percentage'], values['used'], values['total']
        ),
        level=3
    )

    return values['percentage'], values['used'], values['total']


def has_difference_between(metadata, collected):
    threshold = Configuration.get_by_name_as_float(
        "threshold_disk_size_difference", default=1.0
    )

    difference = (metadata * threshold)/100
    max_value = metadata + difference
    min_value = metadata - difference

    return collected > max_value or collected < min_value
