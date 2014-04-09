# -*- coding: utf-8 -*-

from ..base import BaseProvider
import logging
from django.db import transaction
from nfsaas_client import NfsaasClient
from models import EnvironmentAttr, PlanAttr, HostAttr

LOG = logging.getLogger(__name__)

class NfsaasProvider(BaseProvider):

    @classmethod
    def get_credentials(self, environment):
        LOG.info("Getting credentials...")
        from integrations.credentials.manager import IntegrationCredentialManager
        from integrations.credentials.models import IntegrationType
        integration = IntegrationType.objects.get(type= IntegrationType.NFSAAS)

        return IntegrationCredentialManager.get_credentials(environment= environment, integration= integration)

    @classmethod
    def auth(self, environment):
        LOG.info("Conecting with nfsaas...")
        credentials = self.get_credentials(environment= environment)
        return NfsaasClient(baseurl= credentials.endpoint, teamid= credentials.team, 
                                        projectid=credentials.project, username=credentials.user, password= credentials.password)
    
    @classmethod
    @transaction.commit_on_success
    def create_disk(self, environment, plan, host):
        
        nfsaas = self.auth(environment= environment)
        nfsaas_planid = PlanAttr.objects.get(dbaas_plan=plan).nfsaas_plan
        nfsaas_environmentid = EnvironmentAttr.objects.get(dbaas_environment=environment).nfsaas_environment
        
        LOG.info("Creating export on environmen %s and size %s" % (nfsaas_environmentid, nfsaas_planid))
        export = nfsaas.create_export(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid)
        LOG.info("Export created: %s" % export)
        
        LOG.info("Creating access!")
        access = nfsaas.create_access(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export['id'], host=host.hostname)
        LOG.info("Access created: %s" % access)
        
        LOG.info("Saving export info on nfsaas host attr")
        hostattr = HostAttr(host=host, nfsaas_export_id=export['id'], nfsaas_path=export['path'])
        hostattr.save()
        
        return export
        
    @classmethod
    @transaction.commit_on_success
    def destroy_disk(self, environment, plan, host):
        
        nfsaas = self.auth(environment= environment)
        
        hostattr = HostAttr.objects.get(host=host)
        export_id = hostattr.nfsaas_export_id
        nfsaas_environmentid = EnvironmentAttr.objects.get(dbaas_environment=environment).nfsaas_environment
        nfsaas_planid = PlanAttr.objects.get(dbaas_plan=plan).nfsaas_plan
        
        accesses = nfsaas.list_access(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export_id)
        
        for access in accesses:
            LOG.info("Removing access on export (id=%s) from host %s" % (export_id, host))
            nfsaas.drop_access(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export_id, accessid = access['id'])
            LOG.info("Access deleted: %s" % access)
        
        LOG.info("Deleting register from nfsaas host attr")
        hostattr = HostAttr.objects.get(host=host)
        hostattr.delete()
        
        deleted_export = nfsaas.drop_export(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export_id)
        LOG.info("Export deleted: %s" % deleted_export)
        
        return deleted_export
                