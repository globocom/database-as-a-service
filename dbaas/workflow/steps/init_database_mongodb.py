# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_nfsaas.models import HostAttr
from dbaas_cloudstack.models import PlanAttr, HostAttr as CsHostAttr
from itertools import permutations
from util import check_ssh, exec_remote_command, get_credentials_for
import string
import random
from ..exceptions.error_codes import DBAAS_0014
from util import full_stack

LOG = logging.getLogger(__name__)


class InitDatabaseMongoDB(BaseStep):
	def __unicode__(self):
		return "Initializing database..."

	def do(self, workflow_dict):
		try:

			LOG.info("Getting cloudstack credentials...")
			cs_credentials = get_credentials_for(
				environment=workflow_dict['environment'],
				credential_type=CredentialType.CLOUDSTACK)

			cs_provider = CloudStackProvider(credentials=cs_credentials)

			mongodbkey = ''.join(random.choice(string.hexdigits) for i in range(50))

			workflow_dict['replicasetname'] = 'RepicaSet_' + workflow_dict['databaseinfra'].name

			for index, instance in enumerate(workflow_dict['instances']):
				host = instance.hostname

				LOG.info("Getting vm credentials...")
				host_csattr = CsHostAttr.objects.get(host=host)

				LOG.info("Cheking host ssh...")
				host_ready = check_ssh(
					server=host.address, username=host_csattr.vm_user, password=host_csattr.vm_password, wait=5,
					interval=10)

				if not host_ready:
					LOG.warn("Host %s is not ready..." % host)
					return False

				if instance.is_arbiter:
					contextdict = {
						'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
						'DATABASENAME': workflow_dict['name'],
						'ENGINE': 'mongodb'
					}
					databaserule = 'ARBITER'
				else:
					host_nfsattr = HostAttr.objects.get(host=host)
					contextdict = {
						'EXPORTPATH': host_nfsattr.nfsaas_path,
						'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
						'DATABASENAME': workflow_dict['name'],
						'ENGINE': 'mongodb',
						'DBPASSWORD': get_credentials_for(environment=workflow_dict['environment'],
						                                  credential_type=CredentialType.MONGODB).password,
					}

					if index == 0:
						databaserule = 'PRIMARY'
					else:
						databaserule = 'SECONDARY'

				if len(workflow_dict['hosts']) > 1:
					LOG.info("Updating contexdict for %s" % host)

					contextdict.update({
						'DBPASSWORD': get_credentials_for(environment=workflow_dict['environment'],
						                                  credential_type=CredentialType.MONGODB).password,
						'REPLICASETNAME': workflow_dict['replicasetname'],
						'HOST01': workflow_dict['hosts'][0],
						'HOST02': workflow_dict['hosts'][1],
						'HOST03': workflow_dict['hosts'][2],
						'MONGODBKEY': mongodbkey,
						'DATABASERULE': databaserule,
						'SECOND_SCRIPT_FILE': '/opt/dbaas/scripts/dbaas_second_script.sh',
						'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
						'DATABASENAME': workflow_dict['name'],
						'ENGINE': 'mongodb'
					})

				LOG.info("Updating userdata for %s" % host)

				planattr = PlanAttr.objects.get(plan=workflow_dict['plan'])
				cs_provider.update_userdata(
					vm_id=host_csattr.vm_id, contextdict=contextdict, userdata=planattr.userdata)

				LOG.info("Executing script on %s" % host)

				return_code = exec_remote_command(server=host.address,
				                                  username=host_csattr.vm_user,
				                                  password=host_csattr.vm_password,
				                                  command='/opt/dbaas/scripts/dbaas_userdata_script.sh')

				if return_code != 0:
					return False

			if len(workflow_dict['hosts']) > 1:
				for host in workflow_dict['hosts']:

					LOG.info("Executing script on %s" % host)

					return_code = exec_remote_command(server=host.address,
					                                  username=host_csattr.vm_user,
					                                  password=host_csattr.vm_password,
					                                  command=contextdict['SECOND_SCRIPT_FILE'])

					if return_code != 0:
						return False

			return True
		except Exception, e:
			traceback = full_stack()

			workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
			workflow_dict['exceptions']['traceback'].append(traceback)

			return False

	def undo(self, workflow_dict):
		try:
			LOG.info("Remove all database files")

			for host in workflow_dict['hosts']:
				LOG.info("Removing database files on host %s" % host)
				host_csattr = CsHostAttr.objects.get(host=host)

				exec_remote_command(server=host.address,
				                    username=host_csattr.vm_user,
				                    password=host_csattr.vm_password,
				                    command="/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh")

			return True

		except Exception, e:
			traceback = full_stack()

			workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
			workflow_dict['exceptions']['traceback'].append(traceback)

			return False
