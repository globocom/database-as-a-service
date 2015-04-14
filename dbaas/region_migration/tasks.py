import logging
from dbaas.celery import app
from notification.models import TaskHistory
from util import get_worker_name
from util import build_dict
from models import DatabaseRegionMigrationDetail
from workflow.workflow import  start_workflow
from .migration_steps import get_engine_steps

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
    environment = databaseinfra.environment
    
    
    
    engine = database.engine_type
    steps = get_engine_steps(engine)
    workflow_steps = steps[database_region_migration_detail.step].step_classes
    
    workflow_dict = build_dict(database_region_migration_detail = database_region_migration_detail,
                               database_region_migration = database_region_migration,
                               database = database,
                               databaseinfra = databaseinfra,
                               environment= environment,
                               steps = workflow_steps,
                               engine = engine
                               )

    start_workflow(workflow_dict=workflow_dict, task=task_history)    
    
    
    task_history.update_status_for(TaskHistory.STATUS_SUCCESS,
        details='Database region migration was succesfully')