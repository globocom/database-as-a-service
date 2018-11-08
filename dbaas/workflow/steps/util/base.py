# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible
from collections import namedtuple
from dbaas_credentials.models import CredentialType
from util import get_credentials_for

LOG = logging.getLogger(__name__)


@python_2_unicode_compatible
class BaseStep(object):

    def __str__(self):
        return "I am a step"

    def do(self, workflow_dict):
        raise NotImplementedError

    def undo(self, workflow_dict):
        raise NotImplementedError


@python_2_unicode_compatible
class BaseInstanceStep(object):

    def __str__(self):
        return "I am a step"

    def __init__(self, instance):
        self.instance = instance

    @property
    def infra(self):
        return self.instance.databaseinfra

    @property
    def database(self):
        return self.infra.databases.first()

    @property
    def plan(self):
        return self.infra.plan

    @property
    def engine(self):
        return self.infra.engine

    @property
    def disk_offering(self):
        return self.infra.disk_offering

    @property
    def host(self):
        try:
            host = self.instance.hostname
        except ObjectDoesNotExist:
            LOG.info(
                'Instance {} does not have hostname'.format(self.instance))
            return

        if self.host_migrate and host.future_host:
            return host.future_host
        return host

    @property
    def environment(self):
        if self.host_migrate:
            return self.host_migrate.environment
        return self.infra.environment

    @property
    def restore(self):
        restore = self.database.database_restore.last()
        if restore and restore.is_running:
            return restore

    @property
    def snapshot(self):
        try:
            return self.restore.group.backups.get(instance=self.instance)
        except ObjectDoesNotExist:
            return

    @property
    def latest_disk(self):
        return self.instance.hostname.volumes.last()

    @property
    def resize(self):
        resize = self.database.resizes.last()
        if resize and resize.is_running:
            return resize

    @property
    def is_valid(self):
        return True

    @property
    def can_run(self):
        return True

    @property
    def upgrade(self):
        upgrade = self.database.upgrades.last()
        if upgrade and upgrade.is_running:
            return upgrade

    @property
    def host_migrate(self):
        if not self.instance.hostname_id:
            return

        migrate = self.instance.hostname.migrate.last()
        if migrate and migrate.is_running:
            return migrate

    @property
    def reinstall_vm(self):
        reinstall_vm = self.database.reinstall_vm.last()
        if reinstall_vm and reinstall_vm.is_running:
            return reinstall_vm

    @property
    def create(self):
        return self._get_running_task(self.infra.databases_create)

    @property
    def destroy(self):
        return self._get_running_task(self.infra.databases_destroy)

    @property
    def has_database(self):
        return bool(self.database)

    @staticmethod
    def _get_running_task(manager):
        task = manager.last()
        if task and task.is_running:
            return task

    @property
    def has_database(self):
        return bool(self.database)

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class BaseInstanceStepMigration(BaseInstanceStep):

    @property
    def host(self):
        host = super(BaseInstanceStepMigration, self).host
        return host.future_host if host else None

    @property
    def environment(self):
        environment = super(BaseInstanceStepMigration, self).environment
        return environment.migrate_environment

    @property
    def plan(self):
        plan = super(BaseInstanceStepMigration, self).plan
        return plan.migrate_plan

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class HostProviderClient(object):
    credential_type = CredentialType.HOST_PROVIDER

    def __init__(self, env):
        self.env = env
        self._credential = None

    def _request(self, action, url, **kw):
        auth = (self.credential.user, self.credential.password,)
        kw.update(**{'auth': auth} if self.credential.user else {})
        return action(url, **kw)

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                self.env, self.credential_type
            )
        return self._credential

    def get_vm_by_host(self, host):
        api_host_url = '/{}/{}/host/{}'.format(
            self.credential.project,
            self.env.name,
            host.identifier
        )
        resp = self._request(
            requests.get,
            '{}{}'.format(self.credential.endpoint, api_host_url)
        )
        if resp.ok:
            vm = resp.json()
            return namedtuple('VMProperties', vm.keys())(*vm.values())

    def get_offering_id(self, cpus, memory):
        api_host_url = '/{}/{}/credential/{}/{}'.format(
            self.credential.project,
            self.env.name,
            cpus,
            memory
        )
        resp = self._request(
            requests.get,
            '{}{}'.format(self.credential.endpoint, api_host_url
        ))
        if resp.ok:
            data = resp.json()
            return data.get('offering_id')
