# -*- coding: utf-8 -*-

from ..base import BaseProvider
import logging
from django.db import transaction
from django.conf import settings
from nfsaas_client import NfsaasClient
from models import EnvironmentAttr, PlanAttr, HostAttr

LOG = logging.getLogger(__name__)

class NfsaasProvider(BaseProvider):
    
    @classmethod
    @transaction.commit_on_success
    def create_disk(self, environment, plan, host):
        
        nfsaas = NfsaasClient(baseurl = settings.NFSAAS_URL,
                              teamid = settings.NFSAAS_TEAMID,
                              projectid = settings.NFSAAS_PROJECTID,
                              username = settings.NFSAAS_USERNAME,
                              password = settings.NFSAAS_PASSWORD)
                
        nfsaas_environmentid = EnvironmentAttr.objects.get(dbaas_environment=environment).nfsaas_environment
        nfsaas_planid = PlanAttr.objects.get(dbaas_plan=plan).nfsaas_plan
        
        LOG.info("Creating export on environmen %s and size %s" % (nfsaas_environmentid, nfsaas_planid))
        export = nfsaas.create_export(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid)
        LOG.info("Export created: %s" % export)
        
        access = nfsaas.create_access(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export['id'], host=host.hostname)
        LOG.info("Access created: %s" % access)
        
        hostattr = HostAttr(host=host, nfsaas_export_id=export['id'], nfsaas_path=export['path'])
        hostattr.save()
        
        return export
        
        
        
    @classmethod
    @transaction.commit_on_success
    def destroy_disk(self, environment, plan, host):
        
        nfsaas = NfsaasClient(baseurl = settings.NFSAAS_URL,
                              teamid = settings.NFSAAS_TEAMID,
                              projectid = settings.NFSAAS_PROJECTID,
                              username = settings.NFSAAS_USERNAME,
                              password = settings.NFSAAS_PASSWORD)
        
        hostattr = HostAttr.objects.get(host=host)
        export_id = hostattr.nfsaas_export_id
        nfsaas_environmentid = EnvironmentAttr.objects.get(dbaas_environment=environment).nfsaas_environment
        nfsaas_planid = PlanAttr.objects.get(dbaas_plan=plan).nfsaas_plan
        
        accesses = nfsaas.list_access(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export_id)
        
        for access in accesses:
            nfsaas.drop_access(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export_id, accessid = access['id'])
            LOG.info("Access deleted: %s" % access)
        
        hostattr = HostAttr.objects.get(host=host)
        hostattr.delete()
        
        deleted_export = nfsaas.drop_export(environmentid=nfsaas_environmentid, sizeid=nfsaas_planid, exportid=export_id)
        LOG.info("Export deleted: %s" % deleted_export)
        
        return deleted_export
                