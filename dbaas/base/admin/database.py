# encoding: utf-8
from django_services import admin
from ..service.database import DatabaseService


class DatabaseAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseService
