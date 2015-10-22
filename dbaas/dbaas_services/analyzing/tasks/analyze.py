# -*- coding: utf-8 -*-
from dbaas.celery import app
from account.models import User
from logical.models import Database
from util.decorators import only_one
from simple_audit.models import AuditRequest
from dbaas_services.analyzing.integration import AnalyzeService


@app.task
@only_one(key="analyze_databases_service_task", timeout=6000)
def analyze_databases(self, endpoint, healh_check_route, healh_check_string,
                      **kwargs):
    user = User.objects.get(username='admin')
    AuditRequest.new_request("analyze_databases", user, "localhost")
    try:
        databases = Database.objects.filter(is_in_quarantine=False)
        for database in databases:
            database_name, engine, instances = setup_database_info(database)
            result = analyze_service.run(engine=engine, database_name=database_name,
                                         instances=instances, **kwargs)
            print result
    except Exception:
        pass
    finally:
        AuditRequest.cleanup_request()


def setup_database_info(database):
    databaseinfra = database.databaseinfra
    driver = databaseinfra.get_driver()
    database_instances = driver.get_database_instances()
    instances = [db_instance.dns.split('.')[0] for db_instance in database_instances]
    return database.name, database.engine_type, instances
