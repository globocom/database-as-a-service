from dbaas_cloudstack.provider import CloudStackProvider
from pre_provisioned.pre_provisioned_provider import  PreProvisionedProvider
from integrations.monitoring.manager import MonitoringManager
import logging

LOG = logging.getLogger(__name__)

class IaaSManager():
    
    @classmethod
    def destroy_instance(cls, database, *args, **kwargs):
        plan = database.plan
        provider = plan.provider
        if provider == plan.PREPROVISIONED:
            LOG.info("Destroying pre provisioned database...")
            PreProvisionedProvider().destroy_instance(database, *args, **kwargs)
        elif provider == plan.CLOUDSTACK:
            LOG.info("Destroying cloud stack instance...")
            if database.is_in_quarantine:
                MonitoringManager.remove_monitoring(database.databaseinfra)
            CloudStackProvider().destroy_instance(database, *args, **kwargs)
            
    @classmethod 
    def create_instance(cls, plan, environment, name):
        if plan.provider == plan.PREPROVISIONED:
            LOG.info("Creating pre provisioned instance...")
            return PreProvisionedProvider().create_instance(plan, environment)
        elif plan.provider == plan.CLOUDSTACK:
            LOG.info("Creating cloud stack instance...")
            databaseinfra = CloudStackProvider().create_instance(plan, environment, name)
            if databaseinfra is not None:
                MonitoringManager.create_monitoring(databaseinfra)
                databaseinfra.per_database_size_mbytes = plan.max_db_size
                databaseinfra.save()
            return databaseinfra
