# encoding: utf-8
from django_services import admin
from ..service import EnvironmentService


class EnvironmentAdmin(admin.DjangoServicesAdmin):
    search_fields = ("name", )
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    save_on_top = True

