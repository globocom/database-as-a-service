# -*- coding: utf-8 -*-
import logging
from util import full_stack
from ..base import BaseStep
from ....exceptions.error_codes import DBAAS_0019
from dbaas_aclapi.models import DatabaseInfraInstanceBind
from dbaas_aclapi.acl_base_client import AclClient
from util import get_credentials_for
from dbaas_credentials.models import CredentialType

LOG = logging.getLogger(__name__)


class CheckDatabaseBinds(BaseStep):
    def __unicode__(self):
        return "Checking database acl binds..."

    def do(self, workflow_dict):
       return True

    def undo(self, workflow_dict):
        try:
            if not 'databaseinfra' in workflow_dict:
                return False

            action = 'deny'

            database = workflow_dict['databaseinfra'].databases.get()
            for database_bind in database.acl_binds.all():
                acl_environment, acl_vlan = database_bind.bind_address.split('/')
                data = {"kind":"object#acl", "rules":[]}
                default_options = {"protocol": "tcp",
                                             "source": "",
                                             "destination": "",
                                             "description": "{} access for database {} in {}".\
                                             format(database_bind.bind_address, database.name,
                                              database.environment.name),
                                             "action": action,
                                             "l4-options":{ "dest-port-start":"",
                                                                  "dest-port-op":"eq"
                                                                  }
                                             }

                LOG.info("Default options: {}".format(default_options))
                databaseinfra = database.infra
                infra_instances_binds = DatabaseInfraInstanceBind.objects.\
                    filter(databaseinfra= databaseinfra,bind_address= database_bind.bind_address)

                for infra_instance_bind in infra_instances_binds:
                    custom_options = default_options.copy()
                    custom_options['source'] = database_bind.bind_address
                    custom_options['destination'] = infra_instance_bind.instance + '/32'
                    custom_options['l4-options']['dest-port-start'] = infra_instance_bind.instance_port
                    data['rules'].append(custom_options)


                acl_credential = get_credentials_for(environment= database.environment,
                    credential_type=CredentialType.ACLAPI)
                acl_client = AclClient(acl_credential.endpoint, acl_credential.user,
                    acl_credential.password)

                LOG.info("Data used on payload: {}".format(data))
                acl_client.revoke_acl_for(environment= acl_environment,
                    vlan= acl_vlan, payload=data)

                infra_instances_binds.delete()
                database_bind.delete()

                return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
