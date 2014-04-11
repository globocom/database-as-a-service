from dbaas_nfsaas.provider import NfsaasProvider
import logging

LOG = logging.getLogger(__name__)

class StorageManager():
    
    @classmethod
    def create_disk(cls, environment, plan, host):
        LOG.info("Creating nfsaas disk...")
        return NfsaasProvider().create_disk(environment, plan, host)
            
    @classmethod 
    def destroy_disk(cls, environment, plan, host):
        LOG.info("Destroying nfsaas disk...")
        return NfsaasProvider().destroy_disk(environment, plan, host)        
