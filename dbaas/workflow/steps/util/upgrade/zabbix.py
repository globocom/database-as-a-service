# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0012

LOG = logging.getLogger(__name__)


class ZabbixStep(BaseStep):

    zabbix_provider = None

    def build_zabbix_provider(self, instance):
        integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
        environment = instance.databaseinfra.environment
        credentials = Credential.get_credentials(environment, integration)

        return factory_for(
            databaseinfra=instance.databaseinfra,
            credentials=credentials
        )

    def zabbix_logout(self):
        if self.zabbix_provider:
            self.zabbix_provider.logout()

    def do(self, instance):
        raise NotImplementedError

    def undo(self, instance):
        raise NotImplementedError


class DisableAlarms(ZabbixStep):

    def __unicode__(self):
        return "Disable Zabbix alarms..."

    def do(self, instance):
        try:
            zabbix_provider = self.build_zabbix_provider(instance)
            zabbix_provider.disable_alarms_to(instance.hostname.hostname)
            zabbix_provider.disable_alarms_to(instance.dns)
        except Exception:
            if zabbix_provider:
                zabbix_provider.enable_alarms_to(instance.hostname.hostname)
                zabbix_provider.enable_alarms_to(instance.dns)


            return False, DBAAS_0012, full_stack()
        finally:
            self.zabbix_logout()

        return True, None, None

    def undo(self, instance):
        return True, None, None


class DestroyAlarms(ZabbixStep):

    def __unicode__(self):
        return "Destroying Zabbix alarms..."

    def do(self, instance):
        try:
            zabbix_provider = self.build_zabbix_provider(instance)
            zabbix_provider.delete_instance_monitors(instance.hostname.hostname)
            zabbix_provider.delete_instance_monitors(instance.dns)
        except Exception:
            return False, DBAAS_0012, full_stack()
        finally:
            self.zabbix_logout()

        return True, None, None

    def undo(self, instance):
        return True, None, None


class CreateAlarms(ZabbixStep):

    def __unicode__(self):
        return "Creating Zabbix alarms..."

    def do(self, instance):
        try:
            zabbix_provider = self.build_zabbix_provider(instance)
            zabbix_provider.create_instance_basic_monitors(
                instance.hostname
            )
            zabbix_provider.create_instance_monitors(instance)
        except Exception:
            return False, DBAAS_0012, full_stack()
        finally:
            self.zabbix_logout()

        return True, None, None

    def undo(self, instance):
        return True, None, None
