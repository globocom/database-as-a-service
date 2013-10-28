# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import service
from .. import models
from drivers import factory_for


class CredentialService(service.CRUDService):
    model_class = models.Credential

    def __get_engine__(self, credential):
        return factory_for(credential.database.databaseinfra)

    def create(self, credential):
        super(CredentialService, self).create(credential)

        engine = self.__get_engine__(credential)
        engine.create_user(credential)

    def update(self, credential):
        old_credential = self.get(credential.pk)

        # FIXME
        engine = self.__get_engine__(old_credential)
        engine.remove_user(old_credential)

        super(CredentialService, self).update(credential)
        engine.create_user(credential)

    def delete(self, credential):
        engine = self.__get_engine__(credential)
        engine.remove_user(credential)

        super(CredentialService, self).delete(credential)
