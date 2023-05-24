import logging

from models import DatabaseConfigureDBParams
from util.providers import get_configure_db_params_settings
from workflow.workflow import steps_for_instances

LOG = logging.getLogger(__name__)


def create_maintenance(database, task):
    configure_db_params = DatabaseConfigureDBParams()
    configure_db_params.task = task
    configure_db_params.database = database
    configure_db_params.save()

    return configure_db_params


def task_configure_db_params(database, task, retry_from=None):
    configure_db_params = None
    try:
        infra = database.infra
        configure_db_params = create_maintenance(database, task)

        topology_path = database.plan.replication_topology.class_path
        steps = get_configure_db_params_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances = infra.get_driver().get_database_instances()  # nao traz a instance do arbitro (mongodb)

        if steps_for_instances(
                steps, instances, task, configure_db_params.update_step, since_step=since_step
        ):
            database.update_status()
            configure_db_params.set_success()
            task.set_status_success('Auto Configure DB Params is done!')
        else:
            configure_db_params.set_error()
            task.set_status_error(
                'Could not configure DB Paramsg\n'
                'Please check error message and do retry'
            )
    except Exception as erro:
        if configure_db_params is not None:
            configure_db_params.set_error()
        
        task.set_status_error('Error: {erro}.\n'
                              'To create task task_auto_configure_db_params!\n'
                              'Please check error message and start new task.'.format(erro=erro))
        LOG.error('Error: {erro}.\n'
                  'To create task task_auto_configure_db_params!\n'
                  'Please check error message and start new task.'.format(erro=erro))
