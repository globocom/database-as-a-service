# -*- coding: utf-8 -*-
from logging import getLogger
from datetime import datetime, date, timedelta
from time import sleep, strftime
from dbaas.celery import app
from dbaas_credentials.models import CredentialType
from drivers.errors import ConnectionError
from notification.models import TaskHistory
from physical.models import DatabaseInfra, Environment, Volume
from system.models import Configuration
from util.decorators import only_one
from workflow.steps.util.volume_provider import VolumeProviderBase
from models import Snapshot, BackupGroup
from util import (get_worker_name, get_credentials_for,
                  GetCredentialException)

LOG = getLogger(__name__)


def set_backup_error(databaseinfra, snapshot, errormsg):
    LOG.error(errormsg)
    snapshot.set_error(errormsg)
    register_backup_dbmonitor(databaseinfra, snapshot)


def register_backup_dbmonitor(databaseinfra, snapshot):
    try:
        from dbaas_dbmonitor.provider import DBMonitorProvider
        DBMonitorProvider().register_backup(
            databaseinfra=databaseinfra,
            start_at=snapshot.start_at,
            end_at=snapshot.end_at,
            size=snapshot.size,
            status=snapshot.status,
            type=snapshot.type,
            error=snapshot.error
        )
    except Exception as e:
        LOG.error("Error register backup on DBMonitor {}".format(e))


def mysql_binlog_save(client, instance):
    try:
        client.query('show master status')
        r = client.store_result()
        row = r.fetch_row(maxrows=0, how=1)
        binlog_file = row[0]['File']
        binlog_pos = row[0]['Position']

        client.query("show variables like 'datadir'")
        r = client.store_result()
        row = r.fetch_row(maxrows=0, how=1)
        datadir = row[0]['Value']

        command = ('echo "master=%s;position=%s" > '
                   '%smysql_binlog_master_file_pos && sync') % (
            binlog_file, binlog_pos, datadir
        )

        instance.hostname.ssh.run_script(command)
    except Exception as e:
        LOG.error(
            "Error saving mysql master binlog file and position: {}".format(e))


def lock_instance(driver, instance, client):
    try:
        LOG.debug('Locking instance {}'.format(instance))
        driver.lock_database(client)
        LOG.debug('Instance {} is locked'.format(instance))
        return True
    except Exception as e:
        LOG.warning('Could not lock {} - {}'.format(instance, e))
        return False


def unlock_instance(driver, instance, client):
    try:
        LOG.debug('Unlocking instance {}'.format(instance))
        driver.unlock_database(client)
        LOG.debug('Instance {} is unlocked'.format(instance))
        return True
    except Exception as e:
        LOG.warning('Could not unlock {} - {}'.format(instance, e))
        return False


def make_instance_snapshot_backup(instance, error, group,
                                  provider_class=VolumeProviderBase,
                                  target_volume=None,
                                  current_hour=None):
    LOG.info("Make instance backup for {}".format(instance))
    provider = provider_class(instance)
    infra = instance.databaseinfra
    database = infra.databases.first()

    snapshot = Snapshot.create(
        instance, group, target_volume or provider.volume
    )

    snapshot_final_status = Snapshot.SUCCESS
    locked = None
    driver = infra.get_driver()
    client = None
    try:
        client = driver.get_client(instance)
        locked = lock_instance(driver, instance, client)
        if not locked:
            snapshot_final_status = Snapshot.WARNING

        if 'MySQL' in type(driver).__name__:
            mysql_binlog_save(client, instance)

        current_time = datetime.now()
        has_snapshot = Snapshot.objects.filter(
            status=Snapshot.WARNING,
            instance=instance,
            end_at__year=current_time.year,
            end_at__month=current_time.month,
            end_at__day=current_time.day
        )
        backup_hour_list = Configuration.get_by_name_as_list(
            'make_database_backup_hour'
            )
        if (snapshot_final_status == Snapshot.WARNING and has_snapshot):
            if str(current_hour) in backup_hour_list:
                raise Exception(
                    "Backup with WARNING already created today."
                    )
        else:
            response = provider.take_snapshot()
            snapshot.done(response)
            snapshot.save()
    except Exception as e:
        errormsg = "Error creating snapshot: {}".format(e)
        error['errormsg'] = errormsg
        set_backup_error(infra, snapshot, errormsg)
        return snapshot
    finally:
        unlock_instance(driver, instance, client)

    if not snapshot.size:
        command = "du -sb /data/.snapshot/%s | awk '{print $1}'" % (
            snapshot.snapshot_name
        )
        try:
            output = instance.hostname.ssh.run_script(command)
            size = int(output['stdout'][0])
            snapshot.size = size
        except Exception as e:
            snapshot.size = 0
            LOG.error("Error exec remote command {}".format(e))

    backup_path = database.backup_path
    if backup_path:
        now = datetime.now()
        target_path = "{}/{}/{}/{}/{}".format(
            backup_path,
            now.strftime("%Y_%m_%d"),
            instance.hostname.hostname.split('.')[0],
            now.strftime("%Y%m%d%H%M%S"),
            infra.name
        )
        snapshot_path = "/data/.snapshot/{}/data/".format(
            snapshot.snapshot_name
        )
        command = """
        if [ -d "{backup_path}" ]
        then
            rm -rf {backup_path}/20[0-9][0-9]_[0-1][0-9]_[0-3][0-9] &
            mkdir -p {target_path}
            cp -r {snapshot_path} {target_path} &
        fi
        """.format(backup_path=backup_path,
                   target_path=target_path,
                   snapshot_path=snapshot_path)
        try:
            instance.hostname.ssh.run_script(command)
        except Exception as e:
            LOG.error("Error exec remote command {}".format(e))

    snapshot.status = snapshot_final_status
    snapshot.end_at = datetime.now()
    snapshot.save()
    register_backup_dbmonitor(infra, snapshot)

    return snapshot


@app.task(bind=True)
@only_one(key="updatesslkey")
def update_ssl(self):
    from account.models import User
    from notification.tasks import TaskRegister
    from logical.models import Database
    LOG.info("Updating ssl certificates")
    worker_name = get_worker_name()
    user = User.objects.get(username="admin")
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, user=None
    )
    task_history.relevance = TaskHistory.RELEVANCE_ERROR
    for db in Database.objects.filter(
        databaseinfra__ssl_expire_at__gte=(datetime.date.now() -
                                           timedelta(days=30))
    ):
        TaskRegister.update_ssl(db, user)


@app.task(bind=True)
@only_one(key="makedatabasebackupkey", timeout=60*60*2)
def make_databases_backup(self):
    LOG.info("Making databases backups")
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, user=None
    )
    task_history.relevance = TaskHistory.RELEVANCE_ERROR

    backup_group_interval = Configuration.get_by_name_as_int(
        'backup_group_interval', default=1
    )
    waiting_msg = "\nWaiting {} minute(s) to start the next backup group".format(
        backup_group_interval
    )
    status = TaskHistory.STATUS_SUCCESS
    environments = Environment.objects.all()
    prod_envs = Environment.prod_envs()
    dev_envs = Environment.dev_envs()
    env_names_order = list(prod_envs) + list(dev_envs)
    if not env_names_order:
        env_names_order = [env.name for env in environments]

    current_time = datetime.now()
    current_hour = current_time.hour

    # Get all infras with a backup today until the current hour
    infras_with_backup_today = DatabaseInfra.objects.filter(
        instances__backup_instance__status=Snapshot.SUCCESS,
        backup_hour__lt=current_hour,
        plan__has_persistence=True,
        instances__backup_instance__end_at__year=current_time.year,
        instances__backup_instance__end_at__month=current_time.month,
        instances__backup_instance__end_at__day=current_time.day).distinct()

    # Get all infras with pending backups based on infras_with_backup_today
    infras_pending_backup = DatabaseInfra.objects.filter(
        backup_hour__lt=current_hour,
        plan__has_persistence=True,
    ).exclude(pk__in=[infra.pk for infra in infras_with_backup_today])

    # Get all infras to backup on the current hour
    infras_current_hour = DatabaseInfra.objects.filter(
        plan__has_persistence=True,
        backup_hour=current_time.hour
    )

    # Merging pending and current infras to backup list
    infras = infras_current_hour | infras_pending_backup

    for env_name in env_names_order:
        try:
            env = environments.get(name=env_name)
        except Environment.DoesNotExist:
            continue

        msg = '\nStarting Backup for env {}'.format(env.name)
        task_history.update_details(persist=True, details=msg)
        databaseinfras_by_env = infras.filter(environment=env)
        error = {}
        backup_number = 0
        backups_per_group = len(infras) / 12
        for infra in databaseinfras_by_env:
            if not infra.databases.first():
                continue

            if backups_per_group > 0:
                if backup_number < backups_per_group:
                    backup_number += 1
                else:
                    backup_number = 0
                    task_history.update_details(waiting_msg, True)
                    sleep(backup_group_interval*60)

            group = BackupGroup()
            group.save()

            for instance in infra.instances.filter(read_only=False):
                try:
                    driver = instance.databaseinfra.get_driver()
                    is_eligible = driver.check_instance_is_eligible_for_backup(
                        instance
                    )
                    if not is_eligible:
                        LOG.info(
                            'Instance {} is not eligible for backup'.format(
                                instance
                            )
                        )
                        continue
                except Exception as e:
                    status = TaskHistory.STATUS_ERROR
                    msg = "Backup for %s was unsuccessful. Error: %s" % (
                        str(instance), str(e))
                    LOG.error(msg)

                time_now = str(strftime("%m/%d/%Y %H:%M:%S"))
                start_msg = "\n{} - Starting backup for {} ...".format(
                    time_now, instance
                )
                task_history.update_details(persist=True, details=start_msg)
                try:
                    snapshot = make_instance_snapshot_backup(
                        instance=instance, error=error, group=group,
                        current_hour=current_hour
                    )
                    if snapshot and snapshot.was_successful:
                        msg = "Backup for %s was successful" % (str(instance))
                        LOG.info(msg)
                    elif snapshot and snapshot.was_error:
                        status = TaskHistory.STATUS_ERROR
                        msg = "Backup for %s was unsuccessful. Error: %s" % (
                            str(instance), error['errormsg'])
                        LOG.error(msg)
                    else:
                        status = TaskHistory.STATUS_WARNING
                        msg = "Backup for %s has warning" % (str(instance))
                        LOG.info(msg)
                    LOG.info(msg)
                except Exception as e:
                    status = TaskHistory.STATUS_ERROR
                    msg = "Backup for %s was unsuccessful. Error: %s" % (
                        str(instance), str(e))
                    LOG.error(msg)

                time_now = str(strftime("%m/%d/%Y %H:%M:%S"))
                msg = "\n{} - {}".format(time_now, msg)
                task_history.update_details(persist=True, details=msg)

    task_history.update_status_for(status, details="\nBackup finished")

    return


def remove_snapshot_backup(snapshot, provider=None, force=0, msgs=None):
    snapshots = snapshot.group.backups.all() if snapshot.group else [snapshot]
    for snapshot in snapshots:

        if snapshot.purge_at:
            continue

        LOG.info("Removing backup for {}".format(snapshot))

        if not provider:
            provider = VolumeProviderBase(snapshot.instance)
        removed = provider.delete_snapshot(snapshot, force=force)
        if removed:
            snapshot.purge_at = datetime.now()
            snapshot.save()
            msg = "Backup {} removed".format(snapshot)
            LOG.info(msg)
            if msgs is not None:
                msgs.append(msg)

    return


@app.task(bind=True)
@only_one(key="removedatabaseoldbackupkey")
def remove_database_old_backups(self):
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, user=None
    )
    task_history.relevance = TaskHistory.RELEVANCE_WARNING

    snapshots = []
    msgs = []
    for env in Environment.objects.all():
        try:
            snapshots += get_snapshots_by_env(env)
        except GetCredentialException as ex:
            status = TaskHistory.STATUS_ERROR
            LOG.error(str(ex))
            msgs.append(str(ex))
            task_history.update_status_for(
                status, details="\n".join(msgs))
            return

    status = TaskHistory.STATUS_SUCCESS
    if len(snapshots) == 0:
        msgs.append("There is no snapshot to purge")

    for snapshot in snapshots:
        try:
            remove_snapshot_backup(snapshot=snapshot, msgs=msgs)
        except Exception as e:
            msg = "Error removing backup {}. Error: {}".format(snapshot, e)
            status = TaskHistory.STATUS_ERROR
            LOG.error(msg)
            msgs.append(msg)
    task_history.update_status_for(status, details="\n".join(msgs))
    return


def get_snapshots_by_env(env):
    credential = get_credentials_for(env, CredentialType.VOLUME_PROVIDER)
    retention_days = credential.get_parameter_by_name('retention_days')
    if retention_days:
        retention_days = int(retention_days)
    else:
        retention_days = Configuration.get_by_name_as_int(
            'backup_retention_days'
        )

    backup_time_dt = date.today() - timedelta(days=retention_days)
    return Snapshot.objects.filter(
        start_at__lte=backup_time_dt,
        purge_at__isnull=True,
        instance__isnull=False,
        snapshopt_id__isnull=False,
        instance__databaseinfra__environment=env
    )


@app.task(bind=True)
@only_one(key="purge_unused_exports")
def purge_unused_exports_task(self):
    from notification.tasks import TaskRegister
    task = TaskRegister.purge_unused_exports()

    task = TaskHistory.register(
        request=self.request, worker_name=get_worker_name(), task_history=task
    )

    task.add_detail('Getting all inactive exports without snapshots')
    if purge_unused_exports(task):
        task.set_status_success('Done')
    else:
        task.set_status_error('Error')


def purge_unused_exports(task=None):
    success = True
    for volume in Volume.objects.filter(is_active=False):
        if volume.backups.filter(purge_at=None).exists():
            continue
        if task:
            task.add_detail('Removing: {}'.format(volume), level=2)

        provider = VolumeProviderBase(volume.host.instances.first())
        try:
            if task:
                task.add_detail('Add access...', level=3)
            provider.add_access(volume, volume.host)

            if task:
                task.add_detail('Clean up...', level=3)
            provider.clean_up(volume)

            if task:
                task.add_detail('Detach disk...', level=3)
            provider.detach_disk(volume)

            if task:
                task.add_detail('Destroy volume...', level=3)
            provider.destroy_volume(volume)
        except Exception as e:
            success = False
            LOG.info('Error removing {} - {}'.format(volume, e))
            if task:
                task.add_detail('Error: {}'.format(e), level=4)
        else:
            if task:
                task.add_detail('Success', level=4)

    return success


def _get_backup_instance(database, task):
    eligibles = []

    task.add_detail('Searching for backup eligible instances...')
    driver = database.infra.get_driver()
    instances = database.infra.instances.filter(read_only=False)
    for instance in instances:
        try:
            task.add_detail('Instance: {}'.format(instance), level=1)
            if driver.check_instance_is_eligible_for_backup(instance):
                task.add_detail('Is Eligible', level=2)
                eligibles.append(instance)
            else:
                task.add_detail('Not eligible', level=2)
        except ConnectionError:
            task.add_detail('Connection error', level=2)
            continue

    if not eligibles:
        task.add_detail('No instance eligible for backup', level=1)

    return eligibles


def _check_snapshot_limit(instances, task):
    for instance in instances:
        task.add_detail('\nChecking older backups for {}...'.format(instance))
        limit = Configuration.get_by_name_as_int('backup_retention_days')
        snapshots_count = Snapshot.objects.filter(
            purge_at__isnull=True, instance=instance,
            snapshopt_id__isnull=False
        ).order_by('start_at').count()
        task.add_detail(
            'Current snapshot limit {}, used {}'.format(
                limit, snapshots_count
            ),
            level=1
        )


def _create_database_backup(instance, task, group):
    task.add_detail('\nStarting backup for {}...'.format(instance))

    error = {}
    try:
        snapshot = make_instance_snapshot_backup(
            instance=instance, error=error, group=group
        )
    except Exception as e:
        task.add_detail('\nError: {}'.format(e))
        return False

    if 'errormsg' in error:
        task.add_detail('\nError: {}'.format(error['errormsg']))
        return False

    return snapshot


@app.task(bind=True)
def make_database_backup(self, database, task):
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, task_history=task
    )

    if not database.pin_task(task):
        task.error_in_lock(database)
        return False

    task_history.add_detail('Starting database {} backup'.format(database))

    instances = _get_backup_instance(database, task)
    if not instances:
        task.set_status_error('Could not find eligible instances', database)
        return False

    _check_snapshot_limit(instances, task)

    group = BackupGroup()
    group.save()

    has_warning = False
    for instance in instances:
        snapshot = _create_database_backup(instance, task, group)

        if not snapshot:
            task.set_status_error(
                'Backup was unsuccessful in {}'.format(instance), database
            )
            return False

        snapshot.is_automatic = False
        snapshot.save()

        if not has_warning:
            has_warning = snapshot.has_warning

    if has_warning:
        task.set_status_warning('Backup was warning', database)
    else:
        task.set_status_success('Backup was successful', database)

    return True


@app.task(bind=True)
def remove_database_backup(self, task, snapshot):
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, task_history=task
    )

    task_history.add_detail('Removing {}'.format(snapshot))
    try:
        remove_snapshot_backup(snapshot, force=1)
    except Exception as e:
        task_history.add_detail('Error: {}'.format(e))
        task.set_status_error('Could not delete backup')
        return False
    else:
        task.set_status_success('Backup deleted with success')
        return True
