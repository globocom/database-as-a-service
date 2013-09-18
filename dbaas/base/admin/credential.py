# encoding: utf-8
from django_services import admin
from ..service.credential import CredentialService


class CredentialAdmin(admin.DjangoServicesAdmin):
    service_class = CredentialService
    search_fields = ['user', 'database__name', 'database__instance__name']
    list_filter = ["database",]
    list_display = ['user', 'database_name', 'instance_name']
    save_on_top = True

    def database_name(self, credential):
        return credential.database.name

    def instance_name(self, credential):
        return credential.database.instance.name
