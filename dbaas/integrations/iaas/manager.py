from cloudstack.cloudstack_client import CloudStackProvider
from cloudstack.models import PlanAttr
from pre_provisioned.pre_provisioned_client import  PreProvisionedProvider
import logging

LOG = logging.getLogger(__name__)

class IaaSManager():
    
    def __init__(self, plan, environment):
        LOG.info("IaaS manager initialized...")
        self.plan = plan
        self.environment = plan

        if PlanAttr.objects.filter(plan=self.plan):
            self.create_cloud_stack_instance()
        else:
        	self.create_pre_provisioned_instance()

    def create_cloud_stack_instance(self):
        LOG.info("Creating cloud stack instance...")
        self.instance = CloudStackProvider().create_instance(self.plan, self.environment)

    def create_pre_provisioned_instance(self):
        LOG.info("Creating pre provisioned instance...")
        self.instance =  PreProvisionedProvider().create_instance(self.plan, self.environment)

