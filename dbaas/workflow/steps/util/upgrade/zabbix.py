# -*- coding: utf-8 -*-
from util import full_stack
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0012


class ZabbixStep(BaseStep):

    def __init__(self, instance):
        self.instance = instance

        integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
        environment = instance.databaseinfra.environment
        credentials = Credential.get_credentials(environment, integration)

        self.zabbix_provider = factory_for(
            databaseinfra=instance.databaseinfra,
            credentials=credentials
        )

    def __del__(self):
        self.zabbix_provider.logout()

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class DisableAlarms(ZabbixStep):

    def __unicode__(self):
        return "Disable Zabbix alarms..."

    def do(self):
        try:
            self.zabbix_provider.disable_alarms_to(self.instance.hostname.hostname)
            self.zabbix_provider.disable_alarms_to(self.instance.dns)
        except Exception:
            self.zabbix_provider.enable_alarms_to(self.instance.hostname.hostname)
            self.zabbix_provider.enable_alarms_to(self.instance.dns)

            return False, DBAAS_0012, full_stack()

        return True, None, None

    def undo(self):
        return True, None, None


class DestroyAlarms(ZabbixStep):

    def __unicode__(self):
        return "Destroying Zabbix alarms..."

    def do(self):
        try:
            self.zabbix_provider.delete_instance_monitors(
                self.instance.hostname.hostname
            )
            self.zabbix_provider.delete_instance_monitors(self.instance.dns)
        except Exception:
            return False, DBAAS_0012, full_stack()

        return True, None, None

    def undo(self):
        return True, None, None


class CreateAlarms(ZabbixStep):

    def __unicode__(self):
        return "Creating Zabbix alarms..."

    def do(self):
        try:
            self.zabbix_provider.create_instance_basic_monitors(
                self.instance.hostname
            )
            self.zabbix_provider.create_instance_monitors(self.instance)
        except Exception:
            return False, DBAAS_0012, full_stack()

        return True, None, None

    def undo(self):
        return True, None, None
