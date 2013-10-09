# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.database import DatabaseService


class DatabaseAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseService
    search_fields = ("name", "instance__name")
    list_display = ("name", "instance",)
    list_filter = ("instance", "product",)
    save_on_top = True
    
    def get_readonly_fields(self, request, obj = None):
        """
        if in edit mode, name is readonly.
        """
        if obj: #In edit mode
            return ('name',) + self.readonly_fields

        return self.readonly_fields

