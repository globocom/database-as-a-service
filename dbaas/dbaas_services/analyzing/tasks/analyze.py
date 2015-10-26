# -*- coding: utf-8 -*-
import logging
from dbaas.celery import app
from account.models import User
from logical.models import Database
from util.decorators import only_one
from simple_audit.models import AuditRequest
from dbaas_services.analyzing.models import AnalyzeRepository
from dbaas_services.analyzing.integration import AnalyzeService
from dbaas_services.analyzing.exceptions import ServiceNotAvailable


LOG = logging.getLogger(__name__)


@app.task(bind=True)
@only_one(key="analyze_databases_service_task", timeout=6000)
def analyze_databases(self, endpoint, healh_check_route, healh_check_string,
                      **kwargs):
    user = User.objects.get(username='admin')
    AuditRequest.new_request("analyze_databases", user, "localhost")
    try:
        try:
            analyze_service = AnalyzeService(endpoint, healh_check_route,
                                             healh_check_string)
        except ServiceNotAvailable as e:
            LOG.warn(e)
            return

        databases = Database.objects.filter(is_in_quarantine=False)
        for database in databases:
            database_name, engine, instances, environment_name= setup_database_info(database)
            result = analyze_service.run(engine=engine, database=database_name,
                                         instances=instances, **kwargs)
            if result['status'] == 'success':
                for instance in result['msg']:
                    repo_instance = AnalyzeRepository(database_name=database_name,
                                                      instance_name=instance,
                                                      engine_name=engine,
                                                      environment_name=environment_name,
                                                      )
                    repo_instance.save()
    except Exception as e:
        LOG.warn(e)
        return
    finally:
        AuditRequest.cleanup_request()


def setup_database_info(database):
    databaseinfra = database.databaseinfra
    driver = databaseinfra.get_driver()
    database_instances = driver.get_database_instances()
    instances = [db_instance.dns.split('.')[0] for db_instance in database_instances]
    return database.name, database.engine_type, instances, database.environment.name
