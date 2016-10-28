# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_networkapi.utils import get_vip_ip_from_databaseinfra
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class SetInfraEndpoint(BaseStep):

    def __unicode__(self):
        return "Setting infra Endpoint..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            vip_ip = get_vip_ip_from_databaseinfra(databaseinfra=databaseinfra)
            databaseinfra.endpoint = vip_ip + ":3306"
            databaseinfra.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            databaseinfraattr = workflow_dict['source_secondary_ips'][0]
            databaseinfra = workflow_dict['databaseinfra']
            databaseinfra.endpoint = databaseinfraattr.ip + ":3306"
            databaseinfra.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
