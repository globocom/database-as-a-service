# -*- coding: utf-8 -*-
from base import BaseInstanceStep
from dbaas_aclapi.tasks import replicate_acl_for
from dbaas_aclapi.acl_base_client import AclClient
from dbaas_credentials.models import CredentialType
from util import get_credentials_for, GetCredentialException
from workflow.steps.util.base import ACLFromHellClient

import logging

LOG = logging.getLogger(__name__)


class CantSetACLError(Exception):
    pass


class ACLStep(BaseInstanceStep):

    def __init__(self, instance):
        super(ACLStep, self).__init__(instance)

        try:
            acl_credential = get_credentials_for(
                environment=self.environment,
                credential_type=CredentialType.ACLAPI)
        except (IndexError, GetCredentialException):
            self.acl_client = None
        else:
            self.acl_client = AclClient(
                acl_credential.endpoint,
                acl_credential.user,
                acl_credential.password,
                self.environment)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class ReplicateAcls2NewInstance(ACLStep):

    def __unicode__(self):
        return "Replicating ACLs..."

    @property
    def source_host(self):
        return self.infra.instances.filter(
            is_active=True, read_only=False
        ).first().hostname

    @property
    def destination_host(self):
        return self.instance.hostname

    def do(self):
        if self.acl_client is None:
            return
        replicate_acl_for(
            database=self.database,
            old_ip=self.source_host.address,
            new_ip=self.destination_host.address,
            old_sa=self.source_host.infra.service_account,
            new_sa=self.destination_host.infra.service_account
        )


class ReplicateAclsMigrate(ReplicateAcls2NewInstance):

    @property
    def source_host(self):
        return self.host_migrate.host

    @property
    def destination_host(self):
        return self.host


class ReplicateVipAclsMigrate(ACLStep):
    def __unicode__(self):
        return "Replicating VIP ACLs..."

    def do(self):
        if self.acl_client is None:
            return
        replicate_acl_for(
            database=self.database,
            old_ip=self.vip.vip_ip,
            new_ip=self.future_vip.vip_ip,
            old_sa=self.infra.service_account,
            new_sa=self.infra.service_account
        )


class BindNewInstance(ACLStep):

    def __unicode__(self):
        return "Binding new instance ..."

    def __init__(self, instance):
        super(BindNewInstance, self).__init__(instance)
        self.instances = [self.instance]
        self.instance_address_list = [self.instance.address]

    @property
    def acl_from_hell_client(self):
        return ACLFromHellClient(self.environment)

    def get_rule(self):
        resp = self.acl_from_hell_client.get_rule(self.database)

        if resp.ok:
            return resp.json()

        return None

    def add_acl_for_vip(self, database, app_name):
        self.acl_from_hell_client.add_acl_for_vip_if_needed(
            database, app_name
        )

    def add_acl_for_host(self, database, app_name):
        resp = self.acl_from_hell_client.add_acl(
            database, app_name, self.host.hostname
        )
        if not resp.ok:
            raise CantSetACLError(resp.content)

    def add_acl_for(self, database):
        tsuru_rules = self.get_rule()
        apps_name = []
        for rule in tsuru_rules:
            if rule.get('Removed'):
                continue
            app_name = rule.get('Source', {}).get('TsuruApp', {}).get('AppName')
            if not app_name:
                raise CantSetACLError("App name not found on data")
            if app_name in apps_name:
                continue
            apps_name.append(app_name)
            self.add_acl_for_vip(database, app_name)
            self.add_acl_for_host(database, app_name)

        '''
        tsuru_rules = self.get_rule()
        if tsuru_rules:
            rule = tsuru_rules[0]
            app_name = rule.get('Source', {}).get('TsuruApp', {}).get('AppName')
            if app_name:
                self.acl_from_hell_client.add_acl_for_vip_if_needed(
                    database,
                    app_name
                )
                return self.acl_from_hell_client.add_acl(
                    database,
                    app_name,
                    self.host.hostname
                )
            else:
                raise CantSetACLError("App name not found on data")
        '''

        return None

    def do(self):
        if not self.database:
            return

        self.add_acl_for(self.database)
        '''
        resp = self.add_acl_for(self.database)
        if resp and not resp.ok:
            raise CantSetACLError(resp.content)
        '''

    def undo(self):
        pass


class BindNewInstanceDatabaseMigrate(BindNewInstance):
    def add_acl_for_vip(self, database, app_name):
        vips = []
        if self.vip:
            vips.append(self.vip.vip_ip)
        if self.future_vip:
            vips.append(self.future_vip.vip_ip)
        for vip_address in vips:
            resp = self.acl_from_hell_client.add_acl(
                database, app_name, vip_address
            )
            if not resp.ok:
                raise CantSetACLError(resp.content)

    def add_acl_for_host(self, database, app_name):
        hosts = [self.instance.hostname.address, self.host.hostname.address]
        for host_address in hosts:
            resp = self.acl_from_hell_client.add_acl(
                database, app_name, host_address
            )
            if not resp.ok:
                raise CantSetACLError(resp.content)