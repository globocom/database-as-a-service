# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.credential import CredentialService


class CredentialAdmin(admin.DjangoServicesAdmin):
    service_class = CredentialService
    search_fields = ("user", "database__name", "database__databaseinfra__name")
    list_filter = ("database", "database__databaseinfra",)
    list_display = ("user", "database", "databaseinfra_name")
    save_on_top = True

    def databaseinfra_name(self, credential):
        return credential.database.databaseinfra.name
    
    databaseinfra_name.admin_order_field = "database__databaseinfra__name"

    def get_readonly_fields(self, request, obj = None):

        if obj: #In edit mode
            return ('user', 'database',) + self.readonly_fields

        return self.readonly_fields
