# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
# from django.utils.translation import ugettext_lazy as _
from ..service.database import DatabaseService
from ..forms import DatabaseForm


class DatabaseAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseService
    search_fields = ("name", "instance__name")
    list_display = ("name", "instance",)
    list_filter = ("instance", "product",)
    change_form_template = "logical/database_change_form.html"
    fieldsets = (
        (None, {
            'fields': ('name', 'product')
            }
        ),
        ('reuse_instance', {
            'fields': ('instance',),
            'classes': ('reuse_instance',),
            },
        ),
        ('new_instance', {
            'fields': ('engine', 'plan'),
            'classes': ('new_instance',),
            },
        )
    )
    form = DatabaseForm


    def get_readonly_fields(self, request, obj = None):
        """
        if in edit mode, name is readonly.
        """
        if obj: #In edit mode
            return ('name',) + self.readonly_fields

        return self.readonly_fields

    # def add_view(self, request, form_url='', extra_context=None, **kwargs):
    #     return super(DatabaseAdmin, self).add_view(request, form_url, extra_context, **kwargs)


