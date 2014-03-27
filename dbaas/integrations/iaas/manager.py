from cloudstack.cloudstack_client import CloudStackProvider
from pre_provisioned.pre_provisioned_client import  PreProvisionedProvider
import logging

LOG = logging.getLogger(__name__)

class IaaSManager():
    
    def __init__(self, plan=None, environment=None, database=None, *args, **kwargs):
        LOG.info("IaaS manager initialized...")

        if database:
            provider = database.plan.provider
            if provider == 0:
                LOG.info("Destroying pre provisioned database...")
                PreProvisionedProvider().destroy_instance(database, *args, **kwargs)
            elif provider == 1:
                LOG.info("Destroying cloud stack instance...")
                CloudStackProvider().destroy_instance(database, *args, **kwargs)
        else:
            self.plan = plan
            self.environment = environment

            if plan.provider == 0:
                LOG.info("Creating pre provisioned instance...")
                self.instance =  PreProvisionedProvider().create_instance(self.plan, self.environment)
            elif plan.provider == 1:
                LOG.info("Creating cloud stack instance...")
                self.instance = CloudStackProvider().create_instance(self.plan, self.environment)
        
