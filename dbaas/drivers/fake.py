# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from . import BaseDriver, DatabaseInfraStatus, DatabaseAlreadyExists, CredentialAlreadyExists, InvalidCredential

LOG = logging.getLogger(__name__)

# {
#   databaseinfra_name: {
#       database_name: {
#           database_user: pwd
#       }
#   }
# }
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

    def __concatenate_instances(self):
        return ",".join(["%s:%s" % (instance.address, instance.port) for instance in self.databaseinfra.instances.filter(is_arbiter=False, is_active=True).all()])

    def get_connection(self, database=None):
        return "fake://%s" % self.__concatenate_instances()

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
        # if credential.user in instance_data[credential.database.name]:
        # raise CredentialAlreadyExists
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
        # if credential.user not in instance_data[credential.database.name]:
        # raise InvalidCredential
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

    def change_default_pwd(self, instance):
        LOG.info('Change default password')
