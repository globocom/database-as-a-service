# -*- coding: utf-8 -*-
import logging
from dbaas.celery import app
from datetime import datetime
from account.models import User
from logical.models import Database
from util.decorators import only_one
from simple_audit.models import AuditRequest
from dbaas_services.analyzing.models import ExecutionPlan
from dbaas_services.analyzing.actions import database_can_not_be_resized
from dbaas_services.analyzing.models import AnalyzeRepository
from dbaas_services.analyzing.integration import AnalyzeService
from dbaas_services.analyzing.exceptions import ServiceNotAvailable


LOG = logging.getLogger(__name__)


@app.task(bind=True)
@only_one(key="analyze_databases_service_task", timeout=6000)
def analyze_databases(self,):
    endpoint, healh_check_route, healh_check_string = get_analyzing_credentials()
    user = User.objects.get(username='admin')
    AuditRequest.new_request("analyze_databases", user, "localhost")
    try:
        try:
            analyze_service = AnalyzeService(endpoint, healh_check_route, healh_check_string)
        except ServiceNotAvailable as e:
            LOG.warn(e)
            return

        databases = Database.objects.filter(is_in_quarantine=False)
        today = datetime.now()
        for database in databases:
            database_name, engine, instances, environment_name, databaseinfra_name = setup_database_info(database)
            for execution_plan in ExecutionPlan.objects.all():
                if database_can_not_be_resized(database, execution_plan):
                    continue
                params = execution_plan.setup_execution_params()
                result = analyze_service.run(engine=engine, database=database_name,
                                             instances=instances, **params)
                if result['status'] == 'success':
                    if result['msg'] != instances:
                        continue
                    for instance in result['msg']:
                        try:
                            get_analyzing_objects = AnalyzeRepository.objects.get
                            LOG.info(today)
                            repo_instance = get_analyzing_objects(analyzed_at=today,
                                                                  database_name=database_name,
                                                                  instance_name=instance,
                                                                  engine_name=engine,
                                                                  databaseinfra_name=databaseinfra_name,
                                                                  environment_name=environment_name,)
                        except AnalyzeRepository.DoesNotExist as e:
                            LOG.info(e)
                            repo_instance = AnalyzeRepository(analyzed_at=today,
                                                              database_name=database_name,
                                                              instance_name=instance,
                                                              engine_name=engine,
                                                              databaseinfra_name=databaseinfra_name,
                                                              environment_name=environment_name)

                        setattr(repo_instance, execution_plan.alarm_repository_attr, True)
                        setattr(repo_instance, execution_plan.threshold_repository_attr,
                                execution_plan.threshold)
                        repo_instance.save()
    except Exception as e:
        LOG.warn(e)
        return
    finally:
        AuditRequest.cleanup_request()


def get_analyzing_credentials():
    from dbaas_credentials.models import CredentialType
    from dbaas_credentials.models import Credential
    credential = Credential.objects.get(integration_type__type=CredentialType.DBAAS_SERVICES_ANALYZING)

    return credential.endpoint, credential.get_parameter_by_name('healh_check_route'), credential.get_parameter_by_name('healh_check_string')


def setup_database_info(database):
    databaseinfra = database.databaseinfra
    driver = databaseinfra.get_driver()
    database_instances = driver.get_database_instances()
    instances = [db_instance.dns.split('.')[0] for db_instance in database_instances]
    return database.name, database.engine_type, instances, database.environment.name, database.databaseinfra
