from datetime import datetime
from dbaas.celery import app
import models
import logging

from maintenance.tasks_disk_resize import find_zabbix_and_grafana_credentials_for_environment, go_through_databases
from notification.models import TaskHistory
from system.models import Configuration
from dbaas_credentials.models import CredentialType
from util import get_worker_name, \
    build_context_script, get_dict_lines
from util.decorators import only_one
from registered_functions.functools import get_function
from util.task_register import TaskRegisterBase
from workflow.steps.util.dns import ChangeTTLTo5Minutes, ChangeTTLTo3Hours
from workflow.steps.util.db_monitor import DisableMonitoring, EnableMonitoring
from workflow.steps.util.zabbix import DisableAlarms, EnableAlarms
from workflow.workflow import steps_for_instances

LOG = logging.getLogger(__name__)


@app.task(bind=True)
def execute_scheduled_maintenance(self, maintenance_id):
    LOG.debug("Maintenance id: {}".format(maintenance_id))
    maintenance = models.Maintenance.objects.get(id=maintenance_id)
    models.Maintenance.objects.filter(id=maintenance_id).update(
        status=maintenance.RUNNING, started_at=datetime.now()
    )
    LOG.info("Maintenance {} is RUNNING".format(maintenance,))

    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name
    )
    task_history.relevance = TaskHistory.RELEVANCE_CRITICAL
    LOG.info("id: {} | task: {} | kwargs: {} | args: {}".format(
        self.request.id, self.request.task,
        self.request.kwargs, str(self.request.args)
    ))
    task_history.update_details(
        persist=True, details="Executing Maintenance: {}".format(maintenance)
    )
    for hm in models.HostMaintenance.objects.filter(maintenance=maintenance):
        # main_output = {}
        hm.status = hm.RUNNING
        hm.started_at = datetime.now()
        hm.save()
        if hm.host is None:
            hm.status = hm.UNAVAILABLEHOST
            hm.finished_at = datetime.now()
            hm.save()
            continue

        host = hm.host
        update_task = "\nRunning Maintenance on {}".format(host)

        if maintenance.disable_alarms:
            disable_alarms(hm.host)

        param_dict = {}
        params = models.MaintenanceParameters.objects.filter(
            maintenance=maintenance
        )
        for param in params:
            param_function = get_function(param.function_name)
            param_dict[param.parameter_name] = param_function(host.id)

        main_script = build_context_script(param_dict, maintenance.main_script)
        main_output = host.ssh.run_script(
            script=main_script,
            raise_if_error=False
        )

        if main_output['exit_code'] == 0:
            hm.status = hm.SUCCESS
        else:
            if maintenance.rollback_script:
                hm.status = hm.ROLLBACK
                hm.save()

                rollback_script = build_context_script(
                    param_dict, maintenance.rollback_script
                )
                rollback_output = host.ssh.run_script(
                    script=rollback_script,
                    raise_if_error=False
                )

                if rollback_output['exit_code'] == 0:
                    hm.status = hm.ROLLBACK_SUCCESS
                else:
                    hm.status = hm.ROLLBACK_ERROR

                hm.rollback_log = get_dict_lines(rollback_output)

            else:
                hm.status = hm.ERROR

        if maintenance.disable_alarms:
            enable_alarms(hm.host)

        update_task += "...status: {}".format(hm.status)

        task_history.update_details(persist=True, details=update_task)

        hm.main_log = get_dict_lines(main_output)
        hm.finished_at = datetime.now()
        hm.save()

    models.Maintenance.objects.filter(id=maintenance_id).update(
        status=maintenance.FINISHED, finished_at=datetime.now()
    )
    task_history.update_status_for(
        TaskHistory.STATUS_SUCCESS, details='Maintenance executed succesfully'
    )
    LOG.info("Maintenance: {} has FINISHED".format(maintenance))


def disable_alarms(host):
    for instance in host.instances.all():
        DisableMonitoring(instance).do()
        DisableAlarms(instance).do()


def enable_alarms(host):
    for instance in host.instances.all():
        EnableMonitoring(instance).do()
        EnableAlarms(instance).do()


def region_migration_prepare(infra):
    instance = infra.instances.first()
    ChangeTTLTo5Minutes(instance).do()


def region_migration_finish(infra):
    instance = infra.instances.first()
    ChangeTTLTo3Hours(instance).do()


@app.task(bind=True)
def region_migration_start(self, infra, instances, since_step=None):
    steps = [{
        'Disable monitoring and alarms': (
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.db_monitor.DisableMonitoring',
        )}, {
        'Stopping infra': (
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.database.CheckIsDown',
        )}, {
        'Creating new virtual machine': (
            'workflow.steps.util.vm.MigrationCreateNewVM',
        )}, {
        'Creating new infra': (
            'workflow.steps.util.vm.MigrationWaitingBeReady',
            'workflow.steps.util.infra.MigrationCreateInstanceOldCode',
            'workflow.steps.util.disk.MigrationCreateExport',
        )}, {
        'Configuring new infra': (
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationMigration',
            'workflow.steps.util.plan.ConfigureMigration',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
        )}, {
        'Preparing new environment': (
            'workflow.steps.util.disk.AddDiskPermissionsOldest',
            'workflow.steps.util.disk.MountOldestExportMigration',
            'workflow.steps.util.disk.CopyDataBetweenExportsMigration',
            'workflow.steps.util.disk.FilePermissionsMigration',
            'workflow.steps.util.disk.UnmountNewerExportMigration',
            'workflow.steps.util.vm.ChangeInstanceHost',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.infra.OfferingMigration',
            'workflow.steps.util.infra.UpdateMigrateEnvironment',
            'workflow.steps.util.infra.UpdateMigratePlan',
        )}, {
        'Starting new infra': (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.metric_collector.RestartTelegraf',
        )}, {
        'Enabling access': (
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.acl.ReplicateAclsMigration',
        )}, {
        'Destroying old infra': (
            'workflow.steps.util.disk.DisableOldestExportMigration',
            'workflow.steps.util.disk.DiskUpdateHost',
            'workflow.steps.util.vm.RemoveHostMigration',
        )}, {
        'Enabling monitoring and alarms': (
            'workflow.steps.util.db_monitor.EnableMonitoring',
            'workflow.steps.util.zabbix.CreateAlarms',
        )}, {
        'Restart replication': (
            'workflow.steps.util.database.SetSlavesMigration',
        )
    }]

    task = TaskHistory()
    task.task_id = self.request.id
    task.task_name = "migrating_zone"
    task.task_status = TaskHistory.STATUS_RUNNING
    task.context = {'infra': infra, 'instances': instances}
    task.arguments = {'infra': infra, 'instances': instances}
    task.user = 'admin'
    task.save()

    if steps_for_instances(steps, instances, task, since_step=since_step):
        task.set_status_success('Region migrated with success')
    else:
        task.set_status_error('Could not migrate region')

    database = infra.databases.first()
    database.environment = infra.environment
    database.save()


@app.task(bind=True)
def restore_database(self, database, task, snapshot, user, retry_from=None):
    task = TaskHistory.register(request=self.request, task_history=task, user=user, worker_name=get_worker_name())

    from backup.models import Snapshot
    snapshot = Snapshot.objects.get(id=snapshot)

    from tasks_restore_backup import restore_snapshot
    restore_snapshot(database, snapshot.group, task, retry_from)


@app.task(bind=True)
def upgrade_disk_type_database(self, database, new_disk_type_upgrade, task, user, retry_from=None):
    task = TaskHistory.register(request=self.request, task_history=task, user=user, worker_name=get_worker_name())

    from task_upgrade_type_disk import task_upgrade_disk_type
    task_upgrade_disk_type(database, new_disk_type_upgrade, task, retry_from)


@app.task(bind=True)
def start_database_vm(self, database, task, user, retry_from=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=user,
        worker_name=get_worker_name()
    )

    from task_start_database_vm import task_start_database_vm
    task_start_database_vm(database, task, retry_from)


@app.task(bind=True)
def stop_database_vm(self, database, task, user, retry_from=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=user,
        worker_name=get_worker_name()
    )

    from task_stop_database_vm import task_stop_database_vm
    task_stop_database_vm(database, task, retry_from)

@app.task(bind=True)
def auto_upgrade_database_vm_offering(self, database, task, user, retry_from=None, resize_target=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=user,
        worker_name=get_worker_name()
    )

    from task_auto_upgrade_vm_offering import task_auto_upgrade_vm_offering
    task_auto_upgrade_vm_offering(database, task, retry_from, resize_target)


@app.task(bind=True)
def configure_db_params(self, database, task, user, retry_from=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=user,
        worker_name=get_worker_name()
    )

    from task_configure_db_params import task_configure_db_params
    task_configure_db_params(database, task, retry_from)


@app.task(bind=True)
def configure_static_db_params(self, database, task, user, retry_from=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=user,
        worker_name=get_worker_name()
    )

    from task_configure_static_db_params import task_configure_static_db_params
    task_configure_static_db_params(database, task, retry_from)


def _create_database_rollback(self, rollback_from, task, user):
    task = TaskHistory.register(request=self.request, task_history=task, user=user, worker_name=get_worker_name())

    from tasks_create_database import rollback_create
    rollback_create(rollback_from, task, user)


@app.task(bind=True)
def create_database_rollback(self, rollback_from, task, user):
    _create_database_rollback(self, rollback_from, task, user)


@app.task(bind=True)
def node_zone_migrate(self, host, zone, new_environment, task, since_step=None, step_manager=None, zone_origin=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=task.user,
        worker_name=get_worker_name()
    )
    from tasks_migrate import node_zone_migrate
    node_zone_migrate(
        host, zone, new_environment, task, since_step, step_manager=step_manager, zone_origin=zone_origin
    )

@app.task(bind=True)
def recreate_slave(self, database, host, task, since_step=None, step_manager=None):
    from maintenance.models import RecreateSlave
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())
    instance = host.instances.first()
    if step_manager:
        step_manager = step_manager
        step_manager.id = None
        step_manager.started_at = None
        since_step = step_manager.current_step
    else:
        retry_from = RecreateSlave.objects.filter(can_do_retry=True, host=host, status=RecreateSlave.ERROR).last()
        step_manager = RecreateSlave()
        if retry_from:
            step_manager.current_step = retry_from.current_step
            step_manager.snapshot = retry_from.snapshot
            since_step = retry_from.current_step
    step_manager.host = instance.hostname
    step_manager.task = task
    step_manager.save()

    steps = host.instances.first().databaseinfra.recreate_slave_steps()
    result = steps_for_instances(
        steps, [instance], task, step_manager.update_step, since_step, step_manager=step_manager
    )
    step_manager = RecreateSlave.objects.get(id=step_manager.id)
    if result:
        step_manager.set_success()
        task.set_status_success('Slave recreated with success')
    else:
        step_manager.set_error()
        task.set_status_error('Could not recreate slave')


@app.task(bind=True)
def update_ssl(self, database, task, since_step=None, step_manager=None, scheduled_task=None, auto_rollback=False):
    from maintenance.models import UpdateSsl
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())
    if step_manager:
        step_manager = step_manager
        step_manager.id = None
        step_manager.started_at = None
        since_step = step_manager.current_step
    else:
        retry_from = UpdateSsl.objects.filter(can_do_retry=True, database=database, status=UpdateSsl.ERROR).last()
        step_manager = UpdateSsl()
        if retry_from:
            step_manager.current_step = retry_from.current_step
            since_step = retry_from.current_step
            step_manager.task_schedule = retry_from.task_schedule
    step_manager.database = database
    step_manager.task = task
    if scheduled_task:
        step_manager.task_schedule = scheduled_task
    step_manager.set_running()
    step_manager.save()

    steps = database.databaseinfra.update_ssl_steps()

    hosts = []
    for instance in database.infra.instances.all():
        if instance.hostname not in hosts:
            hosts.append(instance.hostname)
    instances = []
    for host in hosts:
        instances.append(host.instances.all()[0])

    result = steps_for_instances(
        steps, instances, task, step_manager.update_step, since_step, step_manager=step_manager
    )
    step_manager = UpdateSsl.objects.get(id=step_manager.id)
    if result:
        step_manager.set_success()
        task.set_status_success('SSL Update with success')
    else:
        step_manager.set_error()
        task.set_status_error('Could not update SSL')
        if auto_rollback:
            from workflow.workflow import rollback_for_instances_full
            new_task = task
            new_task.id = None
            new_task.details = ''
            new_task.task_name += '_rollback'
            new_task.task_status = new_task.STATUS_RUNNING
            new_task.save()
            rollback_step_manager = step_manager
            rollback_step_manager.id = None
            rollback_step_manager.task_schedule = None
            rollback_step_manager.can_do_retry = 0
            rollback_step_manager.save()
            result = rollback_for_instances_full(
                steps, instances, new_task, rollback_step_manager.get_current_step, rollback_step_manager.update_step,
            )
            if result:
                rollback_step_manager.set_success()
                task.set_status_success('Rollback SSL Update with success')
            else:
                if hasattr(rollback_step_manager, 'cleanup'):
                    rollback_step_manager.cleanup(instances)
                rollback_step_manager.set_error()
                task.set_status_error('Could not rollback update SSL')


@app.task(bind=True)
def restart_database(
        self, database, task, since_step=None, step_manager=None, scheduled_task=None, auto_rollback=False, auto_cleanup=False
):
    from maintenance.async_jobs import RestartDatabaseJob
    async_job = RestartDatabaseJob(
        request=self.request,
        database=database,
        task=task,
        since_step=since_step,
        step_manager=step_manager,
        scheduled_task=scheduled_task,
        auto_rollback=auto_rollback,
        auto_cleanup=auto_cleanup
    )
    async_job.run()


@app.task(bind=True)
def node_zone_migrate_rollback(self, migrate, task):
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())
    from tasks_migrate import rollback_node_zone_migrate
    rollback_node_zone_migrate(migrate, task)


@app.task(bind=True)
def region_migrate(self, database, environment, offering, task, hosts_zones, flag_region, since_step=None, step_manager=None):
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())

    from tasks_region_migrate import region_migrate
    region_migrate(database, environment, offering, task, hosts_zones, flag_region, since_step, step_manager=step_manager)


@app.task(bind=True)
def region_migrate_rollback(self, step_manager, task):
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())

    from tasks_region_migrate import rollback_region_migrate
    rollback_region_migrate(step_manager, task)


@app.task(bind=True)
def database_environment_migrate(
    self, database, new_environment, new_offering, task, hosts_zones, since_step=None, step_manager=None
):
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())
    from tasks_database_migrate import database_environment_migrate
    database_environment_migrate(
        database, new_environment, new_offering, task, hosts_zones, since_step, step_manager=step_manager
    )


@app.task(bind=True)
def database_environment_migrate_rollback(self, step_manager, task):
    task = TaskHistory.register(request=self.request, task_history=task, user=task.user, worker_name=get_worker_name())
    from tasks_database_migrate import rollback_database_environment_migrate
    rollback_database_environment_migrate(step_manager, task)


@app.task(bind=True)
@only_one(key="disk_auto_resize", timeout=600)
def update_disk_used_size(self):
    worker_name = get_worker_name()
    task = TaskHistory.register(request=self.request, user=None, worker_name=worker_name)
    task.relevance = TaskHistory.RELEVANCE_WARNING
    task.add_detail(message='Collecting disk used space from Zabbix')

    from .tasks_disk_resize import zabbix_collect_used_disk
    zabbix_collect_used_disk(task=task)


@app.task(bind=True)
def zabbix_alert_resize_disk_task(self, task_history, database):
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        task_history=task_history, request=self.request,
        user=None, worker_name=worker_name
    )

    databases = [database]
    status = TaskHistory.STATUS_SUCCESS
    threshold_disk_resize = Configuration.get_by_name_as_int(
        "threshold_disk_resize", default=80.0
    )
    integration = CredentialType.objects.get(type=CredentialType.ZABBIX_READ_ONLY)
    zabbix_credential, graf_credential = find_zabbix_and_grafana_credentials_for_environment(
        database.environment, integration, task_history)
    project_domain = graf_credential.get_parameter_by_name('project_domain')

    collected, problems, resizes, status = go_through_databases(databases=databases, task=task_history,
                                                                zabbix_credential=zabbix_credential,
                                                                project_domain=project_domain, collected=1, problems=0,
                                                                resizes=0, status=status,
                                                                threshold_disk_resize=threshold_disk_resize)

    details = "Resize: {} | Problems: {}".format(resizes, problems)

    task_history.update_status_for(status=status, details=details)


class TaskRegisterMaintenance(TaskRegisterBase):
    @classmethod
    def zabbix_alert_resize_disk(cls, database, is_running):
        task_params = {
            'task_name': 'resize_disk_from_zabbix_alert',
            'arguments': 'Resizing disk for database {}'.format(
                database),
            'database': database,
            'user': None,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)

        if is_running:
            LOG.warning("Database {} already has a resize task runing.".format(database.name))
            details = "Database {} already has a resize task runing".format(database.name)
            status = TaskHistory.STATUS_WARNING

            task.update_status_for(status=status, details=details)
        else:
            zabbix_alert_resize_disk_task.delay(task_history=task, database=database)
