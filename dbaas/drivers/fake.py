# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from drivers import BaseDriver, DatabaseInfraStatus
from drivers.errors import ConnectionError
from physical.models import Instance

LOG = logging.getLogger(__name__)

DATABASES_INFRA = {}
DATABASES_CREATED = {}


def database_created(databaseinfra_name, database_name):
    return database_name in DATABASES_INFRA.get(databaseinfra_name, {})


def database_created_list(database_name):
    return DATABASES_CREATED.get(database_name, None)


class FakeDriver(BaseDriver):

    default_port = 12345

    def __get_database_infra(self):
        if self.databaseinfra.name not in DATABASES_INFRA:
            DATABASES_INFRA[self.databaseinfra.name] = {}
        return DATABASES_INFRA[self.databaseinfra.name]

    def concatenate_instances(self):
        return ",".join(["%s:%s" % (instance.address, instance.port) for instance in self.databaseinfra.instances.exclude(instance_type=Instance.MONGODB_ARBITER).filter(is_active=True).all()])

    def get_connection(self, database=None):
        return "fake://%s" % self.concatenate_instances()

    def create_database(self, database):
        instance_data = self.__get_database_infra()
        instance_data[database.name] = {}
        DATABASES_CREATED[database.name] = database
        LOG.info('Created database %s', database)

    def remove_database(self, database):
        instance_data = self.__get_database_infra()
        del instance_data[database.name]
        LOG.info('Deleted database %s', database)

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        instance_data = self.__get_database_infra()
        instance_data[credential.database.name][
            credential.user] = credential.password
        LOG.info('Created user %s', credential)

    def remove_user(self, credential):
        instance_data = self.__get_database_infra()
        instance_data[credential.database.name].pop(credential.user, None)
        LOG.info('Deleted user %s', credential)

    def update_user(self, credential):
        LOG.info('Update user %s', credential)
        instance_data = self.__get_database_infra()
        instance_data[credential.database.name][
            credential.user] = credential.password
        LOG.info('Created user %s', credential)

    def check_status(self, instance=None):
        LOG.info('Check status')
        return True

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(
            databaseinfra_model=self.databaseinfra)
        LOG.info('Info')
        return databaseinfra_status

    def get_master_instance(self, ):
        instances = self.get_database_instances()
        masters = []
        for instance in instances:
            try:
                if self.check_instance_is_master(instance):
                    masters.append(instance)
            except ConnectionError:
                continue

        if masters:
            if len(masters) == 1:
                return masters[0]
            else:
                return masters
        else:
            return None

    def change_default_pwd(self, instance):
        LOG.info('Change default password')

    @classmethod
    def topology_name(cls):
        return ['fake']
