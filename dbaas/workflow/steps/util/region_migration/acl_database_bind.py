# -*- coding: utf-8 -*-
import logging
from util import full_stack
from ..base import BaseStep
from ....exceptions.error_codes import DBAAS_0020
from dbaas_aclapi.models import DatabaseInfraInstanceBind
from dbaas_aclapi.acl_base_client import AclClient
from dbaas_aclapi.tasks import monitor_acl_job
from dbaas_aclapi.models import ERROR
from dbaas_cloudstack.models import DatabaseInfraAttr
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
import copy

LOG = logging.getLogger(__name__)


class BindNewInstances(BaseStep):

    def __unicode__(self):
        return "Binding new instances ..."

    def do(self, workflow_dict):

        try:

            action = 'permit'

            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password)

            instances = databaseinfra.instances.filter(
                future_instance__isnull=True)
            port = instances[0].port

            databaseinfraattr_instances = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                           equivalent_dbinfraattr__isnull=True)
            instance_address_list = []
            for instance in instances:
                instance_address_list.append(instance.address)
            for instance in databaseinfraattr_instances:
                instance_address_list.append(instance.ip)

            for database_bind in database.acl_binds.all():
                acl_environment, acl_vlan = database_bind.bind_address.split(
                    '/')
                data = {"kind": "object#acl", "rules": []}
                default_options = {
                    "protocol": "tcp",
                    "source": "",
                    "destination": "",
                    "description": "{} access for database {} in {}".format(database_bind.bind_address,
                                                                            database.name,
                                                                            database.environment.name),
                    "action": action,
                    "l4-options": {"dest-port-start": "",
                                   "dest-port-op": "eq"}
                }

                LOG.info("Default options: {}".format(default_options))

                for instance in instances:
                    custom_options = copy.deepcopy(default_options)
                    custom_options['source'] = database_bind.bind_address
                    custom_options['destination'] = instance.address + '/32'
                    custom_options[
                        'l4-options']['dest-port-start'] = instance.port
                    data['rules'].append(custom_options)

                    LOG.debug(
                        "Creating bind for instance: {}".format(instance))

                    instance_bind = DatabaseInfraInstanceBind(instance=instance.address,
                                                              databaseinfra=databaseinfra,
                                                              bind_address=database_bind.bind_address,
                                                              instance_port=instance.port)
                    instance_bind.save()

                    LOG.debug("InstanceBind: {}".format(instance_bind))

                LOG.debug("Instance binds created!")

                for instance in databaseinfraattr_instances:
                    custom_options = copy.deepcopy(default_options)
                    custom_options['source'] = database_bind.bind_address
                    custom_options['destination'] = instance.ip + '/32'
                    custom_options['l4-options']['dest-port-start'] = port
                    data['rules'].append(custom_options)

                    LOG.debug(
                        "Creating bind for instance: {}".format(instance))

                    instance_bind = DatabaseInfraInstanceBind(instance=instance.ip,
                                                              databaseinfra=databaseinfra,
                                                              bind_address=database_bind.bind_address,
                                                              instance_port=port)
                    instance_bind.save()

                    LOG.debug(
                        "DatabaseInraAttrInstanceBind: {}".format(instance_bind))

                LOG.info("Data used on payload: {}".format(data))
                response = acl_client.grant_acl_for(environment=acl_environment,
                                                    vlan=acl_vlan,
                                                    payload=data)

                if 'job' in response:
                    monitor_acl_job(job_id=response['job'],
                                    database_bind=database_bind,
                                    instances=instances + databaseinfraattr_instances)
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
            action = 'deny'

            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password)

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
                acl_environment, acl_vlan = database_bind.bind_address.split(
                    '/')
                data = {"kind": "object#acl", "rules": []}
                default_options = {
                    "protocol": "tcp",
                    "source": "",
                    "destination": "",
                    "description": "{} access for database {} in {}".format(database_bind.bind_address,
                                                                            database.name,
                                                                            database.environment.name),
                    "action": action,
                    "l4-options": {"dest-port-start": "",
                                   "dest-port-op": "eq"}
                }

                LOG.info("Default options: {}".format(default_options))

                infra_instances_binds = DatabaseInfraInstanceBind.objects.filter(
                    databaseinfra=databaseinfra,
                    instance__in=instance_address_list,
                    bind_address=database_bind.bind_address)
                LOG.info(
                    "infra_instances_binds: {}".format(infra_instances_binds))
                for infra_instance_bind in infra_instances_binds:
                    custom_options = copy.deepcopy(default_options)
                    custom_options['source'] = database_bind.bind_address
                    custom_options[
                        'destination'] = infra_instance_bind.instance + '/32'
                    custom_options[
                        'l4-options']['dest-port-start'] = infra_instance_bind.instance_port
                    data['rules'].append(custom_options)

                LOG.info("Data used on payload: {}".format(data))
                acl_client.revoke_acl_for(environment=acl_environment,
                                          vlan=acl_vlan,
                                          payload=data)
                infra_instances_binds.delete()

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
            action = 'deny'

            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password)

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
                acl_environment, acl_vlan = database_bind.bind_address.split(
                    '/')
                data = {"kind": "object#acl", "rules": []}
                default_options = {
                    "protocol": "tcp",
                    "source": "",
                    "destination": "",
                    "description": "{} access for database {} in {}".format(database_bind.bind_address,
                                                                            database.name,
                                                                            database.environment.name),
                    "action": action,
                    "l4-options": {"dest-port-start": "",
                                   "dest-port-op": "eq"}
                }

                LOG.info("Default options: {}".format(default_options))

                infra_instances_binds = DatabaseInfraInstanceBind.objects.filter(
                    databaseinfra=databaseinfra,
                    instance__in=instance_address_list,
                    bind_address=database_bind.bind_address)
                LOG.info(
                    "infra_instances_binds: {}".format(infra_instances_binds))
                for infra_instance_bind in infra_instances_binds:
                    custom_options = copy.deepcopy(default_options)
                    custom_options['source'] = database_bind.bind_address
                    custom_options[
                        'destination'] = infra_instance_bind.instance + '/32'
                    custom_options[
                        'l4-options']['dest-port-start'] = infra_instance_bind.instance_port
                    data['rules'].append(custom_options)

                LOG.info("Data used on payload: {}".format(data))
                acl_client.revoke_acl_for(environment=acl_environment,
                                          vlan=acl_vlan,
                                          payload=data)
                infra_instances_binds.delete()

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):

        LOG.info("Running undo...")
        try:

            action = 'permit'

            database = workflow_dict['database']
            databaseinfra = workflow_dict['databaseinfra']

            acl_credential = get_credentials_for(environment=database.environment,
                                                 credential_type=CredentialType.ACLAPI)
            acl_client = AclClient(acl_credential.endpoint,
                                   acl_credential.user,
                                   acl_credential.password)

            instances = databaseinfra.instances.filter(
                future_instance__isnull=False)
            port = instances[0].port

            databaseinfraattr_instances = DatabaseInfraAttr.objects.filter(databaseinfra=databaseinfra,
                                                                           equivalent_dbinfraattr__isnull=False)
            instance_address_list = []
            for instance in instances:
                instance_address_list.append(instance.address)
            for instance in databaseinfraattr_instances:
                instance_address_list.append(instance.ip)

            for database_bind in database.acl_binds.all():
                acl_environment, acl_vlan = database_bind.bind_address.split(
                    '/')
                data = {"kind": "object#acl", "rules": []}
                default_options = {
                    "protocol": "tcp",
                    "source": "",
                    "destination": "",
                    "description": "{} access for database {} in {}".format(database_bind.bind_address,
                                                                            database.name,
                                                                            database.environment.name),
                    "action": action,
                    "l4-options": {"dest-port-start": "",
                                   "dest-port-op": "eq"}
                }

                LOG.info("Default options: {}".format(default_options))

                for instance in instances:
                    custom_options = copy.deepcopy(default_options)
                    custom_options['source'] = database_bind.bind_address
                    custom_options['destination'] = instance.address + '/32'
                    custom_options[
                        'l4-options']['dest-port-start'] = instance.port
                    data['rules'].append(custom_options)

                    LOG.debug(
                        "Creating bind for instance: {}".format(instance))

                    instance_bind = DatabaseInfraInstanceBind(instance=instance.address,
                                                              databaseinfra=databaseinfra,
                                                              bind_address=database_bind.bind_address,
                                                              instance_port=instance.port)
                    instance_bind.save()

                    LOG.debug("InstanceBind: {}".format(instance_bind))

                LOG.debug("Instance binds created!")

                for instance in databaseinfraattr_instances:
                    custom_options = copy.deepcopy(default_options)
                    custom_options['source'] = database_bind.bind_address
                    custom_options['destination'] = instance.ip + '/32'
                    custom_options['l4-options']['dest-port-start'] = port
                    data['rules'].append(custom_options)

                    LOG.debug(
                        "Creating bind for instance: {}".format(instance))

                    instance_bind = DatabaseInfraInstanceBind(instance=instance.ip,
                                                              databaseinfra=databaseinfra,
                                                              bind_address=database_bind.bind_address,
                                                              instance_port=port)
                    instance_bind.save()

                    LOG.debug(
                        "DatabaseInraAttrInstanceBind: {}".format(instance_bind))

                LOG.info("Data used on payload: {}".format(data))
                response = acl_client.grant_acl_for(environment=acl_environment,
                                                    vlan=acl_vlan,
                                                    payload=data)

                if 'job' in response:
                    monitor_acl_job(job_id=response['job'],
                                    database_bind=database_bind,
                                    instances=instances + databaseinfraattr_instances)
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
