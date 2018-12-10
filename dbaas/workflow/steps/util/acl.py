# -*- coding: utf-8 -*-
import requests
from base import BaseInstanceStep
from dbaas_aclapi.tasks import replicate_acl_for
from dbaas_aclapi.acl_base_client import AclClient
from dbaas_aclapi import helpers
from dbaas_aclapi.models import DatabaseInfraInstanceBind
from dbaas_aclapi.models import ERROR
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
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
        except IndexError:
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
    def source_instance(self):
        return self.infra.instances.filter(
            is_active=True, read_only=False
        ).first()

    @property
    def destination_instance(self):
        return self.instance

    def do(self):
        if self.acl_client is None:
            return
        replicate_acl_for(
            database=self.database,
            old_ip=self.source_instance.address,
            new_ip=self.destination_instance.address
        )


class ReplicateAclsMigrate(ReplicateAcls2NewInstance):

    @property
    def source_instance(self):
        return self.host_migrate.host

    @property
    def destination_instance(self):
        return self.host


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

    def add_acl_for(self, database):
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

        return None

    def do(self):
        if not self.database:
            return

        resp = self.add_acl_for(self.database)
        if resp and not resp.ok:
            raise CantSetACLError(resp.content)

    def undo(self):
        if not self.database:
            return
