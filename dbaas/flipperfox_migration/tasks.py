import logging
from datetime import datetime
from dbaas.celery import app
from notification.models import TaskHistory
from util import get_worker_name
from util import build_dict
from util import full_stack
from simple_audit.models import AuditRequest
from models import DatabaseFlipperFoxMigrationDetail
from workflow.workflow import start_workflow, stop_workflow
from .migration_steps import get_flipeerfox_migration_steps
from physical.models import Instance

LOG = logging.getLogger(__name__)


@app.task(bind=True)
def execute_database_flipperfox_migration(self,
                                          database_flipperfox_migration_detail_id,
                                          task_history=None, user=None):
    AuditRequest.new_request(
        "execute_database_flipperfox_migration", user, "localhost")
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

        database_flipperfox_migration_detail = DatabaseFlipperFoxMigrationDetail.objects.get(
            id=database_flipperfox_migration_detail_id)

        database_flipperfox_migration_detail.started_at = datetime.now()
        database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.RUNNING
        database_flipperfox_migration_detail.save()

        database_flipperfox_migration = database_flipperfox_migration_detail.database_flipperfox_migration
        database = database_flipperfox_migration.database
        databaseinfra = database.databaseinfra
        steps = get_flipeerfox_migration_steps()
        workflow_steps = steps[
            database_flipperfox_migration_detail.step].step_classes
        source_instances = []
        source_hosts = []
        for instance in Instance.objects.filter(databaseinfra=databaseinfra):
            if database_flipperfox_migration.current_step > 0 and not instance.future_instance:
                continue
            source_instances.append(instance)
            if instance.instance_type != instance.REDIS:
                source_hosts.append(instance.hostname)

        source_plan = databaseinfra.plan
        target_plan = source_plan.flipperfox_equivalent_plan

        offering = databaseinfra.cs_dbinfra_offering.get().offering

        workflow_dict = build_dict(
            databaseinfra=databaseinfra,
            environment=databaseinfra.environment,
            database=database,
            steps=workflow_steps,
            source_instances=source_instances,
            source_hosts=source_hosts,
            source_plan=source_plan,
            target_plan=target_plan,
            offering=offering,
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

            database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.ROLLBACK
            database_flipperfox_migration_detail.finished_at = datetime.now()
            database_flipperfox_migration_detail.save()

            task_history.update_status_for(
                TaskHistory.STATUS_ERROR, details=error)

            return

        else:
            database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.SUCCESS
            database_flipperfox_migration_detail.finished_at = datetime.now()
            database_flipperfox_migration_detail.save()

            current_step = database_flipperfox_migration.current_step
            database_flipperfox_migration.current_step = current_step + 1
            database_flipperfox_migration.save()

            task_history.update_status_for(
                TaskHistory.STATUS_SUCCESS, details='Database flipper fox migration was succesfully')
            return

    except Exception as e:
        traceback = full_stack()
        LOG.error("Ops... something went wrong: %s" % e)
        LOG.error(traceback)

        database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.ROLLBACK
        database_flipperfox_migration_detail.finished_at = datetime.now()
        database_flipperfox_migration_detail.save()

        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details=traceback)
        return

    finally:
        AuditRequest.cleanup_request()
        pass


@app.task(bind=True)
def execute_database_flipperfox_migration_undo(self,
                                               database_flipperfox_migration_detail_id,
                                               task_history=None, user=None):
    AuditRequest.new_request(
        "execute_database_flipperfox_migration", user, "localhost")
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

        database_flipperfox_migration_detail = DatabaseFlipperFoxMigrationDetail.objects.get(
            id=database_flipperfox_migration_detail_id)

        database_flipperfox_migration_detail.started_at = datetime.now()
        database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.RUNNING
        database_flipperfox_migration_detail.is_migration_up = False
        database_flipperfox_migration_detail.save()

        database_flipperfox_migration = database_flipperfox_migration_detail.database_flipperfox_migration
        database = database_flipperfox_migration.database
        databaseinfra = database.databaseinfra
        steps = get_flipeerfox_migration_steps()
        workflow_steps = steps[
            database_flipperfox_migration_detail.step].step_classes
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
        target_plan = source_plan.flipperfox_equivalent_plan

        if not source_hosts:
            raise Exception('There is no source host')
        if not source_instances:
            raise Exception('There is no source instance')
        if not target_hosts:
            raise Exception('There is no target host')
        if not target_instances:
            raise Exception('There is no target instance')

        workflow_dict = build_dict(database_flipperfox_migration_detail=database_flipperfox_migration_detail,
                                   database_flipperfox_migration=database_flipperfox_migration,
                                   database=database,
                                   databaseinfra=databaseinfra,
                                   environment=databaseinfra.environment,
                                   steps=workflow_steps,
                                   source_instances=source_instances,
                                   source_plan=source_plan,
                                   target_plan=target_plan,
                                   source_hosts=source_hosts,
                                   target_instances=target_instances,
                                   target_hosts=target_hosts,
                                   )

        stop_workflow(workflow_dict=workflow_dict, task=task_history)

        current_step = database_flipperfox_migration.current_step
        database_flipperfox_migration.current_step = current_step - 1
        database_flipperfox_migration.save()

        database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.SUCCESS
        database_flipperfox_migration_detail.finished_at = datetime.now()
        database_flipperfox_migration_detail.save()

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details='Database flipper fox migration was succesfully')

    except Exception as e:
        traceback = full_stack()
        LOG.error("Ops... something went wrong: %s" % e)
        LOG.error(traceback)

        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details=traceback)

        database_flipperfox_migration_detail.status = database_flipperfox_migration_detail.ERROR
        database_flipperfox_migration_detail.finished_at = datetime.now()
        database_flipperfox_migration_detail.save()

        return

    finally:
        AuditRequest.cleanup_request()
