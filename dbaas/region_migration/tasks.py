import logging
from datetime import datetime
from dbaas.celery import app
from notification.models import TaskHistory
from util import get_worker_name
from util import build_dict
from util import full_stack
from simple_audit.models import AuditRequest
from models import DatabaseRegionMigrationDetail
from workflow.workflow import  start_workflow, stop_workflow
from .migration_steps import get_engine_steps
from physical.models import Environment, Instance
from sets import Set

LOG = logging.getLogger(__name__)

@app.task(bind=True)
def execute_database_region_migration(self, database_region_migration_detail_id, task_history=None, user=None):
    AuditRequest.new_request("execute_database_region_migration", user, "localhost")
    try:
    
        if task_history:
            arguments = task_history.arguments
        else:
            arguments = None
    
        task_history = TaskHistory.register(request=self.request,
            task_history = task_history,
            user = user,
            worker_name = get_worker_name())

        if arguments:
            task_history.arguments = arguments
            task_history.save()
    
        database_region_migration_detail = DatabaseRegionMigrationDetail.objects.get(id=database_region_migration_detail_id)
        
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
        workflow_steps = steps[database_region_migration_detail.step].step_classes
        source_instances = []
        source_hosts = []
        for instance in Instance.objects.filter(databaseinfra=databaseinfra):
            source_instances.append(instance)
            if instance.instance_type != instance.REDIS_SENTINEL:
                source_hosts.append(instance.hostname)
    
        source_plan = databaseinfra.plan
        target_plan = source_plan.equivalent_plan_id
    
        workflow_dict = build_dict(
                               databaseinfra = databaseinfra,
                               target_environment = target_environment,
                               steps = workflow_steps,
                               source_instances = source_instances,
                               source_hosts = source_hosts,
                               target_plan = target_plan,
                               )

        start_workflow(workflow_dict = workflow_dict, task = task_history)    
        
        
        if workflow_dict['created'] == False:

            if 'exceptions' in workflow_dict:
                error = "\n".join(": ".join(err) for err in workflow_dict['exceptions']['error_codes'])
                traceback = "\nException Traceback\n".join(workflow_dict['exceptions']['traceback'])
                error = "{}\n{}\n{}".format(error, traceback, error)
            else:
                error = "There is not any infra-structure to allocate this database."
            
            database_region_migration.next_step = database_region_migration.current_step + 1
            database_region_migration.save()

            database_region_migration_detail.status = database_region_migration_detail.ROLLBACK
            database_region_migration_detail.finished_at = datetime.now()
            database_region_migration_detail.save()

            task_history.update_status_for(TaskHistory.STATUS_ERROR, details=error)

            return
        
        else:
            database_region_migration_detail.status = database_region_migration_detail.SUCCESS
            database_region_migration_detail.finished_at = datetime.now()
            database_region_migration_detail.save()
            
            current_step = database_region_migration.current_step + 1
            database_region_migration.current_step = current_step
            next_step = current_step + 1
            
            total_steps = len(database_region_migration.get_steps())
            
            LOG.debug("current_step:{} - next_step: {} - steps: {}".format(current_step, next_step, total_steps))
            
            if next_step < total_steps:
                database_region_migration.next_step = next_step
            else:
                database_region_migration.next_step = None
            database_region_migration.save()

            task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details='Database region migration was succesfully')
            return

    except Exception, e:
        traceback = full_stack()
        LOG.error("Ops... something went wrong: %s" % e)
        LOG.error(traceback)

        database_region_migration.next_step = database_region_migration.current_step + 1
        database_region_migration.save()

        database_region_migration_detail.status = database_region_migration_detail.ROLLBACK
        database_region_migration_detail.finished_at = datetime.now()
        database_region_migration_detail.save()

        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=traceback)
        return

    finally:
        AuditRequest.cleanup_request()
        pass



@app.task(bind=True)
def execute_database_region_migration_undo(self, database_region_migration_detail_id, task_history=None, user=None):
    #AuditRequest.new_request("execute_database_region_migration", user, "localhost")
    try:
    
        if task_history:
            arguments = task_history.arguments
        else:
            arguments = None
    
        task_history = TaskHistory.register(request=self.request,
            task_history = task_history,
            user = user,
            worker_name = get_worker_name())

        if arguments:
            task_history.arguments = arguments
            task_history.save()
    
        database_region_migration_detail = DatabaseRegionMigrationDetail.objects.get(id=database_region_migration_detail_id)
        database_region_migration = database_region_migration_detail.database_region_migration
        database = database_region_migration.database
        databaseinfra = database.databaseinfra
        source_environment = databaseinfra.environment
        target_environment = source_environment.equivalent_environment
        engine = database.engine_type
        steps = get_engine_steps(engine)
        workflow_steps = steps[database_region_migration_detail.step].step_classes
        source_instances = []
        source_hosts = []
        for instance in databaseinfra.instances.filter(future_instance__isnull = False):
            source_instances.append(instance)
            source_hosts.append(instance.hostname)
        
        target_instances = []
        target_hosts = []
        for instance in databaseinfra.instances.filter(future_instance__isnull = True):
            target_instances.append(instance)
            target_hosts.append(instance.hostname)
        
        source_plan = databaseinfra.plan
        target_plan = source_plan.equivalent_plan_id
    
        workflow_dict = build_dict(database_region_migration_detail = database_region_migration_detail,
                               database_region_migration = database_region_migration,
                               database = database,
                               databaseinfra = databaseinfra,
                               source_environment = source_environment,
                               target_environment = target_environment,
                               steps = workflow_steps,
                               engine = engine,
                               source_instances = source_instances,
                               source_plan = source_plan,
                               target_plan = target_plan,
                               source_hosts = source_hosts,
                               target_instances = target_instances,
                               target_hosts = target_hosts
                               )

        stop_workflow(workflow_dict = workflow_dict, task = task_history)    

        task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details='Database region migration was succesfully')

    except Exception, e:
        traceback = full_stack()
        LOG.error("Ops... something went wrong: %s" % e)
        LOG.error(traceback)

        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=traceback)
        return

    finally:
        #AuditRequest.cleanup_request()
        pass
   