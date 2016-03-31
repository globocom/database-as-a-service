# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import get_credentials_for
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0019
from dbaas_aclapi.models import DatabaseInfraInstanceBind
from dbaas_aclapi.acl_base_client import AclClient
from dbaas_aclapi import helpers
from dbaas_credentials.models import CredentialType


LOG = logging.getLogger(__name__)


class CheckDatabaseBinds(BaseStep):

    def __unicode__(self):
        return "Checking database acl binds..."

    def do(self, workflow_dict):
        return True

    def undo(self, workflow_dict):
        try:
            if 'databaseinfra' not in workflow_dict:
                return False

            database = workflow_dict['databaseinfra'].databases.get()
            databaseinfra = database.databaseinfra

            acl_credential = get_credentials_for(
                environment=database.environment,
                credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(
                acl_credential.endpoint, acl_credential.user,
                acl_credential.password, database.environment)

            for database_bind in database.acl_binds.all():
                infra_instances_binds = DatabaseInfraInstanceBind.objects.filter(
                    databaseinfra=databaseinfra,
                    bind_address=database_bind.bind_address)
                try:
                    helpers.unbind_address(
                        database_bind, acl_client, infra_instances_binds, True)
                except Exception as e:
                    LOG.warn(e)
                    continue

                return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
