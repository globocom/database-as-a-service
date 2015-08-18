import logging
from datetime import datetime
from dbaas.celery import app
from notification.models import TaskHistory
from util import get_worker_name
from util import build_dict
from util import full_stack
from simple_audit.models import AuditRequest
from models import DatabaseRegionMigrationDetail
from workflow.workflow import start_workflow, stop_workflow
from .migration_steps import get_engine_steps
from physical.models import Instance
from dbaas_cloudstack.models import DatabaseInfraAttr

LOG = logging.getLogger(__name__)


@app.task(bind=True)
def execute_database_region_migration(self,
                                      database_region_migration_detail_id,
                                      task_history=None, user=None):
    AuditRequest.new_request(
        "execute_database_region_migration", user, "localhost")
    try:

        if task_history:
            arguments = task_history.arguments
        else:
            arguments = None

        task_history = TaskHistory.register(request=self.request,
                                            task_history=task_history,
                                            user=user,
                                            worker_name=get_worker_name())

        if arguments:
            task_history.arguments = arguments
            task_history.save()

        database_region_migration_detail = DatabaseRegionMigrationDetail.objects.get(
            id=database_region_migration_detail_id)

        database_region_migration_detail.started_at = datetime.now()
        database_region_migration_detail.status = database_region_migration_detail.RUNNING
        database_region_migration_detail.save()

        database_region_migration = database_region_migration_detail.database_region_migration
        database = database_region_migration.database
        databaseinfra = database.databaseinfra
        source_environment = databaseinfra.environment
        target_environment = source_environment.equivalent_environment
        engine = database.engine_type
        steps = get_engine_steps(engine)
        workflow_steps = steps[
            database_region_migration_detail.step].step_classes
        source_instances = []
        source_hosts = []
        for instance in Instance.objects.filter(databaseinfra=databaseinfra):
            if database_region_migration.current_step > 0 and not instance.future_instance:
                continue
            source_instances.append(instance)
            if instance.instance_type != instance.REDIS:
                source_hosts.append(instance.hostname)

        source_plan = databaseinfra.plan
        target_plan = source_plan.equivalent_plan

        source_offering = databaseinfra.cs_dbinfra_offering.get().offering
        target_offering = source_offering.equivalent_offering

        source_secondary_ips = []

        for secondary_ip in DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra):
            if database_region_migration.current_step > 0 and\
                    not secondary_ip.equivalent_dbinfraattr:
                continue
            source_secondary_ips.append(secondary_ip)

        workflow_dict = build_dict(
            databaseinfra=databaseinfra,
            database=database,
            source_environment=source_environment,
            target_environment=target_environment,
            steps=workflow_steps,
            source_instances=source_instances,
            source_hosts=source_hosts,
            source_plan=source_plan,
            target_plan=target_plan,
            source_offering=source_offering,
            target_offering=target_offering,
            source_secondary_ips=source_secondary_ips,
        )

        start_workflow(workflow_dict=workflow_dict, task=task_history)

        if workflow_dict['created'] == False:

            if 'exceptions' in workflow_dict:
                error = "\n".join(
                    ": ".join(err) for err in workflow_dict['exceptions']['error_codes'])
                traceback = "\nException Traceback\n".join(
                    workflow_dict['exceptions']['traceback'])
                error = "{}\n{}\n{}".format(error, traceback, error)
            else:
                error = "There is not any infra-structure to allocate this database."

            database_region_migration_detail.status = database_region_migration_detail.ROLLBACK
            database_region_migration_detail.finished_at = datetime.now()
            database_region_migration_detail.save()

            task_history.update_status_for(
                TaskHistory.STATUS_ERROR, details=error)

            return

        else:
            database_region_migration_detail.status = database_region_migration_detail.SUCCESS
            database_region_migration_detail.finished_at = datetime.now()
            database_region_migration_detail.save()

            current_step = database_region_migration.current_step
            database_region_migration.current_step = current_step + 1
            database_region_migration.save()

            task_history.update_status_for(
                TaskHistory.STATUS_SUCCESS, details='Database region migration was succesfully')
            return

    except Exception as e:
        traceback = full_stack()
        LOG.error("Ops... something went wrong: %s" % e)
        LOG.error(traceback)

        database_region_migration_detail.status = database_region_migration_detail.ROLLBACK
        database_region_migration_detail.finished_at = datetime.now()
        database_region_migration_detail.save()

        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details=traceback)
        return

    finally:
        AuditRequest.cleanup_request()
        pass


@app.task(bind=True)
def execute_database_region_migration_undo(self,
                                           database_region_migration_detail_id,
                                           task_history=None, user=None):
    AuditRequest.new_request(
        "execute_database_region_migration", user, "localhost")
    try:

        if task_history:
            arguments = task_history.arguments
        else:
            arguments = None

        task_history = TaskHistory.register(request=self.request,
                                            task_history=task_history,
                                            user=user,
                                            worker_name=get_worker_name())

        if arguments:
            task_history.arguments = arguments
            task_history.save()

        database_region_migration_detail = DatabaseRegionMigrationDetail.objects.get(
            id=database_region_migration_detail_id)

        database_region_migration_detail.started_at = datetime.now()
        database_region_migration_detail.status = database_region_migration_detail.RUNNING
        database_region_migration_detail.is_migration_up = False
        database_region_migration_detail.save()

        database_region_migration = database_region_migration_detail.database_region_migration
        database = database_region_migration.database
        databaseinfra = database.databaseinfra
        source_environment = databaseinfra.environment
        target_environment = source_environment.equivalent_environment
        engine = database.engine_type
        steps = get_engine_steps(engine)
        workflow_steps = steps[
            database_region_migration_detail.step].step_classes
        source_instances = []
        source_hosts = []
        for instance in databaseinfra.instances.filter(future_instance__isnull=False):
            source_instances.append(instance)
            if instance.instance_type != instance.REDIS:
                source_hosts.append(instance.hostname)

        target_instances = []
        target_hosts = []
        for instance in databaseinfra.instances.filter(future_instance__isnull=True):
            target_instances.append(instance)
            if instance.instance_type != instance.REDIS:
                target_hosts.append(instance.hostname)

        source_plan = databaseinfra.plan
        target_plan = source_plan.equivalent_plan_id

        if not source_hosts:
            raise Exception('There is no source host')
        if not source_instances:
            raise Exception('There is no source instance')
        if not target_hosts:
            raise Exception('There is no target host')
        if not target_instances:
            raise Exception('There is no target instance')

        source_secondary_ips = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                equivalent_dbinfraattr__isnull=False)

        source_secondary_ips = list(source_secondary_ips)

        workflow_dict = build_dict(database_region_migration_detail=database_region_migration_detail,
                                   database_region_migration=database_region_migration,
                                   database=database,
                                   databaseinfra=databaseinfra,
                                   source_environment=source_environment,
                                   target_environment=target_environment,
                                   steps=workflow_steps,
                                   engine=engine,
                                   source_instances=source_instances,
                                   source_plan=source_plan,
                                   target_plan=target_plan,
                                   source_hosts=source_hosts,
                                   target_instances=target_instances,
                                   target_hosts=target_hosts,
                                   source_secondary_ips=source_secondary_ips,
                                   )

        stop_workflow(workflow_dict=workflow_dict, task=task_history)

        current_step = database_region_migration.current_step
        database_region_migration.current_step = current_step - 1
        database_region_migration.save()

        database_region_migration_detail.status = database_region_migration_detail.SUCCESS
        database_region_migration_detail.finished_at = datetime.now()
        database_region_migration_detail.save()

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details='Database region migration was succesfully')

    except Exception as e:
        traceback = full_stack()
        LOG.error("Ops... something went wrong: %s" % e)
        LOG.error(traceback)

        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details=traceback)

        database_region_migration_detail.status = database_region_migration_detail.ERROR
        database_region_migration_detail.finished_at = datetime.now()
        database_region_migration_detail.save()

        return

    finally:
        AuditRequest.cleanup_request()
