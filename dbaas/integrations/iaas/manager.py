from cloudstack.cloudstack_provider import CloudStackProvider
from pre_provisioned.pre_provisioned_provider import  PreProvisionedProvider
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
            CloudStackProvider().destroy_instance(database, *args, **kwargs)
            
    @classmethod 
    def create_instance(cls, plan, environment):
        if plan.provider == plan.PREPROVISIONED:
            LOG.info("Creating pre provisioned instance...")
            return PreProvisionedProvider().create_instance(plan, environment)
        elif plan.provider == plan.CLOUDSTACK:
            LOG.info("Creating cloud stack instance...")
            return CloudStackProvider().create_instance(plan, environment)        
