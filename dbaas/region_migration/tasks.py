import logging
from dbaas.celery import app
from notification.models import TaskHistory
from util import get_worker_name
from util import build_dict
from models import DatabaseRegionMigrationDetail
from workflow.workflow import  start_workflow
from .migration_steps import get_engine_steps
from physical.models import Environment, Instance
from sets import Set

LOG = logging.getLogger(__name__)

@app.task(bind=True)
def execute_database_region_migration(self, database_region_migration_detail_id, task_history=None, user=None):
    
    from time import sleep
    
    sleep(30)
    
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
    for instance in Instance.objects.filter(databaseinfra=databaseinfra):
        source_instances.append(instance)
    source_hosts = []
    for instance in source_instances:
        source_hosts.append(instance.hostname)
    source_hosts = list(Set(source_hosts))
    
    
    
    workflow_dict = build_dict(database_region_migration_detail = database_region_migration_detail,
                               database_region_migration = database_region_migration,
                               database = database,
                               databaseinfra = databaseinfra,
                               source_environment = source_environment,
                               target_environment = target_environment,
                               steps = workflow_steps,
                               engine = engine,
                               source_instances = source_instances,
                               source_hosts = source_hosts,
                               )

    start_workflow(workflow_dict=workflow_dict, task=task_history)    
    
    
    task_history.update_status_for(TaskHistory.STATUS_SUCCESS,
        details='Database region migration was succesfully')