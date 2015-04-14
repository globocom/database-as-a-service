# -*- coding: utf-8 -*-
import logging
from util import get_credentials_for
from util import full_stack
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import PlanAttr
from dbaas_cloudstack.models import HostAttr
from dbaas_cloudstack.models import LastUsedBundle
from dbaas_cloudstack.models import DatabaseInfraOffering
from django.core.exceptions import ObjectDoesNotExist
from physical.models import Host
from physical.models import Instance
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0011

LOG = logging.getLogger(__name__)


class CreateVirtualMachine(BaseStep):

    def __unicode__(self):
        return "Creating virtualmachines..."

    def do(self, workflow_dict):
        try:
            from time import sleep
            sleep(60)
            
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0011)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0011)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
