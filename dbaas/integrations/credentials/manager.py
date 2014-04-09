import models
import logging

LOG = logging.getLogger(__name__)

class IntegrationCredentialManager(object):
    
    @classmethod
    def get_credentials(cls, environment, integration):
    	return models.IntegrationCredential.objects.filter(environments=environment, integration_type=integration)[0]