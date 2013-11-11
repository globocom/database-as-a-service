# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin as django_admin
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django_services import admin
from ..service.databaseinfra import DatabaseInfraService
from ..models import Instance
from util.html import render_progress_bar


class InstanceModelFormSet(BaseInlineFormSet):

    def clean(self):
        super(InstanceModelFormSet, self).clean()

        for error in self.errors:
            if error:
                return

        completed = 0
        for cleaned_data in self.cleaned_data:
            # form has data and we aren't deleting it.
            if cleaned_data and not cleaned_data.get('DELETE', False):
                completed += 1

        # example custom validation across forms in the formset:
        if completed  == 0:
            raise ValidationError({'instances': _("Specify at least one valid instance")})
        # elif completed > 1:
            # raise ValidationError({'instances': _("Currently, you can have only one instance per databaseinfra")})


class InstanceAdmin(django_admin.TabularInline):
    model = Instance
    fields = ('hostname', 'address', 'port', 'is_active', 'is_arbiter')
    # max_num = 1
    # can_delete = False
    extra = 1
    formset = InstanceModelFormSet


class DatabaseInfraAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseInfraService
    search_fields = ("name", "user", "instances__address",)
    list_display = ("name", "user", "instance", "capacity_bar")
    list_filter = ("engine",)
    save_on_top = True

    def capacity_bar(self, datainfra):
        return render_progress_bar(datainfra.used, datainfra.capacity)
    capacity_bar.short_description = "Capacity"
    capacity_bar.admin_order_field = 'capacity'

    inlines = [
        InstanceAdmin
    ]

