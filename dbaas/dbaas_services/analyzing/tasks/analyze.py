# -*- coding: utf-8 -*-
import logging
from dbaas.celery import app
from datetime import datetime
from account.models import User
from util import get_worker_name
from django.db import transaction
from logical.models import Database
from util.decorators import only_one
from simple_audit.models import AuditRequest
from notification.models import TaskHistory
from dbaas_services.analyzing.models import ExecutionPlan
from dbaas_services.analyzing.models import AnalyzeRepository
from dbaas_services.analyzing.integration import AnalyzeService
from dbaas_services.analyzing.actions import database_can_be_resized

LOG = logging.getLogger(__name__)


@app.task(acks_late=True, bind=True)
@only_one(key="analyze_databases_service_task", timeout=6000)
def analyze_databases(self, task_history=None):
    endpoint, healh_check_route, healh_check_string = get_analyzing_credentials()
    user = User.objects.get(username='admin')
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        task_history=task_history, request=self.request, user=user,
        worker_name=worker_name
    )
    task_history.update_details(persist=True, details="Loading Process...")
    AuditRequest.new_request("analyze_databases", user, "localhost")

    try:
        analyze_service = AnalyzeService(endpoint, healh_check_route,
                                         healh_check_string)
        with transaction.atomic():
            databases = Database.objects.filter(is_in_quarantine=False)
            today = datetime.now()
            for database in databases:
                database_name, engine, instances, environment_name, databaseinfra_name = setup_database_info(database)
                for execution_plan in ExecutionPlan.objects.all():
                    if not database_can_be_resized(database, execution_plan):
                        continue

                    params = execution_plan.setup_execution_params()
                    result = {
                        'msg': 'Could not analyse {}'.format(database_name)
                    }

                    try:
                        result = analyze_service.run(
                            engine=engine, database=database_name,
                            instances=instances, **params
                        )
                        if result['status'] == 'success':
                            task_history.update_details(
                                persist=True,
                                details="\nDatabase {} {} was analysed.".format(
                                    database, execution_plan.plan_name
                                )
                            )

                            if result['msg'] != instances:
                                continue

                            for instance in result['msg']:
                                insert_analyze_repository_record(
                                    today, database_name, instance, engine,
                                    databaseinfra_name, environment_name,
                                    execution_plan
                                )
                        else:
                            raise Exception("Check your service logs..")
                    except Exception:
                        task_history.update_details(
                            persist=True,
                            details="\nDatabase {} {} could not be analysed.".format(
                                database, execution_plan.plan_name
                            )
                        )
                        task_history.update_status_for(
                            TaskHistory.STATUS_ERROR,
                            details='Analysis finished with errors!'
                                    '\nError: {}'.format(result['msg'])
                        )

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details='Analysis ok!'
        )
    except Exception:
        task_history.update_details(persist=True, details="\nProcess crashed")
        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details='Analysis could not be started'
        )
    finally:
        AuditRequest.cleanup_request()


def get_analyzing_credentials():
    from dbaas_credentials.models import CredentialType
    from dbaas_credentials.models import Credential
    credential = Credential.objects.get(integration_type__type=CredentialType.DBAAS_SERVICES_ANALYZING)

    return credential.endpoint, credential.get_parameter_by_name('healh_check_route'), credential.get_parameter_by_name('healh_check_string')


def insert_analyze_repository_record(date_time, database_name, instance,
                                     engine, databaseinfra_name, environment_name,
                                     execution_plan):
    try:
        get_analyzing_objects = AnalyzeRepository.objects.get
        LOG.info(date_time)
        repo_instance = get_analyzing_objects(analyzed_at=date_time,
                                              database_name=database_name,
                                              instance_name=instance,
                                              engine_name=engine,
                                              databaseinfra_name=databaseinfra_name,
                                              environment_name=environment_name,)
    except AnalyzeRepository.DoesNotExist as e:
        LOG.info(e)
        repo_instance = AnalyzeRepository(analyzed_at=date_time,
                                          database_name=database_name,
                                          instance_name=instance,
                                          engine_name=engine,
                                          databaseinfra_name=databaseinfra_name,
                                          environment_name=environment_name)

    setattr(repo_instance, execution_plan.alarm_repository_attr, True)
    setattr(repo_instance, execution_plan.threshold_repository_attr,
            execution_plan.threshold)
    repo_instance.save()


def setup_database_info(database):
    databaseinfra = database.databaseinfra
    driver = databaseinfra.get_driver()
    database_instances = driver.get_database_instances()

    instances = []
    for db_instance in database_instances:
        if db_instance.dns != db_instance.address:
            instances.append(db_instance.dns.split('.')[0])

    return database.name, database.engine_type, instances, database.environment.name, database.databaseinfra
