# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_zabbix.provider import ZabbixProvider
from ..exceptions.error_codes import DBAAS_0012
from util import full_stack


LOG = logging.getLogger(__name__)


class CreateZabbix(BaseStep):
	def __unicode__(self):
		return "Registering zabbix monitoring..."

	def do(self, workflow_dict):
		try:

			if not 'databaseinfra' in workflow_dict:
				return False

			if workflow_dict['enginecod'] == workflow_dict['MYSQL']:
				dbtype = "mysql"
			elif workflow_dict['enginecod'] == workflow_dict['MONGODB']:
				dbtype = "mongodb"

			LOG.info("Creating zabbix monitoring for %s..." % dbtype)

			ZabbixProvider().create_monitoring(dbinfra=workflow_dict['databaseinfra'], dbtype=dbtype)

			return True
		except Exception, e:
			traceback = full_stack()

			workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
			workflow_dict['exceptions']['traceback'].append(traceback)

			return False


	def undo(self, workflow_dict):
		try:
			if not 'databaseinfra' in workflow_dict:
				return False

			LOG.info("Destroying zabbix monitoring...")

			ZabbixProvider().destroy_monitoring(dbinfra=workflow_dict['databaseinfra'])

			return True
		except Exception, e:
			traceback = full_stack()

			workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
			workflow_dict['exceptions']['traceback'].append(traceback)

			return False
