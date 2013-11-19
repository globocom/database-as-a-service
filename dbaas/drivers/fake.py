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

def database_created(databaseinfra_name, database_name):
    return database_name in DATABASES_INFRA.get(databaseinfra_name, {})


class FakeDriver(BaseDriver):

    default_port = 12345

    def __get_database_infra(self):
        if self.databaseinfra.name not in DATABASES_INFRA:
            DATABASES_INFRA[self.databaseinfra.name] = {}
        return DATABASES_INFRA[self.databaseinfra.name]

    def get_connection(self):
        return "%s:%s" % (self.databaseinfra.instance.address, self.databaseinfra.instance.port)

    def create_database(self, database):
        instance_data = self.__get_database_infra()
        # if database.name in instance_data:
            # raise DatabaseAlreadyExists
        instance_data[database.name] = {}
        LOG.info('Created database %s', database)

    def remove_database(self, database):
        instance_data = self.__get_database_infra()
        del instance_data[database.name]
        LOG.info('Deleted database %s', database)

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        instance_data = self.__get_database_infra()
        # if credential.user in instance_data[credential.database.name]:
            # raise CredentialAlreadyExists
        instance_data[credential.database.name][credential.user] = credential.password
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
        instance_data[credential.database.name][credential.user] = credential.password
        LOG.info('Created user %s', credential)

    def check_status(self, instance=None):
        LOG.info('Check status')
        return True

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(databaseinfra_model=self.databaseinfra)
        LOG.info('Info')
        return databaseinfra_status

    def change_default_pwd(self, instance):
        LOG.info('Change default password')
