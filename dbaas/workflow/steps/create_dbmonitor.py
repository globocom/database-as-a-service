# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_dbmonitor.provider import DBMonitorProvider
from ..exceptions.error_codes import DBAAS_0006
from util import full_stack

LOG = logging.getLogger(__name__)


class CreateDbMonitor(BaseStep):
	def __unicode__(self):
		return "Registering dbmonitor monitoring..."

	def do(self, workflow_dict):
		try:

			if not 'databaseinfra' in workflow_dict:
				return False

			LOG.info("Creating dbmonitor monitoring...")

			DBMonitorProvider().create_dbmonitor_monitoring(workflow_dict['databaseinfra'])

			return True
		except Exception, e:
			traceback = full_stack()

			workflow_dict['exceptions']['error_codes'].append(DBAAS_0006)
			workflow_dict['exceptions']['traceback'].append(traceback)

			return False

	def undo(self, workflow_dict):
		try:
			if not 'databaseinfra' in workflow_dict:
				return False

			LOG.info("Destroying dbmonitor monitoring...")

			DBMonitorProvider().remove_dbmonitor_monitoring(workflow_dict['databaseinfra'])

			return True
		except Exception, e:
			traceback = full_stack()

			workflow_dict['exceptions']['error_codes'].append(DBAAS_0006)
			workflow_dict['exceptions']['traceback'].append(traceback)

			return False
