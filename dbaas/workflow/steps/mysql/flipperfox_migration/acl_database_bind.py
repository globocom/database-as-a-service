# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import get_credentials_for
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import DatabaseInfraAttr
from dbaas_aclapi.models import DatabaseInfraInstanceBind
from dbaas_aclapi.acl_base_client import AclClient
from dbaas_aclapi import helpers
from dbaas_aclapi.models import ERROR


LOG = logging.getLogger(__name__)


class BindNewInstances(BaseStep):

    def __unicode__(self):
        return "Binding new instances ..."

    def do(self, workflow_dict):

        try:
            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password,
                                   database.environment)

            instances = databaseinfra.instances.filter(
                future_instance__isnull=True)

            databaseinfraattr_instances = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                           equivalent_dbinfraattr__isnull=True)
            instance_address_list = []
            for instance in instances:
                instance_address_list.append(instance.address)
            for instance in databaseinfraattr_instances:
                instance_address_list.append(instance.ip)

            for database_bind in database.acl_binds.all():
                if helpers.bind_address(
                        database_bind, acl_client, instances=instances,
                        infra_attr_instances=databaseinfraattr_instances):
                    continue
                else:
                    LOG.error("The AclApi is not working properly.")
                    database_bind.bind_status = ERROR
                    database_bind.save()
                    DatabaseInfraInstanceBind.objects.filter(databaseinfra=databaseinfra,
                                                             bind_address=database_bind.bind_address,
                                                             instance__in=instance_address_list
                                                             ).update(bind_status=ERROR)
            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):

        LOG.info("Running undo...")
        try:
            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password,
                                   database.environment)

            instances = databaseinfra.instances.filter(
                future_instance__isnull=True)
            databaseinfraattr_instances = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                           equivalent_dbinfraattr__isnull=True)

            instance_address_list = []
            for instance in instances:
                instance_address_list.append(instance.address)
            for instance in databaseinfraattr_instances:
                instance_address_list.append(instance.ip)

            for database_bind in database.acl_binds.all():
                infra_instances_binds = DatabaseInfraInstanceBind.objects.filter(
                    databaseinfra=databaseinfra,
                    instance__in=instance_address_list,
                    bind_address=database_bind.bind_address)
                if helpers.unbind_address(
                    database_bind, acl_client, infra_instances_binds, False
                ):
                    continue

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False


class UnbindOldInstances(BaseStep):

    def __unicode__(self):
        return "Unbinding old instances ..."

    def do(self, workflow_dict):

        try:
            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password,
                                   database.environment)

            instances = databaseinfra.instances.filter(
                future_instance__isnull=False)
            databaseinfraattr_instances = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                           equivalent_dbinfraattr__isnull=False)

            instance_address_list = []
            for instance in instances:
                instance_address_list.append(instance.address)
            for instance in databaseinfraattr_instances:
                instance_address_list.append(instance.ip)

            for database_bind in database.acl_binds.all():
                infra_instances_binds = DatabaseInfraInstanceBind.objects.filter(
                    databaseinfra=databaseinfra,
                    instance__in=instance_address_list,
                    bind_address=database_bind.bind_address)
                if helpers.unbind_address(
                    database_bind, acl_client, infra_instances_binds, False
                ):
                    continue

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):

        LOG.info("Running undo...")
        try:
            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password,
                                   database.environment)

            instances = databaseinfra.instances.filter(
                future_instance__isnull=False)

            databaseinfraattr_instances = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                           equivalent_dbinfraattr__isnull=False)
            instance_address_list = []
            for instance in instances:
                instance_address_list.append(instance.address)
            for instance in databaseinfraattr_instances:
                instance_address_list.append(instance.ip)

            for database_bind in database.acl_binds.all():
                if helpers.bind_address(
                        database_bind, acl_client, instances=instances,
                        infra_attr_instances=databaseinfraattr_instances):
                    continue
                else:
                    LOG.error("The AclApi is not working properly.")
                    database_bind.bind_status = ERROR
                    database_bind.save()
                    DatabaseInfraInstanceBind.objects.filter(databaseinfra=databaseinfra,
                                                             bind_address=database_bind.bind_address,
                                                             instance__in=instance_address_list
                                                             ).update(bind_status=ERROR)
            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
