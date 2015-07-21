# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_zabbix.provider import ZabbixProvider
from ..base import BaseStep
from ....exceptions.error_codes import DBAAS_0012

LOG = logging.getLogger(__name__)


class CreateZabbix(BaseStep):

    def __unicode__(self):
        return "Registering zabbix monitoring..."

    def do(self, workflow_dict):
        try:

            if not 'databaseinfra' in workflow_dict:
                return False

            LOG.info("Creating zabbix monitoring for %s..." %
                     workflow_dict['dbtype'])
            ZabbixProvider().create_monitoring(
                dbinfra=workflow_dict['databaseinfra'], dbtype=workflow_dict['dbtype'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            if not 'databaseinfra' in workflow_dict:
                return False

            LOG.info("Destroying zabbix monitoring for %s..." %
                     workflow_dict['dbtype'])
            ZabbixProvider().destroy_monitoring(
                dbinfra=workflow_dict['databaseinfra'], dbtype=workflow_dict['dbtype'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
