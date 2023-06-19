
import logging

from models import DatabaseConfigureStaticDBParams
from util.providers import get_configure_static_db_params_settings
from workflow.workflow import steps_for_instances

LOG = logging.getLogger(__name__)


def create_maintenance(database, task):
    configure_static_db_params = DatabaseConfigureStaticDBParams()
    configure_static_db_params.task = task
    configure_static_db_params.database = database
    configure_static_db_params.save()

    return configure_static_db_params


def task_configure_static_db_params(database, task, retry_from=None):
    maintenance = None
    try:
        infra = database.infra
        maintenance = create_maintenance(database, task)

        topology_path = database.plan.replication_topology.class_path
        steps = get_configure_static_db_params_settings(topology_path)

        since_step = retry_from.current_step if retry_from else None
        instances = infra.get_driver().get_database_instances()  # nao traz a instance do arbitro (mongodb)

        if steps_for_instances(
                steps, instances, task, maintenance.update_step, since_step=since_step
        ):
            database.update_status()
            maintenance.set_success()
            task.set_status_success('Auto Configure Static DB Params is done!')
        else:
            maintenance.set_error()
            task.set_status_error(
                'Could not configure static DB Params\n'
                'Please check error message and do retry'
            )
    except Exception as erro:
        if maintenance is not None:
            maintenance.set_error()
        
        task.set_status_error('Error: {erro}.\n'
                              'To create task task_auto_configure_static_db_params!\n'
                              'Please check error message and start new task.'.format(erro=erro))
        LOG.error('Error: {erro}.\n'
                  'To create task task_auto_configure_static_db_params!\n'
                  'Please check error message and start new task.'.format(erro=erro))
