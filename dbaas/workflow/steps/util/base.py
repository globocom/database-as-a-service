# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import requests
from collections import namedtuple
from time import sleep

from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible

from dbaas_credentials.models import CredentialType
from util import get_credentials_for, AuthRequest
from physical.models import Vip
from util import check_ssh


LOG = logging.getLogger(__name__)
CHECK_SECONDS = 10
CHECK_ATTEMPTS = 30


class CantSetACLError(Exception):
    pass


@python_2_unicode_compatible
class BaseInstanceStep(object):

    def __str__(self):
        return "I am a step"

    def __init__(self, instance):
        self.instance = instance
        self._vip = None
        self._driver = None

    @property
    def infra(self):
        return self.instance.databaseinfra

    @property
    def driver(self):
        if self._driver is None:
            self._driver = self.infra.get_driver()

        return self._driver

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
    def upgrade_patch(self):
        upgrade_patch = self.database.upgrades_patch.last()
        if upgrade_patch and upgrade_patch.is_running:
            return upgrade_patch

    @property
    def engine_migration(self):
        engine_migration = self.database.engine_migrations.last()

        if engine_migration and engine_migration.is_running:
            return engine_migration

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

    def _get_vip(self, vip_identifier, env):
        client = VipProviderClient(env)
        return client.get_vip(vip_identifier)

    @property
    def vip(self):
        if self._vip:
            return self._vip
        vip_identifier = Vip.objects.get(infra=self.infra).identifier
        self._vip = self._get_vip(vip_identifier, self.infra.environment)
        return self._vip

    @vip.setter
    def vip(self, vip):
        self._vip = vip

    @property
    def future_vip(self):
        original_vip = Vip.objects.get(infra=self.infra)
        future_vip_identifier = Vip.original_objects.get(
            infra=self.infra,
            original_vip=original_vip
        ).identifier
        return self._get_vip(future_vip_identifier, self.environment)

    def __is_instance_status(self, expected, attempts=None):
        if self.host_migrate and self.instance.hostname.future_host:
            self.instance.address = self.instance.hostname.future_host.address
        for _ in range(attempts or CHECK_ATTEMPTS):
            try:
                status = self.driver.check_status(instance=self.instance)
            except Exception as e:
                LOG.debug('{} is down - {}'.format(self.instance, e))
                status = False

            if status == expected:
                return True
            else:
                sleep(CHECK_SECONDS)
        return False

    def vm_is_up(self, attempts=2, wait=5, interval=10):
        return check_ssh(
            self.host,
            retries=attempts,
            wait=wait,
            interval=interval
        )

    def database_is_up(self, attempts=None):
        return self.__is_instance_status(True, attempts=attempts)

    def database_is_down(self, attempts=None):
        return self.__is_instance_status(False, attempts=attempts)

    def run_script(self, script, host=None):
        from util import run_script

        return run_script(self, script, host or self.host)

    @property
    def is_first_instance(self):
        return self.instance == self.infra.instances.first()

    @property
    def is_last_instance(self):
        return self.instance == self.infra.instances.last()

    @property
    def is_persisted(self):
        return self.plan.has_persistence is True

    @property
    def is_database_instance(self):
        return self.instance in self.driver.get_database_instances()

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


class VipProviderClient(object):
    credential_type = CredentialType.VIP_PROVIDER
    auth_request = AuthRequest()

    def __init__(self, env):
        self.env = env
        self._credential = None

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                self.env, self.credential_type
            )
        return self._credential

    def get_vip(self, vip_id):
        api_host_url = '/{}/{}/vip/{}'.format(
            self.credential.project,
            self.env.name,
            vip_id
        )
        resp = self.auth_request.get(
            self.credential,
            '{}{}'.format(self.credential.endpoint, api_host_url)
        )
        if resp.ok:
            vm = resp.json()
            return namedtuple('VipProperties', vm.keys())(*vm.values())

    def is_vip_healthy(self, vip_id):
        url = '{}/{}/{}/vip/healthy'.format(
            self.credential.endpoint,
            self.credential.project,
            self.env.name,
        )
        data = {
            'vip_id': vip_id
        }
        resp = self.auth_request.post(
            self.credential,
            url,
            json=data
        )

        if resp.ok:
            resp = resp.json()
            return resp.get('healthy', False)


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


class ACLFromHellClient(object):

    def __init__(self, env):
        self.environment = env
        self._credential = None

    @property
    def credential(self):
        if not self._credential:
            try:
                self._credential = get_credentials_for(
                    self.environment, CredentialType.ACLFROMHELL
                )
            except IndexError:
                raise Exception(
                    "Credential ACLFROMHELL for env {} not found".format(
                        self.environment.name
                    )
                )

        return self._credential

    def _request(self, action, url, **kw):
        return action(
            url,
            auth=(self.credential.user, self.credential.password),
            **kw
        )

    def get_rule(self, database, app_name=None, extra_params=None):
        params = {
            'metadata.owner': 'dbaas',
            'metadata.service-name': self.credential.project,
            'metadata.instance-name': database.name,
        }
        if app_name:
            params.update({'source.tsuruapp.appname': app_name})
        if extra_params:
            params.update(extra_params)


        LOG.debug("Tsuru get rule for {} params:{}".format(
            database.name, params))

        return self._request(
            requests.get,
            self.credential.endpoint,
            params=params,
        )

    @staticmethod
    def _get_vip_dns(infra):
        return infra.endpoint_dns.split(':')[0]

    def _need_add_acl_for_vip(self, database, app_name):
        infra = database.infra
        if infra.vips.exists():
            vip_dns = self._get_vip_dns(infra)
            resp = self.get_rule(
                database,
                app_name,
                extra_params={'destination.externaldns.name': vip_dns}
            )
            if resp and not resp.ok:
                LOG.info("ACLFROMHELL Add VIP ACL for {}: {}".format(
                    vip_dns, resp.content)
                )
            return not (resp and resp.ok and resp.json())
        return False

    def add_acl_for_vip_if_needed(self, database, app_name):

        if self._need_add_acl_for_vip(database, app_name):
            vip_dns = self._get_vip_dns(database.infra)

            vip_resp = self.add_acl(
                database,
                app_name,
                vip_dns
            )
            if not vip_resp:
                raise CantSetACLError("Cant set acl for VIP {} error: {}".format(
                    vip_dns,
                    vip_resp.content
                ))

    def add_acl(self, database, app_name, hostname):
        infra = database.infra
        driver = infra.get_driver()

        payload = {
            "source": {
                "tsuruapp": {
                    "appname": app_name
                }
            },
            "destination": {
                "externaldns": {
                    "name": hostname,
                    "ports": map(
                        lambda p: {
                            'protocol': 'tcp',
                            'port': p
                        },
                        driver.ports
                    )
                }
            },
            "target": "accept",
            "metadata": {
                'owner': 'dbaas',
                "service-name": self.credential.project,
                "instance-name": database.name
            }
        }

        LOG.info("Tsuru Add ACL: payload for host {}:{}".format(
            hostname, payload))
        resp = self._request(
            requests.post,
            self.credential.endpoint,
            json=payload,
        )
        if not resp.ok:
            msg = "Error bind {} database on {} environment: {}".format(
                database.name, self.environment, resp.content
            )
            LOG.info(msg)
        LOG.info("Tsuru Add ACL Status for host {}: {}".format(
            hostname, resp.status_code
        ))

        return resp

    def remove_acl(self, database, app_name):

        resp = self.get_rule(database, app_name)
        if not resp.ok:
            msg = "Rule not found for {}.".format(
                database.name)
            LOG.error(msg)

        rules = resp.json()
        for rule in rules:
            rule_id = rule.get('RuleID')
            host = rule.get('Destination', {}).get('ExternalDNS', {}).get('Name')
            if rule_id:
                LOG.info('Tsuru Unbind App removing rule for {}'.format(host))
                resp = self._request(
                    requests.delete,
                    '{}/{}'.format(self.credential.endpoint, rule_id)
                )
                if not resp.ok:
                    msg = "Error on delete rule {} for {}.".format(
                        rule_id, host)
                    LOG.error(msg)
        return None
